# Year-end workbook builder

These are the prototype scripts that built `data/NGX_Year_End_Prices_2022_2026.xlsx`.
They predate the `ngxprices` package. New work should use the package; these files are kept so the workbook can be rebuilt exactly.

| File | Role |
| --- | --- |
| `parse2.py` | Parses the Daily Official List (Equities) PDF by column position |
| `prices1.py` | Parses PRICES1.pdf (traded securities, by symbol) |
| `plist2.py` | Parses PRICES_LIST2.pdf (full price list by board, incl. Growth Board) |
| `build3.py` | Merges the dates, writes the workbook (prices, % change, band formulas) |

## Rebuild

1. For each date in `YEARS` (in `build3.py`), download into a work folder:
   - `pdfs/DOL_DD-MM-YYYY.pdf` from `https://doclib.ngxgroup.com/DownloadsContent/Daily%20Official%20List%20-%20Equities%20for%20DD-MM-YYYY.pdf`
   - `zips/DD-MM-YYYY/` = unzipped `https://doclib.ngxgroup.com/DownloadsContent/GAINERS%20AND%20PRICE%20LIST%20FOR%20DD-MM-YYYY.zip`
2. Run `python build3.py <workfolder> out.xlsx` (needs `pdfplumber` and `openpyxl`).
3. Recalculate the formulas by opening the file in Excel or LibreOffice.

These scripts do not check the date printed inside each file. The `ngxprices` package does. All five workbook dates were checked by hand and are correct.
