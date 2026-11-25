import json

import pytest

from ngxprices import portfolio as P


@pytest.fixture()
def data(tmp_path):
    d = tmp_path
    (d / "holdings.json").write_text(json.dumps([
        {"id": "A1-AAA", "account": "Account 1", "ticker": "AAA", "name": "Aaa", "sector": "S", "units": 100, "unit_cost": 10.0},
        {"id": "A2-AAA", "account": "Account 2", "ticker": "AAA", "name": "Aaa", "sector": "S", "units": 50, "unit_cost": 12.0},
        {"id": "A1-BBB", "account": "Account 1", "ticker": "BBB", "name": "Bbb", "sector": "S", "units": 10, "unit_cost": 100.0},
    ]))
    (d / "transactions.json").write_text("[]")
    (d / "watchlist.json").write_text(json.dumps([
        {"ticker": "AAA", "rule": "low", "trigger": 11.0},
        {"ticker": "BBB", "rule": "cost", "trigger": None},
    ]))
    (d / "price_history.json").write_text(json.dumps([
        {"id": "AAA-2026-11-13", "ticker": "AAA", "date": "2026-11-13", "close": 12.0, "volume": 1000, "source": "x"},
        {"id": "BBB-2026-11-13", "ticker": "BBB", "date": "2026-11-13", "close": 110.0, "volume": 10, "source": "x"},
    ]))
    (d / "prices_2026-11-13.json").write_text(json.dumps([
        {"ticker": "AAA", "name": "Aaa Plc", "price": 12.0, "as_of": "2026-11-13", "prev_close": 12.0, "chg_1d_pct": 0},
        {"ticker": "BBB", "name": "Bbb Plc", "price": 110.0, "as_of": "2026-11-13", "prev_close": 110.0, "chg_1d_pct": 0},
    ]))
    (d / "daily_log.json").write_text(json.dumps([
        {"date": "2026-11-13", "value": 2900.0, "cost": 2600.0, "gain": 300.0, "cash_in": 0, "day_pl": None,
         "day_pl_pct": None, "holdings": 2, "note": "hand-written"},
    ], indent=1))
    return d


def day(kind, aaa, bbb, vol_a=5000):
    label = P.OFFICIAL_SOURCE if kind == "official" else P.LIVE_PREFIX + ", test"
    return {"date": "2026-11-16", "kind": kind, "label": label, "rows": {
        "AAA": {"symbol": "AAA", "name": "AAA PLC", "close": aaa, "prev_close": 12.0, "volume": vol_a, "trades": 9, "value_ngn": 1.0},
        "BBB": {"symbol": "BBB", "name": "BBB PLC", "close": bbb, "prev_close": 110.0, "volume": 10, "trades": 1, "value_ngn": 2.0},
    }}


def test_cost_and_units(data):
    units, cost = P.units_and_cost(data)
    assert units == {"AAA": 150, "BBB": 10} and cost == 2600.0


def test_live_day_then_official_upgrade(data):
    s = P.upsert_day(day("live", 10.0, 120.0), data)
    assert s["value"] == 150 * 10.0 + 10 * 120.0 and s["day_pl"] == 2700.0 - 2900.0
    wl = {w["ticker"]: w for w in s["watchlist"]}
    assert wl["AAA"]["breach"] and not wl["BBB"]["breach"]
    assert wl["BBB"]["trigger"] == 100.0  # average cost
    assert s["volume"][0]["ticker"] == "AAA" and s["volume"][0]["ratio"] == 5.0
    log = json.loads((data / "daily_log.json").read_text())
    assert log[0]["note"] == "hand-written" and log[1]["auto_note"] and "AAA 10.00 below 11.00" in log[1]["note"]
    # official figures replace the live rows, no duplicates, auto note regenerated
    s2 = P.upsert_day(day("official", 11.5, 120.0, vol_a=6000), data)
    ph = json.loads((data / "price_history.json").read_text())
    rows = [r for r in ph if r["date"] == "2026-11-16"]
    assert len(rows) == 2 and all(r["source"] == P.OFFICIAL_SOURCE for r in rows)
    assert next(r for r in rows if r["ticker"] == "AAA")["volume"] == 6000
    log = json.loads((data / "daily_log.json").read_text())
    assert len(log) == 2 and log[1]["value"] == s2["value"] == 150 * 11.5 + 1200
    assert "all above their triggers" in log[1]["note"]
    prices = json.loads((data / "prices_2026-11-16.json").read_text())
    assert {p["ticker"]: p["name"] for p in prices}["AAA"] == "Aaa Plc"  # display names kept


def test_missing_held_price_refused(data):
    d = day("live", 10.0, 120.0)
    del d["rows"]["BBB"]
    with pytest.raises(RuntimeError):
        P.upsert_day(d, data)


def test_stage(data, tmp_path):
    P.upsert_day(day("live", 10.0, 120.0), data)
    out = P.stage_dashboard_files(data, tmp_path / "stage")
    assert out["prices"].endswith("prices_2026-11-16.json") and out["daily"].endswith("daily_2026-11-16.json")


def test_rules_loss_trail_warn(data):
    (data / "rules.json").write_text(json.dumps({"loss_limit_pct": 20, "warn_pct": 10, "trail_pct": 15,
                                                "trail_min_peak_gain_pct": 20}))
    ph = json.loads((data / "price_history.json").read_text())
    ph.append({"id": "BBB-2026-11-12", "ticker": "BBB", "date": "2026-11-12", "close": 150.0, "volume": 1, "source": "x"})
    (data / "price_history.json").write_text(json.dumps(ph))
    # AAA avg cost 10.6667: 8.0 is past -20%; BBB peak 150 (+50%), 120 is 20% off peak -> trail
    s = P.upsert_day(day("official", 8.0, 120.0), data)
    wl = {w["ticker"]: w for w in s["watchlist"]}
    assert wl["AAA"]["status"] == "loser" and wl["AAA"]["rule"] == "loss_limit" and wl["AAA"]["trigger"] == 8.53
    assert wl["BBB"]["status"] == "trail" and wl["BBB"]["trigger"] == 127.5 and wl["BBB"]["peak"] == 150.0
    gen = json.loads((data / "watchlist.json").read_text())
    assert {w["ticker"]: w["rule"] for w in gen} == {"AAA": "loss_limit", "BBB": "trailing"}
    assert "past the loss limit: AAA" in json.loads((data / "daily_log.json").read_text())[-1]["note"]
    # warning band, and trailing inactive when the peak gain is under 20%
    s = P.upsert_day(day("official", 9.5, 130.0), data)
    wl = {w["ticker"]: w for w in s["watchlist"]}
    assert wl["AAA"]["status"] == "warn" and wl["AAA"]["trail_level"] is None  # AAA peak 12 is only +12.5%
    assert wl["BBB"]["status"] == "ok"


def test_early_warning_lights():
    rules = {"warn_pct": 10}
    base = dict(status="ok", trail_level=90.0, off_peak_pct=-11.0, gap_pct=3.0, gain_pct=50.0)
    days = [f"2026-10-{d:02d}" for d in range(1, 32)] + [f"2026-11-{d:02d}" for d in range(1, 18)]
    hist = [{"date": d, "close": 100.0, "volume": 100} for d in days[-30:]]
    hist[-1] = {"date": days[-1], "close": 90.0, "volume": 300}  # -10% on 3x volume
    ew = P.early_warning(base, hist, rules, "2026-11-17")
    assert ew["light"] == "amber" and len(ew["tolerance_signals"]) == 2
    assert any("heavy volume" in g for g in ew["general_signs"]) and any("limit-down" in g for g in ew["general_signs"])
    flat = [{"date": d, "close": 100.0, "volume": 100} for d in days[-30:]]
    assert P.early_warning(base, flat, rules, "2026-11-17")["light"] == "watch"
    calm = dict(base, off_peak_pct=-2.0, gap_pct=15.0)
    assert P.early_warning(calm, hist, rules, "2026-11-17")["light"] == "note"
    assert P.early_warning(calm, flat, rules, "2026-11-17")["light"] == "green"
    assert P.early_warning(dict(base, status="trail"), flat, rules, "2026-11-17")["light"] == "red"


def test_take_profit():
    rules = {}
    r = dict(close=300.0, gain_pct=200.0)
    tp = P.take_profit(r, 1000, 100000.0, 1_000_000.0, [], rules)
    kinds = {x["kind"]: x for x in tp["take_profit"]}
    assert kinds["target"]["units"] == 500 and "+50% and +100%" in kinds["target"]["text"]
    assert kinds["recover_cost"]["units"] == 341  # 100,000 / (300 x 0.98) rounded up
    assert kinds["size_cap"]["units"] == 500 and tp["weight_pct"] == 30.0  # 300K of 1M, cap 15%
    # one sell since the rules were set = first target taken
    tp = P.take_profit(r, 750, 100000.0, 10_000_000.0, [{"total": 40000.0}], rules)
    assert [x["kind"] for x in tp["take_profit"]] == ["target", "recover_cost"]
    assert tp["take_profit"][0]["units"] == 187 and "+100%" in tp["take_profit"][0]["text"]
    assert P.take_profit(dict(close=110.0, gain_pct=10.0), 10, 1000.0, 1e6, [], rules)["take_profit"] == []


def test_adjusted_history_dividend_and_reconstruction():
    rows = [{"ticker": "ZZ", "date": "2026-10-07", "close": 7.7, "volume": 1000},
            {"ticker": "ZZ", "date": "2026-10-08", "close": 77.0, "volume": 10},
            {"ticker": "DD", "date": "2026-10-23", "close": 120.9, "volume": 5},
            {"ticker": "DD", "date": "2026-10-26", "close": 119.4, "volume": 5}]
    acts = [{"ticker": "ZZ", "ex_date": "2026-10-08", "type": "reconstruction", "old_per_new": 10},
            {"ticker": "DD", "ex_date": "2026-10-26", "type": "dividend", "amount": 1.5}]
    a = {(r["ticker"], r["date"]): r for r in P.adjusted_history(rows, acts)}
    assert a[("ZZ", "2026-10-07")]["close"] == 77.0 and a[("ZZ", "2026-10-07")]["volume"] == 100
    assert a[("ZZ", "2026-10-07")]["raw_close"] == 7.7 and "raw_close" not in a[("ZZ", "2026-10-08")]
    assert a[("DD", "2026-10-23")]["close"] == 119.4 and a[("DD", "2026-10-26")]["close"] == 119.4
    assert rows[0]["close"] == 7.7  # input untouched


def test_peak_from_and_accounts(data):
    (data / "rules.json").write_text(json.dumps({"loss_limit_pct": 20, "warn_pct": 10, "trail_pct": 15,
                                                "trail_min_peak_gain_pct": 20, "peak_from_default": "2026-11-01"}))
    ph = json.loads((data / "price_history.json").read_text())
    ph.append({"id": "BBB-2026-10-01", "ticker": "BBB", "date": "2026-10-01", "close": 200.0, "volume": 1, "source": "x"})
    ph.append({"id": "BBB-2026-11-12", "ticker": "BBB", "date": "2026-11-12", "close": 150.0, "volume": 1, "source": "x"})
    (data / "price_history.json").write_text(json.dumps(ph))
    rows = {r["ticker"]: r for r in P.rules_status(data, "2026-11-13")}
    assert rows["BBB"]["peak"] == 150.0 and rows["BBB"]["peak_from"] == "2026-11-01"  # 1 Oct peak is before
    assert rows["BBB"]["accounts"] == []
    acc = rows["AAA"]["accounts"]
    assert [(a["account"], a["units"], a["gain_pct"]) for a in acc] == [("Account 1", 100, 20.0), ("Account 2", 50, 0.0)]
    h = json.loads((data / "holdings.json").read_text())
    h[2]["bought_from"] = "2026-09-01"
    (data / "holdings.json").write_text(json.dumps(h))
    rows = {r["ticker"]: r for r in P.rules_status(data, "2026-11-13")}
    assert rows["BBB"]["peak"] == 200.0 and rows["BBB"]["peak_from"] == "2026-09-01"


def test_dashboard_build(data, tmp_path):
    from ngxprices import dashboard as D
    (data / "accounts.json").write_text(json.dumps([{"account": "Account 1", "broker": "B", "short": "B", "cscs": "SECRET-1"}]))
    tpl = tmp_path / "t.html"
    tpl.write_text("<script>const DATA = " + D.MARK + ";</script>")
    out = tmp_path / "o" / "index.html"
    info = D.build(data, tpl, out)
    assert info["date"] == "2026-11-13" and info["holdings"] == 3
    html = out.read_text()
    assert "SECRET-1" not in html and D.MARK not in html
    blob = json.loads(html.split("const DATA = ", 1)[1].rsplit(";</script>", 1)[0])
    assert blob["history"]["AAA"] == {"d": ["2026-11-13"], "c": [12.0], "v": [1000]}
    assert blob["source"] == "x" and len(blob["status"]) >= 1


def test_realistic_price_stale_and_block():
    hist = [{"date": f"2026-11-{d:02d}", "close": 100.0, "volume": 1000, "value_ngn": 90000.0} for d in range(1, 21)]
    rp = P.realistic_price(100.0, hist, {})
    assert rp["real_price"] == 90.0 and "unchanged" in rp["price_note"] and rp["max_units_day"] == 200
    moving = [dict(x, close=100.0 + i) for i, x in enumerate(hist)]
    assert P.realistic_price(119.0, moving, {})["real_price"] == 119.0  # close moves: not stale
    moving[-1] = dict(moving[-1], volume=10000, value_ngn=10000 * 107.0)  # block at -10%
    rp = P.realistic_price(119.0, moving, {})
    assert rp["real_price"] == 107.0 and "block" in rp["price_note"]
    junk = [dict(x, value_ngn=1.0) for x in hist]  # absurd trade prices are ignored
    assert P.realistic_price(100.0, junk, {})["real_price"] == 100.0


def test_eps_view_and_horizon_signals():
    res = [{"ticker": "X", "period": p, "eps": e} for p, e in
           [("H1 2025", 10), ("H1 2026", 8), ("9M 2025", 15), ("9M 2026", 12), ("FY 2025", 20)]]
    v = P.eps_view(res, "X")
    assert v["ttm_eps"] == 17 and v["latest_fell"] and v["thesis_broken"]
    hz = {k: dict(P.HZ_DEFAULTS[k]) for k in P.HZ_DEFAULTS}
    s = P.horizon_signals("short", v, "2026-11-20", "2026-11-24", hz)
    assert len(s) == 1 and s[0].startswith("earnings stop")
    assert any(x.startswith("time stop") for x in P.horizon_signals("short", v, "2026-09-01", "2026-11-24", hz))
    assert P.horizon_signals("long", v, "2026-11-20", "2026-11-24", hz)[0].startswith("thesis check")
    up = P.eps_view([dict(r, eps=r["eps"] * (2 if "2026" in r["period"] else 1)) for r in res], "X")
    assert not up["thesis_broken"] and P.horizon_signals("long", up, "2026-01-01", "2026-11-24", hz) == []
    # bonus issue: prior-year EPS restated on the new share count clears a false fall
    bonus = [dict(r, prior_eps_restated=11) if r["period"] == "9M 2026" else r for r in res]
    assert not P.eps_view(bonus, "X")["thesis_broken"]


def test_take_profit_by_horizon():
    # short term: +30% sells half; long term: no targets but recover cost and P/E ceiling
    r = dict(close=150.0, real_price=150.0, gain_pct=50.0, horizon="short", max_units_day=100)
    tp = P.take_profit(r, 1000, 100000.0, 1e7, [], {})["take_profit"]
    assert tp[0]["kind"] == "target" and tp[0]["units"] == 500 and "over about 5 days" in tp[0]["text"]
    r = dict(close=300.0, real_price=300.0, gain_pct=200.0, horizon="long", pe=30.0)
    kinds = [x["kind"] for x in P.take_profit(r, 1000, 100000.0, 1e7, [], {})["take_profit"]]
    assert kinds == ["recover_cost", "pe_ceiling"]
    # fee check: a stale close shows +11% but the realistic price is break-even -> no target; size cap says loss
    r = dict(close=1656.8, real_price=1498.0, gain_pct=0.02, horizon=None)
    tp = P.take_profit(r, 1030, 1030 * 1497.65, 1030 * 1498 / 0.17, [], {})["take_profit"]
    assert [x["kind"] for x in tp] == ["size_cap"] and "at a loss after fees" in tp[0]["text"]
