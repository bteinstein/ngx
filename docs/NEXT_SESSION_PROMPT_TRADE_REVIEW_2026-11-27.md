NGX portfolio: independent review of the Zenith/GTCO short-term trade plan (set 27 Nov 2026).

Read first, in this order:
1. `CLAUDE.md` (sections "Sell rules", "Short-term trades", "Rules (always follow)").
2. `data/trades.json` (the plan: budgets, levels, rules, expected dividends) and `data/rules.json`.
3. `src/ngxprices/trades.py` (how buy/sell alerts are calculated) and its tests in `tests/test_portfolio.py`
   (`test_trade_levels_and_alerts`).
4. `src/ngxprices/portfolio.py`: `realistic_price`, `rules_status`, `upsert_day` (where trades are checked each
   refresh) and `.claude/skills/refresh/SKILL.md` (how alerts are reported).
5. Data: `data/holdings.json` (ZENITHBANK 3,075 @ ₦88.26; GTCO 250 @ ₦41.25, tagged short term with an exit flag),
   `data/company_results.json`, `data/corporate_actions.json` (past dividends), `data/price_history.json`,
   the newest `data/prices_<date>.json`.

The plan in one paragraph: ₦200K Zenith + ₦200K GTCO now, ₦100K reserve (only on a 5%+ dip below entry). Profit
is net of ~2% fees each way and includes dividends received after 10% withholding tax. Take profit 1 at +10% net
(sell half), take profit 2 at +20% net (sell the rest), protect at +5% net after TP1, stop at 10% below the all-in
unit cost (lowered by dividends received), review at 6 months, dividend notice 45 days before the expected
ex-date (Zenith ~27 Apr 2027 ₦8.75, GTCO ~14 Apr 2027 ₦11.76; both estimated from 2026). Buy with a limit at
most 1% above the planned price; wait if 5%+ above. Alerts are checked on every refresh (incl. the 22:15 WAT
nightly task) and shown first.

Job: review the plan and its code for anything missed or wrong. Do NOT change rules, data or code; write
findings and proposals only. Check at least:
- Fees: the real Nigerian fee stack per side (brokerage, SEC, NGX, CSCS, VAT, stamp duty) for Meristem and
  AfriInvest; is 2% each way right, and does any minimum charge matter at ₦100–200K?
- Taxes: dividend withholding (10%?) and whether any capital gains tax on shares applies from 2026.
- Market mechanics: ±10% daily limit, the 100,000-unit rule for a close to move, T+2 settlement (can sale
  proceeds fund the reserve in time?), partial fills, stop on the official close vs intraday.
- Dividends: qualification/closure date vs ex-date, payment date vs the 6-month review, interim dividends,
  what happens to the targets if the FY 2026 dividend differs from the estimate or is not declared.
- Fundamentals: pull Zenith and GTCO Q3 2026 filings from NGX disclosures (recipe in
  `docs/HANDOFF_2026-11-24.md` §4). Zenith's 9M 2026 is missing from `company_results.json` (group PAT ₦675.8bn vs
  ₦764.2bn, EPS ₦16.41 vs ₦18.60, per the filing). Any recapitalisation, rights issue, CBN or forbearance news
  that changes the risk.
- Risk: reward vs risk of +10/+20% targets with a −10% stop (−12% after fees); bank-sector concentration after
  buying; is the ₦100K reserve rule sound; do protect/stop/targets conflict or fire on noise.
- Code: run `pip install -e . --no-build-isolation` and `python -m pytest -q tests`; then
  `ngxprices portfolio trades`. Check edge cases (price gaps through two levels in one day, a sale recorded
  between refreshes, dividend after a partial sale, live vs official prices, the reserve once used).
- Conflicts: the old 250 GTCO units carry a short-term "exit" flag while the plan buys more; how should the
  report show both without confusing him?
- Alerts: will he actually be told? (nightly push notification wording, what happens if a refresh fails).

Output: a short report in `docs/TRADE_PLAN_REVIEW_<date>.md`: findings ranked by importance, each with
evidence and a concrete proposal (rule/setting/code change). Then give him a summary in chat as a numbered list,
and ask which proposals to apply. Apply only what he chooses, with tests; commit to main via a pull request.

He reads on an Android phone: short, plain answers, numbered lists, tables where useful. Information only;
every decision is his. Pull NGX data on demand (never tell him to wait). No Claude attribution in git.
