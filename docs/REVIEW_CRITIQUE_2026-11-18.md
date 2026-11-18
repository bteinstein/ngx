# Expert critique of the sell rules — 18 Nov 2026

**Scope.** Five independent reviewers (risk manager, NGX market specialist, portfolio-construction
specialist, growth/momentum investor, quant and data auditor) critiqued the sell rules, the early-warning
lights and the take-profit setup in `data/rules.json` and `src/ngxprices/portfolio.py`, using this
portfolio's data at the **17 Nov 2026 close** (value ₦10,497,293, cost ₦8,023,767; both re-checked).
This is information, not financial advice. Every decision, and every change to `data/`, is the owner's.
Nothing in `data/` has been changed by this review.

## Reconciled with the corrected data (18 Nov, after the data review)

The experts worked on the 17 Nov data **before** the data review (`docs/DATA_REVIEW_2026-11-18.md`).
Since then: Sterling corrected, peaks dividend-adjusted, official NGX closes back-filled for 2 Jan–30 Sep
2026 (7,934 rows), 40 corporate actions recorded in `data/corporate_actions.json`, and the owner chose
peaks from 1 Jan 2026 (or the purchase date when known) with combined rules plus per-account lines.
**Where this section and the text below disagree, this section is current.**

**Portfolio at 17 Nov:** value ₦10,159,793 · cost ₦8,023,767 · gain ₦2,136,026.
**Lights now:** red 25, amber 4, note 1, green 9 (the text below says red 11).

| Item | Status now |
|---|---|
| 1.1 Sterling | **Fixed.** Owner confirmed 500 units → 500 @ ₦58.70; daily log corrected from 9 Oct. With the 2026 history (×10 before 8 Oct) its peak is ₦89.50 (25 Feb), so Sterling is now **red, −16.2% from peak**. |
| 1.2 Dividends | **Fixed** for peaks, the 20-day average and "falls in a row" (all use adjusted closes). Zenith's ex-date is **26 Oct** (NGX previous close ₦119.40 vs ₦120.90 on 23 Oct); the 21 Oct step was an ordinary price move. Zenith: **amber**, −14.1%. Dividend income is still not booked. |
| 1.3 News peaks | **The premise was wrong.** The news rows were checked against NGX's Daily Official List: Okomu ₦1,575 (11 Jun) and Dangote Sugar ₦77 (3 Aug) are real NGX closes. "Highest official close ₦1,276.20 / ₦70.00" only meant the highest since 2 Oct. All peaks now come from official closes since 1 Jan 2026. Five non-official figures were corrected (Presco ×2, BUA Cement, Seplat, GTCO). |
| 1.4 Per-account | Owner chose **combined rules** with each account's units, cost and gain shown next to every flag (`HELD IN:` line). Per-lot rules (the critique's proposal) were not adopted. MTN Account 3 cost ₦169.70 confirmed from the owner's InvestNaija screenshot. |
| 1.5 Size cap | Still open. Presco 16.8%; code says 111 units (sale money kept in the total), exact trim 130 (sale money leaves). Cash still not counted. |
| 1.6 Take-profit bookkeeping | Still open. |
| 1.7 Minor code | Peak date fixed (history now sorted by date). 20-day signs have enough rows. DANGCEM's 5 Nov row is still the unofficial Mansa figure (NGX published nothing that day). |
| 2.3, 2.4, 2.10, 2.15 | Their counts (triggers, backtest, lights) were on the old data; see the backtest below. |

**What changed the picture:** with peaks since 1 Jan, 14 more holdings are past the 15% trailing level:
ELLAHLAKES (−58% from peak), PZ (−39%), BUACEMENT (−35%), CUSTODIAN (−31%), DANGSUGAR (−28%),
UBA (−26%), NB (−26%), CWG (−25%), MANSARD (−24%), GTCO (−23%), FCMB (−19%), BUAFOODS (−19%),
ACCESSCORP (−18%), VFDGROUP (−18%), STERLINGNG (−16%). Most peaks are from February–May, when the
market was higher. **Caveat:** for holdings bought after their peak, the trail should start later. Only
the owner's purchase dates can settle this; until then, the default is 1 Jan 2026.

**Backtest on the corrected data (2 Oct–17 Nov):** 18 holdings were already red on 2 Oct. Selling each
at its first red close would have come out **+₦95,856 ahead of holding** (not −₦158,626). Presco alone is
+₦151,600 (sold at ₦1,840.80 on 27 Oct, now ₦1,656.80); without it, −₦55,744. Worst: WEMABANK −₦45,800,
DANGSUGAR −₦36,972, NGXGROUP −₦35,770, MANSARD −₦30,967. Best after Presco: FIRSTHOLDCO +₦42,300,
CWG +₦32,700, OKOMUOIL +₦20,461. Six weeks, mostly one stock: direction only, not proof.

| Ticker | First red | Close then → 17 Nov | Sell vs hold |
|---|---|---|---|
| PRESCO | 27 Oct | 1,840.80 → 1,656.80 | +₦151,600 |
| FIRSTHOLDCO | 12 Oct | 140.00 → 109.00 | +₦42,300 |
| CWG | 2 Oct | 20.75 → 18.70 | +₦32,700 |
| OKOMUOIL | 2 Oct | 1,264.70 (adj.) → 1,137.10 | +₦20,461 |
| CUSTODIAN | 2 Oct | 70.00 → 62.00 | +₦16,909 |
| WEMABANK | 22 Oct | 29.00 → 33.00 | −₦45,800 |
| DANGSUGAR | 2 Oct | 68.00 → 69.00 | −₦36,972 |
| NGXGROUP | 22 Oct | 152.50 → 175.00 | −₦35,770 |
| MANSARD | 2 Oct | 11.40 → 14.00 | −₦30,967 |
| BUACEMENT | 2 Oct | 297.00 → 298.00 | −₦20,820 |
| 18 others | | | +₦2,215 net |
| **All 28** | | | **+₦95,856** |

**Open questions, updated:** 1 (Sterling) answered: 500. 3 (purchase dates): default 1 Jan 2026 is in
use; rough purchase months would still sharpen the trailing flags. Still open: 2, 4–10.

## In plain words

- **The maths in the code is right.** The problems are in the data the rules are fed, not the formulas.
- **Sterling is almost certainly overstated by ₦337,500.** NGX did a 10-for-1 share consolidation on
  8 Oct; your file still says 5,000 units. Please check your Meristem statement: 500 units?
- **Six thin stocks really trade about 10% below their "official" price** (Presco, Julius Berger,
  BUA Foods, Okomu, NNFM, Transcorp Hotels). Presco is about break-even at the real price, not +10.6%.
- **Two red flags are partly false:** Zenith's (an unadjusted ₦1.50 dividend; the reviewers disagree on
  whether it should still be red) and Okomu's (its peak comes from a June news story, not an NGX close).
- **Rules should run per account.** Combined lines hide a −12% Mansard lot at AfriInvest and a +393%
  MTN lot at InvestNaija.
- **Selling at every first red close would have lost ₦158,626** (2 Oct–17 Nov), mostly on one-day dips.
  A "two closes in a row" check for jumpy stocks would have avoided most of that.
- **The take-profit list (14 stocks, ~₦1.28M) is a one-off backlog**, and the growth reviewer argues it
  cuts winners; the 15% size cap and the trailing stop do most of the useful work.
- **There is no cash record**, so the 15% cap and any sale money have nowhere to be counted.

---

## 1. Bugs and data errors (fix with the owner's OK)

### 1.1 STERLINGNG: 10-for-1 consolidation not applied — HIGH
*Raised by: NGX, quant, construction, momentum.*
- **What:** NGX reconstructed Sterling's shares on 8 Oct; `holdings.json` still has 5,000 units at ₦5.87.
- **Evidence:** official rows 2–9 Oct have volume 0 (suspended), close ₦7.70 → ₦77.00 on 8 Oct with no
  trades (checked). NGX Shares Outstanding: 68,502,331,708 (7 Oct) → 6,850,233,171 (8 Oct), market cap
  unchanged. Trading resumed 12 Oct (10.1M units, average ₦72.76).
- **Effect if 10:1 applies to his units:** 500 units at ₦58.70. Value overstated by ₦337,500
  (₦10,497,293 → ₦10,159,793); gain +27.8%, not +1,177.7%; two false take-profit lines (sell 2,500
  units ≈ ₦183,750; recover cost 400 units) disappear; PRESCO's weight rises 16.26% → 16.80%. Every
  `daily_log` row from 9 Oct is high by 4,500 × that day's close (₦337.5K–346.5K). The trailing stop
  stays on (peak ₦77 is +31%; level ₦65.45; no flag today).
- **Proposal:** after the owner confirms the unit count, record a corporate-action entry, set 500 at
  ₦58.70, scale pre-8 Oct closes ×10 for peaks, recalc `daily_log` from 9 Oct. Add a detector: any
  official move >10.5% (or a change in NGX shares outstanding) pauses the rules for that ticker until
  units are confirmed. INTBREW's proposed capital reorganisation is the next candidate.

### 1.2 Dividends are not taken out of peaks (Zenith red flag, Seplat level) — HIGH
*Raised by: NGX, quant, risk (Seplat).*
- **What:** trailing peaks set before an ex-dividend date include the dividend.
- **Evidence:** Zenith peak ₦136.50 (8 Oct, official) is before its ₦1.50 interim. Raw level ₦116.025;
  closes ₦115.90–116.00 since 11 Nov → red. Adjusted peak ₦135.00 → level ₦114.75 → ₦116.00 is −14.07%
  from peak, about 1.1% above the trigger: amber, not red. Seplat level ₦14,025 → ₦13,805.6 after the
  ₦258.10 dividend (ex 13 Nov). In-window ex-dates (NGX price lists): PZ 12 Oct ₦2.50, GTCO 13 Oct ₦1.00,
  STANBIC 16 Oct ₦4.50, ZENITH ₦1.50, OKOMUOIL 12 Nov ₦11.50 (counted as a −1% "fall"), SEPLAT 13 Nov.
  Dividend income in the window ≈ ₦27,317 gross (~₦24,585 after 10% WHT) is in no gain figure.
- **Disagreement:**
  - *Ex-date:* NGX specialist reads 26 Oct from NGX's previous-close column (119.40); quant infers
    21 Oct from the exact ₦1.50 step (123.50 → 122.00). Either way the adjusted level is ₦114.75.
  - *Should Zenith still be red?* Risk manager: **keep the flag**. It is the most liquid holding
    (~₦2.7bn a day), a 1.0% typical daily move, a steady 6-week slide, and it would have fired on 28 Oct
    at ₦120 under his proposed 12% trail for quiet stocks. NGX/quant: on correct (adjusted) data it is
    not a breach under the current 15% rule. Both views agree the trend is real; the 12 Oct lot alone
    (1,500 at ₦131.37) is −11.7%.
- **Proposal:** add a small dividends table (ticker, ex-date, amount; columns exist in the Daily Official
  List). Subtract later dividends from earlier closes for peaks, 20-day average and "falls in a row".
  Compare on unrounded levels; round only for display. Book dividend income as its own line.

### 1.3 Peaks taken from news and third-party rows — HIGH
*Raised by: risk, NGX, momentum, quant.*
- **Evidence (checked):** OKOMUOIL peak ₦1,575 is a BusinessDay row (11 Jun); highest official close
  is ₦1,276.20 → level ₦1,084.77, close ₦1,137.10 is −10.9% from peak (watch/amber, not red). It has
  been red all 33 days for this reason alone. DANGSUGAR's ₦77 (StockAnalysis, 3 Aug) is the only reason
  its trail is active (needs ₦76.50; highest official close ₦70.00); it went red 4–16 Nov, then rose to
  ₦69. Other news peaks (MTNN, BUACEMENT, BUAFOODS, JBERGER) change no status today.
- **Note:** NGX's printed 52-week highs are higher still (OKOMU ₦1,765, GTCO ₦156.95, PZ ₦109.45 …).
  Using them would flip 8 more holdings to trailing flags, but purchase dates are unknown, so they may
  predate ownership.
- **Proposal:** take peaks only from official/live NGX rows, starting no earlier than the lot's buy
  date (or 2 Oct 2026 where unknown). If older peaks are kept, label them "peak from news" and let them
  raise only a watch note, never red. Save NGX's 52-week high each refresh as a cross-check.

### 1.4 Holdings pooled across accounts hide signals — HIGH
*Raised by: risk, NGX, construction, quant.*
- **Evidence (checked):**

| Ticker | Lot | Gain | Hidden by the combined line |
|---|---|---|---|
| MANSARD | A1 Meristem 3,750 @ ₦8.18 | +71.1% | +50% target (937 units, ~₦12.9K) |
| MANSARD | A2 AfriInvest 7,200 @ ₦15.99 | −12.4% | −10% warning (combined shows +5.1%, "OK") |
| MTNN | A3 InvestNaija 105 @ ₦169.70 | +393% | targets (52 units) or recover cost (22) |
| MTNN | A1 Meristem 240 @ ₦856.34 (12 Oct) | −2.3% | its trail uses a 30 Jul peak from before purchase |
| DANGSUGAR | A1 13,666 @ ₦65.09 / A2 2,000 @ ₦54.58 | +6.0% / +26.4% | trail never active for A1 |
| ZENITHBANK | 12 Oct lot 1,500 @ ₦131.37 | −11.7% | warning (blended +31.4%) |

- **Proposal:** run loss limit, warning, trail activation and take-profit per account lot; keep size,
  sector and theme caps per ticker across accounts. Every sell line names the account and its units.

### 1.5 Size cap: wrong denominator and too-small trim — HIGH
*Raised by: construction, quant.*
- **Evidence (checked):** PRESCO 16.26% of invested value; the code's trim `(V − 15%·T)/close` = 80
  units, which leaves 15.19% (sale money leaves the total). Exact trim to 15% = 94 units; 130 if
  Sterling is corrected (weight 16.80%). Cash is not in the total at all: if the ~₦1.32M of the ₦2.2M
  plan never invested is still at the brokers, PRESCO is ~14.4% and under the cap.
- **Proposal:** cap on total equity (holdings + cash per account); units = ceil((V − c·T)/(close·(1 − c))).
  Hold any PRESCO cap trim until Sterling's units and the cash balance are known.

### 1.6 Take-profit bookkeeping will misfire after the first sale — MEDIUM
*Raised by: construction, momentum, quant.*
- **Evidence (code checked):** `pending = reached[len(sells):]` counts **every** sell since 18 Nov, any
  size, reason or account, as a target taken (an 80-unit cap trim would use up PRESCO's +50% target).
  Recover-cost subtracts sale proceeds from a cost that `holdings.json` has already reduced (example:
  100 @ ₦10, sell 25 @ ₦30 → code says 1 more unit; true figure 10). "Another 25%" is computed on units
  left, i.e. 18.75% of the original. The unit test passes original cost, so it hides this.
- **Proposal:** add `reason` to sells (target_50, target_100, recover_cost, size_cap, trail,
  loss_limit, other) and count only matching sells per lot; treat a target as taken at ≥80% of planned
  units; track paid-in and returned money per lot from transactions; owner chooses "25% of original or
  of what's left"; add tests.

### 1.7 Minor code issues — LOW
*Raised by: quant.* Peak date is the first equal close in file order, not date order (Sterling shows
19 Oct instead of 8 Oct; NNFM/TRANSCOHOT 19 Oct instead of 2 Oct). The 20-day signs need >20 rows, so
they could not fire before 30 Oct (backtest only). DANGCEM's "limit-down 05/11" comes from an
unofficial Mansa row. **Proposal:** sort by date before finding the peak; mark signs from non-official
rows.

---

## 2. Rule changes to propose (the owner decides)

### 2.1 Use a "realistic price" for thin stocks whose official close does not move — HIGH
*Raised by: all five.* (NGX and quant class it as a data error; it is listed here because the official
close is correct by NGX's rules; using another price is a choice.)
- **Evidence (checked):** closes unchanged on 32 of 32 day-pairs since 2 Oct for JBERGER, BUAFOODS,
  NNFM, TRANSCOHOT; 30 of 32 for PRESCO and OKOMUOIL. NGX does not move the official price on fewer than
  100,000 units (inferred: 0 non-corporate exceptions in 1,341 day-pairs; tiered rule postponed in 2026).
  Shares change hands ~10% lower every day:

| Ticker | Close | 5-day avg traded (value/volume) | Gap | Gain at close / traded |
|---|---|---|---|---|
| PRESCO | 1,656.80 | 1,491.21 | −10.0% | +10.6% / −0.4% |
| JBERGER | 310.80 | 279.80 | −10.0% | +134% / +111% |
| BUAFOODS | 760.60 | 690.84 | −9.2% | +22% / +11% |
| TRANSCOHOT | 290.50 | 262.12 | −9.8% | +91% / +72% |
| NNFM | 79.40 | 71.50 | −9.9% | +92% / +73% |
| OKOMUOIL | 1,137.10 | 1,065.30 | −6.3% | +198% / +179% |

  At traded prices these six are worth ~₦306,900 less (2.9%); NGX's figure using the 17 Nov VWAP and
  adding SEPLAT is ~₦356K (3.4%). The owner bought Seplat at ₦14,576 on 12 Oct when the close was
  ₦16,000.10. JBERGER, NNFM, TRANSCOHOT, BUAFOODS show green because a stuck close never "falls".
  Repricing comes in −10% steps (PRESCO 27 Oct and 5/6 Nov; OKOMU 11 Nov).
- **Proposal:** flag a holding "stale" and check loss limit, warning, trail, gain and take-profit
  against min(close, recent traded price), showing both. Thresholds offered: risk — close unchanged on
  ≥50% of the last 20 sessions; NGX — unchanged ≥5 sessions and VWAP/close ≤0.95; momentum/quant —
  unchanged ≥10 sessions. Add an early-warning sign "trades at the floor" (VWAP/close ≤0.91 on any of the
  last 5 days): fires today for all six. Exclude block days. Caveat: relies on NGX's `value_ngn`.

### 2.2 Take-profit targets: backlog, not signals — HIGH
*Raised by: momentum (main), construction, NGX, quant.*
- **Evidence:** 14 holdings flagged at 17 Nov; target sales ₦1,277,235 after fees (12.2%), ₦1,093,485
  without Sterling. Construction's ₦1,407,128 / ₦1,223,378 is the same list plus the PRESCO cap trim
  (₦129,893). Gain on cost has ~zero rank correlation (−0.005) with 4-week relative strength; flagged
  names did no worse than the rest over 2 Oct–17 Nov (−3.2% vs −3.1% equal-weighted). Applied since
  purchase, targets would have sold FIRSTHOLDCO at ₦41–55 (now ₦109), DANGCEM at ₦737–983 (now ₦1,323).
  Five flagged holdings are each under 1% (UPDCREIT line is ₦4,728).
- **Options (owner decides):** (a) drop gain-on-cost targets; let the trail and the 15% cap sell.
  (b) fire targets only on a fresh cross after 18 Nov; show today's backlog once as a review list.
  (c) targets only for holdings ≥3% (or ₦300K) and only when 4-week relative strength ≤0 or the close
  is below the 20-day average. In all cases, show "recover cost" as an option (at +100% it duplicates
  both targets) and hide lines under ~₦25K.

### 2.3 Trail width: one 15% for all, or by volatility — HIGH (reviewers disagree)
*Raised by: risk, momentum, quant.*
- **Evidence:** typical daily move ranges 0.4–0.8% (MTNN, SEPLAT, NB, BUACEMENT) to 4.0–5.5%
  (FIDELITYBK, FIRSTHOLDCO, UPDCREIT, DANGCEM). Over 2 Oct–17 Nov the 15% rule raised 7 new triggers:
  2 helped (FIRSTHOLDCO −13.2% since, UPDCREIT −8.7%), 3 were whipsaws (FIDELITYBK +12.5%, DANGSUGAR
  +6.0%, CWG +19.9% on the loss limit), 2 flat (ZENITH, PRESCO).
- **Risk manager:** tiers re-measured each refresh: 12% for typical move <1.5% and no limit move in 20
  sessions; 15% for 1.5–3%; 20% for >3% or ≥2 limit moves. FIDELITYBK stops firing; Zenith fires 28 Oct
  at ₦120.
- **Momentum investor:** keep 15% for holdings with peak gain >100%. Wider hurts: FIRSTHOLDCO fires at
  ₦119.15 (20%), ₦112.7 (25%), ₦107 (30%) instead of ₦125.55; UPDCREIT at 20% fires at ₦19.05 (now
  +1.3%). Whipsaws were on small-peak holdings; for peak gain <30% either raise activation to 30%
  (DANGSUGAR then falls back to its ₦51 loss limit, ~₦226K more drawdown) or require confirmation.
- **Common ground:** the risk tier would put FIRSTHOLDCO and UPDCREIT on 20%, which momentum's data says
  costs ~5% on the best saves. Only 7 triggers in 33 sessions: illustrative, not proof.

### 2.4 Two-close confirmation before red — MEDIUM (trade-off)
*Raised by: risk, quant, momentum (option); NGX warns of the cost.*
- **Evidence:** CWG closed ₦15.60 on 4 Nov (limit ₦15.66) on ~5× volume, then +9.9% next day; ₦18.70
  now (checked). Selling every first red close would have lost ₦158,626 vs holding (−₦8,891 without CWG
  and DANGSUGAR). Confirmation removes CWG's 1-day red and Zenith's 2 Nov red; it delays FIRSTHOLDCO
  ₦125.55 → ₦119.15 (−5%, ~₦9,600). Risk's backtest: tiers + confirmation averaged −1.6% after firing
  (stops helped) vs +2.4% for today's rule (stops hurt).
- **NGX view:** on a stock that falls in two limit-down days (FIRSTHOLDCO 28–29 Oct), waiting can cost
  up to 10% more.
- **Proposal:** 2 consecutive closes (or one close ≥1% through) for volatile stocks (typical move >3%
  or a limit move in 20 sessions); quiet stocks keep one close. Day 1 shows amber "touched; confirm
  tomorrow".

### 2.5 Concentration: PRESCO, palm-oil theme, sector and group caps — HIGH
*Raised by: construction, momentum.*
- **Evidence:** PRESCO is 16.3% of value but ~62% of daily P/L variance (2 Oct–17 Nov). The two worst
  portfolio days were PRESCO limit-downs (27 Oct −₦199K, 5 Nov −₦201K). Palm oil (PRESCO + OKOMUOIL)
  18.4%; agriculture 19.1%; consumer goods 21.2%; BUA group 13.4%, Dangote 12.8%. A ~₦250bn PRESCO rights
  issue is reported (chat summary only). PRESCO's 4-week relative strength is −19.6%.
- **Proposal:** keep 15% per name; add 20% theme/issuer-group and 25% sector caps (guard rails; none
  breached today); no new buy taking a name over 10% at cost; decide in advance on PRESCO rights only up
  to the cap; show "share of daily swings" next to weight. Optional 12% review line under the 15% cap.

### 2.6 Size and sell by liquidity — HIGH
*Raised by: construction, risk, NGX, quant.*
- **Evidence:** 46.8% of value sits in 8 stocks whose close changed on 0–2 of 32 sessions. NNFM: 600
  units vs a median ~450–570 a day (≥100% of a day). JBERGER: 1,610 units vs 2,600–3,220 a day; its
  805-unit take-profit sale is ~25–31% of a day.
- **Proposal:** note "illiquid" when units held exceed 20–25% of 20-day median volume (or 20% of median
  value traded); show such sales as "limit orders over several days"; cap suggested units at ~20% of
  median daily volume.

### 2.7 Cash and proceeds policy — HIGH
*Raised by: construction.*
- **Evidence:** no cash balance anywhere; only ₦877,548 of the ₦2.2M plan was invested on 12 Oct; the
  rest (~₦1.32M) is untracked. Flagged sales plus the six losers ≈ ₦1.73M (16.5%). Meristem holds 80.7%
  of value, AfriInvest 18.4%, InvestNaija 0.8%.
- **Proposal:** add `data/cash.json` per account (from contract notes and dividend notices) and count it
  in weights. Owner picks a proceeds rule, e.g. cash 5–25% of equity; redeploy only into plan lines whose
  trigger has fired or green holdings under a target weight (4–8%), within all caps.

### 2.8 A "past the limit" state for the six old losers — MEDIUM
*Raised by: risk.*
- **Evidence:** SUNUASSUR, LASACO, INTBREW, OANDO, AFRIPRUD, TRANSCORP were all ≥20% down on 2 Oct, so the
  stop never had a chance. Cost ₦824,349, value ₦514,168 (−37.6%, 4.9% of portfolio). Roughly flat since
  2 Oct (TRANSCORP −12.3%); INTBREW and AFRIPRUD made their best close since 2 Oct on 17 Nov yet top the
  red list. Gain needed to get back to cost: +43% (TRANSCORP) to +86% (SUNUASSUR).
- **Proposal:** show once as "past limit: decide (keep or sell)". If kept, re-base a floor at the lower of
  the 20-day low and 17 Nov × 0.85 (SUNUASSUR ₦2.55, LASACO ₦1.56, INTBREW ₦8.40, OANDO ₦30.60, AFRIPRUD
  ₦9.52, TRANSCORP ₦27.20); red only below that. Optional 6-month review date.

### 2.9 Stop averaging down from clearing a loser flag — MEDIUM
*Raised by: risk, momentum.*
- **Evidence:** the loss limit is 80% of blended average cost. INTBREW (25,999 @ ₦16.06, −37.1%): ~35,400
  more at ₦10.10 lifts the average to ₦12.63 and clears red with no price change. SUNUASSUR: ~75,600 more
  at ₦3.00 does the same.
- **Proposal:** freeze the loss-limit level at the first breach; each new buy is its own lot with its own
  20% level; show a warning when a buy lowers the average. Momentum adds: no buys in red or amber holdings.

### 2.10 Fewer, more meaningful lights — MEDIUM
*Raised by: risk, NGX.*
- **Evidence:** 27 of 39 holdings are not green (red 11, amber 7, watch 1, note 8). "Below 20-day
  average" fires on 14 holdings at depths of 0–3%; UCAP and LINKASSURE are amber only because of a 1–2%
  dip. LINKASSURE's 13 Nov block (3.10bn units, 44 trades, ₦3.72bn, VWAP ₦1.20 vs close ₦1.56; ~10% of
  the company) inflates its 20-day mean volume until ~11 Dec. GTCO's heavy-volume sign rests on a
  provisional live volume (2.018× vs a 2.0× threshold).
- **Proposal:** count "below the 20-day average" only at ≥3% or ≥1 typical daily move; skip it for stale
  stocks. Use 20-day **median** volume, drop days >20× median or with VWAP >10% off the close (show them as
  a "block trade" note), and require ≥100,000 units for "fell on heavy volume". Effect: UCAP, LINKASSURE,
  ACCESSCORP amber → watch; FCMB, VFDGROUP, STERLINGNG, FIDELITYBK note → green.

### 2.11 Near-trigger cushion and limit-down days — MEDIUM
*Raised by: risk, NGX.*
- **Evidence:** DANGCEM fell −9.99% on 17 Nov (₦1,469.90 → ₦1,323.00, checked) with every trade at the
  floor and only 312 deals; no dividend since 18 Jun. It is 4.5% above its ₦1,266.50 trail; next session's
  range is ₦1,190.70–1,455.30, so one more limit-down crosses it. Limit moves in 20 sessions: DANGCEM 6,
  UPDCREIT 4, FIRSTHOLDCO 3, CWG 2, PRESCO 2.
- **Proposal:** near_trigger_pct 10% (one limit step) for holdings with a limit move in 20 sessions, 5%
  otherwise; add a "locked limit-down" sign (close ≤−9.5% and VWAP within 0.5% of close); show the next
  session's allowed range beside each trigger.

### 2.12 Execution: flags are reviews, not stop orders — MEDIUM
*Raised by: NGX, risk.*
- **Evidence:** Meristem's MeriTrade guide lists only market and limit orders (AfriInvest, InvestNaija not
  checked). Checks run at 22:15 WAT, so action is next session, up to 10% worse, possibly unfilled on a
  locked limit-down. A 20% trigger can mean a 25–30% realised loss after fees.
- **Proposal:** word flags as "review at the next session with a limit order", showing the floor price and
  an "expected exit" = min(close, 5-day traded price) − 2% fee, with quantities per account.

### 2.13 Monitor the ₦2.2M plan — MEDIUM
*Raised by: construction, momentum.*
- **Evidence:** nothing reads `plan_2_2M.json`. DANGCEM's ₦400K "buy now" was never executed (holding is
  still 200 @ ₦491.38). Aradel's ₦1,740 stop is 34% above ₦1,296; GTCO's ₦140 is 20% above ₦117.
  "Wema above ₦32" first met 4 Nov (₦32.40), dipped to ₦31.90 on 10 Nov, crossed again 11 Nov (₦33.00);
  no alert either time (checked).
- **Proposal:** status (done / pending / cancelled) and a 60-day expiry per line; check buy-stops every
  refresh; show weights before any plan buy (₦300K GTCO takes banking 16.5% → 18.8%).

### 2.14 Relative strength and a buy-back rule — MEDIUM
*Raised by: momentum.*
- **Evidence:** against an equal-weight index of the 43 tracked stocks (no ASI series in `data/`), 4-week
  laggards: FIRSTHOLDCO −21.2%, PRESCO −19.6%, CUSTODIAN −12.1%, TRANSCORP −12.0%, OKOMUOIL −11.6%;
  leaders: DANGCEM +30.2%, MANSARD +26.3%, FIDELITYBK +10.0%. NGXGROUP (+8.5%) carries a "sell 50%"
  target. "Sell part, buy back lower" on PRESCO: the trigger (₦1,738.50) was skipped by a −10% step;
  buying back 257 units breaks even only ≥3.9% lower; a step up to ₦1,840.80 costs ₦65,266.
- **Proposal:** monthly "laggard review" (RS ≤−10% and below 20-day average) and "leader" tag (RS ≥+5% and
  above it). Buy back only after a sign of strength, ≥8% below the sale price, and never above the 15% cap.
  Optional pyramiding: steps ≤1% of portfolio, on a new official closing high with volume ≥ 20-day
  average, only for green holdings under 10%.

### 2.15 Small positions — MEDIUM
*Raised by: construction.* 39 tickers but an effective N of 15.2; 16 under 1% (8.4% in total); six under
0.5% (LASACO ₦9,150 … NNFM ₦47,640), five of them red or amber. **Proposal:** minimum new buy 1% of
equity (~₦105K); for holdings under 0.5%, owner chooses top up or exit in one batch; meanwhile report them
weekly, not as daily alerts. Aim for ~15–25 holdings at 2–8%.

### 2.16 Fees and settlement — LOW
*Raised by: NGX.* Meristem buy fees are 1.83% (commission 1.35% + VAT, SEC 0.30%, stamp 0.08%, ₦4.75
alert); NGX/CSCS lines are 0% on buys, likely charged on sells. No sell note exists, so the 2% sell fee is
unverified. Settlement on all four notes is **T+1**, not T+2. **Proposal:** set fee_pct from one sell
contract note; update the docs to T+1.

---

## 3. Confirmed-good choices

1. **The rules engine is correct — HIGH** *(quant).* Independent rebuild: value ₦10,497,293.10, cost
   ₦8,023,767.46, all 39 rows (trigger, gap, light, take-profit units and ₦) match, and 0 status
   mismatches over 1,287 ticker-days. Tests: 20 pass, 1 skipped (network). Fix inputs, don't rewrite logic.
2. **The level design fits NGX — MEDIUM** *(risk, momentum).* 20% = two limit steps, −10% warning = one;
   a 15% trail from a +20% peak starts at ~1.02 × cost, about break-even after fees. 15% protected the
   big winners in this window (FIRSTHOLDCO, UPDCREIT, OKOMU).
3. **15% single-name cap on market value, 2% fee — MEDIUM** *(construction, momentum).* Within the usual
   10–20% range; value (not cost) is the right base; 2% is slightly conservative vs 1.83–1.84% actual.
   The cap is the most useful profit-taking rule today (only PRESCO breaches it).
4. **Live-feed and stop-gap closes match NGX — MEDIUM** *(NGX, quant).* 17 Nov previous closes match the
   16 Nov live closes for all tickers; 30 Oct and 5 Nov closes also match. Volumes for those days remain
   provisional and should be labelled so.
5. **No other corporate actions — LOW** *(NGX).* Shares outstanding identical 2 Oct vs 17 Nov for all
   other holdings; only Sterling changed.
6. **Buy-stops in the ₦2.2M plan did their job — MEDIUM** *(momentum).* Aradel (−15.3% since 2 Oct) and
   GTCO (−11.9%) never triggered, so no plan money went into falling stocks.
7. **Stanbic's +136.4% is right — LOW** *(quant).* 500 @ ₦69.80, close ₦165. The +1,177.7% the owner saw
   is Sterling's (and itself wrong, see 1.1). For phone reading, show take-profit rows as one short block
   per stock with full name, account, units and ₦.

---

## Quant backtest (2 Oct–17 Nov, 33 sessions): sell all at first red close vs hold

| Ticker | First red | Why | Close then → 17 Nov | Sell vs hold (2% fee) |
|---|---|---|---|---|
| CWG | 4 Nov | loss limit (1 day) | 15.60 → 18.70 | −₦68,240 |
| DANGSUGAR | 4 Nov | trail (news peak) | 65.10 → 69.00 | −₦81,495 |
| PRESCO | 5 Nov | trail | 1,656.80 → 1,656.80 | −₦34,130 |
| FIDELITYBK | 12 Oct | trail (4 days) | 20.45 → 23.00 | −₦7,693 |
| ZENITHBANK | 2 Nov | trail (dividend-unadjusted) | 116.00 → 116.00 | −₦7,134 |
| INTBREW / OANDO / AFRIPRUD / LASACO | 2 Oct | old losers | | −₦12,486 |
| FIRSTHOLDCO | 29 Oct | trail | 125.55 → 109.00 | +₦21,059 |
| OKOMUOIL | 2 Oct | trail (news peak) | 1,276.20 → 1,137.10 | +₦22,715 |
| TRANSCORP / SUNUASSUR / UPDCREIT | | | | +₦8,777 |
| **Total** | | | | **−₦158,626** |

Red count per day: 7 (2 Oct) → 11 (4 Nov) → 12 (11–16 Nov) → 11 (17 Nov). Two-close confirmation drops
CWG and Zenith's 2 Nov red; official-only peaks drop DANGSUGAR's 8 red days and make OKOMU watch/amber.
Six weeks of data: direction only, not proof.

## Open questions for the owner

1. **Sterling:** how many units does your Meristem/CSCS statement show — 5,000 or 500?
2. **Cash:** is the ~₦1.32M of the ₦2.2M plan that was not invested still at a broker? Which account?
3. **Purchase dates:** roughly when were the older lots bought? (Decides which peaks count.)
4. **Stale prices:** value the six thin stocks at the official close, or at the lower traded price?
5. **Take-profit:** keep the targets, fire them only on fresh crosses, or drop them (2.2 a/b/c)?
6. **Trail:** one 15% for all, volatility tiers, or 30% activation for small winners (2.3)? Two-close
   confirmation for jumpy stocks (2.4)?
7. **Old losers:** keep or sell each; if kept, accept re-based floors (2.8)?
8. **"Another 25%":** 25% of the original holding or of what is left?
9. **Sell fees:** can you share one sell contract note (or Meristem's fee schedule)?
10. **Stop orders:** do AfriInvest or InvestNaija offer stop or stop-limit orders?

## Audit notes

Re-checked against `data/` (17 Nov close) before writing:
- Portfolio value ₦10,497,293.10 and cost ₦8,023,767.46: **hold**.
- Sterling rows (volume 0 on 2–9 Oct, ₦7.70 → ₦77.00 on 8 Oct, 5,000 @ ₦5.87; 4,500 × ₦75 = ₦337,500):
  **hold**. Share-count figures come from NGX files the NGX reviewer downloaded; not re-fetched.
- Stale prices: unchanged-close counts, 5-day traded prices and the ₦306,900 gap (PRESCO −₦170,553,
  gain +10.6% → −0.4%): **hold** exactly.
- PRESCO weight 16.26%, code trim 80 units, exact 94 (130 with Sterling fixed): **hold**.
- OKOMU (news ₦1,575 vs official ₦1,276.20) and DANGSUGAR (₦77 vs ₦70.00) peaks: **hold**.
- Zenith: peak ₦136.50 (8 Oct) and closes ₦115.90–116.00 from 11 Nov: **hold**. The ₦1.50 step appears
  in our data on 21 Oct (123.50 → 122.00), but 23 Oct and 26 Oct both show ₦120.90; the NGX reviewer's
  26 Oct ex-date comes from NGX's previous-close column. Date unresolved; the adjusted level is the same.
- Per-account gains (MANSARD +71.1% / −12.4%, MTNN −2.3% / +393%, DANGSUGAR +6.0% / +26.4%): **hold**.
- CWG 4 Nov ₦15.60 vs limit ₦15.66, ₦17.15 next day; DANGCEM −9.99% on 17 Nov: **hold**.
- Wema: reviewers gave 4 Nov and 11 Nov for the ₦32 cross; both are true (it dipped back below on
  10 Nov). Shown as such.
- Take-profit totals: momentum (₦1,277,235) and construction (₦1,407,128) differ by exactly the PRESCO
  cap trim (₦129,893); reconciled, not an error.
- Stale-price value gap: risk ₦306,900 (6 stocks, 5-day average) vs NGX ₦356K (17 Nov VWAP, adds SEPLAT);
  both shown.
- No claim was dropped. Not re-checked: relative-strength correlations, P/L variance shares, the
  backtest's ₦ totals, and the NGX 100,000-unit rule (inferred from data and press, rulebook not read).
