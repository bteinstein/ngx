---
name: decisions
description: Turn the owner's sell rules into a clear decision list for every holding (exit, sell part, recover cost, hold), with units per account. Use when the owner says "what should I decide", "decisions", "what do my rules say", "what do I sell", "action list", or finds the rule flags unclear.
---

# Decision list from the owner's rules

The owner (BT) makes every decision. This skill states what his own rules in `data/rules.json` say
for each holding, grouped so he can decide group by group. Information, not advice: never say
"you should"; say "your rules say".

## 1. Fresh data

Follow the `refresh` skill, steps 1–3, unless a refresh ran in this session today. Data can be pulled
at any time; never tell the owner to wait.

## 2. Group the holdings

```bash
ngxprices portfolio decisions          # add --json for the raw groups
```
Groups, in order (from `decision_groups` in `src/ngxprices/portfolio.py`):
1. **Short-term trades that failed**: past the short-term loss limit (15%). Rules say exit everything.
   His choice: sell all, or move to long term *on purpose* (logged in `horizon_log.json`; the webinar
   lesson is not to turn a losing trade into an investment).
2. **Short-term winners whose earnings fell**: earnings stop fired. Rules say exit everything; at least
   take the +30% target (sell half) where shown.
3. **Short-term holdings off their peak or stalled**: trailing stop (10%) or 8-week time stop, earnings
   fine. Sell part, or move to long term.
4. **Long term (or untagged) in loss**: past the 20% limit (15% once EPS is falling) or on warning.
   Sell, or keep only if he still trusts the business.
5. **Long-term winners up 100%+**: recover-cost rule. His rule says sell enough to get the cost back;
   the coach holds true investments. Ask him to pick one approach for all of them.
6. **Hold**: within the rules. Mention a size-cap note (e.g. PRESCO over 15%) and whether that sale
   would be at a loss after fees.

Then list buy levels hit (the `Buy levels` line): alerts only, closes only.

## 3. Check before reporting

For each holding in groups 1–4: the day's volume against its 20-day average, a dividend or ex-date
that explains a drop, and whether the close is live (provisional) or official. Use the realistic price
when the rules did (thin stocks: JBERGER, NNFM, OKOMUOIL, PRESCO and others).

## 4. Report (phone-sized)

One short section per non-empty group: a bold title saying what the rules say, one line per holding
(ticker, gain on cost, the gain needed to break even for losses, the account(s) it sits in), then the
one choice he has to make for that group. Put "Everything else: hold" in one line. End with:
place limit orders (not market orders), check that day's volume, about 2% fees each way, and spread
thin stocks over the days shown. Offer exact units per account for the groups he acts on.

When he decides, record nothing until a contract note or his confirmation of a fill; sells go in
`data/transactions.json` (they count as targets taken), and a change of term goes in the lot's
`horizon` and `horizon_note` in `holdings.json` (the refresh logs it).
