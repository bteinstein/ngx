"""PDF parsers for NGX daily documents.

* ``parse_dol``          - "Daily Official List - Equities for DD-MM-YYYY.pdf" (position based)
* ``parse_prices1``      - PRICES1.pdf inside the "GAINERS AND PRICE LIST" zip (traded securities)
* ``parse_prices_list2`` - PRICES_LIST2.pdf inside the same zip (full list by board, by company name)
* ``parse_shares_outstanding`` - "SHARES OUTSTANDING FOR DD-MM-YYYY.pdf" (position based)

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


def _iso(d: str) -> str:
    """dd/mm/yy -> yyyy-mm-dd ('' if not a valid date). yy < 70 -> 20yy, else 19yy."""
    m = re.fullmatch(r"(\d\d)/(\d\d)/(\d\d)", d or "")
    if not m:
        return ""
    dd, mm, yy = (int(x) for x in m.groups())
    if not (1 <= dd <= 31 and 1 <= mm <= 12):
        return ""
    return f"{2000 + yy if yy < 70 else 1900 + yy:04d}-{mm:02d}-{dd:02d}"


# Right-hand DOL columns (x positions of their header text). Their words run together in the
# text layer ("48.3016.8018/08/25..."), so they are rebuilt from the character stream: a token
# ends at a space, a gap, or where x moves backwards (the next column's text starts).
_DOL_DATE_COLS = [(664.1, "last_exdiv_date"), (683.8, "last_exscrip_date"), (703.6, "div_paid_date")]
_DOL_NUM_COLS = [(720.0, 740.0, "div_interim"), (740.0, 760.0, "div_final"),
                 (760.0, 780.0, "eps"), (780.0, 830.0, "pe")]


_DOL_PIECE = re.compile(r"\d\d/\d\d/\d\d|-?(?:\d{1,3}(?:,\d{3})+|\d+)\.\d{2}")


def _dol_right(chars, top) -> dict:
    row = [c for c in chars if abs(c["top"] - top) < 1.5 and c["x0"] >= 490]
    toks, cur, prev = [], [], None
    for c in row:  # stream order
        brk = (c["text"].isspace() or prev is None or c["x0"] < prev["x0"] - 0.5
               or c["x0"] - prev["x1"] > 2.5)
        if brk and cur:
            toks.append(cur)
            cur = []
        if not c["text"].isspace():
            cur.append(c)
        prev = c
    if cur:
        toks.append(cur)
    out: dict = {}
    wk = []
    pieces = []
    for t in toks:
        txt = "".join(c["text"] for c in t)
        if t[0]["x0"] < 620 and not re.search(r"/", txt):
            pieces.append((txt, t[0]["x0"]))
            continue
        # values can still run together ("48.3016.80", "16.8018/08/25"); every value here is a
        # 2-decimal number or a dd/mm/yy date, so split on those shapes
        ms = list(_DOL_PIECE.finditer(txt))
        if not ms:
            continue
        for m in ms:
            pieces.append((m.group(0), t[m.start()]["x0"]))
    for txt, x in pieces:
        if x < 528:
            out["last_trade"] = _num(txt)
        elif x < 582:
            if re.fullmatch(r"\d\d/\d\d/\d\d", txt):
                out["last_trade_date"] = _iso(txt)
        elif x < 620:
            out["last_trade_qty"] = _num(txt)
        elif x < 663 and not re.search(r"/", txt):
            wk.append(_num(txt))
        elif re.fullmatch(r"\d\d/\d\d/\d\d", txt):
            name = min(_DOL_DATE_COLS, key=lambda h: abs(h[0] - x))[1]
            out[name] = _iso(txt)
        else:
            for a, b, name in _DOL_NUM_COLS:
                if a <= x < b:
                    out[name] = _num(txt)
                    break
    if wk:
        out["week52_high"] = wk[0]
    if len(wk) > 1:
        out["week52_low"] = wk[1]
    return out


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
                        r["_right"] = _dol_right(pg.chars, f["top"])
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
        rec = dict(
            symbol=r["symbol"], name=r.get("name", ""), board=r["board"], sector=r["sector"],
            subsector=r["subsector"], par=_num(r["par"]), close=_num(r["mkt"]),
            last_trade=_num(r.get("bdprice")), last_trade_date=_iso(dm.group(0)) if dm else "")
        rec.update({k: v for k, v in r.get("_right", {}).items() if v not in (None, "")})
        out[r["symbol"]] = rec
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
                        symbol=g[1], pclose=_num(g[2]), official_open=_num(g[3]), open=_num(g[4]),
                        high=_num(g[5]), low=_num(g[6]), pct_spread=_num(g[7]), official_close=_num(g[8]),
                        close=_num(g[9]), change=_num(g[10]), pct_change=_num(g[11]),
                        trades=_num(g[12]), volume=_num(g[13]), value=_num(g[14])))
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
                                     pct_change=_num(m.group(5)),
                                     board=board, sector=sector, subsector=sub,
                                     trades=_num(m.group(6)), volume=_num(m.group(7))))
                elif line.isupper() and not re.search(r"\d", line) and len(line) < 40:
                    sector = line
    return rows


# ---------------------------------------------------------------- SHARES OUTSTANDING

# x-ranges of the numeric columns; the symbol is every character left of SO_NAME_X
# (symbol and name run together in the text layer, e.g. "ACCESSCORPACCESS HOLDINGS PLC").
SO_NAME_X = 91.5
SO_COLS = [("nominal_value", 265, 318), ("close", 318, 368), ("shares_outstanding", 368, 462),
           ("market_cap", 462, 600)]


def parse_shares_outstanding(src) -> dict[str, dict]:
    """Parse "SHARES OUTSTANDING FOR DD-MM-YYYY.pdf" (every listed equity, by symbol).

    Returns symbol -> {symbol, name, nominal_value, close, shares_outstanding, market_cap}.
    """
    out: dict[str, dict] = {}
    with pdfplumber.open(src) as pdf:
        for pg in pdf.pages:
            lines: dict[int, list] = {}
            for c in pg.chars:
                if not c["text"].isspace():
                    lines.setdefault(round(c["top"]), []).append(c)
            for top in sorted(lines):
                cs = sorted(lines[top], key=lambda c: c["x0"])
                sym = "".join(c["text"] for c in cs if c["x0"] < SO_NAME_X)
                if not re.fullmatch(r"[A-Z0-9][A-Z0-9&.\-]*", sym or ""):
                    continue
                words = [w for w in pg.extract_words() if abs(w["top"] - cs[0]["top"]) < 2]
                rec = dict(symbol=sym, name=" ".join(w["text"] for w in words if SO_NAME_X <= w["x0"] < 265
                                                      or (w["x0"] < SO_NAME_X < w["x1"])))
                for w in words:
                    mid = (w["x0"] + w["x1"]) / 2
                    for name, a, b in SO_COLS:
                        if a <= mid < b:
                            rec[name] = _num(w["text"])
                if rec.get("shares_outstanding") is None or rec.get("nominal_value") is None:
                    continue
                if rec["name"].startswith(sym):  # run-together first word
                    rec["name"] = rec["name"][len(sym):]
                out.setdefault(sym, rec)
    return out


# ---------------------------------------------------------------- embedded date

def pdf_as_of(src) -> str | None:
    """Return the trading date printed on page 1 as DD-MM-YYYY (e.g. "Daily Official List (Equities)
    For 06/03/2025", "Prices for Securities Traded as of 07/03/2025" or "List of Equities as of Date
    31/12/2025"). NGX occasionally uploads a
    file under the wrong date, so callers should compare this with the requested date."""
    with pdfplumber.open(src) as p:
        txt = p.pages[0].extract_text() or ""
    for line in txt.split("\n")[:4]:
        m = re.search(r"(?:For|as of(?: Date)?|End Date)\s+(\d\d)/(\d\d)/(\d{4})", line, re.I)
        if m:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None
