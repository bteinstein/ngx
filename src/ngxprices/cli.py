"""Command line interface: ``ngxprices fetch|range|files|validate``."""
from __future__ import annotations

import argparse
import json
import sys

from .core import BASIC_FIELDS, FIELDS, get_daily_prices, get_range, list_files, validate, write_csv
from .http import Fetcher


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ngxprices", description="NGX daily equity prices, volume and metadata")
    ap.add_argument("--cache", help="cache directory (default ~/.cache/ngxprices or $NGXPRICES_CACHE)")
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between requests (default 1)")
    ap.add_argument("--fields", choices=["full", "basic"], default="full",
                    help="full = prices, volume, size, fundamentals, dividends (default); basic = v0.1 columns")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("fetch", help="prices for one date")
    p.add_argument("--date", required=True, help="YYYY-MM-DD or DD-MM-YYYY")
    p.add_argument("--out", help="CSV path (default stdout)")
    p = sub.add_parser("range", help="prices for every trading day in a range")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--out", help="CSV path (default stdout)")
    p = sub.add_parser("files", help="list documents NGX published for a date")
    p.add_argument("--date", required=True)
    p = sub.add_parser("validate", help="cross-check a day's files (closes, volumes, market caps) as JSON")
    p.add_argument("--date", required=True)
    p.add_argument("--details", action="store_true", help="list every mismatch, not just counts")
    a = ap.parse_args(argv)

    f = Fetcher(cache_dir=a.cache, delay=a.delay)
    if a.cmd == "files":
        json.dump(list_files(a.date, f), sys.stdout, indent=1)
        print()
        return 0
    if a.cmd == "validate":
        v = validate(a.date, f)
        if not a.details:
            for k, x in v.items():
                if isinstance(x, dict):
                    v[k] = {kk: (len(vv) if isinstance(vv, list) else vv) for kk, vv in x.items()}
        json.dump(v, sys.stdout, indent=1)
        print()
        return 0
    fields = FIELDS if a.fields == "full" else BASIC_FIELDS
    rows = get_daily_prices(a.date, f) if a.cmd == "fetch" else get_range(a.start, a.end, f)
    if a.cmd == "fetch" and not rows:
        print(f"No files published for {a.date} (non-trading day or not yet published)", file=sys.stderr)
        return 1
    if a.out:
        write_csv(rows, a.out, fields)
        print(f"wrote {len(rows)} rows to {a.out}", file=sys.stderr)
    else:
        import csv
        w = csv.DictWriter(sys.stdout, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return 0


def _entry() -> int:
    try:
        return main()
    except BrokenPipeError:  # e.g. `ngxprices fetch ... | head`
        import os
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 0


if __name__ == "__main__":
    sys.exit(_entry())
