# Dashboard

`index.html` is the portfolio dashboard, one self-contained file built from `data/`. It needs no
server, no internet and no claude.ai runtime: open it in any browser, including on a phone
(download it, then open it from the Files app).

| File | What it is |
|---|---|
| `index.html` | **Generated.** The page with the data built in. Don't edit by hand. |
| `template.html` | The page's HTML, CSS and JavaScript. Edit this one. |
| `index_claude_ai_version.html` | The old claude.ai page code, kept for reference only. |

## Build

```bash
pip install -e .
ngxprices portfolio dashboard   # options: --data-dir data --template dashboard/template.html --out dashboard/index.html
```

The builder is `src/ngxprices/dashboard.py`. It reads `data/` and writes nothing back there. The data
is put in place of the `/*__DASHBOARD_DATA__*/null` placeholder in the template:

- the latest `prices_<date>.json`, with that day's source (official or live feed) from `price_history.json`;
- `holdings`, `transactions`, `daily_log`, `rules`, `plan_2_2M`, `company_results`, `stock_facts`, `webinar_levels`;
- `accounts`: only account, broker, short name, date confirmed and note. Broker account, customer and CSCS
  numbers are left out;
- `status`: `portfolio.rules_status()`, the same sell-rule check `ngxprices portfolio losers` runs
  (traffic light, loss and trailing levels, adjusted peaks, take-profit, accounts);
- `volume`: `portfolio.volume_highlights()` (2× the 20-day average or more);
- `history`: closes and volumes from 1 Dec 2025 for held, plan, research and webinar stocks
  (about 370 KB in all, not the full 2.6 MB file).

The refresh skill rebuilds it after every refresh, and the nightly scheduled task follows the skill,
so `index.html` stays current with each commit.

## Tabs

- **Overview:** value, day P/L, gain, cost; value by day; value by sector; largest holdings.
- **Sell rules:** every holding with its traffic light, status, gain on cost, adjusted peak, distance
  from peak, trigger, weight, accounts, warning signs and take-profit flags. Filter by light.
- **Daily:** day P/L and movers (your ₦ move per stock), heavy volume, daily log with notes, transactions.
- **Holdings:** accounts summary, then every lot. Filter by account. Tap a row to open the stock.
- **Stock:** closes and volume from 1 Jan 2026 with avg cost and rule level marked, rule status, key
  figures, results year on year.
- **₦2.2M plan:** orders and status against buy-stop levels, webinar levels.

Charts are inline SVG (no libraries). Tap or hover a chart to read a value. Tables sort when you tap a
heading. Light and dark mode follow the phone.
