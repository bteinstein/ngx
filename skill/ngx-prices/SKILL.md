---
name: ngx-prices
description: Download and parse Nigerian Exchange (NGX / Nigerian Stock Exchange) daily equity closing prices for any trading day or date range, using the local `ngxprices` Python package and CLI. Use when the user asks for NGX/Nigerian stock closing prices, historical NGX price data, year-end or month-end prices of Nigerian listed companies, or wants to build a price history/CSV for NGX tickers (e.g. MTNN, DANGCEM, GTCO, ZENITHBANK).
---

# NGX daily closing prices (`ngxprices`)

Package source: https://github.com/bteinstein/ngx-prices (src layout).
If `import ngxprices` fails, install it: `pip install -e '<path to your clone of ngx-prices>[test]'` (or `pip install git+https://github.com/bteinstein/ngx-prices`).

## CLI

```bash
ngxprices fetch --date 2025-12-31 --out prices.csv          # one day (exit 1 if no files that day)
ngxprices range --start 2025-12-01 --end 2025-12-31 --out dec.csv   # skips weekends + holidays
ngxprices files --date 2025-12-31                            # JSON list of every NGX document for that day
# global options (before the subcommand): --cache DIR  --delay SECONDS (default 1.0)
```
Dates accept `YYYY-MM-DD` or `DD-MM-YYYY`. CSV columns: `date,symbol,name,board,sector,subsector,close,source`.

## Python

```python
from ngxprices import list_files, get_daily_prices, get_range, get_live_prices, fetch_sources, Fetcher
rows = get_daily_prices("2025-12-31")      # list[dict]; [] for non-trading days
rows = get_range("2025-01-01", "2025-01-31")
files = list_files("2025-12-31")           # [{title,url,created,modified}] (UTC upload times)
s = fetch_sources("2025-12-31")            # raw parsed dol / prices1 / plist2 + errors + mislabelled
live = get_live_prices()                   # today's snapshot from NGX JSON API (not cached)
f = Fetcher(cache_dir="...", delay=1.5, retries=3)   # pass as fetcher= to any function
```
Downloads are cached in `~/.cache/ngxprices` (override with `$NGXPRICES_CACHE` or `--cache`); index results are
cached only for dates older than 3 days. Requests are spaced by `delay` seconds and retried with backoff.

## How it works / sources (doclib.ngxgroup.com, no auth)
1. SharePoint index `_api/Web/Lists/GetByTitle('DownloadsContent')/items?$filter=substringof('DD-MM-YYYY',Title)`
   decides whether a date is a trading day (no files = holiday/weekend/not yet published).
2. **Daily Official List - Equities for DD-MM-YYYY.pdf** (DOL): primary source. `close` = the
   **"Current Market Price"** column (official close; for untraded stocks it equals the previous close).
3. **GAINERS AND PRICE LIST FOR DD-MM-YYYY.zip** containing `PRICES1.pdf` (traded securities by symbol with
   PCLOSE/OPEN/HIGH/LOW/CLOSE) and `PRICES_LIST2.pdf` (full list by board by company *name*). Member names vary; the
   package globs for them.
Merge priority: DOL > PRICES_LIST2 (Growth Board and other name-mapped rows) > PRICES1. The `source` column says
which document each price came from. `compare_dol_prices1()` cross-checks DOL vs PRICES1 closes (normally 0 diffs).

## Data caveats (tell the user when relevant)
- **Growth Board** stocks (CHELLARAM, RONCHESS, MCNICHOLS, LIVINGTRUST, MECURE, BAPLC, TIP, JULI, ZICHIS…) are NOT
  in the DOL; they come from PRICES_LIST2 by company name via `GROWTH_SYMBOLS` in `core.py`. A new Growth Board
  listing gets its symbol by a unique price match against PRICES1, otherwise a placeholder symbol starting with `?`
  - add it to `GROWTH_SYMBOLS` when that happens.
- **Suspended stocks** are sometimes omitted from the DOL; JAIZBANK (Non-Interest board) may appear only in PRICES1.
- **Ticker renames / corporate actions**: e.g. FBNH -> FIRSTHOLDCO (2025); delistings
  (FLOURMILL Dec 2024, GLAXOSMITH 2024); new listings (TRANSPOWER, ARADEL 2024). Join histories with care.
  Prices are not adjusted for dividends, bonuses or splits.
- **Mislabelled / missing files happen**: the package checks the trading date printed on each PDF and ignores
  documents for the wrong day (seen: 07-03-2025 DOL actually 06-03-2025; 12-03-2026 zip actually 13-03-2026).
  Some days lack the DOL (13-03-2024) - then PRICES_LIST2 is used with symbols taken from a nearby day's DOL - or
  lack PRICES1/PRICES_LIST2 inside the zip. Index titles can also be wrong (17-06-2025 zip titled as "FOREIGN
  EQUITY LISTING"), so files are matched by URL name too. Check `fetch_sources(d)["errors"]` for such issues; a day
  with only PRICES1 covers only traded stocks.
- **Publication timing**: market closes 14:30 Lagos time (UTC+1). Files are uploaded typically 15:15-21:30 Lagos
  time (median about 17:30; sometimes later or replaced the next day). Before that, `list_files(today)` is empty -
  use `get_live_prices()` for intraday/today data, or retry later. Don't treat an empty result for today as a holiday.
- Only equities (Main, Premium, Growth, ASeM, Non-Interest, REIT & Closed-End Fund boards); ETFs, bonds and mutual
  funds are excluded. Company names may be abbreviated in the DOL (improved from PRICES_LIST2 where possible).

## Tests
`python -m pytest -q` (from the repo root) (offline fixtures; set `NGX_NETWORK_TESTS=1` for the network
test). `python scripts/random_days.py` re-runs the 20-random-day validation into `test_output/`.
