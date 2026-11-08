import pdfplumber, glob, re
EQ_SECTIONS=('PREMIUM BOARD','MAIN BOARD','GROWTH BOARD','ASEM','REAL ESTATE INVESTMENT TRUST','NON-INTEREST FINANCE BOARD')
def parse(d,S):
    f=glob.glob(f'{S}/zips/{d}/*/PRICES_LIST2.pdf')[0]; rows=[]; sec=kind=None; sector=sub=None
    with pdfplumber.open(f) as p:
        for pg in p.pages:
            for l in (pg.extract_text() or '').split('\n'):
                if l.startswith('Price List ('): kind=l; continue
                if l.startswith('PRICES FOR'): sec=l[11:].replace(' SECURITIES','').strip(); continue
                m=re.match(r'^S/N (.+) MARKET CAP\(Nm\) PRICE',l)
                if m: sub=m.group(1); continue
                m=re.match(r'^(\d+) (.+?) ([\d,]+\.\d+) ([\d,]+\.\d+) (\S+) ([\d,]+) ([\d,]+)$',l)
                if m and kind and 'Equities' in kind:
                    board=sec
                    if board=='MUTUAL FUND' : continue
                    rows.append(dict(sn=int(m.group(1)),name=m.group(2),mcap_m=float(m.group(3).replace(',','')),price=float(m.group(4).replace(',','')),board=board,subsector=sub))
                elif l.isupper() and not re.search(r'\d',l) and len(l)<40: sector=l
    return rows
