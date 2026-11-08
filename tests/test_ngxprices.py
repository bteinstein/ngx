import datetime as dt
import os
import zipfile
from pathlib import Path

import pytest

from ngxprices import compare_dol_prices1, merge
from ngxprices.core import _zip_member, ngx_date, to_date
from ngxprices.parsers import parse_dol, parse_prices1, parse_prices_list2

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def sources():
    dol = parse_dol(FIX / "DOL_31-12-2025.pdf")
    with zipfile.ZipFile(FIX / "PRICELIST_31-12-2025.zip") as zf:
        p1 = parse_prices1(_zip_member(zf, "PRICES1"))
        pl2 = parse_prices_list2(_zip_member(zf, "PRICES_LIST2"))
    return dol, p1, pl2


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
