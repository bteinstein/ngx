"""PDF parsers for NGX daily documents.

* ``parse_dol``          - "Daily Official List - Equities for DD-MM-YYYY.pdf" (position based)
* ``parse_prices1``      - PRICES1.pdf inside the "GAINERS AND PRICE LIST" zip (traded securities)
* ``parse_prices_list2`` - PRICES_LIST2.pdf inside the same zip (full list by board, by company name)

All functions accept a path or a binary file-like object.
"""
from __future__ import annotations

import re

import pdfplumber

# ---------------------------------------------------------------- helpers

def _num(s):
    if s is None:
        return None
    s = s.strip()
    if s in ("", "-"):
        return None
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


# ---------------------------------------------------------------- Daily Official List

# column x-ranges (pdf points) of the DOL equities table
DOL_COLS = [("name", 90, 190), ("par", 190, 236), ("open", 236, 305), ("close_col", 305, 368),
            ("mkt", 368, 430), ("exdiv", 430, 490), ("bdprice", 490, 528), ("bddate", 528, 582),
            ("qty", 582, 620)]
DOL_BOARDS = {"EQTY": "Main Board", "PREMIUM": "Premium Board", "ASeM": "ASeM",
              "REITCEF": "REIT & Closed-End Fund", "GROWTH": "Growth Board",
              "NONINT": "Non-Interest Finance Board", "NI": "Non-Interest Finance Board"}


def _dol_col(x):
    for n, a, b in DOL_COLS:
        if a <= x < b:
            return n
    return None


def parse_dol(src) -> list[dict]:
    """Parse the Daily Official List (Equities). Close = "Current Market Price" column."""
    rows = []
    board = sector = sub = None
    with pdfplumber.open(src) as pdf:
        for pg in pdf.pages:
            lines: dict[int, list] = {}
            for w in pg.extract_words():
                lines.setdefault(round(w["top"]), []).append(w)
            cur = None
            for top in sorted(lines):
                L = sorted(lines[top], key=lambda w: w["x0"])
                txt = " ".join(w["text"] for w in L)
                m = re.match(r"^(\S+) - (.+)", txt)
                if m and (m.group(1) in DOL_BOARDS or "Non-Interest" in m.group(2) or "Non Interest" in m.group(2)) \
                        and m.group(1) != "Ex":
                    board = DOL_BOARDS.get(m.group(1), m.group(2).strip())
                    cur = None
                    continue
                f = L[0]
                if f["x0"] < 90 and len(L) > 1 and L[1]["x0"] >= 90 and re.fullmatch(r"[A-Z0-9][A-Z0-9&.\-]*", f["text"]):
                    r = {"board": board, "sector": sector, "subsector": sub, "symbol": f["text"]}
                    for w in L[1:]:
                        if w["x0"] >= 620:
                            continue
                        c = _dol_col((w["x0"] + w["x1"]) / 2)
                        if c:
                            r[c] = (r.get(c, "") + " " + w["text"]).strip()
                    if _num(r.get("par")) is not None and _num(r.get("mkt")) is not None:
                        rows.append(r)
                        cur = r
                        continue
                if cur and all(90 <= w["x0"] < 190 for w in L):  # wrapped company name
                    cur["name"] = (cur.get("name", "") + " " + txt).strip()
                    continue
                cur = None
                if f["x0"] < 90 and txt.isupper() and not re.search(r"\d", txt):
                    sector = txt
                elif 60 <= f["x0"] < 90 and "Ex - Business" not in txt and not re.search(r"\d", txt) \
                        and not txt.startswith(("Public", "Quotation", "Symbol")):
                    sub = txt
    out: dict[str, dict] = {}
    for r in rows:
        if r["symbol"] in out:
            continue
        dm = re.search(r"\d\d/\d\d/\d\d", r.get("bddate", ""))
        out[r["symbol"]] = dict(
            symbol=r["symbol"], name=r.get("name", ""), board=r["board"], sector=r["sector"],
            subsector=r["subsector"], par=_num(r["par"]), close=_num(r["mkt"]),
            last_trade=_num(r.get("bdprice")), last_trade_date=dm.group(0) if dm else "")
    return list(out.values())


# ---------------------------------------------------------------- PRICES1

_P1_ROW = re.compile(r"^(\d+) (\S+)" + r" (\S+)" * 13 + r"$")


def parse_prices1(src) -> dict[str, dict]:
    """Parse PRICES1.pdf, equity section only. Returns symbol -> record."""
    out: dict[str, dict] = {}
    section = None
    with pdfplumber.open(src) as p:
        for pg in p.pages:
            for line in (pg.extract_text() or "").split("\n"):
                if line.startswith("PRICES FOR"):
                    section = line
                    continue
                if not section or "EQUITY" not in section:
                    continue
                m = _P1_ROW.match(line)
                if m:
                    g = m.groups()
                    # S/N SYM PCLOSE OOPEN OPEN HIGH LOW %SPREAD OCLOSE CLOSE CHANGE %CHANGE TRADES VOLUME VALUE
                    out.setdefault(g[1], dict(
                        symbol=g[1], pclose=_num(g[2]), open=_num(g[4]), high=_num(g[5]), low=_num(g[6]),
                        close=_num(g[9]), trades=_num(g[12]), volume=_num(g[13]), value=_num(g[14])))
    return out


# ---------------------------------------------------------------- PRICES_LIST2

_PL2_ROW = re.compile(r"^(\d+) (.+?) ([\d,]+\.\d+) ([\d,]+\.\d+) (\S+) ([\d,]+) ([\d,]+)$")


def parse_prices_list2(src) -> list[dict]:
    """Parse PRICES_LIST2.pdf equities lists (by board, by company name). Mutual funds skipped."""
    rows = []
    kind = board = sector = sub = None
    with pdfplumber.open(src) as p:
        for pg in p.pages:
            for line in (pg.extract_text() or "").split("\n"):
                if line.startswith("Price List ("):
                    kind = line
                    continue
                if line.startswith("PRICES FOR"):
                    board = line[11:].replace(" SECURITIES", "").strip()
                    continue
                m = re.match(r"^S/N (.+) MARKET CAP\(Nm\) PRICE", line)
                if m:
                    sub = m.group(1)
                    continue
                m = _PL2_ROW.match(line)
                if m and kind and "Equities" in kind:
                    if board == "MUTUAL FUND":
                        continue
                    rows.append(dict(name=m.group(2), mcap_m=_num(m.group(3)), price=_num(m.group(4)),
                                     board=board, sector=sector, subsector=sub,
                                     trades=_num(m.group(6)), volume=_num(m.group(7))))
                elif line.isupper() and not re.search(r"\d", line) and len(line) < 40:
                    sector = line
    return rows


# ---------------------------------------------------------------- embedded date

def pdf_as_of(src) -> str | None:
    """Return the trading date printed on page 1 as DD-MM-YYYY (e.g. "Daily Official List (Equities)
    For 06/03/2025" or "Prices for Securities Traded as of 07/03/2025"). NGX occasionally uploads a
    file under the wrong date, so callers should compare this with the requested date."""
    with pdfplumber.open(src) as p:
        txt = p.pages[0].extract_text() or ""
    for line in txt.split("\n")[:4]:
        m = re.search(r"(?:For|as of|End Date)\s+(\d\d)/(\d\d)/(\d{4})", line, re.I)
        if m:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None
