"""Command line interface: ``ngxprices fetch|range|live|files|validate|portfolio``."""
from __future__ import annotations

import argparse
import json
import sys

from .core import (BASIC_FIELDS, FIELDS, LIVE_FIELDS, get_daily_prices, get_live, get_range, list_files,
                   validate, write_csv)
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
    p = sub.add_parser("live", help="live prices (NGX: 30-minute delay) plus latest end-of-day metadata")
    p.add_argument("--out", help="CSV path (default stdout)")
    p.add_argument("--meta-date", help="take shares/EPS/P/E/dividends from this date (default: latest available)")
    p = sub.add_parser("portfolio", help="update and check the portfolio data in data/")
    psub = p.add_subparsers(dest="pcmd", required=True)
    q = psub.add_parser("refresh", help="add/refresh a day (official files, else live feed) and upgrade earlier live days")
    q.add_argument("--date", help="trading day (default: the latest)")
    q.add_argument("--data-dir", default="data")
    q.add_argument("--json", action="store_true", help="print the summary as JSON")
    q = psub.add_parser("losers", help="watchlist stocks against their triggers (latest prices file)")
    q.add_argument("--data-dir", default="data")
    q.add_argument("--json", action="store_true")
    q = psub.add_parser("stage", help="copy the dashboard's three data files into a folder, with dated names")
    q.add_argument("--data-dir", default="data")
    q.add_argument("--out", required=True)
    q = psub.add_parser("dashboard", help="build the self-contained dashboard page from data/")
    q.add_argument("--data-dir", default="data")
    q.add_argument("--template", default="dashboard/template.html")
    q.add_argument("--out", default="dashboard/index.html")
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
    if a.cmd == "portfolio":
        return _portfolio(a, f)
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
    if a.cmd == "live":
        rows, info = get_live(f, a.meta_date)
        print(f"live prices for {info['trade_date']} ({info['stocks']} stocks); metadata from "
              f"{info['metadata_date']}", file=sys.stderr)
        for n in info["notes"]:
            print("note: " + n, file=sys.stderr)
        fields = LIVE_FIELDS if a.fields == "full" else BASIC_FIELDS
        if a.out:
            write_csv(rows, a.out, fields)
            print(f"wrote {len(rows)} rows to {a.out}", file=sys.stderr)
        else:
            import csv
            w = csv.DictWriter(sys.stdout, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        return 0
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


def _naira(v) -> str:
    return ("-" if v < 0 else "+") + "\u20a6" + f"{abs(v):,.0f}"


def _portfolio(a, f) -> int:
    from . import portfolio as P
    if a.pcmd == "dashboard":
        from . import dashboard as D
        print(json.dumps(D.build(a.data_dir, a.template, a.out), indent=1))
        return 0
    if a.pcmd == "stage":
        print(json.dumps(P.stage_dashboard_files(a.data_dir, a.out), indent=1))
        return 0
    if a.pcmd == "losers":
        rows = P.watchlist_status(a.data_dir)
        if a.json:
            print(json.dumps(rows, indent=1))
            return 0
        for w in rows:
            if "status" in w:
                extra = f"  {w['off_peak_pct']:+.1f}% from peak" if w["trail_level"] else ""
                if w.get("price_note"):
                    extra += f"\n            REAL PRICE {w['real_price']:,.2f}: {w['price_note']}"
                for x in w.get("exit_signals", []):
                    extra += "\n            EXIT: " + x
                sig = w.get("tolerance_signals", []) + w.get("general_signs", [])
                if sig and w["light"] != "red":
                    extra += "\n            " + "; ".join(sig)
                for x in w.get("take_profit", []):
                    extra += "\n            TAKE PROFIT: " + x["text"]
                if w.get("accounts"):
                    extra += "\n            HELD IN: " + P.accounts_text(w["accounts"])
                print(f"{w['ticker']:<11} {(w.get('horizon') or '-')[:5]:<5} {w['light'].upper():<6} {w['status'].upper():<6} close {w['close']:>10,.2f}  cost {w['avg_cost']:>10,.2f}"
                      f" ({w['gain_pct']:+.1f}%)  {w['rule']} {w['trigger']:>10,.2f} ({w['gap_pct']:+.1f}%){extra}")
                continue
            flag = "BELOW TRIGGER" if w["breach"] else "above"
            print(f"{w['ticker']:<11} close {w['close']:>10,.2f}  trigger {w['trigger'] or 0:>10,.2f}  {flag} ({w['gap_pct']:+.1f}%)")
        return 0
    s = P.refresh(a.date, a.data_dir, f)
    if a.json:
        print(json.dumps(s, indent=1, default=str))
        return 0
    pct = f" ({s['day_pl_pct'] * 100:+.2f}%)" if s.get("day_pl_pct") is not None else ""
    print(f"{s['date']} ({s['kind']}): value \u20a6{s['value']:,.0f}, day {_naira(s['day_pl'] or 0)}{pct}, gain \u20a6{s['gain']:,.0f}")
    print("Source:", s["source"])
    if s["upgraded"]:
        print("Upgraded to official:", ", ".join(s["upgraded"]))
    print("Up:  ", ", ".join(f"{t} {_naira(m)}" for t, m in s["up"]) or "-")
    print("Down:", ", ".join(f"{t} {_naira(m)}" for t, m in s["down"]) or "-")
    br = [w for w in s["watchlist"] if w["breach"]]
    print("Watchlist:", "; ".join(f"{w['ticker']} {w.get('status', '')} {w['close']} vs {w['trigger']}" for w in br)
          if br else "all within their triggers")
    if s["volume"]:
        print("Heavy volume:", ", ".join(f"{v['ticker']} {v['ratio']}x" for v in s["volume"]))
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
