# ngx

Download, parse and validate Nigerian Exchange (NGX) daily equity data from NGX's free public document library (doclib.ngxgroup.com). For every listed stock and trading day you get the closing price, open/high/low, change, trades, volume, value traded, shares outstanding, market cap, 52-week range, EPS, P/E and dividends. No API key or login is needed.

## What's here

| Path | What it is |
| --- | --- |
| `src/ngxprices/` | Python package: `get_daily_prices`, `get_range`, `validate`, `list_files`, `get_live_prices`, plus the `ngxprices` CLI |
| `tests/` | Offline pytest tests (NGX files from 31 Dec 2025); set `NGX_NETWORK_TESTS=1` for the network test |
| `scripts/random_days.py` | Validation run on 5 random trading days per year, 2023 to 2026 |
| `test_output/` | Results of that run (`random_days.csv`, `report.json`) |
| `skill/ngx-prices/SKILL.md` | Claude Code skill; copy to `~/.claude/skills/ngx-prices/` |
| `data/` | Year-end closing price workbooks (2022 to 6 Nov 2026, with Top 10 Gainer / Loser / Mid Performer bands) |
| `scripts/year_end_workbook/` | Prototype scripts that built the workbooks |

## Install

```bash
pip install -e '.[test]'
```

## Use

```bash
ngxprices fetch --date 2025-12-31 --out day.csv
ngxprices range --start 2025-12-01 --end 2025-12-31 --out dec.csv
ngxprices validate --date 2025-12-31
ngxprices --fields basic fetch --date 2025-12-31   # only the v0.1 columns
ngxprices files --date 2025-12-31
```

```python
from ngxprices import get_daily_prices, validate
rows = get_daily_prices("2025-12-31")  # one dict per stock, columns below
```

## Columns

| Group | Columns |
| --- | --- |
| Identity | date, symbol, name, board, sector, subsector |
| Price and activity | close, prev_close, open, high, low, change, pct_change, trades, volume, value_ngn |
| Size | nominal_value, shares_outstanding, market_cap_ngn |
| Fundamentals | week52_high, week52_low, last_trade_price, last_trade_date, last_trade_qty, eps, pe |
| Dividends | last_exdiv_date, last_exscrip_date, div_paid_date, div_interim, div_final |
| Provenance | source, sources_used |

Untraded stocks get volume 0, with open, high, low and close equal to the previous close. If NGX's activity files are missing for a day, activity columns are blank rather than 0. `last_trade_qty` is the size of the last trade, not the day's volume.

## How it works

For each trading day, NGX publishes a Daily Official List (Equities) PDF, a "Gainers and Price List" ZIP and a Shares Outstanding PDF. The package:

- Finds the files through the library's index.
- Reads the close, 52-week range, EPS, P/E and dividends from the official list.
- Reads open, high, low, trades, volume and value from the traded-price list (PRICES1), and trades and volume for every stock from the full price list (PRICES_LIST2).
- Reads nominal value, shares outstanding and market cap from the Shares Outstanding file.
- Fills in Growth Board and other stocks the official list leaves out.

Files whose printed date doesn't match the requested day are skipped.

Validation (`ngxprices validate`): closes are compared across three files, volumes across two, and market cap against shares × close. On 20 random trading days from 2023 to 2026, every check that could run found 0 mismatches. On days when NGX left a file out, the affected check is marked "not compared". NGX files appear between about 15:15 and 21:30 Lagos time (median about 17:30), so schedule daily fetches after 22:00 WAT.

## Caveats

- % changes are price only. They are not adjusted for dividends, bonus issues or splits.
- EPS, P/E and dividend columns are as NGX prints them. The interim dividend column is empty in NGX's files.
- Ticker changes (e.g. FBNH → FIRSTHOLDCO) appear as separate symbols.
- The official list leaves out the Growth Board and some suspended stocks. The package fills them in where NGX's other files allow.
- Parsing depends on NGX's PDF layout. Re-run the tests if NGX changes its format.
