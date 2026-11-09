---
name: ngx-prices
description: Download and parse Nigerian Exchange (NGX / Nigerian Stock Exchange) equity data for any trading day, date range, or right now (live prices, 30-minute delayed), using the `ngxprices` Python package and CLI. Gives closing price, open/high/low, change, trades, volume, value traded, shares outstanding, market cap, 52-week range, EPS, P/E and dividends per stock. Use when the user asks for NGX/Nigerian stock prices, trading volume or turnover, market capitalisation, shares outstanding, EPS/P/E, dividends, historical NGX data, year-end or month-end figures for Nigerian listed companies, or wants a CSV/history for NGX tickers (e.g. MTNN, DANGCEM, GTCO, ZENITHBANK).
---

# NGX daily equity data (`ngxprices`)

Package source: https://github.com/bteinstein/ngx (src layout).
If `import ngxprices` fails, install it from a clone: `pip install -e '<path to your clone of ngx>[test]'`.

## CLI

```bash
ngxprices fetch --date 2025-12-31 --out day.csv              # one day, all fields (exit 1 if no files that day)
ngxprices range --start 2025-12-01 --end 2025-12-31 --out dec.csv   # skips weekends + holidays
ngxprices --fields basic fetch --date 2025-12-31             # v0.1 columns only (date..close, source)
ngxprices live --out now.csv                                # live prices (NGX 30-min delay) + latest metadata
ngxprices validate --date 2025-12-31 [--details]             # cross-check the day's files (JSON)
ngxprices files --date 2025-12-31                            # JSON list of every NGX document for that day
# global options (before the subcommand): --cache DIR  --delay SECONDS (default 1.0)  --fields full|basic
```
Dates accept `YYYY-MM-DD` or `DD-MM-YYYY`.

## Columns (one row per stock per trading day)

| Group | Columns | Source file |
| --- | --- | --- |
| Identity | date, symbol, name, board, sector, subsector | Daily Official List (DOL) |
| Close | close (official close = DOL "Current Market Price") | DOL, else PRICES_LIST2 / Shares Outstanding / PRICES1 |
| Activity | prev_close, open, high, low, change, pct_change, trades, volume, value_ngn | PRICES1 (traded stocks); trades/volume for the rest from PRICES_LIST2 |
| Size | nominal_value, shares_outstanding, market_cap_ngn | SHARES OUTSTANDING FOR DD-MM-YYYY.pdf |
| Fundamentals | week52_high, week52_low, last_trade_price, last_trade_date, last_trade_qty, eps, pe | DOL |
| Dividends | last_exdiv_date, last_exscrip_date, div_paid_date, div_interim, div_final | DOL (best effort) |
| Provenance | source (file the close came from), sources_used | |

- **Untraded stocks:** trades = volume = value_ngn = 0 and open = high = low = close = prev_close.
- **Activity unknown:** if neither PRICES1 nor PRICES_LIST2 is usable that day, activity columns are blank, not 0.
- When NGX prints "-" for high/low on a traded stock, high/low fall back to max/min(open, close).
- `last_trade_qty` is the size of the last trade, **not** the day's volume. Use `volume`.
- `div_interim` is blank in every file seen so far; NGX does not fill that column.
- EPS/P/E are as NGX prints them, and some look odd (e.g. MTNN EPS 0.01, P/E 50,216 on 31 Dec 2025).

## Python

```python
from ngxprices import get_daily_prices, get_range, validate, list_files, fetch_sources, get_live_prices, Fetcher, FIELDS
rows = get_daily_prices("2025-12-31")      # list[dict] with FIELDS; [] for non-trading days
rows = get_range("2025-01-01", "2025-01-31")
v = validate("2025-12-31")                 # cross-checks; each has compared / mismatches / status
s = fetch_sources("2025-12-31")            # raw parsed dol / prices1 / plist2 / shares + errors + mislabelled
files = list_files("2025-12-31")           # [{title,url,created,modified}] (UTC upload times)
rows, info = get_live()                    # live rows (LIVE_FIELDS) + info: trade_date, metadata_date, notes
live = get_live_prices()                   # raw snapshot from NGX JSON API (not cached)
f = Fetcher(cache_dir="...", delay=1.5, retries=3)   # pass as fetcher= to any function
```
Downloads are cached in `~/.cache/ngxprices` (override with `$NGXPRICES_CACHE` or `--cache`). Index results are
cached only for dates older than 3 days. Requests are spaced by `delay` seconds and retried with backoff.

## Live prices (delayed)

```bash
ngxprices live --out now.csv            # every stock, NGX's 30-minute-delayed prices + latest metadata
ngxprices live --meta-date 2026-11-06   # take shares/EPS/P/E/dividends from a chosen day
```

`get_live()` / `ngxprices live` reads NGX's free live API (prices delayed 30 minutes by NGX) and adds shares
outstanding, EPS, P/E, dividends and the 52-week range from the most recent day with published files
(`metadata_date` column). Market cap is recomputed as shares x live price. Checked against end-of-day files for
6 Nov 2026: closes matched for all 146 stocks; volume matched for 145. FIRSTHOLDCO's live volume was 11.2m vs
18.9m in both end-of-day files, so treat live volume as provisional and the end-of-day files as final.
Real-time (undelayed) data is a paid NGX service (X-DataPortal, brokers, data vendors).

## Sources (doclib.ngxgroup.com, no auth)
1. The SharePoint index `_api/Web/Lists/GetByTitle('DownloadsContent')/items?$filter=substringof('DD-MM-YYYY',Title)`
   decides whether a date is a trading day (no files = holiday/weekend/not yet published).
2. **Daily Official List - Equities for DD-MM-YYYY.pdf** (DOL): close, names, boards, 52-week range, last trade,
   EPS, P/E, dividends. The right-hand columns run together in the PDF text, so they are rebuilt from character
   positions.
3. **GAINERS AND PRICE LIST FOR DD-MM-YYYY.zip**: `PRICES1.pdf` (traded securities by symbol: previous close,
   open, high, low, close, change, trades, volume, value) and `PRICES_LIST2.pdf` (every equity by company *name*:
   price, % change, trades, volume, market cap).
4. **SHARES OUTSTANDING FOR DD-MM-YYYY.pdf**: every equity by symbol: nominal value, close, shares, market cap.

## Validation
`validate(date)` / `ngxprices validate` compares: DOL close vs PRICES1, DOL close vs Shares Outstanding, PRICES1
volume vs PRICES_LIST2, and market cap vs shares × close (0.5% tolerance). Status `not compared` means a file
was missing, so the check proves nothing that day. On 20 random days (2023 to 2026) every check that ran found
0 mismatches.

## Data caveats (tell the user when relevant)
- **Growth Board** stocks (CHELLARAM, RONCHESS, MCNICHOLS, LIVINGTRUST, MECURE, BAPLC, TIP, JULI, ZICHIS…) are NOT
  in the DOL. They come from PRICES_LIST2 and Shares Outstanding; names map to symbols via the Shares Outstanding
  file and `GROWTH_SYMBOLS` in `core.py`.
- **Suspended stocks** are sometimes omitted from the DOL. JAIZBANK (Non-Interest board) may appear only in PRICES1.
- **Ticker renames / corporate actions:** e.g. FBNH -> FIRSTHOLDCO (2025); delistings (FLOURMILL Dec 2024,
  GLAXOSMITH 2024); new listings (TRANSPOWER, ARADEL 2024). Join histories with care. Prices are not adjusted
  for dividends, bonuses or splits.
- **Mislabelled / missing files happen.** The package checks the date printed on each PDF and ignores documents
  for the wrong day (seen: 07-03-2025 DOL actually 06-03-2025; 12-03-2026 zip actually 13-03-2026). Some days lack
  the DOL (13-03-2024) or a file inside the zip. Index titles can be wrong (17-06-2025 zip titled "FOREIGN
  EQUITY LISTING"), so files are matched by URL name too. Check `fetch_sources(d)["errors"]`.
- **Publication timing:** the market closes 14:30 Lagos time (UTC+1). Files are uploaded typically 15:15-21:30
  Lagos time (median about 17:30; sometimes replaced the next day). Before that, `list_files(today)` is empty;
  use `get_live()` / `ngxprices live` for today, or fetch after 22:00. Don't treat an empty result for today as a holiday.
- Only equities (Main, Premium, Growth, ASeM, Non-Interest, REIT & Closed-End Fund boards). ETFs, bonds and
  mutual funds are excluded.

## Tests
`python -m pytest -q` from the repo root (offline fixtures; set `NGX_NETWORK_TESTS=1` for the network test).
`python scripts/random_days.py` re-runs the 20-random-day validation into `test_output/`.
