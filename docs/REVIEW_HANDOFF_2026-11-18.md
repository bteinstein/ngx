# Handoff for review — 18 Nov 2026

Written at the end of the session of 17–18 Nov 2026 for **a brand-new session**. Read this file,
`CLAUDE.md`, `data/rules.json` and `src/ngxprices/portfolio.py` (functions `rules_status`,
`early_warning`, `take_profit`) before doing anything.

**Two jobs, in this order:**
1. **Data review:** verify the numbers. The owner does not trust the take-profit table (section 4).
2. **Expert critique:** an orchestrator sets up five stock-trading and investment experts to critique
   the rules and the build (section 6).

Information only. No financial advice; every decision is the owner's. Keep owner-facing answers short:
he reads on an Android phone.

---

## 1. What was done (17–18 Nov 2026)

All of it is on `main`. Commits, oldest first:
- `de1fb0f` Add 17 Nov closes (official)
- `7c69899` Reset watchlist triggers to 2-week lows to 17 Nov (superseded the same day)
- `113fa57` Add owner's sell rules: 20% loss limit and 15% trailing level on all holdings
- `d5c627f` Add early-warning traffic light to the sell rules
- `cd65e59` Add take-profit flags: targets, recover cost and 15% size cap

**Data**
- 17 Nov closes are NGX official. Value ₦10,497,293 · cost ₦8,023,767 · gain ₦2,473,526 ·
  day +₦67,569 (+0.65%).
- 16 Nov: NGX published **no files** at all. Checked by title, by upload time (`Created`), by `Modified`
  and with 10 date spellings, plus a 13 Nov control query. 16 Nov keeps live-feed closes, which are
  final, with provisional volumes. `ngxprices portfolio refresh` upgrades it automatically if NGX ever
  publishes.

**The owner's rules** (`data/rules.json`), set 18 Nov and applied to all holdings:
- **Goals:** serious capital appreciation; loss tolerance 20%.
- **Loss limit:** a close ≥20% below average cost → `loser` (red). Warning at −10%.
- **Trailing stop:** if the peak close was ≥20% above cost, a close ≥15% below that peak → `trail`
  (red, "sell-part review"). The peak is the highest close in `price_history.json`, which is sparse
  before 2 Oct; some peaks come from news reports (for example, Okomu's ₦1,575 in June).
- **Trigger shown** = the higher of the loss-limit level (cost × 0.80) and the trailing level
  (peak × 0.85).
- **Early-warning light:**
  - red: a rule fired;
  - amber: a tolerance signal (−10% on cost; −10% from peak when trailing is active; within 5% of the
    trigger) plus ≥1 general sign (a fall on ≥2× 20-day volume in the last 5 days; a close below the
    20-day average; a −9% day in the last 10; 3 falls in a row);
  - watch: tolerance signal only;
  - note: general sign only;
  - green: nothing.
- **Take profit (sell into strength):**
  - targets: at +50% sell 25%; at +100% sell another 25%;
  - recover cost: once up 100%, sell the units whose sale (after ~2% fees) returns everything paid;
  - size cap: no holding above 15% of the portfolio.
  - Sells recorded in `transactions.json` after 18 Nov count as targets taken.
- The old six "losers" with 2-week-low triggers (SUNUASSUR, LASACO, INTBREW, OANDO, AFRIPRUD,
  TRANSCORP, plus PRESCO at cost) were replaced by these rules. `watchlist.json` is now generated from
  `rules.json` on every refresh.

**Code:** `ngxprices portfolio losers` prints every holding with its light, status, trigger, signals and
take-profit lines. `refresh` writes the regenerated watchlist and an auto note in `daily_log.json`.
Tests: `python -m pytest -q tests` (20 pass).

**Dashboard** (https://claude.ai/artifact/QD661V95bkFogP8jifQ6kF): the datasets `prices`,
`price_history`, `daily` and `watchlist` point at new blobs, and their descriptions explain the rules.
The page code (`files/index.html`) was **not** changed. Known issues:
- its "losers value / loss so far" box now sums every holding (it counts `rule !== 'cost'`);
- it shows the light and the take-profit flags only inside each row's note.

The owner has not yet answered whether to fix the page.

## 2. Results at the 17 Nov close (as reported to the owner; verify, see section 4)

- **Red, loser:** SUNUASSUR −46%, LASACO −39%, INTBREW −37%, OANDO −36%, AFRIPRUD −31%,
  TRANSCORP −30% on cost.
- **Red, trail:** FIRSTHOLDCO −30%, OKOMUOIL −28%, UPDCREIT −27%, PRESCO −19%, ZENITHBANK −15.0% from
  peak. Zenith is exactly on the line: ₦116.00 vs ₦116.02.
- **Amber:** UCAP, LINKASSURE, ELLAHLAKES, GTCO, ACCESSCORP, DANGCEM, UBA.
- **Watch:** DANGSUGAR.
- DANGCEM fell −9.99% (limit-down) on 17 Nov, from ₦1,469.90 to ₦1,323, on official data with no
  dividend to explain it.
- **Take profit:** 15 holdings flagged, because nothing has ever been sold. PRESCO is 16.3% of the
  portfolio, over the cap.

## 3. What the owner said (his words, summarised)

- Loss tolerance is 20%.
- On Presco: his gain was once above 40% and fell to about 10%. Action should have been taken by
  selling part, then averaging down or buying back lower afterwards.
- Aim: serious capital appreciation.
- Chose: 15% trailing, all holdings, apply to the six old losers now; then the early-warning lights;
  then all three take-profit rules with a 15% size cap.
- Asked for plain-language explanations: he is new to this.

## 4. OPEN: the owner does not trust the take-profit table. Verify first.

The owner wrote that "Stanbic is showing 134% instead of 1,178%". In the table, Stanbic was +136%,
Julius Berger +134% and Sterling +1,178%. Reconcile what he sees (dashboard or his broker app) with
what the code prints. Check every row: units, average cost, close, gain %, units to sell and ₦ amounts.

**Found at handoff, almost certainly wrong: STERLINGNG (Sterling Financial Holdings).**
- `price_history.json` (NGX official) shows ₦7.70 on 2–7 Oct, then **₦77.00 on 8 Oct**, a 10× jump in
  one day. NGX caps daily moves at about 10%.
- This looks like a share reconstruction (10 old shares → 1 new) or another corporate action.
- `holdings.json` still has **5,000 units at ₦5.87** (Account 1, Meristem). That gives +1,178%, a
  "recover cost" of 400 units and a 3.6% weight.
- If it was a 10:1 consolidation, the owner holds about **500 units at about ₦58.70**: a gain of about
  +28%, and a portfolio value overstated by about **₦337,500** (5,000 × ₦75 vs 500 × ₦75). Every daily
  value since 8 Oct would also be affected.
- To do: confirm with the NGX corporate-action notice or Sterling's announcement, and the owner's
  Meristem statement. Then fix `holdings.json` (record it, for example as a note or a transaction) and
  recalculate the daily log from 8 Oct.
- **Do not change the data before the owner confirms the unit count.**

Other checks to make:
- No other held stock has an overnight jump of more than 12%. The large jumps elsewhere are months
  apart: sparse pre-October history.
- Peaks from pre-October news rows (OKOMUOIL, DANGSUGAR, MTNN, JBERGER, BUACEMENT): are they real
  closes? They drive the trailing triggers.
- Holdings in more than one account (MANSARD, DANGSUGAR, ACCESSCORP, MTNN): the take-profit unit counts
  use the combined holding. Say which account the units sit in.
- `CLAUDE.md` says 43 holdings, but there are 39 tickers (some are held in two accounts).
- Seplat's peak is before its ex-dividend date. Dividends are not adjusted in peaks.

## 5. Other open items

- The dashboard page fixes (section 1). They need the owner's yes.
- The owner hasn't confirmed any trades since 12 Oct. Contract notes for future sells go into
  `transactions.json`; they also mark take-profit targets as taken.
- `CLAUDE.md` "Data status" and "Portfolio at 16 Nov" are stale. Update them after the review.

## 6. Expert critique: instructions for the orchestrator

Set up **five independent expert reviewers**, each with deep knowledge of stock trading and
investment. Give each the same material: this file, `data/rules.json`, the output of
`ngxprices portfolio losers`, `data/holdings.json` and the latest `data/prices_*.json`. Give them the
facts, not your conclusions. Each critiques the rules and the build from their angle, with concrete
examples from this portfolio, and proposes specific changes with numbers.

1. **Risk manager (stop-loss and trailing-stop design).** Are a 20% loss limit, a −10% warning and a
   15% trailing stop with a 20% activation sensible on NGX, given its ±10% daily price limits, thin
   liquidity and gaps? Should the levels differ by stock volatility (ATR-based) or by market cap? Is
   one rule per holding right, or should it be per account?
2. **NGX market specialist (Nigerian market structure).** Liquidity, limit-up and limit-down
   behaviour, block trades, dividend and ex-dividend effects, corporate actions (see Sterling), fees
   (~1.8–2% each way), settlement, how brokers (Meristem, AfriInvest, InvestNaija) handle stop orders,
   and the reliability of the official files vs the live feed.
3. **Portfolio-construction specialist (position sizing and diversification).** The 15% size cap,
   sector concentration (banks, consumer goods, oil), 39 holdings on ₦10.5M, cash management, the
   ₦2.2M plan's buy-stops, and where the money from profit-taking should go.
4. **Growth and momentum investor (capital appreciation).** Do the take-profit targets (+50% → sell
   25%, +100% → sell 25%) cut winners too early for the owner's goal? Compare letting winners run,
   pyramiding and relative-strength rules. Critique "sell part, then average down" on falling stocks.
5. **Quant and data auditor (correctness and backtest).** Re-derive the numbers independently from
   `data/`. Check `rules_status`, `early_warning` and `take_profit` for bugs and edge cases: peaks from
   sparse or news data, multi-account holdings, ex-dividend drops, live vs official rows. Backtest the
   rules over 2 Oct–17 Nov using `price_history.json` and report what they would have flagged, and
   when.

**Output:** a consolidated critique, ranked by impact. Separate:
- bugs and data errors (fix with the owner's OK);
- rule changes to propose (the owner decides);
- confirmed-good choices.

Write it to `docs/REVIEW_CRITIQUE_<date>.md`, commit it to `main` and push. Give the owner a short,
plain-language summary for his phone. No financial advice, and no Claude attribution in git.
