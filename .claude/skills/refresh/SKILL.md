---
name: refresh
description: Update the NGX portfolio end to end, on demand at any time - pull the latest NGX prices and volumes (official files if published, else NGX's live feed), update data/, push the new data to the claude.ai dashboard, commit, and report. Use when the owner says "refresh", "update", "update the dashboard", "today's prices", "how did my portfolio do", or asks for prices for a specific day.
---

# Refresh the portfolio

Run every step without asking. Data can be pulled at any time: never tell the owner to wait for the
close, for 22:00 or for official files. If a step fails, show the exact error and what you tried.

## 1. Pull and write the data

```bash
pip install -q -e . 2>/dev/null; ngxprices portfolio refresh --json > /tmp/refresh.json; cat /tmp/refresh.json
```
- For a specific day: add `--date YYYY-MM-DD`.
- It uses NGX's official files when they exist for the day, otherwise the live feed (about 30 min
  delayed; after the 14:30 close its prices are final, volume provisional). Earlier live days are
  upgraded to official automatically (`upgraded` in the output).
- It writes `data/price_history.json`, `data/prices_<date>.json` and a `data/daily_log.json` row with
  an auto note. A hand-written note on that day is kept.
- If it fails with "no price for held stocks", report which and stop.

## 2. Update the claude.ai dashboard

Dashboard: https://claude.ai/artifact/BAjKJSa87hvxs8zjAPr3b7 (My NGX Portfolio).

1. Stage the files: `ngxprices portfolio stage --out /tmp/dash_upload` (prints three paths).
2. Upload each file as an asset, one call each (JSON files can't be batched):
   Artifact tool, `url` = the dashboard, `asset: true`, `file_path` = the staged file. Note each
   returned `/_blob/<id>` url.
3. Read the three datasets to get their versions: ArtifactData `get`, collection `datasets`, doc ids
   `prices`, `price_history`, `daily`.
4. One ArtifactData `batch` of three `update`s (pin each with `if_version`):
   - `source`: `{kind: "file", name: <staged file name>, url: <blob url>, format: "json"}`
   - `updated`: `{at: <UTC now ISO>, by: "Claude"}`, `edit`: `{via: "claude", at: <same>}`
   - `prices.description`: one sentence: "Closes for <day> from <source kind and time>; …" (say when
     volume is provisional).
5. Don't change the page (`files/index.html`) unless asked.

## 3. Commit and push

```bash
git add data && git commit -m "Add <d Mon> closes (<official|live feed>)" && git push -u origin HEAD
```
Use "Update <d Mon> closes to official" when only upgrades happened. No Claude attribution lines.

## 4. Report (short; the owner reads on a phone)

From the JSON: value and day P/L (₦ and %), the source (official or live, and time), the top 3 up and
down, any sell-rule flags (losers, sell-part reviews, new AMBER early warnings, new take-profit flags; or "all within the rules"), heavy-volume stocks (≥2× their average), any
upgraded days, and the dashboard link. Information only, no advice.
