import datetime as dt
import os
import zipfile
from pathlib import Path

import pytest

from ngxprices import FIELDS, compare_dol_prices1, merge, validate
from ngxprices.core import _zip_member, ngx_date, to_date
from ngxprices.parsers import parse_dol, parse_prices1, parse_prices_list2, parse_shares_outstanding

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def sources():
    dol = parse_dol(FIX / "DOL_31-12-2025.pdf")
    with zipfile.ZipFile(FIX / "PRICELIST_31-12-2025.zip") as zf:
        p1 = parse_prices1(_zip_member(zf, "PRICES1"))
        pl2 = parse_prices_list2(_zip_member(zf, "PRICES_LIST2"))
    return dol, p1, pl2


@pytest.fixture(scope="module")
def shares():
    return parse_shares_outstanding(FIX / "SHARES_31-12-2025.pdf")


@pytest.fixture(scope="module")
def full_rows(sources, shares):
    dol, p1, pl2 = sources
    return {r["symbol"]: r for r in merge("2025-12-31", dol, p1, pl2, shares=shares)}


def test_dates():
    assert to_date("31-12-2025") == dt.date(2025, 12, 31)
    assert ngx_date("2025-01-02") == "02-01-2025"


def test_dol_parse(sources):
    dol, _, _ = sources
    by = {r["symbol"]: r for r in dol}
    assert len(dol) > 120
    assert {"MTNN", "DANGCEM", "GTCO", "ZENITHBANK"} <= set(by)
    assert all(r["close"] > 0 for r in dol)
    assert by["VANLEER"]["board"] == "Main Board"


def test_prices1_parse(sources):
    _, p1, _ = sources
    assert len(p1) > 100
    assert p1["ACCESSCORP"]["close"] == 21.00
    assert p1["ABBEYBDS"]["pclose"] == 6.40


def test_dol_matches_prices1(sources):
    dol, p1, _ = sources
    assert compare_dol_prices1(dol, p1) == []


def test_merge_includes_growth_board(sources):
    dol, p1, pl2 = sources
    rows = merge("2025-12-31", dol, p1, pl2)
    syms = {r["symbol"]: r for r in rows}
    assert len(syms) == len(rows)
    for s in ("CHELLARAM", "RONCHESS", "MECURE", "BAPLC", "TIP", "JULI"):
        assert syms[s]["board"] == "Growth Board"
    assert syms["JAIZBANK"]["source"] == "PRICES1"
    assert all(r["date"] == "2025-12-31" for r in rows)


def test_full_fields_present(full_rows):
    for r in full_rows.values():
        assert set(FIELDS) <= set(r)


def test_trading_activity(full_rows):
    a = full_rows["ACCESSCORP"]
    assert a["volume"] == 57601512 and a["trades"] == 2064
    assert a["value_ngn"] == 1216179886.40
    assert (a["prev_close"], a["open"], a["high"], a["low"]) == (21.35, 21.35, 21.90, 21.00)
    assert a["change"] == -0.35 and a["pct_change"] == -1.64
    staco = full_rows["STACO"]  # not traded on 31 Dec 2025
    assert staco["volume"] == 0 and staco["trades"] == 0
    assert staco["open"] == staco["high"] == staco["low"] == staco["close"] == staco["prev_close"]


def test_size(full_rows, shares):
    u = full_rows["UBA"]
    assert u["shares_outstanding"] == 41039305642
    assert u["market_cap_ngn"] == 1709287079989.30
    assert full_rows["MTNN"]["nominal_value"] == 0.02
    assert shares["ACCESSCORP"]["name"] == "ACCESS HOLDINGS PLC"  # symbol/name split
    assert full_rows["MECURE"]["shares_outstanding"] == 4_000_000_000  # Growth Board


def test_fundamentals_and_dividends(full_rows):
    c = full_rows["CUSTODIAN"]
    assert (c["eps"], c["pe"]) == (3.29, 13.06)
    assert (c["week52_high"], c["week52_low"]) == (48.30, 16.80)
    assert c["last_exdiv_date"] == "2025-08-18" and c["last_exscrip_date"] == "1996-07-07"
    assert c["div_final"] == 0.25
    z = full_rows["ZENITHBANK"]
    assert z["last_trade_date"] == "2025-12-31"  # date sits half a point lower than its row
    assert full_rows["OKOMUOIL"]["week52_low"] == 444.00


def test_cross_checks(sources, shares):
    dol, p1, pl2 = sources
    v = validate("2025-12-31", sources=dict(dol=dol, prices1=p1, plist2=pl2, shares=shares,
                                            errors=[], mislabelled=[]))
    assert v["close_dol_vs_prices1"]["mismatches"] == []
    assert v["close_dol_vs_shares"]["mismatches"] == []
    assert v["volume_prices1_vs_prices_list2"]["compared"] > 100
    assert v["volume_prices1_vs_prices_list2"]["mismatches"] == []
    assert v["market_cap_check"]["pass_rate"] >= 0.95


def test_zip_member_glob(tmp_path):
    p = tmp_path / "x.zip"
    with zipfile.ZipFile(p, "w") as zf:
        zf.writestr("some folder/prices_list2.PDF", b"a")
        zf.writestr("other/PRICES1.pdf", b"b")
    with zipfile.ZipFile(p) as zf:
        assert _zip_member(zf, "PRICES1").read() == b"b"
        assert _zip_member(zf, "PRICES_LIST2").read() == b"a"


@pytest.mark.network
@pytest.mark.skipif(not os.environ.get("NGX_NETWORK_TESTS"), reason="set NGX_NETWORK_TESTS=1")
def test_list_files_network():
    from ngxprices import list_files
    assert list_files("2025-12-31")
    assert list_files("2025-12-25") == []  # Christmas
