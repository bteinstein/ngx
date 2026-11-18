# Data review — 18 Nov 2026 (handoff section 4)

Checked against the 17 Nov 2026 close (NGX official). Everything was re-derived independently
from `data/` and compared with `ngxprices portfolio losers`, then checked against NGX's own files
(Daily Official List, Shares Outstanding, Daily Summary) fetched with `ngxprices` on 18 Nov.

## 1. What is right

- **Totals:** value ₦10,497,293 · cost ₦8,023,767 · gain ₦2,473,526 at 17 Nov. The sum of
  units × close for all 43 rows (39 tickers) matches the daily log exactly.
- **Daily log:** every value from 9 Oct to 17 Nov equals units × official close (difference ₦0).
- **Take-profit table:** all 15 rows (units to sell, ₦ after fees, recover-cost units, Presco's
  size-cap sale) match an independent recalculation. No arithmetic errors.
- **Stanbic +136%** is correct (cost ₦69.80, close ₦165). **Julius Berger is +134%**. The +1,178%
  belonged to **Sterling**, and that one is wrong (section 2).
- Only Sterling's share count changed between 2 Oct and 17 Nov (NGX Shares Outstanding files).
- News-sourced closes now match NGX official closes for BUAFOODS, DANGCEM, DANGSUGAR, JBERGER, MTNN,
  OKOMUOIL (×3), SEPLAT and WEMABANK (×2), each noted "Checked 18 Nov 2026" in `price_history.json`.

## 2. Sterling (STERLINGNG): 10-for-1 share reconstruction on 8 Oct 2026. Confirmed.

NGX's official files show:

| | 7 Oct 2026 | 8 Oct 2026 |
|---|---|---|
| Shares outstanding | 68,502,331,708 | 6,850,233,171 (÷10) |
| Close | ₦7.70 | ₦77.00 (×10) |
| Market cap | ₦527.47bn | ₦527.47bn (unchanged) |
| P/E | 25.80 | 258.05 (EPS not yet restated) |

It last traded on 22 Sep at ₦7.70. It had no trades from 23 Sep to 9 Oct (suspended), and trading
resumed on 12 Oct around ₦76–77. I could not find the announcement text in NGX's daily files. The
numbers above are from NGX's official lists.

What it means for the holding (Account 1, Meristem; recorded as 5,000 units at ₦5.87 = ₦29,350):

| If Meristem now shows… | Units | Avg cost | Value at ₦75 | Gain | Portfolio effect |
|---|---|---|---|---|---|
| **(a) 500 units** (old 5,000 ÷ 10). The ₦5.87 cost fits the old price | 500 | ₦58.70 | ₦37,500 | +27.8% | value −₦337,500 → ₦10,159,793; gain ₦2,136,026 |
| (b) 5,000 units (the 5,000 was already the new count; cost not restated) | 5,000 | ₦58.70 | ₦375,000 | +27.8% | cost +₦264,150 → ₦8,287,917; gain ₦2,209,376 |

Either way Sterling is **+27.8%, not +1,178%**: no take-profit target is reached, and its weight is
0.4% (a) or 3.6% (b). Under (a) every daily-log value from 9 Oct is overstated by ₦337,500–346,500
(4,500 × that day's close), and Presco's size-cap sale rises from 80 to about 111 units.
**Owner confirmed 500 units on Meristem (18 Nov). Applied:** holdings 500 @ ₦58.70; every daily-log value from 9 Oct lowered (notes give the old figures); the event is recorded in `data/corporate_actions.json`.
The four pre-8 Oct price rows now carry a note explaining the ×10.

## 3. Fixed today (NGX official closes replace wrong news figures)

| Ticker | Date | Was | Official | Effect |
|---|---|---|---|---|
| PRESCO | 31 Dec 2025 | ₦1,709.95 | ₦1,450.00 | none (not a peak) |
| PRESCO | 28 Jul 2026 | ₦2,039.44 | ₦2,070.00 | new stored peak; trailing level ₦1,738.50 → ₦1,759.50 (still a sell-part review) |
| BUACEMENT | 23 Jul 2026 | ₦325.00 (day's high) | ₦324.00 | trailing level ₦276.25 → ₦275.40 (still fine) |

`watchlist.json` was regenerated. Nothing else changed.

## 4. Peaks are understated. This matters more than Sterling.

The trailing rule uses the highest close in `price_history.json`, which has only a few rows before
2 Oct. NGX's own 52-week high (17 Nov Daily Official List) is much higher for most holdings. With
that as the peak, **14 more holdings would be at the 15% trailing level** (25 red instead of 11):

ELLAHLAKES (−61% from 52-wk high), PZ (−41%), BUACEMENT (−35%), NB (−32%), CUSTODIAN (−31%),
DANGSUGAR (−28%), UBA (−27%), CWG (−26%), GTCO (−25%), ACCESSCORP (−25%), MANSARD (−25%),
FCMB (−24%), BUAFOODS (−21%), VFDGROUP (−21%).

Caveats: the 52-week high may come from **before the owner bought** (purchase dates for pre-12 Oct
holdings are not recorded). It may also be an intraday high rather than a close, and it is not
adjusted for dividends. Proper fix: back-fill official closes from Jan 2026 with `ngxprices range`,
and decide whether a peak counts only after the purchase date. **Owner to decide.**

## 5. Dividends make Zenith's flag a false alarm

NGX's previous-close adjustments show the ex-dividend dates: GTCO ₦1.00 (13 Oct), Stanbic ₦4.50
(16 Oct), Zenith ₦1.50 (26 Oct), Okomu ₦11.50 (12 Nov), Seplat ₦258.09 (13 Nov). Peaks are not
adjusted.
- **Zenith:** peak ₦136.50 (8 Oct) was before its ₦1.50 dividend. Adjusted peak ₦135.00 → trailing
  level ₦114.75; close ₦116.00 is −14.1%, **not** past the 15% line. Its red flag comes only from the
  dividend.
- Seplat: adjusted peak ₦16,241.91; close is at the peak, not −1.6%.
- Stanbic: adjusted peak ₦163.50; makes no difference to its status.

## 6. Holdings split across accounts

The table uses the combined holding and average cost. Per account the picture differs:

| Ticker | Account 1 | Account 2 / 3 | Combined |
|---|---|---|---|
| MTNN | 240 @ ₦856.34 (−2.3%) | A3: 105 @ ₦169.70 (**+393%**) | 345 @ ₦647.36 (+29%) |
| MANSARD | 3,750 @ ₦8.18 (**+71%**) | A2: 7,200 @ ₦15.99 (**−12%**) | 10,950 @ ₦13.32 (+5%) |
| DANGSUGAR | 13,666 @ ₦65.09 (+6%) | A2: 2,000 @ ₦54.58 (+26%) | 15,666 @ ₦63.75 (+8%) |
| ACCESSCORP | 1,604 @ ₦20.49 (+31%) | A2: 5,000 @ ₦21.18 (+27%) | 6,604 @ ₦21.01 (+28%) |

Per account, MTN (Account 3) and Mansard (Account 1) would reach take-profit targets, and Mansard
(Account 2) would be at the −10% warning. **Owner to decide** whether rules apply per account.
The MTN Account 3 cost (₦169.70) is worth confirming with InvestNaija.

## 7. Owner's answers (18 Nov) and what was done

1. Sterling: **500 units** → applied (section 2). At 17 Nov: value ₦10,159,793 · cost ₦8,023,767 ·
   gain ₦2,136,026 · day +₦67,569.
2. Dividend-adjusted peaks: **yes** → `data/corporate_actions.json` (Sterling 10:1 plus six dividends
   verified from NGX previous-close adjustments, 12 Oct–13 Nov) and `adjusted_history()` in
   `portfolio.py`, used by `rules_status` for peaks and early-warning signs. Zenith is now amber
   (−14.1% from its adjusted peak), not red. Take-profit flags: 14 (Sterling dropped); Presco is 16.8%
   of the portfolio, size-cap sale 111 units. Earlier 2026 dividends (before Oct) are not in yet: NGX's
   mid-year files are inconsistent and need the back-fill first.
3. Peaks and per-account rules: owner asked for a recommendation (still open):
   - Peaks: back-fill official closes for 2026 and count a peak only from the purchase date where
     known (otherwise from 1 Jan 2026). Needs rough purchase dates from the owner.
   - Accounts: keep one combined signal per stock (same price, one decision), but show each account's
     units and cost next to any sell suggestion so the owner chooses which account to sell from.
4. MTN Account 3 cost ₦169.70: **confirmed** from the owner's InvestNaija screenshot (cost ₦17,818.50, value ₦87,885 at ₦837).

## 8. Back-fill and full 2026 peaks (18 Nov, later)

- Official NGX closes for 2 Jan–30 Sep 2026 added for all 43 tracked tickers (7,934 rows; 1 Oct was a
  holiday). Five non-official figures replaced (Presco 31 Dec and 28 Jul, BUA Cement 23 Jul, Seplat and
  Aradel 19 Feb, GTCO 29 Sep); other news rows matched NGX exactly.
- `data/corporate_actions.json` now has 40 entries: Sterling's 10-for-1 reconstruction, NGX Group's
  1-for-3 bonus (13 Apr, with a ₦2 dividend) and 38 dividends, each checked against NGX's previous close
  on the ex-date. Other 2026 share-count changes (Access, Dangote Sugar, Ellah Lakes, FCMB, Fidelity,
  First HoldCo, GTCO, LASACO, Linkage, Presco, Sterling Jul/Sep, Sunu, UBA, VFD) did not move the price
  (rights issues or placements), so no adjustment.
- Peaks count from 1 Jan 2026 (`rules.json` → `peak_from_default`) or a lot's `bought_from`.
- Result at 17 Nov: **red 25, amber 4, note 1, green 9**. New sell-part reviews: ELLAHLAKES, PZ,
  BUACEMENT, CUSTODIAN, DANGSUGAR, UBA, NB, CWG, MANSARD, GTCO, FCMB, BUAFOODS, ACCESSCORP, VFDGROUP,
  STERLINGNG. Okomu's peak is now ₦1,738.50 (25 Feb, adjusted). Purchase dates would refine these.
- Backtest and the reconciled critique: `docs/REVIEW_CRITIQUE_2026-11-18.md`, first section.
