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
from .parsers import parse_dol, parse_prices1, parse_prices_list2, pdf_as_of

BASE = "https://doclib.ngxgroup.com"
INDEX_URL = (BASE + "/_api/Web/Lists/GetByTitle('DownloadsContent')/items"
             "?$select=Title,EncodedAbsUrl,Created,Modified&$filter=substringof('{d}',Title)&$top=100")
DOL_TITLE = "Daily Official List - Equities for {d}"
ZIP_TITLE = "GAINERS AND PRICE LIST FOR {d}"
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

FIELDS = ["date", "symbol", "name", "board", "sector", "subsector", "close", "source"]

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

    Returns dict(files, dol (list), prices1 (dict), plist2 (list), errors (list), mislabelled (list)).
    A document whose printed trading date differs from ``date`` is ignored (recorded in errors).
    """
    f = _fetcher(fetcher)
    nd = ngx_date(date)
    files = list_files(date, f) if files is None else files
    res = dict(files=files, dol=[], prices1={}, plist2=[], errors=[], mislabelled=[])
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
            rows = merge(d, s["dol"], s["prices1"], s["plist2"])
            return {_norm(r["name"]): r for r in rows if r["name"]}
    return {}


def merge(date, dol: list[dict], prices1: dict, plist2: list[dict], name_map: dict | None = None) -> list[dict]:
    """Merge parsed sources into one row per symbol.

    Priority: DOL (Current Market Price) > PRICES_LIST2 Growth Board / known name map > PRICES1.
    ``name_map`` (from :func:`nearby_name_map`) lets PRICES_LIST2 rows stand in for a missing DOL.
    """
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
        sym = GROWTH_SYMBOLS.get(p["name"]) or EXTRA_SYMBOLS.get(p["name"])
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
    for s, q in prices1.items():
        if s not in out and q["close"] is not None:
            name, board, sector, subsector = PRICES1_META.get(s, ("", "", "", ""))
            if s in by_sym:
                m = by_sym[s]
                name, board, sector, subsector = m["name"], m["board"], m["sector"], m["subsector"]
            out[s] = dict(date=iso, symbol=s, name=name, board=board, sector=sector, subsector=subsector,
                          close=q["close"], source="PRICES1")
    return sorted(out.values(), key=lambda r: r["symbol"])


def compare_dol_prices1(dol: list[dict], prices1: dict, tol: float = 1e-6) -> list[dict]:
    """Symbols present in both whose closes differ."""
    return [dict(symbol=r["symbol"], dol=r["close"], prices1=prices1[r["symbol"]]["close"])
            for r in dol if r["symbol"] in prices1 and prices1[r["symbol"]]["close"] is not None
            and abs(prices1[r["symbol"]]["close"] - r["close"]) > tol]


def get_daily_prices(date, fetcher: Fetcher | None = None) -> list[dict]:
    """Closing prices for every listed equity on ``date``. Empty list for non-trading days.

    Row fields: date, symbol, name, board, sector, subsector, close, source.
    """
    s = fetch_sources(date, fetcher)
    if not s["files"]:
        return []
    if not s["dol"] and not s["prices1"] and not s["plist2"]:
        raise RuntimeError(f"No price data parsed for {ngx_date(date)}: {s['errors']}")
    name_map = nearby_name_map(date, fetcher) if not s["dol"] else None
    return merge(date, s["dol"], s["prices1"], s["plist2"], name_map)


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
    """Current-day equities snapshot from the NGX JSON API (not cached)."""
    f = _fetcher(fetcher)
    data = f.get(LIVE_URL, headers={"Accept": "application/json"}).json()
    return data if isinstance(data, list) else data.get("data", data)


def write_csv(rows: list[dict], path) -> None:
    import csv
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
