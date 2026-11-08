"""Build the NGX year-end price workbook.

Usage: python build3.py WORKDIR OUT.xlsx
WORKDIR must contain pdfs/DOL_<DD-MM-YYYY>.pdf and zips/<DD-MM-YYYY>/ (each date's unzipped
'GAINERS AND PRICE LIST' archive) for every date in YEARS. See README.md in this folder.
"""
import sys, os, difflib, re
S=sys.argv[1]; OUT=sys.argv[2]
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import parse2, plist2, prices1
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
YEARS=[(2022,'30-12-2022','30 Dec 2022'),(2023,'29-12-2023','29 Dec 2023'),(2024,'31-12-2024','31 Dec 2024'),(2025,'31-12-2025','31 Dec 2025'),(2026,'06-11-2026','06 Nov 2026')]
GROWTH={'CHELLARAMS PLC.':'CHELLARAM','RONCHESS GLOBAL RESOURCES PLC':'RONCHESS','MCNICHOLS PLC':'MCNICHOLS',
 'LIVINGTRUST MORTGAGE BANK PLC':'LIVINGTRUST','MECURE INDUSTRIES PLC':'MECURE','BRICLINKS AFRICA PLC':'BAPLC',
 'THE INITIATES PLC':'TIP','JULI PLC.':'JULI','MCNICHOLS CONSOLIDATED PLC':'MCNICHOLS','ZICHIS AGRO ALLIED INDUSTRIES PLC':'ZICHIS'}
BOARDNAME={'GROWTH BOARD':'Growth Board'}
GSECT={'CHELLARAM':'CONGLOMERATES','RONCHESS':'CONSTRUCTION/REAL ESTATE','MCNICHOLS':'CONSUMER GOODS','LIVINGTRUST':'FINANCIAL SERVICES','MECURE':'HEALTHCARE','BAPLC':'ICT','TIP':'SERVICES','JULI':'SERVICES','ZICHIS':'AGRICULTURE'}
def tc(x): return (x or '').title().replace('Ict','ICT').replace(' And ',' and ')
def norm(n): return re.sub(r'[^A-Z0-9]','',n.upper())
data={}   # year -> symbol -> record
for y,d,_ in YEARS:
    D={r['symbol']:r for r in parse2.parse(f'{S}/pdfs/DOL_{d}.pdf')}
    PL=plist2.parse(d,S); P1=prices1.parse(d,S)
    # better full names: PL2 row with same price and most similar name
    for r in D.values():
        r['source']='Daily Official List (Equities)'
        cands=[p for p in PL if abs(p['price']-r['close'])<1e-9 and p['board']!='GROWTH BOARD']
        if cands:
            best=max(cands,key=lambda p:difflib.SequenceMatcher(None,norm(p['name']),norm(r['name'])).ratio())
            if norm(best['name']).startswith(norm(r['name'])[:6]): r['name']=best['name']
    for p in PL:
        if p['board']=='GROWTH BOARD':
            s=GROWTH[p['name']]
            D[s]=dict(symbol=s,name=p['name'],board='Growth Board',sector=GSECT[s],subsector=p['subsector'].title(),par=None,close=p['price'],
                      last_trade=None,last_trade_date='',source='Price List (Equities)')
        if p['name']=='GREIF NIGERIA PLC' and 'VANLEER' not in D:
            D['VANLEER']=dict(symbol='VANLEER',name=p['name'],board='Main Board',sector='INDUSTRIAL GOODS',subsector=p['subsector'].title(),par=None,close=p['price'],
                      last_trade=None,last_trade_date='',source='Price List (Equities); not in Daily Official List')
    if 'JAIZBANK' not in D and 'JAIZBANK' in P1:
        D['JAIZBANK']=dict(symbol='JAIZBANK',name='JAIZ BANK PLC',board='Non-Interest Finance Board',sector='FINANCIAL SERVICES',subsector='Banking',par=None,
                           close=P1['JAIZBANK']['close'],last_trade=None,last_trade_date='',source='Prices for Equity Securities Traded')
    # verification vs PRICES1
    for s,r in D.items():
        if s in P1: assert abs(P1[s]['close']-r['close'])<1e-9,(y,s)
    data[y]=D
syms=sorted(set().union(*[set(v) for v in data.values()]))
NOTES={'FBNH':'Became First HoldCo (FIRSTHOLDCO) in 2025','FIRSTHOLDCO':'Formerly FBN Holdings (FBNH)',
 'FLOURMILL':'Delisted 30 Dec 2024','GLAXOSMITH':'Delisted in 2024','ARADEL':'Listed Oct 2024',
 'TRANSPOWER':'Listed Mar 2024','VANLEER':'Greif Nigeria; appears in Price List only',
 'JULI':'Moved from ASeM to Growth Board in 2025','JAIZBANK':'Non-Interest Finance Board in 2025',
 'STERLNBANK':'Became Sterling Financial Holdings (STERLINGNG) in 2023','STERLINGNG':'Formerly Sterling Bank (STERLNBANK). 2026 jump: check for corporate action',
 'CHIPLC':'Became Consolidated Hallmark Holdings (CONHALLPLC) in 2023','CONHALLPLC':'Formerly Consolidated Hallmark Insurance (CHIPLC)',
 'ABBEYBDS':'Renamed Abbey Bank (ABBEYBANK) in 2026','ABBEYBANK':'Formerly Abbey Mortgage Bank (ABBEYBDS)',
 'UHOMREIT':'Ticker changed to UHREIT in 2026','UHREIT':'Formerly UHOMREIT',
 'WAPCO':'Lafarge Africa; likely now HBM Nigeria (HBMNG), verify','HBMNG':'Likely formerly Lafarge Africa (WAPCO), verify',
 'DEAPCAP':'Possibly now AVA Capital (AVACAP), verify','AVACAP':'Possibly formerly DEAP Capital (DEAPCAP), verify',
 'VFDGROUP':'Listed in 2023','UBN':'Delisted 2023','ARDOVA':'Delisted 2023','ZICHIS':'Listed on Growth Board in 2026','CMFC':'Listed in 2026'}
wb=Workbook(); F='Arial'
hdr_font=Font(name=F,bold=True,color='FFFFFF'); hdr_fill=PatternFill('solid',fgColor='1F4E78')
base=Font(name=F,size=10); thin=Side(style='thin',color='D9D9D9')
def header(ws,cols,widths):
    for i,(c,w) in enumerate(zip(cols,widths),1):
        cell=ws.cell(row=1,column=i,value=c); cell.font=hdr_font; cell.fill=hdr_fill
        cell.alignment=Alignment(wrap_text=True,vertical='center',horizontal='center')
        ws.column_dimensions[get_column_letter(i)].width=w
    ws.row_dimensions[1].height=32; ws.freeze_panes='C2'
# Summary
from openpyxl.formatting.rule import CellIsRule
ws=wb.active; ws.title='Year-End Prices'
cols=['Symbol','Company','Board (latest)','Sector','Sub-sector',
 'Close 30-Dec-2022 (₦)','Close 29-Dec-2023 (₦)','Close 31-Dec-2024 (₦)','Close 31-Dec-2025 (₦)','Close 06-Nov-2026 (₦)',
 '% Change 2023','% Change 2024','% Change 2025','% Change 2026 YTD','% Change 2023→2025',
 'Band 2023','Band 2024','Band 2025','Band 2026 YTD','Notes']
header(ws,cols,[13,40,22,22,28,13,13,13,13,13,10,10,10,11,11,15,15,15,15,38])
n=len(syms)+1
for i,s in enumerate(syms,2):
    latest=next(data[y][s] for y in (2026,2025,2024,2023,2022) if s in data[y])
    sector=next((data[y][s]['sector'] for y in (2026,2025,2024,2023,2022) if s in data[y] and data[y][s].get('sector')),'')
    vals=[s,latest['name'],latest['board'],tc(sector),tc(latest.get('subsector'))]
    vals+=[data[y][s]['close'] if s in data[y] else None for y,_,_ in YEARS]
    for j,v in enumerate(vals,1): ws.cell(row=i,column=j,value=v)
    for col,(p,c) in zip('KLMNO',[('F','G'),('G','H'),('H','I'),('I','J'),('G','I')]):
        ws[f'{col}{i}']=f'=IF(AND(ISNUMBER({p}{i}),ISNUMBER({c}{i}),{p}{i}<>0),{c}{i}/{p}{i}-1,"")'
    for col,pc in zip('PQRS','KLMN'):
        ws[f'{col}{i}']=(f'=IF({pc}{i}="","N/A",IF(AND({pc}{i}>0,RANK({pc}{i},{pc}$2:{pc}${n},0)<=10),"Top 10 Gainer",'
                         f'IF(AND({pc}{i}<0,RANK({pc}{i},{pc}$2:{pc}${n},1)<=10),"Top 10 Loser","Mid Performer")))')
    ws[f'T{i}']=NOTES.get(s,'')
    for j in range(1,21):
        c=ws.cell(row=i,column=j); c.font=base; c.border=Border(bottom=thin)
        if 6<=j<=10: c.number_format='#,##0.00;-#,##0.00;-'; c.font=Font(name=F,size=10,color='0000FF')
        if 11<=j<=15: c.number_format='0.0%;[Red]-0.0%;-'
        if 16<=j<=19: c.alignment=Alignment(horizontal='center')
rng=f'P2:S{n}'
ws.conditional_formatting.add(rng,CellIsRule(operator='equal',formula=['"Top 10 Gainer"'],fill=PatternFill('solid',fgColor='C6EFCE'),font=Font(name=F,color='006100')))
ws.conditional_formatting.add(rng,CellIsRule(operator='equal',formula=['"Top 10 Loser"'],fill=PatternFill('solid',fgColor='FFC7CE'),font=Font(name=F,color='9C0006')))
ws.conditional_formatting.add(rng,CellIsRule(operator='equal',formula=['"N/A"'],fill=PatternFill('solid',fgColor='EDEDED'),font=Font(name=F,color='808080')))
ws.auto_filter.ref=f'A1:T{n}'
r=n+2
ws.cell(row=r,column=1,value='Stocks with a price').font=Font(name=F,bold=True,size=10)
for col in 'FGHIJ':
    c=ws[f'{col}{r}']; c.value=f'=COUNT({col}2:{col}{n})'; c.font=Font(name=F,bold=True,size=10)
for k,lab in enumerate(['Top 10 Gainer','Top 10 Loser','Mid Performer','N/A'],1):
    ws.cell(row=r+k,column=15,value=lab).font=Font(name=F,bold=True,size=10)
    for col in 'PQRS':
        c=ws[f'{col}{r+k}']; c.value=f'=COUNTIF({col}2:{col}{n},O{r+k})'; c.font=Font(name=F,size=10); c.alignment=Alignment(horizontal='center')
ws.cell(row=r+6,column=1,value='Blue = closing prices from NGX PDFs (2026 = last Friday, 6 Nov 2026). Blank = not listed on that date. % changes and Bands are formulas; band rules on "Sources & Notes".').font=Font(name=F,italic=True,size=9)
# Per-year detail
for y,d,lab in YEARS:
    w=wb.create_sheet(f'{y} Detail')
    header(w,['Symbol','Company','Board','Sector','Sub-sector','Nominal Value (₦)','Close (₦)','Last Trade Price (₦)','Last Trade Date','Source'],[13,42,22,24,30,12,12,13,12,40])
    for i,s in enumerate(sorted(data[y]),2):
        x=data[y][s]
        vals=[s,x['name'],x['board'],tc(x.get('sector')),tc(x.get('subsector')),x.get('par'),x['close'],x.get('last_trade'),x.get('last_trade_date',''),x['source']]
        for j,v in enumerate(vals,1):
            c=w.cell(row=i,column=j,value=v); c.font=base
            if j in (6,7,8): c.number_format='#,##0.00'
# Sources
w=wb.create_sheet('Sources & Notes'); w.column_dimensions['A'].width=30; w.column_dimensions['B'].width=110
rows=[('Item','Detail'),
('Price used','"Current Market Price" in NGX Daily Official List = official closing price for the day.'),
('Dates','Last trading day of each year: Fri 30 Dec 2022, Fri 29 Dec 2023, Tue 31 Dec 2024, Wed 31 Dec 2025; 2026 uses last Friday, 6 Nov 2026 (year-to-date).'),
('Band rules','Per year, using that year\'s % change (prior year-end close → year-end close; 2026 = YTD to 6 Nov). Top 10 Gainer: ranks 1-10 by % change and change > 0. Top 10 Loser: ranks 1-10 lowest and change < 0. Mid Performer: every other stock priced at both dates. N/A: no price at start or end (new listing, delisting, ticker change). Ties at rank 10 are all included, so a band can hold more than 10.'),
('Band caveat','Many NGX stocks are thinly traded or suspended, so 0% (unchanged) is common; these fall in Mid Performer.'),
('Coverage','All equities on Main, Premium, Growth, ASeM, Non-Interest and REIT/Closed-End Fund boards. ETFs, bonds and mutual funds excluded.')]
for y,d,lab in YEARS:
    rows.append((f'Source {y} (main)',f'https://doclib.ngxgroup.com/DownloadsContent/Daily%20Official%20List%20-%20Equities%20for%20{d}.pdf'))
    rows.append((f'Source {y} (Growth Board, check)',f'https://doclib.ngxgroup.com/DownloadsContent/GAINERS%20AND%20PRICE%20LIST%20FOR%20{d}.zip'))
rows+=[('Verification','Every close was cross-checked against NGX "Prices for Equity Securities Traded" (PRICES1) where the stock traded: 0 mismatches.'),
('Spot checks','DANGCEM 478.80 / MTNN 200.00 / GTCO 57.00 at end-2024 match published figures.'),
('Caveats','Company names come from the PDFs and may be abbreviated. Ticker changes (e.g. FBNH→FIRSTHOLDCO, STERLNBANK→STERLINGNG) appear as separate rows with band N/A for the change year; see Notes column. % changes are price only (no dividends, bonus or split adjustments).'),
('Compiled','8 Nov 2026'),('Data','2026 column checked against live NGX API (TradeDate 6 Nov 2026).')]
for i,(a,b) in enumerate(rows,1):
    w.cell(row=i,column=1,value=a).font=Font(name=F,bold=(i==1 or True),size=10)
    c=w.cell(row=i,column=2,value=b); c.font=Font(name=F,size=10,bold=(i==1)); c.alignment=Alignment(wrap_text=True)
wb.save(OUT)
print('symbols',len(syms),{y:len(v) for y,v in data.items()})
