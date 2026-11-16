# NGX portfolio project: notes for Claude (updated 9 Nov 2026)

## Where things live
- **Dashboard (source of truth):** https://claude.ai/artifact/BAjKJSa87hvxs8zjAPr3b7 ("My NGX Portfolio").
  Holdings, prices, price history, accounts and the watchlist are datasets in its database (`datasets/*`).
  Read them with the Artifact tool (read_db) before answering portfolio questions.
- **Accounts:** Meristem, AfriInvest, InvestNaija. Holdings as of screenshots 11–13 Oct 2026, plus the
  12 Oct 2026 Meristem buys (MTN 190 + 50, Seplat 32, Zenith 1,500; contract notes in project files).
  The owner confirmed no other buys or sells since then (9 Nov 2026).
- **ngxprices tool (v0.3.0):** private repo github.com/bteinstein/ngx, branch feature/volume-and-metadata.
  Runs on the owner's Mac (~/bt/ngx) or in Cowork. Claude's sandbox cannot reach doclib.ngxgroup.com,
  so data arrives as uploaded CSVs. Research paper: https://claude.ai/artifact/37pd12a6W2bFwfpi5EdobX

## Data status
- Prices are confirmed against NGX official closes for 6 Nov 2026 (all 43 holdings match).
- Volume, trades and value for 6 Nov are NGX official. Volumes before 6 Nov came from news and price
  lists and may be undercounted. Replace them when the owner uploads
  `ngxprices range --start 2026-10-01 --end 2026-11-10 --out oct_nov.csv`.
- Live prices: `ngxprices live --out now.csv` (30-minute delay; live volume is provisional).
  End-of-day files appear 15:15–21:30 Lagos time; fetch after 22:00.

## Open decision: six losers, decide by Wed 11 Nov 2026
Watchlist tab on the dashboard. Trigger = lowest close in the 2 weeks to 6 Nov.
| Stock | Trigger |
|---|---|
| Sunu Assurances (SUNUASSUR) | ₦2.65 |
| LASACO | ₦1.60 |
| International Breweries (INTBREW) | ₦8.50 |
| Oando | ₦31.50 |
| Africa Prudential (AFRIPRUD) | ₦10.00 |
| Transcorp | ₦30.00 |
| Presco (gain-protection watch) | your average cost ₦1,497.65 |
A close below the trigger means selling is continuing. Check volume and dividend dates before
calling a breach. Selling fees are about 1.8–2%. Claude gives information, not financial advice.

## How the owner works
- "update my losers" = refresh prices, then report which watchlist stocks crossed their triggers.
- Reminders requested for Tue 10 Nov 15:00 (check after close) and Wed 11 Nov 08:30 (decide);
  creation on the phone calendar could not be confirmed.
