"""High level API: list_files, get_daily_prices, get_range, get_live_prices."""
from __future__ import annotations

import datetime as dt
import difflib
import io
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import quote, unquote

from .http import Fetcher
from .parsers import parse_dol, parse_prices1, parse_prices_list2, parse_shares_outstanding, pdf_as_of

BASE = "https://doclib.ngxgroup.com"
INDEX_URL = (BASE + "/_api/Web/Lists/GetByTitle('DownloadsContent')/items"
             "?$select=Title,EncodedAbsUrl,Created,Modified&$filter=substringof('{d}',Title)&$top=100")
DOL_TITLE = "Daily Official List - Equities for {d}"
ZIP_TITLE = "GAINERS AND PRICE LIST FOR {d}"
SO_TITLE = "SHARES OUTSTANDING FOR {d}"
LIVE_URL = BASE + "/REST/api/statistics/equities/?market=&sector=&orderby=&pageSize=300&pageNo=0"

# Growth Board companies appear in PRICES_LIST2 by name only.
GROWTH_SYMBOLS = {
    "CHELLARAMS PLC.": "CHELLARAM", "RONCHESS GLOBAL RESOURCES PLC": "RONCHESS",
    "MCNICHOLS PLC": "MCNICHOLS", "LIVINGTRUST MORTGAGE BANK PLC": "LIVINGTRUST",
    "MECURE INDUSTRIES PLC": "MECURE", "BRICLINKS AFRICA PLC": "BAPLC",
    "THE INITIATES PLC": "TIP", "JULI PLC.": "JULI",
    "ZICHIS AGRO ALLIED INDUSTRIES PLC": "ZICHIS",
}
# Other name -> symbol mappings for stocks that the DOL sometimes omits (e.g. suspended).
EXTRA_SYMBOLS = {"GREIF NIGERIA PLC": "VANLEER"}
# Metadata for symbols that may only appear in PRICES1 (symbol -> name, board, sector, subsector).
PRICES1_META = {"JAIZBANK": ("JAIZ BANK PLC", "Non-Interest Finance Board", "FINANCIAL SERVICES", "Banking")}

BOARD_NAMES = {"PREMIUM BOARD": "Premium Board", "MAIN BOARD": "Main Board", "GROWTH BOARD": "Growth Board",
               "ASEM": "ASeM", "NON-INTEREST FINANCE BOARD": "Non-Interest Finance Board",
               "REAL ESTATE INVESTMENT TRUST & CLOSE END FUND": "REIT & Closed-End Fund"}

BASIC_FIELDS = ["date", "symbol", "name", "board", "sector", "subsector", "close", "source"]
FIELDS = BASIC_FIELDS[:-1] + [
    # trading activity
    "prev_close", "open", "high", "low", "change", "pct_change", "trades", "volume", "value_ngn",
    # size
    "nominal_value", "shares_outstanding", "market_cap_ngn",
    # fundamentals (Daily Official List)
    "week52_high", "week52_low", "last_trade_price", "last_trade_date", "last_trade_qty", "eps", "pe",
    # dividends (Daily Official List; best effort)
    "last_exdiv_date", "last_exscrip_date", "div_paid_date", "div_interim", "div_final",
    # provenance
    "source", "sources_used"]

_default_fetcher: Fetcher | None = None


def _fetcher(f: Fetcher | None) -> Fetcher:
    global _default_fetcher
    if f is not None:
        return f
    if _default_fetcher is None:
        _default_fetcher = Fetcher()
    return _default_fetcher


def to_date(d) -> dt.date:
    if isinstance(d, dt.datetime):
        return d.date()
    if isinstance(d, dt.date):
        return d
    s = str(d).strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y%m%d"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Unrecognised date: {d!r}")


def ngx_date(d) -> str:
    return to_date(d).strftime("%d-%m-%Y")


# ---------------------------------------------------------------- index

def list_files(date, fetcher: Fetcher | None = None, use_cache: bool = True) -> list[dict]:
    """List every document NGX published for ``date`` (via the SharePoint REST index).

    Returns [{title, url, created, modified}] (times are UTC ISO strings). Empty list = no files
    (non-trading day, or not yet published). Index results for dates older than 3 days are cached.
    """
    f = _fetcher(fetcher)
    d = to_date(date)
    nd = ngx_date(d)
    cache = f.cache_dir / "index" / f"{nd}.json"
    if use_cache and cache.exists():
        return json.loads(cache.read_text())
    r = f.get(INDEX_URL.format(d=nd), headers={"Accept": "application/json;odata=verbose"})
    items = r.json()["d"]["results"]
    # substringof can over-match; keep titles whose date token equals nd exactly
    out = [dict(title=i["Title"], url=i["EncodedAbsUrl"], created=i.get("Created"), modified=i.get("Modified"))
           for i in items if re.search(rf"(?<![\d]){re.escape(nd)}(?![\d])", i["Title"] or "")]
    if use_cache and out and (dt.date.today() - d).days > 3:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(out, indent=1))
    return out


def _find(files: list[dict], title: str) -> dict | None:
    """Match by title, or by URL file name (titles are sometimes wrong in the index)."""
    t = title.lower()
    hit = next((x for x in files if (x["title"] or "").strip().lower() == t), None)
    if hit:
        return hit
    return next((x for x in files if re.sub(r"\.\w+$", "", unquote(x["url"].rsplit("/", 1)[-1])).lower() == t), None)


def find_file(files: list[dict], title: str) -> dict | None:
    return _find(files, title)


def _url_for(files, title, ext):
    x = _find(files, title)
    if x:
        return x["url"]
    return f"{BASE}/DownloadsContent/{quote(title)}.{ext}"


def _zip_member(zf: zipfile.ZipFile, stem: str) -> io.BytesIO | None:
    """Find e.g. PRICES1.pdf anywhere in the zip (case-insensitive, any folder)."""
    pat = re.compile(rf"(^|/){re.escape(stem)}[^/]*\.pdf$", re.I)
    names = [n for n in zf.namelist() if pat.search(n)]
    if stem.upper() == "PRICES1":  # don't confuse with PRICES_LIST*
        names = [n for n in names if re.search(r"(^|/)PRICES1[^/]*\.pdf$", n, re.I)]
    if not names:
        return None
    return io.BytesIO(zf.read(sorted(names, key=len)[0]))


def _norm(n: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (n or "").upper())


# ---------------------------------------------------------------- daily

def _checked(src, nd: str, label: str, errors: list, wrong: list):
    """Return src if its embedded date matches nd, else record an error and return None."""
    as_of = pdf_as_of(src)
    if hasattr(src, "seek"):
        src.seek(0)
    if as_of and as_of != nd:
        errors.append(f"{label} is mislabelled: file for {nd} contains data for {as_of}; ignored")
        wrong.append(label)
        return None
    return src


def fetch_sources(date, fetcher: Fetcher | None = None, files: list[dict] | None = None,
                  check_dates: bool = True) -> dict:
    """Download + parse the raw sources for a date.

    Returns dict(files, dol (list), prices1 (dict), plist2 (list), shares (dict), errors (list),
    mislabelled (list)).
    A document whose printed trading date differs from ``date`` is ignored (recorded in errors).
    """
    f = _fetcher(fetcher)
    nd = ngx_date(date)
    files = list_files(date, f) if files is None else files
    res = dict(files=files, dol=[], prices1={}, plist2=[], shares={}, errors=[], mislabelled=[])
    errs, wrong = res["errors"], res["mislabelled"]
    if not files:
        errs.append("no files published for this date")
        return res

    def chk(src, label):
        return _checked(src, nd, label, errs, wrong) if check_dates else src

    # Daily Official List
    try:
        p = f.download(_url_for(files, DOL_TITLE.format(d=nd), "pdf"), nd, "DOL.pdf")
        if p is None:
            errs.append("Daily Official List (Equities) PDF not published")
        elif chk(p, "DOL") is not None:
            res["dol"] = parse_dol(p)
    except Exception as e:  # noqa: BLE001
        errs.append(f"DOL: {type(e).__name__}: {e}")
    # Gainers & price list zip
    try:
        p = f.download(_url_for(files, ZIP_TITLE.format(d=nd), "zip"), nd, "PRICELIST.zip")
        if p is None:
            errs.append("price-list zip not published")
        else:
            with zipfile.ZipFile(p) as zf:
                b = _zip_member(zf, "PRICES1")
                if b is None:
                    errs.append("PRICES1.pdf missing in zip")
                elif chk(b, "PRICES1") is not None:
                    res["prices1"] = parse_prices1(b)
                b = _zip_member(zf, "PRICES_LIST2")
                if b is None:
                    errs.append("PRICES_LIST2.pdf missing in zip")
                elif chk(b, "PRICES_LIST2") is not None:
                    res["plist2"] = parse_prices_list2(b)
    except Exception as e:  # noqa: BLE001
        errs.append(f"zip: {type(e).__name__}: {e}")
    # Shares outstanding (nominal value, shares, market cap for every equity)
    try:
        p = f.download(_url_for(files, SO_TITLE.format(d=nd), "pdf"), nd, "SHARES.pdf")
        if p is None:
            errs.append("Shares Outstanding PDF not published")
        elif chk(p, "SHARES") is not None:
            res["shares"] = parse_shares_outstanding(p)
    except Exception as e:  # noqa: BLE001
        errs.append(f"SHARES: {type(e).__name__}: {e}")
    return res


def nearby_name_map(date, fetcher: Fetcher | None = None, max_days: int = 7) -> dict:
    """Name -> row metadata built from the closest earlier (then later) trading day with a valid DOL.
    Used to give symbols to PRICES_LIST2 rows when a day's DOL is missing or mislabelled."""
    f = _fetcher(fetcher)
    d0 = to_date(date)
    for k in [-i for i in range(1, max_days + 1)] + list(range(1, max_days + 1)):
        d = d0 + dt.timedelta(days=k)
        if d.weekday() >= 5 or d > dt.date.today():
            continue
        s = fetch_sources(d, f)
        if s["dol"]:
            rows = merge(d, s["dol"], s["prices1"], s["plist2"], shares=s["shares"])
            return {_norm(r["name"]): r for r in rows if r["name"]}
    return {}


def merge(date, dol: list[dict], prices1: dict, plist2: list[dict], name_map: dict | None = None,
          shares: dict | None = None) -> list[dict]:
    """Merge parsed sources into one row per symbol.

    Close priority: DOL (Current Market Price) > PRICES_LIST2 Growth Board / known name map >
    Shares Outstanding > PRICES1.
    ``name_map`` (from :func:`nearby_name_map`) lets PRICES_LIST2 rows stand in for a missing DOL.
    ``shares`` (from :func:`parse_shares_outstanding`) adds size fields and maps names to symbols.
    Every row then gets the full :data:`FIELDS` set via :func:`_enrich`.
    """
    shares = shares or {}
    so_names = {_norm(v["name"]): k for k, v in shares.items() if v.get("name")}
    iso = to_date(date).isoformat()
    out: dict[str, dict] = {}
    for r in dol:
        out[r["symbol"]] = dict(date=iso, symbol=r["symbol"], name=r["name"], board=r["board"],
                                sector=r["sector"] or "", subsector=r["subsector"] or "",
                                close=r["close"], source="DOL")
    # improve abbreviated DOL names using PRICES_LIST2 (same price + similar name)
    for r in out.values():
        cands = [p for p in plist2 if p["price"] is not None and abs(p["price"] - r["close"]) < 1e-9]
        if cands:
            best = max(cands, key=lambda p: difflib.SequenceMatcher(None, _norm(p["name"]), _norm(r["name"])).ratio())
            if _norm(best["name"]).startswith(_norm(r["name"])[:6]):
                r["name"] = best["name"]
    dol_names = {_norm(r["name"]) for r in out.values()}
    for p in plist2:
        sym = GROWTH_SYMBOLS.get(p["name"]) or EXTRA_SYMBOLS.get(p["name"]) or so_names.get(_norm(p["name"]))
        is_growth = p["board"] == "GROWTH BOARD"
        if sym is None and name_map and _norm(p["name"]) in name_map:
            sym = name_map[_norm(p["name"])]["symbol"]
        if sym is None and is_growth:
            # unknown growth-board name: try a unique price match among PRICES1 symbols not yet used
            m = [s for s, q in prices1.items() if s not in out and q["close"] == p["price"]]
            sym = m[0] if len(m) == 1 else None
        if sym is None:
            if is_growth:
                sym = "?" + _norm(p["name"])[:20]
            else:
                continue
        if sym in out or (not is_growth and _norm(p["name"]) in dol_names):
            continue
        out[sym] = dict(date=iso, symbol=sym, name=p["name"],
                        board=BOARD_NAMES.get(p["board"], (p["board"] or "").title()),
                        sector=p.get("sector") or "", subsector=(p.get("subsector") or "").title(),
                        close=p["price"], source="PRICES_LIST2")
    by_sym = {r["symbol"]: r for r in (name_map or {}).values()}
    # Shares Outstanding carries the official close for every equity (it matched the DOL on every
    # day tested), so it fills stocks that neither the DOL nor PRICES_LIST2 supplied.
    for s, q in shares.items():
        if s in out or q.get("close") is None:
            continue
        m = by_sym.get(s, {})
        name, board, sector, subsector = PRICES1_META.get(s, (q.get("name", ""), "", "", ""))
        if not board and s in GROWTH_SYMBOLS.values():
            board = "Growth Board"
        out[s] = dict(date=iso, symbol=s, name=m.get("name") or name, board=m.get("board") or board,
                      sector=m.get("sector") or sector, subsector=m.get("subsector") or subsector,
                      close=q["close"], source="SHARES")
    for s, q in prices1.items():
        if s not in out and q["close"] is not None:
            name, board, sector, subsector = PRICES1_META.get(s, ("", "", "", ""))
            if s in by_sym:
                m = by_sym[s]
                name, board, sector, subsector = m["name"], m["board"], m["sector"], m["subsector"]
            out[s] = dict(date=iso, symbol=s, name=name, board=board, sector=sector, subsector=subsector,
                          close=q["close"], source="PRICES1")
    rows = sorted(out.values(), key=lambda r: r["symbol"])
    _enrich(rows, dol, prices1, plist2, shares, so_names)
    return rows


def plist2_by_symbol(rows_or_syms, plist2: list[dict], shares: dict | None, dol: list[dict]) -> dict:
    """Map PRICES_LIST2 rows (named) to symbols: Shares Outstanding names first, then the fixed
    Growth/extra maps, then a same-price + similar-name match against DOL names."""
    shares = shares or {}
    so_names = {_norm(v["name"]): k for k, v in shares.items() if v.get("name")}
    dol_by_sym = {r["symbol"]: r for r in dol}
    out: dict[str, dict] = {}
    for p in plist2:
        sym = so_names.get(_norm(p["name"])) or GROWTH_SYMBOLS.get(p["name"]) or EXTRA_SYMBOLS.get(p["name"])
        if sym is None:
            cands = [r for r in dol_by_sym.values()
                     if p["price"] is not None and abs(p["price"] - r["close"]) < 1e-9 and r["symbol"] not in out]
            if cands:
                best = max(cands, key=lambda r: difflib.SequenceMatcher(None, _norm(p["name"]), _norm(r["name"])).ratio())
                if _norm(p["name"]).startswith(_norm(best["name"])[:6]):
                    sym = best["symbol"]
        if sym and sym not in out:
            out[sym] = p
    return out


_COUNT_FIELDS = ("trades", "volume", "shares_outstanding", "last_trade_qty")


def _enrich(rows: list[dict], dol: list[dict], prices1: dict, plist2: list[dict], shares: dict,
            so_names: dict) -> None:
    """Add activity, size, fundamental and dividend fields to merged rows (in place)."""
    dol_by = {r["symbol"]: r for r in dol}
    pl2_by = plist2_by_symbol(rows, plist2, shares, dol)
    have_activity = bool(prices1) or bool(plist2)  # neither usable -> activity unknown, not zero
    for r in rows:
        sym, close = r["symbol"], r["close"]
        p1, d, so, pl = prices1.get(sym), dol_by.get(sym), shares.get(sym), pl2_by.get(sym)
        used = []
        # --- activity
        if p1:
            used.append("PRICES1")
            prev = p1["pclose"] if p1["pclose"] is not None else close
            op = p1["open"] if p1["open"] is not None else prev
            hi, lo = p1["high"], p1["low"]
            trades, volume, value = p1["trades"], p1["volume"], p1["value"]
            pct = p1["pct_change"]
        elif not have_activity:
            prev = op = hi = lo = pct = trades = volume = value = None
        else:
            prev = op = close
            hi = lo = None
            pct = None
            trades = pl["trades"] if pl else 0.0
            volume = pl["volume"] if pl else 0.0
            value = 0.0 if not volume else None
            if pl:
                used.append("PRICES_LIST2")
        # NGX prints "-" for high/low when no trade moved the price; fall back to open/close
        if hi is None and close is not None and op is not None:
            hi = max(op, close)
        if lo is None and close is not None and op is not None:
            lo = min(op, close)
        chg = round(close - prev, 6) if close is not None and prev is not None else None
        if pct is None and chg is not None and prev:
            pct = round(chg / prev * 100, 2)
        if pct is None and chg == 0:
            pct = 0.0
        r.update(prev_close=prev, open=op, high=hi, low=lo, change=chg, pct_change=pct,
                 trades=trades if trades is not None or not have_activity else 0.0,
                 volume=volume if volume is not None or not have_activity else 0.0, value_ngn=value)
        # --- size
        if so:
            used.append("SHARES")
            r.update(nominal_value=so.get("nominal_value"), shares_outstanding=so.get("shares_outstanding"),
                     market_cap_ngn=so.get("market_cap"))
        else:
            r.update(nominal_value=d["par"] if d else None, shares_outstanding=None,
                     market_cap_ngn=round(pl["mcap_m"] * 1e6, 2) if pl and pl.get("mcap_m") is not None else None)
        # --- fundamentals + dividends
        if d:
            used.append("DOL")
            r.update(week52_high=d.get("week52_high"), week52_low=d.get("week52_low"),
                     last_trade_price=d.get("last_trade"), last_trade_date=d.get("last_trade_date", ""),
                     last_trade_qty=d.get("last_trade_qty"), eps=d.get("eps"), pe=d.get("pe"),
                     last_exdiv_date=d.get("last_exdiv_date", ""), last_exscrip_date=d.get("last_exscrip_date", ""),
                     div_paid_date=d.get("div_paid_date", ""), div_interim=d.get("div_interim"),
                     div_final=d.get("div_final"))
        else:
            for k in ("week52_high", "week52_low", "last_trade_price", "last_trade_qty", "eps", "pe",
                      "div_interim", "div_final"):
                r[k] = None
            for k in ("last_trade_date", "last_exdiv_date", "last_exscrip_date", "div_paid_date"):
                r[k] = ""
        if pl and "PRICES_LIST2" not in used:
            used.append("PRICES_LIST2")
        r["sources_used"] = "+".join(sorted(set(used + [r["source"]])))
        for k in _COUNT_FIELDS:  # whole-number counts as ints (33, not 33.0)
            if isinstance(r.get(k), float) and r[k].is_integer():
                r[k] = int(r[k])


def validate(date, fetcher: Fetcher | None = None, sources: dict | None = None, mcap_tol: float = 0.005) -> dict:
    """Cross-check the day's files against each other. Returns a summary dict (never raises on data)."""
    s = sources or fetch_sources(date, fetcher)
    dol, p1, pl2, so = s["dol"], s["prices1"], s["plist2"], s["shares"]
    dol_by = {r["symbol"]: r for r in dol}
    pl_by = plist2_by_symbol(None, pl2, so, dol)
    close_p1 = compare_dol_prices1(dol, p1)
    close_so = [dict(symbol=k, dol=dol_by[k]["close"], shares=v["close"]) for k, v in so.items()
                if k in dol_by and v.get("close") is not None and abs(v["close"] - dol_by[k]["close"]) > 1e-6]
    vol_cmp = [k for k in p1 if k in pl_by]
    vol_bad = [dict(symbol=k, prices1=p1[k]["volume"], prices_list2=pl_by[k]["volume"]) for k in vol_cmp
               if p1[k]["volume"] is not None and pl_by[k]["volume"] is not None
               and abs(p1[k]["volume"] - pl_by[k]["volume"]) > 0.5]
    mc = [(k, v) for k, v in so.items() if v.get("shares_outstanding") and v.get("close") and v.get("market_cap")]
    mc_bad = [dict(symbol=k, market_cap=v["market_cap"], shares_x_close=v["shares_outstanding"] * v["close"])
              for k, v in mc if abs(v["shares_outstanding"] * v["close"] - v["market_cap"]) > mcap_tol * v["market_cap"]]
    out = dict(
        date=to_date(date).isoformat(), errors=s["errors"], mislabelled=s["mislabelled"],
        counts=dict(dol=len(dol), prices1=len(p1), prices_list2=len(pl2), shares=len(so)),
        close_dol_vs_prices1=dict(compared=sum(1 for r in dol if r["symbol"] in p1), mismatches=close_p1),
        close_dol_vs_shares=dict(compared=sum(1 for k in so if k in dol_by), mismatches=close_so),
        volume_prices1_vs_prices_list2=dict(compared=len(vol_cmp), mismatches=vol_bad),
        market_cap_check=dict(compared=len(mc), pass_rate=round(1 - len(mc_bad) / len(mc), 4) if mc else None,
                              failures=mc_bad),
    )
    for k, x in out.items():  # a check with nothing to compare proves nothing
        if isinstance(x, dict) and "compared" in x:
            x["status"] = "not compared" if not x["compared"] else (
                "ok" if not x.get("mismatches", x.get("failures")) else "mismatch")
    return out


def compare_dol_prices1(dol: list[dict], prices1: dict, tol: float = 1e-6) -> list[dict]:
    """Symbols present in both whose closes differ."""
    return [dict(symbol=r["symbol"], dol=r["close"], prices1=prices1[r["symbol"]]["close"])
            for r in dol if r["symbol"] in prices1 and prices1[r["symbol"]]["close"] is not None
            and abs(prices1[r["symbol"]]["close"] - r["close"]) > tol]


def get_daily_prices(date, fetcher: Fetcher | None = None) -> list[dict]:
    """Closing prices for every listed equity on ``date``. Empty list for non-trading days.

    Row fields: see :data:`FIELDS` (close, OHLC, trades, volume, value, shares outstanding,
    market cap, 52-week range, EPS, P/E, dividends, sources). Untraded stocks get volume 0 and
    open = high = low = close = prev_close.
    """
    s = fetch_sources(date, fetcher)
    if not s["files"]:
        return []
    if not s["dol"] and not s["prices1"] and not s["plist2"]:
        raise RuntimeError(f"No price data parsed for {ngx_date(date)}: {s['errors']}")
    name_map = nearby_name_map(date, fetcher) if not s["dol"] else None
    return merge(date, s["dol"], s["prices1"], s["plist2"], name_map, shares=s["shares"])


def get_range(start, end, fetcher: Fetcher | None = None, on_error: str = "warn") -> list[dict]:
    """Prices for every trading day in [start, end]. Weekends are skipped without a request;
    weekdays with no published files (holidays) are skipped via the index."""
    import sys
    d, e = to_date(start), to_date(end)
    rows: list[dict] = []
    while d <= e:
        if d.weekday() < 5:
            try:
                rows.extend(get_daily_prices(d, fetcher))
            except Exception as ex:  # noqa: BLE001
                if on_error == "raise":
                    raise
                print(f"[ngxprices] {d}: {ex}", file=sys.stderr)
        d += dt.timedelta(days=1)
    return rows


def get_live_prices(fetcher: Fetcher | None = None) -> list[dict]:
    """Raw current-day equities snapshot from the NGX JSON API (not cached).

    NGX states that these prices are delayed by 30 minutes. Fields: Symbol, PrevClosingPrice,
    OpeningPrice, HighPrice, LowPrice, ClosePrice, Change, PercChange, Trades, Volume, Value,
    Market, Sector, TradeDate. See :func:`get_live` for rows in the package's own format.
    """
    f = _fetcher(fetcher)
    data = f.get(LIVE_URL, headers={"Accept": "application/json"}).json()
    return data if isinstance(data, list) else data.get("data", data)


LIVE_FIELDS = FIELDS + ["metadata_date"]
# fields copied from the most recent end-of-day rows (they are not in the live API)
_META_FIELDS = ("name", "subsector", "nominal_value", "shares_outstanding", "week52_high", "week52_low",
                "last_trade_price", "last_trade_date", "last_trade_qty", "eps", "pe", "last_exdiv_date",
                "last_exscrip_date", "div_paid_date", "div_interim", "div_final")


def combine_live(live: list[dict], meta_rows: list[dict], meta_date=None) -> list[dict]:
    """Turn raw live-API records into :data:`LIVE_FIELDS` rows.

    Prices, trades, volume and value come from ``live``. Shares outstanding, EPS, P/E, dividends,
    52-week range and names come from ``meta_rows`` (end-of-day rows from :func:`get_daily_prices`
    for ``meta_date``, usually the previous trading day). Market cap is recomputed as
    shares outstanding x live close; EPS/P/E are as of ``meta_date``.
    """
    meta = {r["symbol"]: r for r in meta_rows}
    md = to_date(meta_date).isoformat() if meta_date else ""
    out = []
    for x in live:
        sym = (x.get("Symbol") or "").strip()
        if not sym:
            continue
        close, prev = x.get("ClosePrice"), x.get("PrevClosingPrice")
        op = x.get("OpeningPrice") if x.get("OpeningPrice") is not None else prev
        hi, lo = x.get("HighPrice"), x.get("LowPrice")
        if hi is None and close is not None and op is not None:
            hi = max(op, close)  # NGX leaves high/low empty when no trade moved the price
        if lo is None and close is not None and op is not None:
            lo = min(op, close)
        chg = x.get("Change")
        if chg is None and close is not None and prev is not None:
            chg = round(close - prev, 6)
        pct = x.get("PercChange")
        if pct is None and chg is not None and prev:
            pct = round(chg / prev * 100, 2)
        m = meta.get(sym, {})
        board = BOARD_NAMES.get((x.get("Market") or "").upper(), x.get("Market") or m.get("board", ""))
        r = dict(date=(x.get("TradeDate") or "")[:10], symbol=sym, board=board,
                 sector=x.get("Sector") or m.get("sector", ""), close=close, prev_close=prev, open=op,
                 high=hi, low=lo, change=chg, pct_change=pct, trades=x.get("Trades"), volume=x.get("Volume"),
                 value_ngn=x.get("Value"), source="LIVE", metadata_date=md if m else "")
        for k in _META_FIELDS:
            r[k] = m.get(k, "" if k in ("name", "subsector") or k.endswith("_date") else None)
        if not r["name"]:
            r["name"] = (x.get("Company2") or sym).strip()
        sh = r["shares_outstanding"]
        r["market_cap_ngn"] = round(sh * close, 2) if sh and close is not None else None
        r["sources_used"] = "LIVE" + ("+" + m["sources_used"] if m.get("sources_used") else "")
        for k in _COUNT_FIELDS:
            if isinstance(r.get(k), float) and r[k].is_integer():
                r[k] = int(r[k])
        out.append(r)
    return sorted(out, key=lambda r: r["symbol"])


def latest_trading_day(on_or_before, fetcher: Fetcher | None = None, max_days: int = 10) -> dt.date | None:
    """Most recent date on or before ``on_or_before`` for which NGX has published files."""
    f = _fetcher(fetcher)
    d = to_date(on_or_before)
    for _ in range(max_days + 1):
        if d.weekday() < 5 and list_files(d, f):
            return d
        d -= dt.timedelta(days=1)
    return None


def get_live(fetcher: Fetcher | None = None, meta_date=None) -> tuple[list[dict], dict]:
    """Live (30-minute delayed) prices for every equity, with end-of-day metadata attached.

    Metadata (shares, EPS, P/E, dividends, 52-week range) comes from ``meta_date`` if given,
    else from the most recent day with published files up to the live trade date.
    Returns (rows, info) where info has trade_date, metadata_date, stock count and notes.
    """
    f = _fetcher(fetcher)
    live = get_live_prices(f)
    trade_dates = sorted({(x.get("TradeDate") or "")[:10] for x in live if x.get("TradeDate")})
    td = trade_dates[-1] if trade_dates else dt.date.today().isoformat()
    md = to_date(meta_date) if meta_date else latest_trading_day(td, f)
    meta_rows = get_daily_prices(md, f) if md else []
    rows = combine_live(live, meta_rows, md)
    notes = ["NGX states that live prices are delayed by 30 minutes."]
    if md and md.isoformat() != td:
        notes.append(f"Shares, EPS, P/E, dividends and 52-week range are from {md.isoformat()}; "
                     "market cap uses those shares x the live price.")
    if not md:
        notes.append("No end-of-day files found for metadata; only live price fields are filled.")
    missing = sum(1 for r in rows if not r["metadata_date"])
    if md and missing:
        notes.append(f"{missing} stock(s) had no end-of-day row for metadata.")
    info = dict(trade_date=td, metadata_date=md.isoformat() if md else None, stocks=len(rows), notes=notes)
    return rows, info


def write_csv(rows: list[dict], path, fields: list[str] | None = None) -> None:
    import csv
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields or FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
