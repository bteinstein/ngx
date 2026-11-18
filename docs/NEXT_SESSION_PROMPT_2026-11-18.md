# Prompt for the next session (written 18 Nov 2026)

Copy everything below the line into a new session.

---

NGX portfolio, follow-up to the 18 Nov review. Read CLAUDE.md, then the first section of docs/REVIEW_CRITIQUE_2026-11-18.md (it is the current one), docs/DATA_REVIEW_2026-11-18.md, data/rules.json and src/ngxprices/portfolio.py (rules_status, adjusted_history, early_warning, take_profit).

State at the 17 Nov close: 39 stocks across Meristem, AfriInvest and InvestNaija. Lights: 25 red, 4 amber, 1 note, 9 green. Peaks are official NGX closes since 1 Jan 2026 (rules.json peak_from_default), adjusted for data/corporate_actions.json. A holding lot's "bought_from" in data/holdings.json moves its peak start; for a stock held in two accounts, the earliest lot date applies. Only the Meristem MTN lot has a date (12 Oct 2026).

Two jobs, in order. Ask me before changing any data or rule.

1. Purchase dates. Ask me for rough purchase months (month and year is enough) for the main holdings, account by account. Start with the reds that are still in profit: Presco, BUA Cement, Dangote Sugar, BUA Foods, Okomu, First HoldCo, GTCO, PZ, Access, UBA, Mansard, FCMB, VFD, Ellah Lakes, Sterling, UPDC REIT. Then the rest. Record each as "bought_from" (first day of the month) on that lot in data/holdings.json, add a note, re-run `ngxprices portfolio losers`, and show me which lights changed.

2. The experts' proposals. Go through these one at a time in plain words, each with its effect on my holdings today (which lights change) and in the 2 Oct–17 Nov backtest. Apply only the ones I choose:
   - wider trail for jumpy stocks (risk manager's tiers: 12% / 15% / 20% by typical daily move and limit moves), or a 30% activation for small winners;
   - two closes in a row before red, for jumpy stocks;
   - "realistic price" for thin stocks whose official close doesn't move (Presco, Julius Berger, BUA Foods, Okomu, NNFM, Transcorp Hotels);
   - take-profit: keep, fire only on fresh crosses, or drop;
   - "past the limit" state with re-based floors for the six old losers;
   - fewer noisy lights (20-day average only at ≥3%, median volume, block-trade filter).
   Then implement the chosen ones in rules.json and portfolio.py, with tests (python -m pytest -q tests). Regenerate data/watchlist.json, update the dashboard per the refresh skill (watchlist dataset and its description), update CLAUDE.md, commit and push to main.

I read on an Android phone: keep answers short and plain. Information only, no financial advice; every decision is mine. No Claude attribution in git.
