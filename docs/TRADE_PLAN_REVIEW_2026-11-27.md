# Review: Zenith/GTCO short-term trade plan (27 Nov 2026)

Independent review of `data/trades.json` (set 27 Nov 2026) and `src/ngxprices/trades.py`.
Nothing was changed. Information only; every decision is the owner's.

Checks run: `pytest` 29 passed, 1 skipped; `ngxprices portfolio trades` (output below); dividend-adjusted
back-test on `price_history.json` (2 Jan–27 Nov 2026); Zenith Q3 2026 filing and insider notices from NGX
(docs 48295, 48063, 47969, 198_ZBPLC_*); Meristem contract note 0008187484 (fee lines); web sources listed at the end.

## The plan in prices (27 Nov closes)

| | Zenith | GTCO |
|---|---|---|
| Buy (planned close, after +6.7% / +5.5% day) | ₦108.80 | ₦116.00 |
| All-in cost (+2%) | ₦110.98 | ₦118.32 |
| Break-even after sell fees | ₦113.24 (+4.1%) | ₦120.73 (+4.1%) |
| Take profit 1 (+10% net) | ₦124.56 (**+14.5%**) | ₦132.81 (**+14.5%**) |
| Protect (+5% net) | ₦118.91 (+9.3%) | ₦126.77 (+9.3%) |
| Take profit 2 (+20% net) | ₦135.89 (+24.9%) | ₦144.88 (+24.9%) |
| Stop | ₦99.88 (**−8.2%**) | ₦106.49 (**−8.2%**) |
| Loss at the stop, after fees | −11.8% (≈ −₦23.6K) | −11.8% (≈ −₦23.6K) |

The price must rise 14.5% for the first target but fall only 8.2% to hit the stop.

## Findings, most important first

### 1. Both stocks fail the owner's own short-term "earnings stop" (High)
- Evidence: GTCO 9M 2026 EPS ₦16.58 vs ₦20.71 (−20%); its old 250-unit lot already shows "EXIT RULE: earnings
  stop" in `watchlist.json`. Zenith 9M 2026 (NGX doc 48295, 30 Oct): gross earnings ₦2,865bn vs ₦3,372bn (−15%),
  PAT ₦675.8bn vs ₦764.2bn (−12%), EPS ₦16.41 vs ₦18.60, even though impairments fell from ₦783bn to ₦231bn,
  so core income fell. Zenith 9M is missing from `company_results.json`.
- Context: CBN cut the MPR 350bp to 23% in September; T-bill yields ~17.8%; analysts expect margin pressure from Q4;
  "dividend winter" headlines (Nairametrics, 23 Nov) with UBA and Access suspending dividends. Zenith insiders mixed:
  two directors bought (~117k units at ₦116–120, 2–4 Nov); the staff provident fund sold ~3.8M units at ₦113.70–114.40 (20 Nov).
- Fix: (a) add Zenith 9M 2026 to `company_results.json`; (b) choose: apply the earnings filter to trade plans too
  (BUY becomes "CHECK: EPS falling" until a new report shows growth), or keep the plan and show the falling EPS
  next to each BUY alert so the conflict is visible.

### 2. Reward vs risk is weak; the stop was hit first most of the time in 2026 (High)
- Evidence: back-test, every trading day of 2026 as an entry, 6-month window, dividend-adjusted:
  | | TP1 first | Stop first | Neither |
  |---|---|---|---|
  | Zenith | 83 (37%) | 137 (61%) | 5 |
  | GTCO | 56 (25%) | 149 (66%) | 20 |
  This was a strong year (Zenith ₦64.5 → ₦136.5) and the windows overlap, so treat it as a rough guide.
  Best case after TP1 is ≈ +15% overall (half at +10%, half at +20%); protect gives +7.5%; the stop gives −11.8%.
  With wins of ~+10% and losses of ~−11.8%, the plan needs to win more than ~54% of the time.
- Fix options (owner's choice): (a) widen the stop to 12–15% below cost (fewer noise exits, bigger loss);
  (b) lower TP1 to +7–8% net (≈ +11% price); (c) measure the stop from the buy price, not the all-in cost, so
  −10% means −10% in price; (d) keep as is, knowing the odds.

### 3. Recording a trade buy breaks either the day P/L or the old-lot rules (High, code)
- Evidence: day P/L = value change − `cash_in` (transactions on that day). If a trade buy goes only into
  `trades.json` + `transactions.json` (as CLAUDE.md says), the value does not include the new units but ₦200K
  is subtracted: the day shows a false −₦200K. If it also goes into `holdings.json`, `watchlist_status` combines
  all lots of a ticker: GTCO becomes 1,940 units at ≈ ₦108 average, still "short" with the EXIT flag, and its
  take-profit text would suggest selling trade units; Zenith's trade units would join the long lot.
- Fix: add the trade lot to `holdings.json` with `"trade_id": "T2-GTCO"`; count it in value and P/L; exclude
  trade lots from the horizon/watchlist/take-profit rules (they have their own); show it as its own row
  ("GTCO trade lot: own rules") under the old lot. Test: a buy day shows no false loss; GTCO old-lot rules unchanged.

### 4. The reserve rule conflicts with the stop and raises the maximum loss by half (Medium-high)
- Evidence: the stop is 8.2% below the buy price; ADD fires at −5%; NEAR STOP fires within 3% of the stop
  (≈ −5.4%). Run on Zenith at ₦100–₦102.5: alerts = `NEAR STOP` and `ADD` together. Adding ₦100K at −5%
  moves the stop to ≈ −9.8% and the loss at the stop from ≈ ₦23.6K to ≈ ₦35.5K. The ₦100K is shared, so both
  trades can say ADD on the same night.
- Fix options: (a) drop averaging down; use the reserve only to re-buy after a stop, or for a third stock;
  (b) keep it but require the dip to be ≥5% AND above the near-stop zone, keep the stop at the first lot's level,
  and say which trade gets it first.

### 5. He may not be told: the nightly task does not ask for trade alerts (Medium-high)
- Evidence: the "NGX nightly portfolio update" prompt, step 4, lists value, P/L, movers, sell-rule flags, but not
  trade alerts (only the refresh skill says "report trade alerts first"). If the refresh fails, nothing says
  "trade alerts not checked". Push goes out only when the run judges it noteworthy.
- Fix: update the scheduled task prompt: "Start the reply with TRADE ALERTS (or 'Trades: no alert'); if any step
  fails, still run `ngxprices portfolio trades` on the last prices and say 'prices not updated'." Also show trade
  alerts at the top of the dashboard.

### 6. The stop works on the close, with a next-day sale, in a ±10% market (Medium)
- Evidence: alerts come at 22:15 WAT; the sale is the next day. NGX moves up to ±10% a day; 2026 had full
  −10% days on Zenith (17 Feb; 27 Apr ex-dividend) and GTCO (19 Jun), and 26 Nov saw "10 major stocks at full
  offer". One such day can jump from above the stop to 2% below it, and the next day can open lower again.
- Fix: say in the plan that the stop is "on the close, sold next day, may fill lower"; optional: ask the broker
  for a standing limit-sell at the stop (Meristem/AfriInvest apps support limit orders, not true stop orders).

### 7. Dividends: estimates are at risk and the ex-date math (Medium)
- Evidence: FY 2026 finals are not declared; profits are down and "dividend winter" headlines are out.
  Interims are known: Zenith ₦1.50 (qualification 23 Oct, paid 30 Oct), GTCO ₦1.00 (13 Oct); the next interims
  fall after the 6-month review (~28 May 2027). Zenith's ₦8.75 is ~8% of the price: the ex-date drop is bigger
  than the stop cushion moves (the stop drops by the net ₦7.88; the price by the gross ₦8.75).
- Fix: label `dividends_expected` as "not declared"; when the board declares, replace the estimate and
  record it in `corporate_actions.json`; if no final is declared by the review date, say so in the REVIEW alert.

### 8. A partial take-profit sale switches off take profit 1 (Medium, code)
- Evidence: `took1 = units_sold > 0`. Test: after selling 100 of 1,800 units at TP1, price ₦126 → no alert
  (the other ~800 of "half" are never prompted); price ₦118 → PROTECT for all remaining units.
- Fix: TP1 counts as done only when sold units ≥ the planned half (less 1%); otherwise say "TAKE PROFIT 1:
  sell N more". Same for the stop: a part-filled stop sale must keep saying "sell the rest".

### 9. Price gaps through both targets, and the "+20%" label (Low)
- Evidence: a jump past ₦135.89 gives only TAKE PROFIT 2 (sell all); fine, but the plan text says TP2 is "+20%":
  the overall trade is ≈ +15% (half at +10%).
- Fix: show the overall trade result in the TP2 alert (it does: "trade result") and say "overall ≈ +15%" in the plan note.

### 10. Fees: 2% each way is about right; split it (Low)
- Evidence: Meristem buy note 0008187484: commission 1.35% + 7.5% VAT, SEC 0.3%, stamp 0.08%, alert ₦4.75
  = **1.83%**. Sell side (NGX table): commission 1.35%, NGX 0.3%, CSCS 0.3%, VAT on all three, stamp 0.08%,
  no SEC fee ≈ **2.18%**. Round trip ≈ 4.0% (plan: 4.0%). No minimum charge matters at ₦100–200K (alert fee ₦4.75).
  AfriInvest: no contract note on file; confirm its commission.
- Fix: `buy_fee_pct` 1.85 and `sell_fee_pct` 2.2 instead of one `fee_pct`; use the real totals from contract notes.

### 11. Settlement and tax facts to correct in the docs (Low)
- NGX moved to **T+1** on 1 Jun 2026 (SEC circular; Meristem's 12 Oct note settled 13 Oct), not T+2: sale money
  is available the next day.
- Capital gains tax (Nigeria Tax Act 2025, from 1 Jan 2026): share sales exempt while disposals are under ₦150M and
  gains under ₦10M in any 12 months, so no CGT here. Dividend withholding: 10% is used; check it on the first dividend advice.
- Dividend qualification: the code counts units bought before the NGX ex-date; that matches NGX price adjustment.

### 12. Bank concentration (Low)
- Banks are 13.6% of the ₦9.97M portfolio now (10 banks); 17.0% after the ₦400K. Zenith + GTCO go from 3.6% to 7.4%.
  Both are hit by the same rate cuts and CBN rules, so the two trades are close to one bet.
- Fix: none needed in code; show the bank share in the plan summary.

### 13. Live vs official prices (Low)
- A refresh during trading uses intraday live prices; a stop/target alert can fire on them. Trade rows do not say
  which. Fix: add the price source to each trade row and mark intraday alerts "intraday, confirm at the close".

### 14. The BUY alert never expires (Low)
- Evidence: a planned trade says BUY every refresh at any price below +5%, even after a big fall or after weeks.
- Fix: say "WAIT" if the price is 5%+ below the plan too (re-plan), and add a plan expiry (e.g. 10 trading days).

## Sources
- NGX: Zenith Q3 2026 statements (doc 48295), interim dividend notice (48063), insider notices (198_ZBPLC_*), fee table
  (ngxgroup.com equities market structure).
- SEC Nigeria circular: transition to T+1 (sec.gov.ng).
- PwC Nigeria: capital gains tax reforms 2026.
- Nairametrics headlines, Nov 2026 (dividend winter; bank stocks slide; sell-off 26 Nov); read as headlines only.
