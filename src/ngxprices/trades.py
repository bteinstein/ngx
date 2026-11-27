"""Short-term trade plans (``data/trades.json``): buy and sell conditions checked on every refresh.

A trade is a separate lot bought for a quick profit, with its own rules (the owner's, 27 Nov 2026):

* profit is measured after fees (``fee_pct`` each way) and counts dividends received while holding
  (after ``dividend_wht_pct`` withholding tax);
* take profit 1: at ``target1_net_pct`` net, sell ``target1_sell_pct`` of the units;
* take profit 2: at ``target2_net_pct`` net, sell the rest;
* protect: once take profit 1 was sold, sell the rest if the net gain falls back to ``protect_net_pct``;
* stop: sell all if the price falls ``stop_pct`` below the all-in unit cost (the stop moves down by
  any dividend received, so an ex-dividend price drop does not trigger it);
* time: review after ``max_hold_days``; a dividend expected soon after is mentioned;
* add: if the price is ``add_on_dip_pct`` below the entry, the reserve may be used.

Buy conditions for a planned trade: buy with a limit at or below ``planned_price`` x (1 + ``buy_limit_pct``);
if the price has run ``wait_if_up_pct`` above the planned price, the alert says wait.

Per-unit levels (c = all-in unit cost, d = net dividend received per unit, f = fee):
  target(X) = (c x (1 + X) - d) / (1 - f);  stop = c x (1 - stop_pct) - d.
Prices are checked on the realistic price (``portfolio.realistic_price``), not a stale close.
"""
from __future__ import annotations

import datetime as dt
import json

TRADE_DEFAULTS = dict(fee_pct=2.0, dividend_wht_pct=10, target1_net_pct=10, target1_sell_pct=50,
                      target2_net_pct=20, protect_net_pct=5, stop_pct=10, max_hold_days=183,
                      add_on_dip_pct=5, near_pct=3, dividend_notice_days=45, buy_limit_pct=1,
                      wait_if_up_pct=5)


def _n(v):
    return f"₦{v:,.2f}"


def _k(v):
    return ("-" if v < 0 else "") + f"₦{abs(v):,.0f}"


def load_trades(data_dir) -> dict | None:
    from .portfolio import _p
    p = _p(data_dir, "trades.json")
    return json.loads(p.read_text()) if p.exists() else None


def levels(c: float, d: float, r: dict) -> dict:
    f = r["fee_pct"] / 100
    t = lambda x: round((c * (1 + x / 100) - d) / (1 - f), 2)  # noqa: E731
    return dict(target1=t(r["target1_net_pct"]), target2=t(r["target2_net_pct"]), protect=t(r["protect_net_pct"]),
                breakeven=t(0), stop=round(c * (1 - r["stop_pct"] / 100) - d, 2))


def _dividends(actions, ticker, start, date, units_at, wht):
    out = []
    for a in actions:
        if a["ticker"] == ticker and a.get("type") == "dividend" and start < a["ex_date"] <= date:
            n = units_at(a["ex_date"])
            out.append(dict(ex_date=a["ex_date"], gross=a["amount"], net=round(a["amount"] * (1 - wht / 100), 4),
                            units=n, cash=round(a["amount"] * (1 - wht / 100) * n, 2)))
    return out


def check_trade(t: dict, price: float, date: str, actions: list[dict], rules: dict, held: dict | None = None,
                reserve_left: float = 0.0) -> dict:
    """Status and alerts for one trade plan at ``price`` (realistic price) on ``date``."""
    r = {**TRADE_DEFAULTS, **rules, **t.get("rules", {})}
    f = r["fee_pct"] / 100
    buys, sells = t.get("buys", []), t.get("sells", [])
    alerts = []
    held = held or {}
    out = dict(id=t["id"], ticker=t["ticker"], name=t.get("name", t["ticker"]), status=t["status"], price=price,
               account=t.get("account"), budget=t.get("budget"))
    if t["status"] == "planned" or not buys:
        pp = t.get("planned_price") or price
        buy_px = min(price, pp * (1 + r["buy_limit_pct"] / 100))
        c = buy_px * (1 + f)
        units = int(t["budget"] // c)
        lv = levels(c, 0.0, r)
        exp = t.get("dividends_expected", [])
        dn = sum(x["gross_est"] for x in exp) * (1 - r["dividend_wht_pct"] / 100)
        lv_div = levels(c, dn, r) if dn else None
        out.update(units=units, entry=round(buy_px, 2), unit_cost=round(c, 2), invested=round(units * c, 2),
                   levels=lv, levels_after_dividend=lv_div, dividend_net_unit_est=round(dn, 4),
                   limit_price=round(pp * (1 + r["buy_limit_pct"] / 100), 2))
        if price > pp * (1 + r["wait_if_up_pct"] / 100):
            alerts.append(dict(kind="wait", text=f"WAIT: {_n(price)} is {(price / pp - 1) * 100:.0f}% above the planned "
                               f"{_n(pp)}; buying now raises every target"))
        else:
            alerts.append(dict(kind="buy", text=f"BUY (planned): about {units:,} units with a limit of "
                               f"{_n(out['limit_price'])} (about {_k(units * c)} with fees); then send the contract note "
                               f"so the sell alerts start"))
        hu, hc = held.get("units", 0), held.get("cost", 0.0)
        if hu:
            nu, ncost = hu + units, hc + units * c
            out["combined"] = dict(units_before=hu, avg_before=round(hc / hu, 2), units_after=nu,
                                   avg_after=round(ncost / nu, 2), cost_after=round(ncost, 2),
                                   value_after=round(nu * price, 2), pl_after=round(nu * price - ncost, 2))
        out["alerts"] = alerts
        return out

    first = min(b["date"] for b in buys)

    def units_at(d):
        return sum(b["units"] for b in buys if b["date"] < d) - sum(s["units"] for s in sells if s["date"] < d)

    bu = sum(b["units"] for b in buys)
    cost = sum(b["total"] for b in buys)
    c = cost / bu
    su = sum(s["units"] for s in sells)
    units = bu - su
    realised = sum(s.get("net") or s["units"] * s["price"] * (1 - f) for s in sells)
    divs = _dividends(actions, t["ticker"], first, date, units_at, r["dividend_wht_pct"])
    d_unit = sum(x["net"] for x in divs)
    div_cash = sum(x["cash"] for x in divs)
    lv = levels(c, d_unit, r)
    net_now = realised + units * price * (1 - f) + div_cash - cost
    held_days = (dt.date.fromisoformat(date) - dt.date.fromisoformat(first)).days
    review = (dt.date.fromisoformat(first) + dt.timedelta(days=r["max_hold_days"])).isoformat()
    out.update(units=units, units_bought=bu, units_sold=su, entry=round(sum(b["units"] * b["price"] for b in buys) / bu, 2),
               unit_cost=round(c, 2), invested=round(cost, 2), realised=round(realised, 2), dividends=divs,
               dividend_cash=round(div_cash, 2), net_pl=round(net_now, 2), net_pl_pct=round(net_now / cost * 100, 2),
               levels=lv, first_buy=first, days_held=held_days, review_date=review)
    took1 = su > 0
    sell_net = lambda n: n * price * (1 - f)  # noqa: E731
    if units > 0:
        if price <= lv["stop"]:
            alerts.append(dict(kind="stop", text=f"SELL (stop): {_n(price)} is at or below the stop {_n(lv['stop'])}: "
                               f"sell all {units:,} units (about {_k(sell_net(units))} after fees; trade result "
                               f"{_k(net_now)}, {net_now / cost * 100:+.1f}%)"))
        elif price >= lv["target2"]:
            alerts.append(dict(kind="target2", text=f"TAKE PROFIT 2: {_n(price)} reached the +{r['target2_net_pct']}% net "
                               f"target {_n(lv['target2'])}: sell the remaining {units:,} units (about {_k(sell_net(units))} "
                               f"after fees; trade result {_k(net_now)})"))
        elif not took1 and price >= lv["target1"]:
            n = int(units * r["target1_sell_pct"] / 100)
            alerts.append(dict(kind="target1", text=f"TAKE PROFIT 1: {_n(price)} reached the +{r['target1_net_pct']}% net "
                               f"target {_n(lv['target1'])}: sell {n:,} units (about {_k(sell_net(n))} after fees); "
                               f"keep {units - n:,} for {_n(lv['target2'])}"))
        elif took1 and price <= lv["protect"]:
            alerts.append(dict(kind="protect", text=f"PROTECT PROFIT: {_n(price)} fell back to the +{r['protect_net_pct']}% "
                               f"net level {_n(lv['protect'])}: sell the remaining {units:,} units"))
        else:
            nxt = lv["target2"] if took1 else lv["target1"]
            if price >= nxt * (1 - r["near_pct"] / 100):
                alerts.append(dict(kind="near", text=f"NEAR TARGET: {_n(price)} is within {r['near_pct']}% of {_n(nxt)}"))
            if price <= lv["stop"] * (1 + r["near_pct"] / 100):
                alerts.append(dict(kind="near_stop", text=f"NEAR STOP: {_n(price)} is within {r['near_pct']}% of the stop {_n(lv['stop'])}"))
        if reserve_left > 0 and price <= out["entry"] * (1 - r["add_on_dip_pct"] / 100) and price > lv["stop"]:
            alerts.append(dict(kind="add", text=f"ADD (reserve): {_n(price)} is {r['add_on_dip_pct']}%+ below your entry "
                               f"{_n(out['entry'])}: up to {_k(reserve_left)} of the reserve may be used"))
        for x in t.get("dividends_expected", []):
            days = (dt.date.fromisoformat(x["ex_date_est"]) - dt.date.fromisoformat(date)).days
            if 0 < days <= r["dividend_notice_days"] and x["ex_date_est"] > max([d["ex_date"] for d in divs], default=""):
                dn = x["gross_est"] * (1 - r["dividend_wht_pct"] / 100)
                alerts.append(dict(kind="dividend", text=f"DIVIDEND: expected around {x['ex_date_est']} (last year {_n(x['gross_est'])}; "
                                   f"about {_k(dn * units)} after 10% tax on {units:,} units). Selling before then gives it up; "
                                   f"after it the price drops by about the dividend, and the targets and stop drop with it"))
        if held_days >= r["max_hold_days"]:
            alerts.append(dict(kind="review", text=f"REVIEW: held {held_days} days (limit {r['max_hold_days']}): decide to sell "
                               f"the {units:,} units or keep them as a longer holding (trade result {_k(net_now)})"))
        elif held_days >= r["max_hold_days"] - 14:
            alerts.append(dict(kind="review_soon", text=f"REVIEW SOON: the 6-month limit is {review}"))
    out["alerts"] = alerts
    return out


def trade_status(data_dir, date: str | None = None, prices: dict | None = None) -> list[dict]:
    """Every plan in ``trades.json`` checked at the latest (or given) prices."""
    from . import portfolio as P
    tr = load_trades(data_dir)
    if not tr:
        return []
    prices = P._prices_for(data_dir, date, prices)
    date = date or next(iter(prices.values()))["as_of"]
    rules = P.load_rules(data_dir) or {}
    raw = {}
    for row in P._load(data_dir, "price_history.json"):
        if row["date"] <= date and row.get("close") not in (None, ""):
            raw.setdefault(row["ticker"], []).append(row)
    actions = P.load_corporate_actions(data_dir)
    held = {}
    for h in P._load(data_dir, "holdings.json"):
        x = held.setdefault(h["ticker"], dict(units=0, cost=0.0))
        x["units"] += h["units"]
        x["cost"] += h["units"] * h["unit_cost"]
    reserve = tr.get("reserve", {})
    reserve_left = float(reserve.get("budget", 0)) - sum(float(b["total"]) for t in tr["plans"] for b in t.get("buys", [])
                                                        if b.get("from_reserve"))
    out = []
    for t in tr["plans"]:
        if t["status"] == "closed":
            continue
        p = prices.get(t["ticker"])
        if not p:
            continue
        close = p["price"]
        rp = P.realistic_price(close, sorted(raw.get(t["ticker"], []), key=lambda x: x["date"]), rules)["real_price"]
        row = check_trade(t, rp, date, actions, tr.get("rules", {}), held.get(t["ticker"]),
                          reserve_left if t["status"] == "open" else 0.0)
        row.update(close=close, date=date)
        out.append(row)
    return out


def alerts_text(rows: list[dict]) -> str:
    """One line for the daily log and report."""
    act = [f"{r['ticker']}: " + "; ".join(a["text"] for a in r["alerts"]) for r in rows if r["alerts"]]
    return " | ".join(act)
