"""Build the self-contained portfolio dashboard (one HTML file) from the JSON in data/.

The page needs no server, no network and no claude.ai runtime: every number it shows is
embedded at build time, so it opens straight from disk (or a phone's Files app). Rebuild it after
each refresh with ``ngxprices portfolio dashboard``.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from . import portfolio as P

MARK = "/*__DASHBOARD_DATA__*/null"
# Fields of accounts.json the page shows. Broker account, customer and CSCS numbers stay out.
ACCOUNT_FIELDS = ("account", "broker", "short", "confirmed", "note")
HISTORY_FROM = "2025-12-01"


def _load(data_dir, name, default=None):
    p = Path(data_dir) / name
    return json.loads(p.read_text()) if p.exists() else default


def _source(data_dir, date) -> str | None:
    """How the closes for ``date`` were sourced (official files or the live feed), from price_history."""
    seen = sorted({r.get("source") or "" for r in _load(data_dir, "price_history.json", []) if r["date"] == date})
    return "; ".join(x for x in seen if x) or None


def _history(data_dir, tickers: set[str]) -> dict:
    """Compact closes and volumes per ticker from HISTORY_FROM: {ticker: {d: [...], c: [...], v: [...]}}."""
    out: dict = {}
    for r in sorted(_load(data_dir, "price_history.json", []), key=lambda r: (r["ticker"], r["date"])):
        if r["ticker"] not in tickers or r["date"] < HISTORY_FROM or r.get("close") is None:
            continue
        h = out.setdefault(r["ticker"], {"d": [], "c": [], "v": []})
        h["d"].append(r["date"])
        h["c"].append(r["close"])
        h["v"].append(r.get("volume"))
    return out


def build_data(data_dir="data") -> dict:
    pf = P.latest_prices_file(data_dir)
    date = pf.stem.split("_", 1)[1] if pf else None
    holdings = _load(data_dir, "holdings.json", [])
    plan = _load(data_dir, "plan_2_2M.json", [])
    facts = _load(data_dir, "stock_facts.json", [])
    webinar = _load(data_dir, "webinar_levels.json", [])
    tickers = {h["ticker"] for h in holdings} | {r["ticker"] for r in plan + facts + webinar}
    try:
        status = P.rules_status(data_dir)
    except Exception as e:  # the page still shows everything else
        status = [{"error": f"{type(e).__name__}: {e}"}]
    return {
        "built": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "date": date,
        "source": _source(data_dir, date) if date else None,
        "prices": json.loads(pf.read_text()) if pf else [],
        "holdings": holdings,
        "accounts": [{k: a.get(k) for k in ACCOUNT_FIELDS} for a in _load(data_dir, "accounts.json", [])],
        "transactions": _load(data_dir, "transactions.json", []),
        "daily": _load(data_dir, "daily_log.json", []),
        "rules": _load(data_dir, "rules.json", {}),
        "status": status,
        "plan": plan,
        "results": _load(data_dir, "company_results.json", []),
        "facts": facts,
        "webinar": webinar,
        "history": _history(data_dir, tickers),
        "volume": P.volume_highlights(data_dir, date) if date else [],
        "trades": _trades(data_dir),
        "trade_plan": _load(data_dir, "trades.json", {}),
    }


def _trades(data_dir):
    from .trades import trade_status
    try:
        return trade_status(data_dir)
    except Exception as e:  # the page still shows everything else
        return [{"error": f"{type(e).__name__}: {e}"}]


def build(data_dir="data", template="dashboard/template.html", out="dashboard/index.html") -> dict:
    html = Path(template).read_text()
    if MARK not in html:
        raise ValueError(f"{template} has no {MARK} placeholder")
    data = build_data(data_dir)
    # "</" can't appear inside a <script>; escaping the slash keeps the JSON identical.
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"), default=str).replace("</", "<\\/")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(html.replace(MARK, blob))
    return {"out": str(out), "date": data["date"], "holdings": len(data["holdings"]),
            "days": len(data["daily"]), "bytes": Path(out).stat().st_size}
