"""Build dashboard/viewer.html: a self-contained page with the latest data embedded.
Run after every refresh:  python3 scripts/build_viewer.py"""
import glob, json, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
d = root / "data"
load = lambda n: json.load(open(d / n))
prices_file = sorted(glob.glob(str(d / "prices_*.json")))[-1]
log = load("daily_log.json")
data = {
    "holdings": load("holdings.json"),
    "prices": json.load(open(prices_file)),
    "watchlist": load("watchlist.json"),
    "daily": [{k: r.get(k) for k in ("date", "value", "cost", "gain", "day_pl", "day_pl_pct")} for r in log],
    "lastNote": log[-1].get("note", ""),
}
tpl = (root / "scripts" / "viewer_template.html").read_text()
out = root / "dashboard" / "viewer.html"
out.write_text(tpl.replace("/*DATA*/null", json.dumps(data, separators=(",", ":"))))
print("wrote", out, out.stat().st_size, "bytes; prices", pathlib.Path(prices_file).name)
