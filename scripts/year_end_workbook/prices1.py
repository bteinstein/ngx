import pdfplumber, glob, re
def num(s):
    return None if s in ('-','') else float(s.replace(',',''))
def parse(d, S):
    f=glob.glob(f'{S}/zips/{d}/*/PRICES1.pdf')[0]; out={}; section=None
    with pdfplumber.open(f) as p:
        for pg in p.pages:
            for l in (pg.extract_text() or '').split('\n'):
                if l.startswith('PRICES FOR'): section=l
                m=re.match(r'^(\d+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+)$',l)
                if m:
                    g=m.groups()
                    out.setdefault(g[1],dict(symbol=g[1],pclose=num(g[2]),close=num(g[9]),trades=g[12],volume=g[13],section=section))
    return out
