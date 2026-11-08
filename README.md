# ngx-prices

Download, parse and validate Nigerian Exchange (NGX) daily equity closing prices from NGX's free public document library (doclib.ngxgroup.com). No API key or login is needed.

## What's here

| Path | What it is |
| --- | --- |
| `src/ngxprices/` | Python package: `list_files`, `get_daily_prices`, `get_range`, `get_live_prices`, plus the `ngxprices` CLI |
| `tests/` | Offline pytest tests (fixtures from 31 Dec 2025); set `NGX_NETWORK_TESTS=1` for the network test |
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
ngxprices fetch --date 2025-12-31 --out prices.csv
ngxprices range --start 2025-12-01 --end 2025-12-31 --out dec.csv
ngxprices files --date 2025-12-31
```

```python
from ngxprices import get_daily_prices
rows = get_daily_prices("2025-12-31")  # [{date, symbol, name, board, sector, subsector, close, source}, ...]
```

## How it works

For each trading day, NGX publishes a Daily Official List (Equities) PDF and a "Gainers and Price List" ZIP. The package:

- Finds both files through the library's index.
- Reads the close from the official list's "Current Market Price" column.
- Fills in Growth Board and other missing stocks from the full price list.
- Cross-checks every close against the separately published traded-price list.

Files whose printed date doesn't match the requested day are skipped.

Validation: 0 price mismatches on every date where both lists were available, including all 20 random test days. NGX files appear between about 15:15 and 21:30 Lagos time (median about 17:30), so schedule daily fetches after 22:00 WAT.

## Caveats

- % changes are price only. They are not adjusted for dividends, bonus issues or splits.
- Ticker changes (e.g. FBNH → FIRSTHOLDCO) appear as separate symbols.
- The official list leaves out the Growth Board and some suspended stocks. The package fills them in where NGX's other files allow.
- Parsing depends on NGX's PDF layout. Re-run the tests if NGX changes its format.
