# Collecting NGX Equity Prices and Trading Data: Sources, Method, Validation and Tooling

8 Nov 2026 · Babatunde Adebayo

> Copy of the research paper kept as a Claude Doc at https://claude.ai/artifact/37pd12a6W2bFwfpi5EdobX
> (as of 9 Nov 2026). The Claude Doc is the living version; update this copy when it changes.

## Abstract

We built a verified dataset of official closing prices for every equity listed on the Nigerian Exchange (NGX) on five dates. The dates are 30 Dec 2022, 29 Dec 2023, 31 Dec 2024, 31 Dec 2025 and 6 Nov 2026 (year to date). It covers 178 tickers in total and 146–157 per date.

All data comes from free public files that NGX publishes for each trading day on its document library, doclib.ngxgroup.com. No paid feed or login is needed.

The method parses two independent NGX publications for the same day and compares them. Across every stock that appears in both, the closing prices matched exactly, with 0 mismatches on all five dates. Prices for 6 Nov 2026 also matched NGX's live price API exactly.

Each stock is placed in a performance band for each year: Top 10 Gainer, Top 10 Loser or Mid Performer. The method has been packaged as a reusable Python library and a Claude Code skill. Version 0.2.0 adds daily trading volume, value traded, open/high/low, shares outstanding, market cap, EPS, P/E and dividends for every stock, cross-checked across four NGX files. It was tested on 20 randomly chosen trading days.

## Background and research questions

The goal was a complete, trustworthy list of NGX year-end stock prices without buying a data feed. The questions came up in this order. The answers reflect what we found.

| # | Question | Answer |
| --- | --- | --- |
| 1 | Where can we get every NGX stock price at the end of 2023, 2024 and 2025? | From NGX's own document library, which holds the Daily Official List for every trading day. Secondary sources (african-markets.com, investing.com, broker reports) only cover one stock at a time or a partial list. |
| 2 | What method, website and URLs did we use? | We downloaded PDFs and ZIPs from doclib.ngxgroup.com and parsed them in Python. The exact URL patterns are in Data sources and the Appendix. |
| 3 | Can we build a skill or Python/Rust package, or does one already exist? | Yes, we built a Python package (ngxprices) and a Claude Code skill. We found no official NGX package. |
| 4 | Is the data available every day? | Yes. NGX publishes the same set of files for every trading day. Non-trading days have no files. |
| 5 | Can we pull three years of daily data? | Yes. That is about 750 trading days. The random-day test shows the method works across 2023 to 2026. |
| 6 | When does the data appear each day? | The market closes at 14:30 Lagos time (WAT, UTC+1). Files are uploaded between about 15:15 and 21:30, with a median around 17:30. Fetch after 22:00 to be safe. |
| 7 | Add 2026 using last Friday's price, and band each stock per year. | Done. 6 Nov 2026 was added, plus 30 Dec 2022 as the base for 2023. Results describes the bands. |

Later questions:

| # | Question | Answer |
| --- | --- | --- |
| 8 | Can we also get volume and other details, not just prices? | Yes. Version 0.2.0 adds trades, volume, value, open/high/low, shares outstanding, market cap, EPS, P/E, dividends and the 52-week range, all from NGX's free daily files. |
| 9 | Is there a live price API, say at 11am, with all the details? | Partly. NGX's free live API covers all equities, but NGX says its prices are delayed by 30 minutes. It has price and trading fields only; shares, EPS, P/E and dividends exist only in the end-of-day files. `ngxprices live` combines the two. |
| 10 | Does real-time data need payment? | Yes. The 30-minute-delayed data is free. Real-time data is paid: for example ₦50,000 a month per Level 1 user, or ₦10 million a year for a company snapshot licence. Stockbroker trading apps are usually the cheapest way to see live prices. |

One access note: the cloud session first blocked ngxgroup.com. NGX could only be reached after the session's network settings were changed to allow it.

## Data sources

Every price comes from five NGX endpoints on doclib.ngxgroup.com. None of them needs a login. DD-MM-YYYY is the trading date.

| Source | URL | What it holds | Gaps |
| --- | --- | --- | --- |
| Document index (SharePoint REST) | [DownloadsContent list API](<https://doclib.ngxgroup.com/_api/Web/Lists/GetByTitle('DownloadsContent')/items?$select=Title,EncodedAbsUrl&$filter=substringof('31-12-2025',Title)&$top=100>) | Every file published for a date: about 12 per trading day | Returns XML (Atom) |
| Daily Official List – Equities (PDF) | [example: 31-12-2025](https://doclib.ngxgroup.com/DownloadsContent/Daily%20Official%20List%20-%20Equities%20for%2031-12-2025.pdf) | Every Main, Premium, ASeM and REIT/Closed-End Fund stock, traded or not: symbol, name, nominal value, Current Market Price (close), last trade, 52-week range, dividends, EPS, P/E | Leaves out the Growth Board, the Non-Interest Board (from 2025) and some suspended stocks |
| Gainers and Price List (ZIP) | [example: 31-12-2025](https://doclib.ngxgroup.com/DownloadsContent/GAINERS%20AND%20PRICE%20LIST%20FOR%2031-12-2025.zip) | PRICES1.pdf: traded securities by symbol with previous close, open, high, low, close, trades, volume, value. PRICES_LIST2.pdf: every listed equity by board and company name, with market cap and price | PRICES1 lists only stocks that traded. PRICES_LIST2 has names but no symbols |
| Live equities API (JSON) | [statistics/equities](https://doclib.ngxgroup.com/REST/api/statistics/equities/?market=&sector=&orderby=&pageSize=300&pageNo=0) | Latest trading day only: symbol, previous close, open, high, low, close, volume, value, board, sector | No history |
| Data pages | [Data Library](https://ngxgroup.com/exchange/data/data-library/), [Equities Price List](https://ngxgroup.com/exchange/data/equities-price-list/) | The web pages that call the APIs above | The Daily Official List page now returns "Page not found" |

Version 0.2.0 of the package uses one more daily file:

| Source | URL | What it holds | Gaps |
| --- | --- | --- | --- |
| Shares Outstanding (PDF) | [example: 31-12-2025](https://doclib.ngxgroup.com/DownloadsContent/SHARES%20OUTSTANDING%20FOR%2031-12-2025.pdf) | Every listed equity by symbol, including the Growth Board: nominal value, closing price, shares outstanding, market cap | None found. Its closes matched the official list on every day tested |

The official list's "Qty" column is the size of the last trade, not the day's volume. Daily volume comes from PRICES1 or PRICES_LIST2.

Secondary sources considered but not used: african-markets.com and investing.com (one stock at a time), EODHD and Bloomberg/LSEG (paid), and broker and press reports (partial lists).

## Methodology

The close we use is the Daily Official List's "Current Market Price" column. It matched published year-end figures, for example Dangote Cement ₦478.80, MTN ₦200.00 and GTCO ₦57.00 on 31 Dec 2024.

1. **Find the files.** Query the document index for the date. If no files come back, the day was not a trading day. This replaced guessing file names, which failed for the ZIP archive.
2. **Download.** Fetch the Daily Official List PDF and the Gainers and Price List ZIP, then unzip PRICES1.pdf and PRICES_LIST2.pdf.
3. **Parse the official list by position.** Its text comes out jumbled, so we read each word's x-position with pdfplumber and assign it to a column. Close sits at about 368–430 points. Each row starts with a symbol in the left margin, and wrapped company names are joined back. Board, sector and sub-sector come from the section headings above each row.
4. **Clean.** Drop sector heading lines mistaken for rows (no nominal value). Remove duplicate rows (one per dividend line), keeping the first.
5. **Fill the gaps.** Add Growth Board stocks from PRICES_LIST2, using a name-to-symbol map of 9 names, for example THE INITIATES PLC → TIP. Add Jaiz Bank (Non-Interest Board) from PRICES1 when missing. Add Greif Nigeria (VANLEER) from PRICES_LIST2 for years it is absent from the official list.
6. **Use better names.** Replace abbreviated official-list names with the full name from PRICES_LIST2 when the price matches and the names start alike.
7. **Combine dates.** Join all dates by symbol. A ticker change makes two rows. They are linked in a Notes column, not merged, because some changes could not be confirmed.
8. **Compute.** % change and band columns are Excel formulas, so they update if a price is corrected.

## Validation

Every check passed. The official-list close equalled the separately published traded price for every stock that appeared in both files, and the stock counts reconciled with NGX's full list on every date.

| Date | Official-list stocks | Traded stocks (PRICES1) | In both | Price mismatches | Full list (PRICES_LIST2) | Final dataset |
| --- | --- | --- | --- | --- | --- | --- |
| 30 Dec 2022 | 150 | 108 | 107 | 0 | 157 | 157 |
| 29 Dec 2023 | 147 | 121 | 116 | 0 | 155 | 155 |
| 31 Dec 2024 | 144 | 127 | 122 | 0 | 152 | 152 |
| 31 Dec 2025 | 139 | 128 | 121 | 0 | 148 | 148 |
| 6 Nov 2026 | 136 | 132 | 125 | 0 | 146 | 146 |

The final dataset is larger than the official list because of the gap-filling in Methodology, step 5. The count for 31 Dec 2025 includes Jaiz Bank, which is listed separately under the Non-Interest Board. Further checks:

- **Live API:** all 146 prices for 6 Nov 2026 matched NGX's live equities API, whose trade date was 6 Nov 2026. None was missing.
- **Name-matched check:** each official-list close was compared with the full list by company name. The only differences came from abbreviated names matching the wrong company, not from prices.
- **Spot checks:** Dangote Cement, MTN and GTCO year-end prices match widely reported figures, and the NGX All-Share Index closed 2024 at 102,926.40 ([Prime Business Africa](https://www.primebusiness.africa/ngx-records-37-65-growth-ends-2024-on-a-high-note)).
- **Workbook:** LibreOffice recalculated all 1,623 formulas with 0 errors.

**Checks added in version 0.2.0.** The `ngxprices validate` command runs four checks every day. On 31 Dec 2025 all four passed:

| Check | Stocks compared | Mismatches |
| --- | --- | --- |
| Close: official list vs PRICES1 | 121 | 0 |
| Close: official list vs Shares Outstanding | 138 | 0 |
| Volume: PRICES1 vs full price list | 127 | 0 |
| Market cap = shares outstanding × close (0.5% tolerance) | 146 | 0 |

If a file is missing, the check that needs it is marked "not compared" rather than passed, because a check that compares nothing proves nothing.

## Results

The workbook NGX_Year_End_Prices_2022_2026.xlsx holds 178 tickers. Each has a closing price on up to five dates, the yearly % change and a performance band for each year. There is also a detail sheet per date and a Sources & Notes sheet.

**Band rules.** Each stock is banded on its % change for the year: prior year-end close to year-end close, or to 6 Nov for 2026.

- **Top 10 Gainer:** among the 10 highest % changes, and the change is above 0.
- **Top 10 Loser:** among the 10 lowest % changes, and the change is below 0.
- **Mid Performer:** every other stock with a price at both dates.
- **N/A:** no price at the start or end of the year, because of a new listing, delisting or ticker change.

Stocks tied at rank 10 are all included.

| Year | Top 10 Gainers (% change) | Top 10 Losers (% change) | Mid | N/A |
| --- | --- | --- | --- | --- |
| 2026 YTD (to 6 Nov) | STERLINGNG +981, FTGINSURE +645, SCOA +365, UNIONDICON +244, BERGER +208, PREMPAINTS +204, UPDCREIT +191, AIRTELAFRI +178, SEPLAT +175, RTBRISCOE +161 | ALEX −54, SUNUASSUR −51, SOVRENINS −49, ROYALEX −48, TRIPPLEG −45, ELLAHLAKES −45, VERITASKAP −44, AUSTINLAZ −44, GUINEAINS −42, REGALINS −41 | 120 | 38 |
| 2025 | NCR +1354, ASOSAVINGS +542, EUNISELL +497, BETAGLAS +470, TIP +432, MBENEFIT +408, GUINNESS +398, MECURE +369, ELLAHLAKES +324, VITAFOAM +300 | VFDGROUP −75, CONOIL −52, SUNUASSUR −49, OANDO −39, JOHNHOLT −37, AFRIPRUD −28, JULI −22, LIVINGTRUST −21, LASACO −21, GOLDBREW −18 | 122 | 36 |
| 2024 | JULI +1646, SUNUASSUR +877, OANDO +529, EUNISELL +502, TRANSCORP +402, CONOIL +362, TANTALIZER +336, RTBRISCOE +310, VERITASKAP +268, JBERGER +261 | VFDGROUP −78, MULTIVERSE −60, DANGSUGAR −43, NASCON −42, CILEASING −33, DAARCOMM −30, THOMASWY −30, MTNN −24, UPDCREIT −22, NESTLE −20 | 128 | 30 |
| 2023 | TRANSCOHOT +1023, CHAMS +795, CWG +722, TRANSCORP +666, MRS +645, NNFM +640, JAPAULGOLD +507, IKEJAHOTEL +471, FTNCOCOA +410, SKYAVN +407 | ROYALEX −41, JULI −25, CHAMPION −25, ELLAHLAKES −19, PHARMDEKO −13, NB −12, UNIONDICON −9, SMURFIT −9, NGXGROUP −6, GUINNESS −5 | 130 | 28 |

These are price changes only. Very large moves, such as STERLINGNG +981% in 2026, may come from a share restructuring or bonus issue rather than market gains. Check them before drawing conclusions.

Ticker changes found:

- **Confirmed:** FBNH → FIRSTHOLDCO (2025), STERLNBANK → STERLINGNG and CHIPLC → CONHALLPLC (2023), ABBEYBDS → ABBEYBANK and UHOMREIT → UHREIT (2026).
- **Likely, still to verify:** WAPCO → HBMNG and DEAPCAP → AVACAP (2026).

## Package and skill

The method is now a Python package, ngxprices (version 0.3.0), in the private GitHub repo [bteinstein/ngx](https://github.com/bteinstein/ngx), with a Claude Code skill. Version 0.2.0 adds trading volume, size, fundamentals and dividends to every row; version 0.3.0 adds the `live` command (see Live prices and real-time data). Both are on the branch feature/volume-and-metadata. Its 12 offline tests pass, and 1 network test runs only when NGX_NETWORK_TESTS=1 is set.

| Module | Role |
| --- | --- |
| http.py | Downloads with a 1-second delay between requests, 3 retries with backoff, and a local cache (~/.cache/ngxprices, or the NGXPRICES_CACHE variable) |
| parsers.py | Parsers for the official list (including its run-together right-hand columns), PRICES1, PRICES_LIST2 and Shares Outstanding, plus a check of the date printed on page 1 |
| core.py | list_files(date), get_daily_prices(date), get_range(start, end), validate(date), get_live_prices() |
| cli.py | The ngxprices command: fetch, range, validate, files |

Command-line use:

```bash
ngxprices fetch --date 2025-12-31 --out day.csv
ngxprices range --start 2025-12-24 --end 2025-12-29 --out range.csv
ngxprices live --out now.csv
ngxprices validate --date 2025-12-31
ngxprices --fields basic fetch --date 2025-12-31
ngxprices files --date 2025-12-31
```

Each row is one stock on one trading day. `--fields basic` keeps only the original 8 columns.

| Group | Columns | Source file |
| --- | --- | --- |
| Identity | date, symbol, name, board, sector, subsector | Official list |
| Close | close | Official list, else full price list, Shares Outstanding or PRICES1 |
| Activity | prev_close, open, high, low, change, pct_change, trades, volume, value_ngn | PRICES1 for traded stocks; trades and volume for the rest from the full price list |
| Size | nominal_value, shares_outstanding, market_cap_ngn | Shares Outstanding |
| Fundamentals | week52_high, week52_low, last_trade_price, last_trade_date, last_trade_qty, eps, pe | Official list |
| Dividends | last_exdiv_date, last_exscrip_date, div_paid_date, div_interim, div_final | Official list |
| Provenance | source, sources_used | |

For example, Access Holdings on 31 Dec 2025: volume 57,601,512, 2,064 trades, ₦1.22 billion traded, 53.3 billion shares and a market cap of ₦1.12 trillion.

- **Untraded stocks:** trades, volume and value are 0, and open, high and low equal the close.
- **Missing activity files:** if neither trading-activity file is usable that day, these columns are left blank instead of 0.

Two safeguards were added after the test runs:

- **Date check:** a file is ignored if the date printed inside it differs from the requested date.
- **File matching:** files are found by URL file name as well as title, because NGX sometimes files them under the wrong title.

The skill (`skill/ngx-prices/SKILL.md` in the repo) tells Claude when to use the package, how to call it, and the data caveats below. A Rust version was not built; the Python package covers the need.

The package only reads public NGX files and adds a delay between requests to avoid overloading NGX's servers.

## Random-day test

Re-run with version 0.2.0, the package returned data for all 20 random trading days, 146–157 stocks each. Every cross-check that could run found 0 mismatches. On 4 days NGX had a missing or misfiled file; the checks that needed it are marked "not compared" below.

We picked 5 random weekdays per year for 2023–2026 (seed 42). If a pick had no files, it moved forward to the next trading day. The output is test_output/random_days.csv (2,995 rows) and test_output/report.json. A fresh download takes about 7 seconds per day, or 13–18 seconds when a nearby day must also be fetched.

Each check cell shows mismatches / stocks compared. "Not compared" means the file the check needs was missing.

| Date | Stocks | Close vs PRICES1 | Close vs Shares | Volume check | Note |
| --- | --- | --- | --- | --- | --- |
| 2026-09-15 | 147 | 0 / 125 | 0 / 136 | 0 / 132 | |
| 2026-08-05 | 147 | not compared | 0 / 136 | not compared | PRICES1.pdf missing from the ZIP. Value traded is blank for traded stocks |
| 2026-07-21 | 146 | 0 / 126 | 0 / 135 | 0 / 134 | |
| 2026-03-12 | 147 | not compared | 0 / 137 | not compared | ZIP overwritten with 13 Mar data. Volume left blank (unknown), not 0 |
| 2026-01-09 | 148 | 0 / 123 | 0 / 138 | 0 / 129 | |
| 2025-12-29 | 147 | 0 / 120 | 0 / 137 | 0 / 126 | |
| 2025-06-17 | 148 | 0 / 123 | 0 / 140 | 0 / 128 | ZIP filed under the title "FOREIGN EQUITY LISTING" |
| 2025-06-05 | 148 | 0 / 121 | 0 / 140 | 0 / 126 | |
| 2025-03-07 | 149 | not compared | not compared | not compared | Official list held 6 Mar data. Closes from Shares Outstanding (was 126 stocks in version 0.1) |
| 2025-01-22 | 152 | 0 / 120 | 0 / 143 | 0 / 124 | |
| 2024-10-29 | 152 | 0 / 119 | 0 / 143 | 0 / 123 | |
| 2024-04-12 | 154 | 0 / 123 | 0 / 146 | 0 / 127 | Picked 9 Apr; 9–11 Apr were public holidays |
| 2024-03-13 | 154 | not compared | not compared | 0 / 77 | Official list not published |
| 2024-03-01 | 153 | 0 / 119 | 0 / 145 | 0 / 124 | |
| 2024-01-23 | 154 | 0 / 119 | 0 / 146 | 0 / 124 | |
| 2023-07-17 | 156 | 0 / 114 | 0 / 149 | 0 / 117 | |
| 2023-06-26 | 156 | 0 / 120 | 0 / 149 | 0 / 122 | |
| 2023-06-09 | 156 | 0 / 118 | 0 / 149 | 0 / 120 | |
| 2023-03-22 | 157 | 0 / 99 | 0 / 150 | 0 / 101 | |
| 2023-01-18 | 157 | 0 / 108 | 0 / 150 | 0 / 111 | |

The market-cap check (shares × close) passed for every stock on all 20 days.

The main lesson is that NGX files can be filed under the wrong date, and that a check with nothing to compare must not be read as a pass. Before the date check was added, the prototype reported 49 and 52 false mismatches on 7 Mar 2025 and 12 Mar 2026. All five dates in the year-end workbook were checked, and each file carries the correct printed date.

On 31 Dec 2025, field coverage was:

- **Volume, trades and value:** all 148 stocks
- **Shares outstanding:** 146 stocks
- **EPS:** 124 stocks
- **52-week high and low:** about 123 stocks
- **P/E:** 91 stocks
- **Final dividend:** 128 stocks

## Daily publication timing

NGX uploads each day's files between about 15:15 and 21:30 Lagos time (WAT, UTC+1). The median is about 17:30, three hours after the 14:30 close. These are the document library's upload times (Created) across the 20 test days.

| File | Earliest | Median | Latest |
| --- | --- | --- | --- |
| Daily Official List – Equities | 15:18 | 17:28 | 21:30 |
| Gainers and Price List (ZIP) | 15:22 | 17:27 | 21:34 |

- In 2023, files often arrived in the evening, between 19:00 and 21:30.
- In 2025 and 2026, most arrived between 15:15 and 17:00. Exceptions were 21:30 on 5 Aug 2026 and a next-day replacement on 12 Mar 2026.
- A scheduled daily fetch should run after 22:00 WAT, and re-check the previous day in case a file was replaced.
- For same-day prices before the files appear, use NGX's live equities API.

The internal timestamps inside the year-end ZIPs (about 12:20–16:15) show when NGX generated the files, not when they were uploaded.

## Live prices and real-time data

During trading hours, NGX's free live API gives prices about 30 minutes old for every equity. True real-time data is a paid service. The live API carries prices and trading activity but no shares, EPS, P/E or dividends.

**The free live API.** It returns all 146 equities in one call ([live API](https://doclib.ngxgroup.com/REST/api/statistics/equities/?market=&sector=&orderby=&pageSize=300&pageNo=0)).

- **Fields:** previous close, open, high, low, close, change, % change, trades, volume, value, board, sector and trade date.
- **Delay:** NGX's [Equities Price List](https://ngxgroup.com/exchange/data/equities-price-list/) page says: "Prices displayed on this website are delayed by 30 minutes."
- **Caching:** the API's response headers allow it to be cached for up to 30 minutes.

**The `ngxprices live` command.** It adds shares outstanding, EPS, P/E, dividends and the 52-week range from the most recent day with published files, shown in a `metadata_date` column. Market cap is recomputed as shares × live price.

**Checked against end-of-day files.** On Monday 9 Nov 2026 before the open, the live API still showed Friday 6 Nov. Compared with Friday's end-of-day files:

- **Closes:** matched for all 146 stocks.
- **Volume, trades and value:** matched for 145. First HoldCo's live volume was 11.2 million, against 18.9 million in both end-of-day files.
- **So:** treat live volume as provisional and the end-of-day files as final.

**Still to check.** Whether the API updates during trading, and how far behind it runs, will be checked on 9 Nov 2026 during trading hours.

**Cost of real-time data.** Undelayed prices are paid. Selected fees from NGX's [Market Data Pricelist](https://ngxgroup.com/exchange/data/data-pricing-policies-contracts/):

| Service | Fee |
| --- | --- |
| Delayed prices (website and live API) | Free to view |
| Real-time Level 1, per data-feed user | ₦50,000 a month |
| Real-time Level 2 (order depth), per data-feed user | ₦75,000 a month |
| Real-time snapshot licence (internal use) | ₦10,000,000 a year |
| Real-time data feed (distributors) | ₦40,000,000 a year |
| Real-time prices on your own website or app | ₦625,000 a year |

NGX sells real-time access through its [X-DataPortal](https://dataportal.ngxgroup.com/), stockbrokers and registered data vendors. For a personal project, a stockbroker's trading app is usually the cheapest way to see live prices.

## Limitations and future work

The main risk is that the parser depends on NGX's PDF layout. A layout change would break column positions without warning, so every run should repeat the cross-source mismatch check.

- **Not adjusted for corporate actions:** % changes ignore dividends, bonus issues, splits and share restructurings.
- **Thin trading:** many stocks do not trade for weeks, so their price stays the same and 0% is common. These stocks land in Mid Performer.
- **Board coverage:** the official list leaves out the Growth Board, the Non-Interest Board and some suspended stocks. A 9-name Growth Board map fills the gap and must be extended when new companies list there.
- **Ticker changes:** they are linked by notes, not merged. Two links (WAPCO → HBMNG, DEAPCAP → AVACAP) are unconfirmed.
- **Access:** the cloud session needs ngxgroup.com and doclib.ngxgroup.com on its allowed list.
- **Scope:** ETFs, bonds and mutual funds are excluded. NGX publishes separate daily lists for them.

Caveats on the version 0.2.0 fields:

- **Fundamentals as printed:** EPS and P/E are taken exactly as NGX prints them, and some look wrong. MTN on 31 Dec 2025 shows EPS 0.01 and P/E 50,216.
- **Interim dividend:** this column is empty in every NGX file checked, so it is always blank.
- **Run-together columns:** the official list's right-hand columns (52-week range, dividend dates, EPS, P/E) run together in the PDF text. The package rebuilds them from character positions and number shapes, so a layout change could break them first.
- **Last trade vs volume:** "last trade quantity" is the size of one trade; use the volume column for the day's total.
- **Fallback high and low:** when NGX prints "-" for a traded stock's high or low, the package uses the higher and lower of open and close.
- **Live data:** prices are 30 minutes old, live volume can undercount (First HoldCo on 6 Nov 2026), and EPS, P/E and dividends in `ngxprices live` come from the previous end-of-day files.

Next steps:

- [ ] Confirm the two unconfirmed ticker changes from NGX notices
- [ ] Pull a full daily history for 2023 to 2026 (about 750 days) into one table
- [ ] Add corporate-action adjustment using NGX's corporate disclosures
- [ ] Schedule a daily fetch after 22:00 WAT that re-checks the previous day

## Appendix: URL patterns and file inventory

Replace DD-MM-YYYY with the trading date. Spaces are encoded as %20.

```text
Index:   https://doclib.ngxgroup.com/_api/Web/Lists/GetByTitle('DownloadsContent')/items?$select=Title,EncodedAbsUrl&$filter=substringof('DD-MM-YYYY',Title)&$top=100
DOL:     https://doclib.ngxgroup.com/DownloadsContent/Daily%20Official%20List%20-%20Equities%20for%20DD-MM-YYYY.pdf
Prices:  https://doclib.ngxgroup.com/DownloadsContent/GAINERS%20AND%20PRICE%20LIST%20FOR%20DD-MM-YYYY.zip
Live:    https://doclib.ngxgroup.com/REST/api/statistics/equities/?market=&sector=&orderby=&pageSize=300&pageNo=0
```

Files NGX publishes for each trading day, as found on 29 Dec 2023, 31 Dec 2024 and 31 Dec 2025:

- Daily Official List – Equities (PDF), Bonds (PDF) and ETFs (PDF)
- Gainers and Price List (ZIP: GAINERS AND LOSERS, PRICES1, PRICES_LIST2)
- Market Capitalization (PDF)
- Daily Summary
- Cover page
- Foreign Equity Listing
- Memorandum Quotation
- P.E Ratio
- Shares Outstanding
- Weekly Summary Statistics (Fridays)

Dates used:

| Year | Last trading day used |
| --- | --- |
| 2022 | Fri 30 Dec 2022 |
| 2023 | Fri 29 Dec 2023 |
| 2024 | Tue 31 Dec 2024 |
| 2025 | Wed 31 Dec 2025 |
| 2026 | Fri 6 Nov 2026 (last Friday, year to date) |

## Sources

- [NGX document library](https://doclib.ngxgroup.com/DownloadsContent/Daily%20Official%20List%20-%20Equities%20for%2031-12-2025.pdf) (Daily Official List, Gainers and Price List, Market Capitalization)
- [NGX live equities API](https://doclib.ngxgroup.com/REST/api/statistics/equities/?market=&sector=&orderby=&pageSize=300&pageNo=0)
- [NGX Data Library page](https://ngxgroup.com/exchange/data/data-library/)
- [NGX Equities Price List page](https://ngxgroup.com/exchange/data/equities-price-list/)
- [Nairametrics: Flour Mills delisted](https://nairametrics.com/2025/01/05/ngx-delists-flour-mills-of-nigeria-from-daily-official-list-after-december-16-suspension/)
- [Prime Business Africa: NGX ends 2024](https://www.primebusiness.africa/ngx-records-37-65-growth-ends-2024-on-a-high-note)
