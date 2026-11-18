"""Portfolio data in ``data/``: add or refresh a trading day, upgrade live rows to official ones,
check the watchlist, and stage files for the claude.ai dashboard.

Files (layouts kept exactly as the dashboard export made them):

* ``holdings.json``       — units and unit cost per account; cost basis = sum(units x unit_cost)
* ``transactions.json``   — contract-note trades (``side`` Buy/Sell, ``units``, ``total``)
* ``price_history.json``  — one row per (ticker, date): close, volume, trades, value_ngn, source
* ``prices_<date>.json``  — that day's closes with 1-day and 7-day change and activity
* ``daily_log.json``      — one row per trading day: value, cost, gain, cash_in, day_pl, note
* ``rules.json``          — the owner's sell rules (loss limit, early warning, trailing level). When it
  exists, every holding is checked against it and ``watchlist.json`` is regenerated from it.
* ``watchlist.json``      — triggers: rule ``loss_limit`` / ``trailing`` (generated from ``rules.json``),
  or hand-set rule ``low`` (fixed level) / ``cost`` (average cost)

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
                   watchlist=_watchlist_and_write(data_dir, date, px), volume=volume_highlights(data_dir, date),
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


def _watchlist_and_write(data_dir, date, px):
    rows = watchlist_status(data_dir, date, px)
    rules = load_rules(data_dir)
    if rules:
        write_rules_watchlist(data_dir, rows, rules)
    return rows


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
    if s["watchlist"] and "status" in s["watchlist"][0]:
        los = [w for w in br if w["status"] == "loser"]
        tr = [w for w in br if w["status"] == "trail"]
        txt = []
        if los:
            txt.append("past the loss limit: " + ", ".join(f"{w['ticker']} ({w['gain_pct']:+.0f}% on cost)" for w in los))
        if tr:
            txt.append("sell-part review: " + ", ".join(f"{w['ticker']} ({w['off_peak_pct']:+.0f}% from peak)" for w in tr))
        amb = [w for w in s["watchlist"] if w.get("light") == "amber"]
        if amb:
            txt.append("early warning (amber): " + ", ".join(w["ticker"] for w in amb))
        tpl = [w for w in s["watchlist"] if w.get("take_profit")]
        if tpl:
            txt.append("take profit: " + ", ".join(w["ticker"] for w in tpl))
        parts.append("Rules: " + ("; ".join(txt) if txt else "all within the rules") + ".")
    else:
        parts.append("Watchlist: " + ("; ".join(f"{w['ticker']} {w['close']:,.2f} below {w['trigger']:,.2f}" for w in br)
                                      if br else "all above their triggers") + ".")
    return " ".join(parts)


# ---------------------------------------------------------------- watchlist and volume

def load_rules(data_dir) -> dict | None:
    f = _p(data_dir, "rules.json")
    return json.loads(f.read_text()) if f.exists() else None


def _prices_for(data_dir, date, prices):
    if prices is None:
        f = _p(data_dir, f"prices_{date}.json") if date else latest_prices_file(data_dir)
        prices = {p["ticker"]: p for p in json.loads(Path(f).read_text())}
    return prices


def load_corporate_actions(data_dir) -> list[dict]:
    f = _p(data_dir, "corporate_actions.json")
    return json.loads(f.read_text()) if f.exists() else []


def adjusted_history(rows: list[dict], actions: list[dict]) -> list[dict]:
    """Price-history rows with closes made comparable with today's (copies; the file is not changed).

    For each action in ``corporate_actions.json``, rows of that ticker dated before ``ex_date`` are adjusted:
    ``dividend`` subtracts ``amount`` from the close; ``reconstruction`` (``old_per_new`` old shares became
    one new share) multiplies the close by ``old_per_new`` and divides the volume by it. Adjusted rows keep
    the raw figure in ``raw_close``.
    """
    by = collections.defaultdict(list)
    for a in actions:
        by[a["ticker"]].append(a)
    out = []
    for r in rows:
        acts = [a for a in by.get(r["ticker"], ()) if r["date"] < a["ex_date"]]
        if not acts or r.get("close") in (None, ""):
            out.append(r)
            continue
        r = dict(r, raw_close=r["close"])
        c, v = float(r["close"]), r.get("volume")
        for a in sorted(acts, key=lambda a: a["ex_date"]):
            if a["type"] == "dividend":
                c -= a["amount"]
            elif a["type"] == "reconstruction":
                c *= a["old_per_new"]
                if v not in (None, ""):
                    v = float(v) / a["old_per_new"]
        r["close"], r["volume"] = round(c, 4), v
        out.append(r)
    return out


def rules_status(data_dir, date: str | None = None, prices: dict | None = None, rules: dict | None = None) -> list[dict]:
    """Every holding checked against the owner's rules (``rules.json``).

    * loss limit: close at or below avg cost x (1 - loss_limit_pct) -> ``loser``
    * early warning: close at or below avg cost x (1 - warn_pct) -> ``warn``
    * trailing: once the peak close gave a gain of at least ``trail_min_peak_gain_pct``, a close at
      or below peak x (1 - trail_pct) -> ``trail`` (review selling part). The peak is the highest
      close in ``price_history.json`` up to ``date`` (history is sparse before Oct 2026), adjusted for
      the dividends and share reconstructions in ``corporate_actions.json`` (``adjusted_history``).
    ``trigger`` is the higher (nearer) of the active levels; ``breach`` = loser or trail.
    """
    rules = rules or load_rules(data_dir)
    prices = _prices_for(data_dir, date, prices)
    date = date or next(iter(prices.values()))["as_of"]
    loss, warn, trail = rules["loss_limit_pct"] / 100, rules["warn_pct"] / 100, rules["trail_pct"] / 100
    min_peak = rules["trail_min_peak_gain_pct"] / 100
    units, _ = units_and_cost(data_dir, date)
    cost = collections.Counter()
    for h in _load(data_dir, "holdings.json"):
        cost[h["ticker"]] += h["units"] * h["unit_cost"]
    for t in _load(data_dir, "transactions.json"):
        if t["date"] > date:
            cost[t["ticker"]] -= (1 if str(t["side"]).lower() == "buy" else -1) * t["total"]
    peak, hist = {}, collections.defaultdict(list)
    for r in adjusted_history(_load(data_dir, "price_history.json"), load_corporate_actions(data_dir)):
        if r["date"] <= date and r.get("close") not in (None, ""):
            c = float(r["close"])
            hist[r["ticker"]].append(r)
            if r["ticker"] not in peak or c > peak[r["ticker"]][0]:
                peak[r["ticker"]] = (c, r["date"])
    out = []
    for t, n in sorted(units.items()):
        if not n:
            continue
        avg = cost[t] / n
        p = prices.get(t)
        close = p["price"] if p else None
        pk, pk_date = peak.get(t, (close, date))
        if close is not None and close > (pk or 0):
            pk, pk_date = close, date
        loss_lvl, warn_lvl = round(avg * (1 - loss), 2), round(avg * (1 - warn), 2)
        trail_on = pk is not None and pk >= avg * (1 + min_peak)
        trail_lvl = round(pk * (1 - trail), 2) if trail_on else None
        rule, trig = ("trailing", trail_lvl) if trail_on and trail_lvl > loss_lvl else ("loss_limit", loss_lvl)
        status = "no price"
        if close is not None:
            if close <= loss_lvl:
                status = "loser"
            elif trail_on and close <= trail_lvl:
                status = "trail"
            elif close <= warn_lvl:
                status = "warn"
            else:
                status = "ok"
        out.append(dict(ticker=t, rule=rule, trigger=trig, close=close, breach=status in ("loser", "trail"),
                        status=status, gap_pct=round((close / trig - 1) * 100, 2) if close is not None else None,
                        avg_cost=round(avg, 2), gain_pct=round((close / avg - 1) * 100, 2) if close is not None else None,
                        loss_level=loss_lvl, warn_level=warn_lvl, trail_level=trail_lvl, peak=pk, peak_date=pk_date,
                        peak_gain_pct=round((pk / avg - 1) * 100, 2) if pk else None,
                        off_peak_pct=round((close / pk - 1) * 100, 2) if close is not None and pk else None))
    total = sum(units[r["ticker"]] * r["close"] for r in out if r["close"] is not None)
    since = rules.get("set", "0000-00-00")
    sells = collections.defaultdict(list)
    for t in _load(data_dir, "transactions.json"):
        if str(t["side"]).lower() == "sell" and since <= t["date"] <= date:
            sells[t["ticker"]].append(t)
    for r in out:
        r.update(early_warning(r, sorted(hist[r["ticker"]], key=lambda x: x["date"]), rules, date))
        r.update(take_profit(r, units[r["ticker"]], cost[r["ticker"]], total, sells[r["ticker"]], rules))
    order = {"loser": 0, "trail": 1, "warn": 2, "ok": 3, "no price": 4}
    lights = {"red": 0, "amber": 1, "watch": 2, "note": 3, "green": 4}
    return sorted(out, key=lambda r: (lights[r["light"]], order[r["status"]],
                                      r["gap_pct"] if r["gap_pct"] is not None else 1e9))


TP_DEFAULTS = dict(targets=[dict(gain_pct=50, sell_pct=25), dict(gain_pct=100, sell_pct=25)],
                   recover_cost_gain_pct=100, size_cap_pct=15, fee_pct=2.0)


def take_profit(r: dict, units: float, cost: float, total: float, sells: list[dict], rules: dict) -> dict:
    """Take-profit flags for one holding (selling into strength, not on a fall).

    * targets: at each gain level (default +50%, +100%) sell the given share of the holding. Sells
      recorded in ``transactions.json`` since the rules were set count as targets taken, in order.
    * recover cost: once the gain reaches ``recover_cost_gain_pct``, the units whose sale (after
      ``fee_pct`` fees) returns everything paid for the holding; skipped once sells since the rules
      were set have returned the cost.
    * size cap: a holding over ``size_cap_pct`` of the portfolio value, and the units that bring it back.
    """
    tp = {**TP_DEFAULTS, **rules.get("take_profit", {})}
    close, out = r["close"], []
    weight = round(units * close / total * 100, 2) if close and total else None
    if not close or not units:
        return dict(take_profit=out, weight_pct=weight)
    net = close * (1 - tp["fee_pct"] / 100)
    gain = r["gain_pct"]
    reached = [t for t in tp["targets"] if gain >= t["gain_pct"]]
    pending = reached[len(sells):]
    if pending:
        pct = sum(t["sell_pct"] for t in pending)
        n = int(units * pct / 100)
        lv = " and ".join(f"+{t['gain_pct']}%" for t in pending)
        out.append(dict(kind="target", text=f"target{'s' if len(pending) > 1 else ''} {lv} reached: sell {pct}% "
                        f"({n:,} units, about ₦{n * net:,.0f} after fees)", units=n))
    returned = sum(float(x.get("total") or 0) for x in sells)
    if gain >= tp["recover_cost_gain_pct"] and returned < cost:
        n = min(units, int(-(-(cost - returned) // net)))
        out.append(dict(kind="recover_cost", text=f"{'or at least, ' if pending else ''}recover your cost: sell {n:,} units ({n / units * 100:.0f}% of the "
                        f"holding, about ₦{n * net:,.0f} after fees) and keep {units - n:,.0f} for free", units=n))
    if weight is not None and weight > tp["size_cap_pct"]:
        n = int(-(-(units * close - tp["size_cap_pct"] / 100 * total) // close))
        out.append(dict(kind="size_cap", text=f"{weight:.1f}% of the portfolio (cap {tp['size_cap_pct']}%): sell "
                        f"{n:,} units (about ₦{n * net:,.0f} after fees) to get back to the cap", units=n))
    return dict(take_profit=out, weight_pct=weight)


EW_DEFAULTS = dict(watch_off_peak_pct=10, near_trigger_pct=5, heavy_volume_ratio=2.0, avg_days=20,
                   heavy_fall_days=5, limit_down_pct=9, limit_down_days=10, falls_in_a_row=3)


def early_warning(r: dict, hist: list[dict], rules: dict, date: str) -> dict:
    """Traffic light for one holding (``r`` from ``rules_status``; ``hist`` its dated rows, oldest first).

    red   = a rule has fired (loser or sell-part review)
    amber = a tolerance signal AND at least one general sign
    watch = a tolerance signal only;  note = general signs only;  green = nothing
    Tolerance signals: at/below the warning level on cost; ``watch_off_peak_pct`` off the peak (when
    trailing is active); within ``near_trigger_pct`` of the trigger. General signs: a fall on heavy
    volume, a close below the ``avg_days`` average, a limit-down day, ``falls_in_a_row`` falls in a row.
    Only daily rows from the last 45 calendar days are used for the general signs.
    """
    ew = {**EW_DEFAULTS, **rules.get("early_warning", {})}
    tol, gen = [], []
    if r["status"] == "warn":
        tol.append(f"{r['gain_pct']:+.0f}% on cost (warning at -{rules['warn_pct']}%)")
    if r["trail_level"] and r["off_peak_pct"] is not None and r["off_peak_pct"] <= -ew["watch_off_peak_pct"]:
        tol.append(f"{r['off_peak_pct']:.0f}% from peak")
    if r["gap_pct"] is not None and 0 < r["gap_pct"] <= ew["near_trigger_pct"]:
        tol.append(f"{r['gap_pct']:.1f}% above its trigger")
    start = (dt.date.fromisoformat(date) - dt.timedelta(days=45)).isoformat()
    h = [x for x in hist if x["date"] >= start]
    c = [float(x["close"]) for x in h]
    v = [float(x["volume"]) if x.get("volume") not in (None, "") else None for x in h]
    n, k = len(c), ew["avg_days"]
    if n > k:
        avg = sum(c[-k:]) / k
        if c[-1] < avg:
            gen.append(f"below its {k}-day average ({(c[-1] / avg - 1) * 100:.0f}%)")
        heavy = []
        for i in range(max(k, n - ew["heavy_fall_days"]), n):
            prev = [x for x in v[i - k:i] if x]
            if v[i] and prev and c[i] < c[i - 1] and v[i] >= ew["heavy_volume_ratio"] * sum(prev) / len(prev):
                heavy.append(h[i]["date"])
        if heavy:
            gen.append("fell on heavy volume (" + ", ".join(d[8:] + "/" + d[5:7] for d in heavy) + ")")
    if n > 1:
        ld = [h[i]["date"] for i in range(max(1, n - ew["limit_down_days"]), n)
              if c[i] / c[i - 1] - 1 <= -ew["limit_down_pct"] / 100]
        if ld:
            gen.append("limit-down day (" + ", ".join(d[8:] + "/" + d[5:7] for d in ld) + ")")
        streak = 0
        for i in range(n - 1, 0, -1):
            if c[i] < c[i - 1]:
                streak += 1
            else:
                break
        if streak >= ew["falls_in_a_row"]:
            gen.append(f"{streak} falls in a row")
    if r["status"] in ("loser", "trail"):
        light = "red"
    elif tol and gen:
        light = "amber"
    elif tol:
        light = "watch"
    elif gen:
        light = "note"
    else:
        light = "green"
    return dict(light=light, tolerance_signals=tol, general_signs=gen)


_STATUS_TEXT = {"loser": "LOSER: at or past your {loss}% loss limit",
                "trail": "SELL-PART REVIEW: {trail}% or more below its peak",
                "warn": "Early warning: {warn}% or more below your cost", "ok": "Within your rules",
                "no price": "No price"}


def write_rules_watchlist(data_dir, rows: list[dict], rules: dict) -> None:
    """Regenerate ``watchlist.json`` (the dashboard's watchlist) from ``rules_status`` rows."""
    fmt = dict(loss=rules["loss_limit_pct"], warn=rules["warn_pct"], trail=rules["trail_pct"])
    wl = []
    for r in rows:
        note = (f"{_STATUS_TEXT[r['status']].format(**fmt)}. Avg cost {r['avg_cost']:,.2f}; "
                f"loss limit {r['loss_level']:,.2f}; warning {r['warn_level']:,.2f}; peak {r['peak']:,.2f} "
                f"({r['peak_date']}, {r['peak_gain_pct']:+.1f}% on cost)")
        note += f"; trailing level {r['trail_level']:,.2f}." if r["trail_level"] else "; trailing not active (peak gain under " \
            f"{rules['trail_min_peak_gain_pct']}%)."
        sig = r.get("tolerance_signals", []) + r.get("general_signs", [])
        if sig:
            note += " Early warning (" + r["light"] + "): " + "; ".join(sig) + "."
        if r.get("take_profit"):
            note += " Take profit: " + "; ".join(x["text"] for x in r["take_profit"]) + "."
        wl.append(dict(ticker=r["ticker"], rule=r["rule"], trigger=r["trigger"], status=r["status"], light=r.get("light"),
                       since=rules.get("compare_since", "2026-10-23"), note=note))
    _p(data_dir, "watchlist.json").write_text(
        "[\n" + ",\n".join(" " + json.dumps(w, ensure_ascii=False) for w in wl) + "\n]\n")


def watchlist_status(data_dir, date: str | None = None, prices: dict | None = None) -> list[dict]:
    """With ``rules.json``: every holding against the owner's rules (see ``rules_status``).
    Otherwise each ``watchlist.json`` stock against its trigger (``low``: fixed level; ``cost``: average cost)."""
    rules = load_rules(data_dir)
    if rules:
        return rules_status(data_dir, date, prices, rules)
    prices = _prices_for(data_dir, date, prices)
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
