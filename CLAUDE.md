# NGX portfolio: memory for Claude Code

Migrated from the claude.ai project "NGX portfolio" on 16 Nov 2026. Data is current to the
**Fri 13 Nov 2026 close**. The owner (Babatunde Adebayo) works mostly from his Android phone.

## What lives where
- `data/` — the source of truth now (was the claude.ai dashboard database):
  - `holdings.json` — 43 holdings across 3 accounts: units and unit cost (fees included).
  - `accounts.json` — Account 1 Meristem (larger portfolio + 12 Oct buys), Account 2 AfriInvest
    (10 stocks), Account 3 InvestNaija (MTN). Check every new contract note against this.
  - `transactions.json` — every buy/sell from contract notes (so far the four 12 Oct Meristem buys).
  - `prices_2026-11-13.json` — latest closes, prev close, 1-day and 7-day change.
  - `price_history.json` — dated closes and volumes per stock (972 rows).
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
- ngxprices tool v0.3.0: private repo github.com/bteinstein/ngx, branch
  `feature/volume-and-metadata`. Install with `pip install -e .`

## Data status (as of 13 Nov 2026)
- Closes 6 Nov and 11 Nov are NGX official. 9–10 Nov from GTI Research; 12–13 Nov from APT Securities,
  cross-checked against GTI. Before 6 Nov: news and broker lists; volumes may be undercounted.
- Seplat went ex-dividend 13 Nov (₦258.10 cut to ₦16,241.90). The daily log does not count dividends.
- Linkage Assurance 13 Nov volume (3.1bn shares) looks wrong; unconfirmed.
- Okomu Oil official 11 Nov close ₦1,137.10 (−10.9%, beyond the usual 10% limit; worth checking).
- Open job: replace estimated volumes with official ones:
  `ngxprices range --start 2026-10-01 --end <latest trading day> --out data/oct_nov.csv`
  The cloud environment needs network access to `*.ngxgroup.com` (default network blocks it).
- NGX closes 14:30 Lagos time (WAT, UTC+1). End-of-day files appear 15:15–21:30; fetch after 22:00.
  `ngxprices live` is ~30 min delayed; from 15:00 its prices equal the close, volume is provisional.

## Portfolio at 13 Nov 2026 close
Value ₦10,365,356 · cost ₦8,023,767 · gain ₦2,341,589 · day −₦17,913 (−0.17%). No trades since 12 Oct
(owner confirmed on 9 Nov; nothing reported since).

## Watchlist (trigger = lowest close in the 2 weeks to 6 Nov)
SUNUASSUR ₦2.65 · LASACO ₦1.60 · INTBREW ₦8.50 · OANDO ₦31.50 · AFRIPRUD ₦10.00 · TRANSCORP ₦30.00 ·
PRESCO = average cost ₦1,497.65 (gain-protection).
A close below the trigger means selling is continuing. Check volume and dividend dates before calling
a breach. Selling fees are about 1.8–2%.
- Status at 13 Nov: **INTBREW closed ₦8.40 on 12 and 13 Nov, below ₦8.50** (AfriInvest, 25,999 units,
  avg cost ₦16.06; a capital reorganisation has been proposed). Sunu dipped below on 10 Nov, then
  recovered to ₦2.88 on 12 Nov. The others were above their triggers.
- The 11 Nov decision date passed. The owner hasn't said whether to keep or reset the triggers. Ask.

## ₦2.2M plan (from 12 Oct 2026)
Buy now: Seplat ₦500K, Dangote Cement ₦400K, Zenith ₦200K, MTN ₦200K.
Buy-stops (buy only on a close above): Aradel ₦400K above ₦1,740; GTCO ₦300K above ₦140.
Cash ₦200K: keep, or buy Wema above ₦32 or NGX Group. Aradel is NOT held in any account.

## How the owner works
- "update the dashboard" / "refresh" = get the latest NGX closes for all 43 holdings, add a row to
  `daily_log.json`, update prices and price history, then report value, day P/L, biggest movers and
  any watchlist breaches. Name the price source. Never add contract notes twice.
- "update my losers" = refresh prices, then report which watchlist stocks crossed their triggers.
- Price sources used so far: NGX official files (ngxprices), GTI Research price lists, APT Securities,
  Century Securities, Kobo Terminal. Cross-check two sources when not official.
- Keep answers short; he reads on a phone. Give information, not financial advice; the decision is his.
- Commit data changes with a clear message (e.g. "Add 16 Nov closes").
