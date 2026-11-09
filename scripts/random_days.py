"""Run ngxprices on 5 random weekdays per year (seed 42) and write a CSV + JSON report
(prices, volume, size, fundamentals and dividends, with per-day cross-checks and field coverage)."""
import collections
import datetime as dt
import json
import random
import sys
import time
from pathlib import Path

from ngxprices import FIELDS, Fetcher, compare_dol_prices1, fetch_sources, list_files, merge, validate, write_csv
from ngxprices.core import DOL_TITLE, ZIP_TITLE, find_file, nearby_name_map

OUT = Path(__file__).resolve().parent.parent / "test_output"
YEARS = {2023: dt.date(2023, 12, 31), 2024: dt.date(2024, 12, 31), 2025: dt.date(2025, 12, 31),
         2026: dt.date(2026, 11, 6)}
LAGOS = dt.timezone(dt.timedelta(hours=1))


def lagos(ts):
    if not ts:
        return None
    return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(LAGOS).isoformat()


def main():
    rng = random.Random(42)
    f = Fetcher(delay=1.0)
    picks = []
    for y, last in YEARS.items():
        days = [dt.date(y, 1, 1) + dt.timedelta(i) for i in range((last - dt.date(y, 1, 1)).days + 1)]
        days = [d for d in days if d.weekday() < 5]
        picks += [(y, d) for d in sorted(rng.sample(days, 5))]

    report, all_rows, used = [], [], set()
    for y, picked in picks:
        t0 = time.time()
        d, files, skipped = picked, [], []
        while True:
            if d.weekday() < 5 and d not in used:
                files = list_files(d, f)
                if files:
                    break
                skipped.append(d.isoformat())
            d += dt.timedelta(days=1)
        used.add(d)
        entry = dict(year=y, picked=picked.isoformat(), date=d.isoformat(), rolled_over=skipped,
                     files_found=len(files), file_titles=[x["title"] for x in files])
        try:
            s = fetch_sources(d, f, files=files)
            nm = nearby_name_map(d, f) if not s["dol"] else None
            rows = merge(d, s["dol"], s["prices1"], s["plist2"], nm, shares=s["shares"])
            v = validate(d, sources=s)
            mm = compare_dol_prices1(s["dol"], s["prices1"])
            entry.update(stock_count=len(rows), dol_count=len(s["dol"]), prices1_count=len(s["prices1"]),
                         plist2_count=len(s["plist2"]),
                         by_source=dict(collections.Counter(r["source"] for r in rows)),
                         by_board=dict(collections.Counter(r["board"] for r in rows)),
                         compared=sum(1 for r in s["dol"] if r["symbol"] in s["prices1"]),
                         mismatch_count=len(mm), mismatches=mm, errors=s["errors"],
                         mislabelled=s["mislabelled"], dol_fallback_used=nm is not None,
                         shares_count=len(s["shares"]),
                         checks={k: dict(compared=v[k].get("compared"), status=v[k]["status"],
                                         mismatches=len(v[k].get("mismatches", v[k].get("failures", []))),
                                         **({"pass_rate": v[k]["pass_rate"]} if "pass_rate" in v[k] else {}))
                                 for k in ("close_dol_vs_prices1", "close_dol_vs_shares",
                                           "volume_prices1_vs_prices_list2", "market_cap_check")},
                         coverage_pct={k: round(100 * sum(1 for r in rows if r.get(k) not in (None, "")) / len(rows), 1)
                                       for k in ("volume", "value_ngn", "shares_outstanding", "market_cap_ngn",
                                                 "week52_high", "eps", "pe", "div_final", "div_paid_date")}
                         if rows else {})
            all_rows += rows
        except Exception as e:  # noqa: BLE001
            entry.update(stock_count=0, mismatch_count=None, errors=[f"{type(e).__name__}: {e}"])
        entry["seconds"] = round(time.time() - t0, 2)
        times = {}
        for key, title in (("dol_equities", DOL_TITLE), ("price_list_zip", ZIP_TITLE)):
            x = find_file(files, title.format(d=d.strftime("%d-%m-%Y")))
            if x:
                times[key] = dict(created_utc=x["created"], modified_utc=x["modified"],
                                  created_lagos=lagos(x["created"]), modified_lagos=lagos(x["modified"]))
        cr = sorted(x["created"] for x in files if x.get("created"))
        if cr:
            times["first_file_created_lagos"] = lagos(cr[0])
            times["last_file_created_lagos"] = lagos(cr[-1])
        entry["upload_times"] = times
        report.append(entry)
        print(f"{entry['picked']} -> {entry['date']}: files={entry['files_found']} stocks={entry.get('stock_count')} "
              f"checks={ {k[:12]: x['status'] for k, x in entry.get('checks', {}).items()} } "
              f"err={entry.get('errors')} {entry['seconds']}s", flush=True)

    OUT.mkdir(exist_ok=True)
    write_csv(all_rows, OUT / "random_days.csv")
    (OUT / "report.json").write_text(json.dumps(dict(seed=42, generated=dt.datetime.now().isoformat(),
                                                     dates=report), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
