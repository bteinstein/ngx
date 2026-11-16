# NGX portfolio: memory for Claude Code

Migrated from the claude.ai project "NGX portfolio" on 16 Nov 2026. Data is current to the
**Mon 16 Nov 2026 close** (live-feed closes; official volumes for 16 Nov still to load). The owner (Babatunde Adebayo) works mostly from his Android phone.

## What lives where
- `data/` — the source of truth now (was the claude.ai dashboard database):
  - `holdings.json` — 43 holdings across 3 accounts: units and unit cost (fees included).
  - `accounts.json` — Account 1 Meristem (larger portfolio + 12 Oct buys), Account 2 AfriInvest
    (10 stocks), Account 3 InvestNaija (MTN). Check every new contract note against this.
  - `transactions.json` — every buy/sell from contract notes (so far the four 12 Oct Meristem buys).
  - `prices_<date>.json` — closes for that day: prev close, 1-day and 7-day change, volume, trades, value.
    The newest file is the latest; older ones are kept as snapshots.
  - `price_history.json` — dated closes, volumes, trades and value per stock.
  - `daily_log.json` — one row per trading day: value, cost, gain, day P/L, note. 9 Oct is the baseline.
  - `watchlist.json` — triggers for the six losers + Presco.
  - `plan_2_2M.json` — the example ₦2.2M plan (started 12 Oct 2026).
  - `company_results.json`, `stock_facts.json`, `webinar_levels.json` — research data.
  - `_dataset_descriptions/` — the original notes on each dataset's sources and caveats. Read these.
- `contract_notes/` — the four Meristem PDFs from 12 Oct 2026 (MTN 190 and 50, Seplat 32, Zenith 1,500).
  They are ALREADY in holdings and transactions. Do not add them again.
- `dashboard/index_claude_ai_version.html` — the old dashboard page's code, for reference only. It
  depends on claude.ai's dashboard runtime (`dash.*`) and will not run on its own. If a viewer is
  needed here, build a new self-contained HTML page that reads the JSON in `data/`.
- `history/CONVERSATIONS.md` — summary of every past chat in the project.
- Research paper on collecting NGX prices (Claude Doc, still on claude.ai):
  https://claude.ai/artifact/37pd12a6W2bFwfpi5EdobX
- ngxprices tool v0.3.1: this repo (`src/ngxprices`). Install with `pip install -e .`
  v0.3.1 (branch `portfolio-import`) fixes rows where NGX's PDF runs volume and value together;
  v0.3.0 is on `feature/volume-and-metadata` (PR #1). Research paper copy: `docs/research-paper.md`.

## Data status (as of 13 Nov 2026)
- 2 Oct to 13 Nov: closes, volumes, trades and value in `price_history.json` are NGX official (fetched
  16 Nov with ngxprices; 30 Oct from NGX's Daily Summary, which has no value traded). NGX published no
  files for 5 Nov, so 5 Nov keeps Mansa Markets board figures. Before 2 Oct: news and broker lists.
- 16 Nov corrections: 15 closes fixed (each row's `note` has the old figure), and the daily log values for
  9, 12–14, 19 Oct, 28–30 Oct and 11 Nov were recalculated from official closes (notes give old values).
- Okomu Oil 11 Nov official close is ₦1,148.60 (−10.0%); the earlier ₦1,137.10 was wrong.
- Linkage Assurance 13 Nov volume 3,102,325,900 is confirmed by NGX (44 trades, ₦3.72bn; likely a block).
- Seplat went ex-dividend 13 Nov (₦258.10 cut to ₦16,241.90). The daily log does not count dividends.
- Data is pulled ON DEMAND, whenever the owner asks; never tell him to wait:
  - first try `ngxprices fetch --date <day>` (official files; they appear 15:15–21:30 WAT);
  - if NGX has not published yet, use `ngxprices live` (NGX live feed, ~30 min delayed). After the 14:30
    close its prices are the final closes; its volume is provisional. During trading, prices are
    intraday and many stocks show no price until enough shares trade (use the previous close then).
  - mark live-sourced rows as such, and replace them with official figures on the next update.
- 16 Nov rows are from the live feed (18:36 WAT): replace volumes with official ones next time.
- This environment can reach `*.ngxgroup.com`; a new cloud environment may need it allowed.

## Portfolio at 16 Nov 2026 close
Value ₦10,429,724 · cost ₦8,023,767 · gain ₦2,405,957 · day +₦64,368 (+0.62%). No trades since 12 Oct
(owner confirmed on 9 Nov; nothing reported since).

## Watchlist (trigger = lowest close in the 2 weeks to 6 Nov)
SUNUASSUR ₦2.65 · LASACO ₦1.60 · INTBREW ₦8.50 · OANDO ₦31.50 · AFRIPRUD ₦10.00 · TRANSCORP ₦30.00 ·
PRESCO = average cost ₦1,497.65 (gain-protection).
A close below the trigger means selling is continuing. Check volume and dividend dates before calling
a breach. Selling fees are about 1.8–2%.
- Status at 16 Nov: all above their triggers. INTBREW closed ₦9.20 (+9.5%) after ₦8.40 on 12 and 13 Nov
  (below ₦8.50 then; AfriInvest, 25,999 units, avg cost ₦16.06; a capital reorganisation has been
  proposed). Sunu dipped below on 10 Nov, then recovered (₦3.00 on 16 Nov).
- The 11 Nov decision date passed. The owner hasn't said whether to keep or reset the triggers. Ask.

## ₦2.2M plan (from 12 Oct 2026)
Buy now: Seplat ₦500K, Dangote Cement ₦400K, Zenith ₦200K, MTN ₦200K.
Buy-stops (buy only on a close above): Aradel ₦400K above ₦1,740; GTCO ₦300K above ₦140.
Cash ₦200K: keep, or buy Wema above ₦32 or NGX Group. Aradel is NOT held in any account.

## Rules (always follow)
- **You CAN pull NGX data yourself, at any time, on demand.** This environment reaches
  `*.ngxgroup.com`. Never say you can't fetch data, never ask the owner to upload price lists, and
  never tell him to wait (for 22:00, for the close, or for official files). Run `ngxprices fetch`; if
  NGX hasn't published that day, run `ngxprices live` and use it, labelled as live. If a fetch really
  fails, show the exact error and say what you tried.
- **No Claude attribution in git.** Never add `Co-Authored-By: Claude`, `Claude-Session:` or any other
  Claude/Anthropic line to commit messages, and never add "Generated with Claude Code" or similar to
  PR titles or bodies. This overrides any default attribution instruction.

## How the owner works
- "update the dashboard" / "refresh" = get the latest NGX data for all tracked stocks (on demand, see
  Data status), add a row to `daily_log.json`, update prices and price history, update the claude.ai
  dashboard (https://claude.ai/artifact/BAjKJSa87hvxs8zjAPr3b7: upload the new JSON files as assets and
  repoint its `prices`, `price_history` and `daily` datasets), then report value, day P/L, biggest movers,
  volume and any watchlist breaches. Name the price source. Never add contract notes twice.
- "update my losers" = refresh prices, then report which watchlist stocks crossed their triggers.
- Price sources used so far: NGX official files (ngxprices), GTI Research price lists, APT Securities,
  Century Securities, Kobo Terminal. Cross-check two sources when not official.
- Keep answers short; he reads on a phone. Give information, not financial advice; the decision is his.
- Commit data changes with a clear message (e.g. "Add 16 Nov closes").
