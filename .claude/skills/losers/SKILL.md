---
name: losers
description: Check every holding ("my losers") against the owner's sell rules (20% loss limit, 15% trailing) with the latest prices, pulled on demand. Use when the owner says "update my losers", "check my triggers", "watchlist", or asks whether a watched stock broke its level.
---

# Update my losers

1. Refresh first: follow the `refresh` skill, steps 1–3 (data, dashboard, commit). Data can be
   pulled at any time; never tell the owner to wait.
2. Then:
   ```bash
   ngxprices portfolio losers
   ```
   Rules in `data/rules.json` (set by the owner 18 Nov 2026), applied to every holding:
   `LOSER` = close ≥20% below average cost; `TRAIL` = peak close was ≥20% above cost and the close
   is ≥15% below that peak (sell-part review); `WARN` = ≥10% below cost. Change the rules only
   when the owner asks (edit `rules.json`, then refresh).
   Each holding also gets an early-warning light: RED (rule fired), AMBER (tolerance signal plus a
   general sign: heavy-volume fall, below 20-day average, limit-down day, 3 falls in a row), WATCH,
   NOTE, GREEN. The signals are listed under each line. `TAKE PROFIT` lines (targets +50%/+100%,
   recover cost, 15% size cap) are selling into strength; report them after the warnings.
3. Then `ngxprices portfolio trades` (short-term trade plans in `data/trades.json`): report its alerts
   first (take profit, protect, stop, add, dividend, review), with units and account.
4. For any LOSER or TRAIL flag, give context before calling it:
   - the day's volume against its 20-day average (from `price_history.json`);
   - a dividend or ex-dividend date that explains the drop (see `data/_dataset_descriptions/` and
     news if needed);
   - whether the close came from the live feed (provisional) or official files.
5. Report short: trade alerts first, then losers (loss on cost), then sell-part reviews (% from peak), then AMBER with
   their signals, then WATCH;
   one line saying how many are within the rules. Mention new flags since the last report. Selling
   fees are about 1.8–2%. Information only; the decision is the owner's.
