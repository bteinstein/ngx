import pdfplumber, re
COLS=[('name',90,190),('par',190,236),('open',236,305),('close',305,368),
      ('mkt',368,430),('exdiv',430,490),('bdprice',490,528),('bddate',528,582),('qty',582,620)]
BOARDS={'EQTY':'Main Board','PREMIUM':'Premium Board','ASeM':'ASeM','REITCEF':'REIT & Closed-End Fund','GROWTH':'Growth Board'}
def col(x):
    for n,a,b in COLS:
        if a<=x<b: return n
def num(s):
    if not s: return None
    try: return float(s.replace(',',''))
    except ValueError: return None
def parse(path):
    rows=[]; board=sector=sub=None
    with pdfplumber.open(path) as pdf:
        for pg in pdf.pages:
            lines={}
            for w in pg.extract_words(): lines.setdefault(round(w['top']),[]).append(w)
            cur=None
            for top in sorted(lines):
                L=sorted(lines[top],key=lambda w:w['x0']); txt=' '.join(w['text'] for w in L)
                m=re.match(r'^(\w+) - ',txt)
                if m and m.group(1) in BOARDS: board=BOARDS[m.group(1)]; cur=None; continue
                f=L[0]
                if f['x0']<90 and len(L)>1 and L[1]['x0']>=90 and re.fullmatch(r'[A-Z0-9][A-Z0-9&.\-]*',f['text']):
                    r={'board':board,'sector':sector,'subsector':sub,'symbol':f['text']}
                    for w in L[1:]:
                        if w['x0']>=620: continue
                        c=col((w['x0']+w['x1'])/2)
                        if c: r[c]=(r.get(c,'')+' '+w['text']).strip()
                    if num(r.get('par')) is not None and num(r.get('mkt')) is not None:
                        rows.append(r); cur=r; continue
                if cur and all(90<=w['x0']<190 for w in L):
                    cur['name']=(cur.get('name','')+' '+txt).strip(); continue
                cur=None
                if f['x0']<90 and txt.isupper() and not re.search(r'\d',txt): sector=txt
                elif 60<=f['x0']<90 and 'Ex - Business' not in txt and not re.search(r'\d',txt) and not txt.startswith(('Public','Quotation','Symbol')): sub=txt
    out={}
    for r in rows:
        if r['symbol'] in out: continue
        d=r.get('bddate',''); dm=re.search(r'\d\d/\d\d/\d\d',d)
        out[r['symbol']]=dict(symbol=r['symbol'],name=r.get('name',''),board=r['board'],sector=r['sector'],subsector=r['subsector'],
            par=num(r['par']),close=num(r['mkt']),last_trade=num(r.get('bdprice')),last_trade_date=dm.group(0) if dm else '')
    return list(out.values())
