import json, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import eval as ev
import config
import capture_audit as ca
judge = ca.make_judge(config.require("jev_api_key", "jev_base_url", "jev_model"))
rids = sorted(p.stem for p in ev.ISO.glob("R*.md"))
def run(rid):
    _, turns = ev.turns_of(rid)
    us = [u for t in turns for u in ev.units_of(t)]
    d = ev.parse(ev.repair_json((ev.R / "write-01" / "qcmp-raw" / f"{rid}-gold.txt").read_text())[0]) or {}
    lab = {x.get("id"): x.get("label") for x in d.get("labels", []) if isinstance(x, dict)}
    gold = [lab.get(f"u{i}") for i in range(len(us))]
    conv = (ev.ISO / f"{rid}.md").read_text()[-8000:]
    return rid, us, gold, ev.flags(judge, conv, us, ev.CUR), ev.flags(judge, conv, us, ev.NEW)
with ThreadPoolExecutor(12) as pool:
    out = list(pool.map(run, rids))
for rid, us, gold, c, n in out:
    for u, g, a, b in zip(us, gold, c, n):
        if g == "record" and a and not b:
            print("NEWMISS", rid, u)
        if g == "record" and not a and b:
            print("NEWHIT", rid, u)
