---
name: losers
description: Check the NGX watchlist ("my losers") against their triggers with the latest prices, pulled on demand. Use when the owner says "update my losers", "check my triggers", "watchlist", or asks whether a watched stock broke its level.
---

# Update my losers

1. Refresh first: follow the `refresh` skill, steps 1–3 (data, dashboard, commit). Data can be
   pulled at any time; never tell the owner to wait.
2. Then:
   ```bash
   ngxprices portfolio losers
   ```
   Rule `low`: trigger = the lowest close in the 2 weeks to 17 Nov (fixed level in
   `data/watchlist.json`). Rule `cost`: trigger = the owner's average cost (Presco).
3. For any stock below its trigger, give context before calling it a breach:
   - the day's volume against its 20-day average (from `price_history.json`);
   - a dividend or ex-dividend date that explains the drop (see `data/_dataset_descriptions/` and
     news if needed);
   - whether the close came from the live feed (provisional) or official files.
4. Report short: each watchlist stock, close vs trigger and the gap in %, breaches first. Selling
   fees are about 1.8–2%. Information only; the decision is the owner's.
