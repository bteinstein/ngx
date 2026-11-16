"""Portfolio data in ``data/``: add or refresh a trading day, upgrade live rows to official ones,
check the watchlist, and stage files for the claude.ai dashboard.

Files (layouts kept exactly as the dashboard export made them):

* ``holdings.json``       — units and unit cost per account; cost basis = sum(units x unit_cost)
* ``transactions.json``   — contract-note trades (``side`` Buy/Sell, ``units``, ``total``)
* ``price_history.json``  — one row per (ticker, date): close, volume, trades, value_ngn, source
* ``prices_<date>.json``  — that day's closes with 1-day and 7-day change and activity
* ``daily_log.json``      — one row per trading day: value, cost, gain, cash_in, day_pl, note
* ``watchlist.json``      — triggers: rule ``low`` (fixed level) or ``cost`` (average cost)

Data is pulled on demand. ``refresh()`` uses NGX's official files when they exist for the day,
otherwise NGX's live feed (about 30 minutes delayed; after the 14:30 close its prices are the
final closes and its volume is provisional). Live rows are labelled and are upgraded to official
figures by the next refresh once NGX publishes them.
"""
from __future__ import annotations

import collections
import datetime as dt
import glob
import json
import os
import shutil
from pathlib import Path

from .core import get_daily_prices, get_live, list_files, to_date
from .http import Fetcher

LAGOS = dt.timezone(dt.timedelta(hours=1))
LIVE_PREFIX = "NGX live feed"
OFFICIAL_SOURCE = "NGX official (Daily Official List / price list), via ngxprices"


# ---------------------------------------------------------------- files

def _p(data_dir, name) -> Path:
    return Path(data_dir) / name


def _load(data_dir, name):
    return json.loads(_p(data_dir, name).read_text())


def _save_history(data_dir, rows) -> None:
    _p(data_dir, "price_history.json").write_text(json.dumps(rows))  # one line, ASCII


def _save_log(data_dir, rows) -> None:
    _p(data_dir, "daily_log.json").write_text(json.dumps(rows, indent=1))


def _save_prices(data_dir, date: str, rows) -> Path:
    path = _p(data_dir, f"prices_{date}.json")
    path.write_text(json.dumps(rows, indent=1))
    return path


def latest_prices_file(data_dir) -> Path | None:
    files = sorted(glob.glob(str(_p(data_dir, "prices_*.json"))))
    return Path(files[-1]) if files else None


def lagos_now() -> dt.datetime:
    return dt.datetime.now(LAGOS)


# ---------------------------------------------------------------- holdings

def units_and_cost(data_dir, date: str | None = None):
    """Units per ticker held at the close of ``date`` (trades after it are undone) and cost basis."""
    holdings = _load(data_dir, "holdings.json")
    units, cost = collections.Counter(), 0.0
    for h in holdings:
        units[h["ticker"]] += h["units"]
        cost += h["units"] * h["unit_cost"]
    if date:
        for t in _load(data_dir, "transactions.json"):
            if t["date"] > date:
                sign = 1 if str(t["side"]).lower() == "buy" else -1
                units[t["ticker"]] -= sign * t["units"]
                cost -= sign * t["total"]
    return units, round(cost, 2)


def cash_in_on(data_dir, date: str) -> float:
    total = 0.0
    for t in _load(data_dir, "transactions.json"):
        if t["date"] == date:
            total += t["total"] if str(t["side"]).lower() == "buy" else -t["total"]
    return round(total, 2)


def tracked_tickers(data_dir) -> list[str]:
    """Holdings plus every ticker that has a price-history row on the latest history date."""
    held = {h["ticker"] for h in _load(data_dir, "holdings.json")}
    ph = _load(data_dir, "price_history.json")
    last = max(r["date"] for r in ph) if ph else None
    return sorted(held | {r["ticker"] for r in ph if r["date"] == last})


# ---------------------------------------------------------------- fetching

def fetch_day(date=None, fetcher: Fetcher | None = None) -> dict:
    """Best available NGX data for ``date`` (default: the latest trading day).

    Returns {date, kind: "official"|"live", label, rows: {symbol: row}}. Official files win;
    otherwise the live feed is used when its trade date is the requested day (or no day was asked).
    Raises RuntimeError if neither source has the day.
    """
    want = to_date(date).isoformat() if date else None
    if want and list_files(want, fetcher):
        rows = get_daily_prices(want, fetcher)
        if rows:
            return dict(date=want, kind="official", label=OFFICIAL_SOURCE, rows={r["symbol"]: r for r in rows})
    live, info = get_live(fetcher)
    td = info["trade_date"]
    if want and td != want:
        raise RuntimeError(f"No NGX data for {want}: no official files, and the live feed is for {td}.")
    if not want and list_files(td, fetcher):  # official files already out for the live feed's day
        rows = get_daily_prices(td, fetcher)
        if rows:
            return dict(date=td, kind="official", label=OFFICIAL_SOURCE, rows={r["symbol"]: r for r in rows})
    now = lagos_now()
    after_close = now.date().isoformat() > td or now.hour * 60 + now.minute >= 14 * 60 + 30
    label = (f"{LIVE_PREFIX}, {dt.date.fromisoformat(td).strftime('%-d %b')} at {now:%H:%M} WAT "
             + ("(final prices after the 14:30 close; volume provisional until NGX publishes its official files)"
                if after_close else "(intraday, about 30 minutes delayed; a stock with no trade yet keeps its previous close)"))
    rows = {}
    for r in live:
        r = dict(r)
        if r.get("close") is None:  # NGX shows no price until enough shares trade
            r["close"] = r.get("prev_close")
        rows[r["symbol"]] = r
    return dict(date=td, kind="live", label=label, rows=rows, after_close=after_close)


# ---------------------------------------------------------------- writing a day

def _num(v):
    return None if v in (None, "") else float(v)


def _int(v):
    v = _num(v)
    return None if v is None else int(round(v))


def upsert_day(day: dict, data_dir="data") -> dict:
    """Write one day's data (from :func:`fetch_day`) into price_history, prices_<date> and daily_log.

    Replaces any earlier rows for that day (e.g. live rows when official ones arrive). Keeps a
    daily-log note written by hand; regenerates notes that this module wrote (``auto_note``).
    """
    date, rows = day["date"], day["rows"]
    tickers = tracked_tickers(data_dir)
    missing = [t for t in tickers if t not in rows or _num(rows[t].get("close")) is None]
    held_units, cost = units_and_cost(data_dir, date)
    held_missing = [t for t in missing if held_units.get(t)]
    if held_missing:
        raise RuntimeError(f"{date}: no price for held stocks {held_missing}")

    ph = _load(data_dir, "price_history.json")
    keep = [r for r in ph if not (r["date"] == date and r["ticker"] in tickers)]
    old_by = {r["ticker"]: r for r in ph if r["date"] == date}
    dates = sorted({r["date"] for r in keep if r["date"] < date})
    close_at = {(r["date"], r["ticker"]): r["close"] for r in keep}
    base7 = max([d for d in dates if d <= (dt.date.fromisoformat(date) - dt.timedelta(days=7)).isoformat()],
                default=None)
    prev_date = dates[-1] if dates else None

    new_rows, prices = [], []
    for t in tickers:
        if t in missing:
            continue
        r = rows[t]
        close = _num(r["close"])
        prev = _num(r.get("prev_close")) or close_at.get((prev_date, t))
        row = dict(id=f"{t}-{date}", ticker=t, date=date, close=close, volume=_int(r.get("volume")),
                   trades=_int(r.get("trades")), value_ngn=_num(r.get("value_ngn")), source=day["label"])
        if t in old_by and old_by[t].get("note"):
            row["note"] = old_by[t]["note"]
        new_rows.append(row)
        b7 = close_at.get((base7, t))
        prices.append(dict(ticker=t, name=r.get("name") or t, price=close,
                           chg_1d_pct=round((close / prev - 1) * 100, 2) if prev else 0.0,
                           chg_7d_pct=round((close / b7 - 1) * 100, 2) if b7 else None,
                           as_of=date, prev_close=prev, volume=row["volume"], trades=row["trades"],
                           value_ngn=row["value_ngn"]))
    # keep display names from the previous prices file where we have them
    prev_file = latest_prices_file(data_dir)
    if prev_file:
        names = {p["ticker"]: p["name"] for p in json.loads(prev_file.read_text())}
        for p in prices:
            p["name"] = names.get(p["ticker"], p["name"])
    _save_history(data_dir, keep + new_rows)
    prices_path = _save_prices(data_dir, date, prices)

    # daily log
    px = {p["ticker"]: p for p in prices}
    log = _load(data_dir, "daily_log.json")
    log = [d for d in log if d["date"] != date] + [d for d in log if d["date"] == date][:1]
    existing = next((d for d in log if d["date"] == date), None)
    log = sorted(log, key=lambda d: d["date"])
    value = round(sum(n * px[t]["price"] for t, n in held_units.items() if n), 2)
    prev_row = max((d for d in log if d["date"] < date), key=lambda d: d["date"], default=None)
    cash_in = cash_in_on(data_dir, date)
    entry = existing or dict(date=date)
    entry.update(value=value, cost=cost, gain=round(value - cost, 2), cash_in=cash_in,
                 holdings=sum(1 for n in held_units.values() if n))
    if prev_row and prev_row["date"] < date:
        dp = round(value - prev_row["value"] - cash_in, 2)
        entry.update(day_pl=dp, day_pl_pct=dp / prev_row["value"])
    moves = sorted(((n * (px[t]["price"] - (px[t]["prev_close"] or px[t]["price"])), t)
                    for t, n in held_units.items() if n and t in px))
    summary = dict(date=date, kind=day["kind"], source=day["label"], value=value, cost=cost,
                   gain=entry["gain"], day_pl=entry.get("day_pl"), day_pl_pct=entry.get("day_pl_pct"),
                   up=[(t, round(m)) for m, t in moves[::-1][:5] if m > 0],
                   down=[(t, round(m)) for m, t in moves[:5] if m < 0],
                   watchlist=watchlist_status(data_dir, date, px), volume=volume_highlights(data_dir, date),
                   prices_file=str(prices_path), missing_unheld=missing)
    if existing is None or existing.get("auto_note"):
        entry["note"] = _auto_note(summary, cash_in)
        entry["auto_note"] = True
    if existing is None:
        log.append(entry)
        log.sort(key=lambda d: d["date"])
    # the next day's P/L depends on this day's value
    for a, b in zip(log, log[1:]):
        if a["date"] == date and b.get("day_pl") is not None:
            dp = round(b["value"] - a["value"] - (b.get("cash_in") or 0), 2)
            b.update(day_pl=dp, day_pl_pct=dp / a["value"])
    _save_log(data_dir, log)
    return summary


def _naira(v) -> str:
    return ("-" if v < 0 else "+") + "₦" + (f"{abs(v) / 1000:,.1f}K" if abs(v) >= 1000 else f"{abs(v):,.0f}")


def _auto_note(s: dict, cash_in: float) -> str:
    parts = ["No trades." if not cash_in else f"New money {_naira(cash_in)[1:]} (contract notes).",
             f"Prices: {s['source']}."]
    if s["up"]:
        parts.append("Up: " + ", ".join(f"{t} ({_naira(m)})" for t, m in s["up"]) + ".")
    if s["down"]:
        parts.append("Down: " + ", ".join(f"{t} ({_naira(m)})" for t, m in s["down"]) + ".")
    br = [w for w in s["watchlist"] if w["breach"]]
    parts.append("Watchlist: " + ("; ".join(f"{w['ticker']} {w['close']:,.2f} below {w['trigger']:,.2f}" for w in br)
                                  if br else "all above their triggers") + ".")
    return " ".join(parts)


# ---------------------------------------------------------------- watchlist and volume

def watchlist_status(data_dir, date: str | None = None, prices: dict | None = None) -> list[dict]:
    """Each watchlist stock's close against its trigger (rule ``low``: fixed level; ``cost``: average cost)."""
    if prices is None:
        f = _p(data_dir, f"prices_{date}.json") if date else latest_prices_file(data_dir)
        prices = {p["ticker"]: p for p in json.loads(Path(f).read_text())}
    holdings = _load(data_dir, "holdings.json")
    out = []
    for w in _load(data_dir, "watchlist.json"):
        t = w["ticker"]
        trig = w.get("trigger")
        if w.get("rule") == "cost":
            hs = [h for h in holdings if h["ticker"] == t]
            u = sum(h["units"] for h in hs)
            trig = round(sum(h["units"] * h["unit_cost"] for h in hs) / u, 2) if u else None
        p = prices.get(t)
        close = p["price"] if p else None
        out.append(dict(ticker=t, rule=w.get("rule"), trigger=trig, close=close,
                        breach=close is not None and trig is not None and close < trig,
                        gap_pct=round((close / trig - 1) * 100, 2) if close is not None and trig else None))
    return out


def volume_highlights(data_dir, date: str, days: int = 20, ratio: float = 2.0) -> list[dict]:
    """Held stocks whose volume on ``date`` is at least ``ratio`` x their average over ``days`` earlier days."""
    held, _ = units_and_cost(data_dir, date)
    by = collections.defaultdict(list)
    for r in _load(data_dir, "price_history.json"):
        by[r["ticker"]].append(r)
    out = []
    for t, n in held.items():
        if not n:
            continue
        today = next((r for r in by[t] if r["date"] == date), None)
        prev = sorted((r for r in by[t] if r["date"] < date and r.get("volume") not in (None, "")),
                      key=lambda r: r["date"], reverse=True)[:days]
        if not today or today.get("volume") in (None, "") or not prev:
            continue
        avg = sum(r["volume"] for r in prev) / len(prev)
        if avg and today["volume"] / avg >= ratio:
            out.append(dict(ticker=t, volume=today["volume"], avg=round(avg), ratio=round(today["volume"] / avg, 1),
                            value_ngn=today.get("value_ngn")))
    return sorted(out, key=lambda x: -x["ratio"])


# ---------------------------------------------------------------- refresh

def live_dates(data_dir) -> list[str]:
    return sorted({r["date"] for r in _load(data_dir, "price_history.json")
                   if str(r.get("source", "")).startswith(LIVE_PREFIX)})


def refresh(date=None, data_dir="data", fetcher: Fetcher | None = None) -> dict:
    """Upgrade earlier live-feed days to official data where NGX has published, then add or
    refresh ``date`` (default: the latest trading day). Returns the day's summary plus
    ``upgraded`` (days switched from live to official)."""
    fetcher = fetcher or Fetcher()
    target = to_date(date).isoformat() if date else None
    upgraded = []
    for d in live_dates(data_dir):
        if d == target:
            continue
        if list_files(d, fetcher, use_cache=False):
            day = fetch_day(d, fetcher)
            if day["kind"] == "official":
                upsert_day(day, data_dir)
                upgraded.append(d)
    day = fetch_day(target, fetcher)
    summary = upsert_day(day, data_dir)
    summary["upgraded"] = upgraded
    return summary


def stage_dashboard_files(data_dir, out_dir) -> dict:
    """Copy the three files the claude.ai dashboard reads into ``out_dir`` with dated names:
    prices_<date>.json, price_history_<date>.json, daily_<date>.json. Returns {dataset: path}."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    pf = latest_prices_file(data_dir)
    date = pf.stem.split("_", 1)[1]
    files = {"prices": out / f"prices_{date}.json", "price_history": out / f"price_history_{date}.json",
             "daily": out / f"daily_{date}.json"}
    shutil.copyfile(pf, files["prices"])
    shutil.copyfile(_p(data_dir, "price_history.json"), files["price_history"])
    shutil.copyfile(_p(data_dir, "daily_log.json"), files["daily"])
    return {k: str(v) for k, v in files.items()}
