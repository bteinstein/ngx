"""Command line interface: ``ngxprices fetch|range|files``."""
from __future__ import annotations

import argparse
import json
import sys

from .core import get_daily_prices, get_range, list_files, write_csv
from .http import Fetcher


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ngxprices", description="NGX daily equity closing prices")
    ap.add_argument("--cache", help="cache directory (default ~/.cache/ngxprices or $NGXPRICES_CACHE)")
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between requests (default 1)")
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
    a = ap.parse_args(argv)

    f = Fetcher(cache_dir=a.cache, delay=a.delay)
    if a.cmd == "files":
        json.dump(list_files(a.date, f), sys.stdout, indent=1)
        print()
        return 0
    rows = get_daily_prices(a.date, f) if a.cmd == "fetch" else get_range(a.start, a.end, f)
    if a.cmd == "fetch" and not rows:
        print(f"No files published for {a.date} (non-trading day or not yet published)", file=sys.stderr)
        return 1
    if a.out:
        write_csv(rows, a.out)
        print(f"wrote {len(rows)} rows to {a.out}", file=sys.stderr)
    else:
        import csv
        from .core import FIELDS
        w = csv.DictWriter(sys.stdout, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
