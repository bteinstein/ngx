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
