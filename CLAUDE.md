# NGX portfolio: memory for Claude Code

Migrated from the claude.ai project "NGX portfolio" on 16 Nov 2026. Data is current to the
**Mon 16 Nov 2026 close** (live-feed closes; official volumes for 16 Nov still to load). The owner (Babatunde Adebayo) works mostly from his Android phone.

## ⚠️ Open review (18 Nov 2026)
Handoff: `docs/REVIEW_HANDOFF_2026-11-18.md`. Data review DONE (`docs/DATA_REVIEW_2026-11-18.md`); expert critique DONE
and reconciled with the corrected data (`docs/REVIEW_CRITIQUE_2026-11-18.md`, first section is current).
Sterling: 10-for-1 reconstruction 8 Oct; owner confirmed 500 units (500 @ ₦58.70). Official closes back-filled
from 2 Jan 2026. Peaks are adjusted for dividends/bonuses/reconstructions in `data/corporate_actions.json` (record new
ones there) and count from 1 Jan 2026 or a lot's `bought_from` (owner's choice). Rules run on the combined holding,
with each account's lot shown. Open: owner's purchase dates, and the critique's rule proposals (owner decides).

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
  - `rules.json` — the owner's sell rules; `watchlist.json` — generated from them each refresh.
  - `plan_2_2M.json` — the example ₦2.2M plan (started 12 Oct 2026).
  - `company_results.json`, `stock_facts.json`, `webinar_levels.json` — research data.
  - `_dataset_descriptions/` — the original notes on each dataset's sources and caveats. Read these.
- `contract_notes/` — the four Meristem PDFs from 12 Oct 2026 (MTN 190 and 50, Seplat 32, Zenith 1,500).
  They are ALREADY in holdings and transactions. Do not add them again.
- `dashboard/index.html` — the repo's own dashboard: one self-contained page built from `data/` by
  `ngxprices portfolio dashboard` (edit `dashboard/template.html`, never index.html; see
  `dashboard/README.md`). The refresh skill rebuilds it each time and publishes it to the owner's
  phone link https://claude.ai/artifact/8oK5Np1GcUhFYMUvM4qq4o (private). From 24 Nov it runs beside the old
  claude.ai dashboard (BAjKJSa87hvxs8zjAPr3b7) for a week; then the old one drops out of the refresh.
- `dashboard/index_claude_ai_version.html` — the old claude.ai dashboard page's code, for reference
  only. It depends on claude.ai's dashboard runtime (`dash.*`) and will not run on its own.
- `history/CONVERSATIONS.md` — summary of every past chat in the project.
- Research paper on collecting NGX prices (Claude Doc, still on claude.ai):
  https://claude.ai/artifact/37pd12a6W2bFwfpi5EdobX
- ngxprices tool v0.4.0: this repo (`src/ngxprices`), incl. `ngxprices portfolio …`. Install with `pip install -e .`
  Everything is on `main` (PR #1 and `portfolio-import` merged 16 Nov); commit new work to `main`.
  Research paper copy: `docs/research-paper.md`.

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

## Portfolio at 17 Nov 2026 close (official; Sterling corrected 18 Nov)
Value ₦10,159,793 · cost ₦8,023,767 · gain ₦2,136,026 · day +₦67,569 (+0.67%). No trades since 12 Oct
(owner confirmed on 9 Nov; nothing reported since).

## Sell rules (owner's, set 18 Nov 2026; `data/rules.json`; apply to ALL holdings)
- **Loss limit 20%:** a close ≥20% below average cost = **loser**. Early warning at −10%.
- **Trailing 15%:** once a holding's peak close was ≥20% above cost, a close ≥15% below that peak =
  **sell-part review** (owner's view: e.g. Presco should have been part-sold as its gain fell from
  40%+ to ~10%, then bought back lower). Peak = highest close in `price_history.json` (official from 2 Jan 2026) since 1 Jan 2026 or the lot's
  `bought_from`, adjusted for `corporate_actions.json`.
- **Early warning (traffic light, added 18 Nov):** red = a rule fired; amber = a tolerance signal
  (−10% on cost, −10% from peak when trailing is active, within 5% of the trigger) plus ≥1 general
  sign (fall on ≥2× 20-day volume in the last 5 days, close below the 20-day average, a −9% day in
  the last 10, 3 falls in a row); watch = tolerance only; note = general only; green = none.
  Settings in `rules.json` → `early_warning`.
- **Take profit (added 18 Nov; `rules.json` → `take_profit`):** targets +50% → sell 25%, +100% →
  another 25%; recover cost once up 100% (units whose sale returns all paid, after ~2% fees); size
  cap 15% of portfolio. Sells in `transactions.json` after 18 Nov count as targets taken, in order.
  At 17 Nov (after the 18 Nov review): 14 holdings flagged; PRESCO is 16.8% of the portfolio (over the cap). Holdings split
  across accounts: say which account the units sit in before suggesting quantities.
- Every refresh checks all holdings and regenerates `data/watchlist.json` (the dashboard's list).
  The old 2-week-low triggers (to 17 Nov) were replaced the same day; the six old losers are included.
- Goal: serious capital appreciation; loss tolerance 20%. Check volume, dividend dates and live vs
  official before calling a flag. Fees ~1.8–2% each way, so a buy-back needs a fall of >~4%.
- At 17 Nov (full 2026 peaks, 18 Nov): red 25, amber 4, note 1, green 9. Losers SUNUASSUR, LASACO, INTBREW,
  OANDO, AFRIPRUD, TRANSCORP (−30% to −46%); sell-part review ELLAHLAKES, PZ, BUACEMENT, OKOMUOIL, FIRSTHOLDCO,
  CUSTODIAN, PRESCO, DANGSUGAR, UPDCREIT, UBA, NB, CWG, MANSARD, GTCO, FCMB, BUAFOODS, ACCESSCORP, VFDGROUP,
  STERLINGNG; amber UCAP, LINKASSURE, ZENITHBANK (−14.1% from its dividend-adjusted peak), DANGCEM (limit-down
  −9.99% on 17 Nov, no dividend). INTBREW: capital reorganisation proposed.

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
- "refresh" / "update" / "update the dashboard" → use the `refresh` skill (`.claude/skills/refresh`):
  `ngxprices portfolio refresh` pulls the data on demand and writes `data/`, then the skill updates the
  claude.ai dashboard (https://claude.ai/artifact/BAjKJSa87hvxs8zjAPr3b7), commits and reports value,
  day P/L, movers, heavy volume and watchlist breaches. Never add contract notes twice.
- "update my losers" → use the `losers` skill: refresh, then `ngxprices portfolio losers` (all holdings vs the sell rules).
- A scheduled task "NGX nightly portfolio update" runs the `refresh` flow every weekday at 22:15 WAT in a
  fresh cloud session (official closes and volumes, dashboard, commit, push notification).
- Price sources used so far: NGX official files (ngxprices), GTI Research price lists, APT Securities,
  Century Securities, Kobo Terminal. Cross-check two sources when not official.
- Keep answers short; he reads on a phone. Give information, not financial advice; the decision is his.
- Commit data changes with a clear message (e.g. "Add 16 Nov closes").
