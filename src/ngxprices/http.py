"""HTTP helpers: polite delay, retries and an on-disk download cache."""
from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path

import requests

DEFAULT_CACHE = Path(os.environ.get("NGXPRICES_CACHE", Path.home() / ".cache" / "ngxprices"))
USER_AGENT = "ngxprices/0.1 (+research; polite)"


class Fetcher:
    def __init__(self, cache_dir: str | Path | None = None, delay: float = 1.0,
                 retries: int = 3, timeout: float = 60.0):
        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE
        self.delay = delay
        self.retries = retries
        self.timeout = timeout
        self._last = 0.0
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT

    def _wait(self):
        gap = time.monotonic() - self._last
        if gap < self.delay:
            time.sleep(self.delay - gap)
        self._last = time.monotonic()

    def get(self, url: str, headers: dict | None = None, allow_404: bool = False) -> requests.Response | None:
        err: Exception | None = None
        for attempt in range(self.retries):
            self._wait()
            try:
                r = self.session.get(url, headers=headers, timeout=self.timeout)
                if r.status_code == 404 and allow_404:
                    return None
                if r.status_code >= 500 or r.status_code == 429:
                    raise requests.HTTPError(f"HTTP {r.status_code} for {url}")
                r.raise_for_status()
                return r
            except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
                err = e
                if isinstance(e, requests.HTTPError) and e.response is not None and 400 <= e.response.status_code < 500 \
                        and e.response.status_code != 429:
                    break
                time.sleep(2 ** attempt)
        raise RuntimeError(f"GET failed after {self.retries} attempts: {url}: {err}")

    def cache_path(self, url: str, subdir: str, name: str) -> Path:
        h = hashlib.sha1(url.encode()).hexdigest()[:10]
        return self.cache_dir / subdir / f"{h}_{name}"

    def download(self, url: str, subdir: str, name: str) -> Path | None:
        """Download url into the cache (once). Returns None on 404."""
        p = self.cache_path(url, subdir, name)
        if p.exists() and p.stat().st_size > 0:
            return p
        r = self.get(url, allow_404=True)
        if r is None:
            return None
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".part")
        tmp.write_bytes(r.content)
        tmp.replace(p)
        return p
