"""Needle files for the app from the needle repo: current state of every race + the election-night history."""
import json, sys, pandas as pd
repo, out = sys.argv[1], sys.argv[2]
d = json.load(open(f"{repo}/data/latest.json"))
names = pd.read_csv(f"{repo}/config/candidates.csv").set_index("id")
rows = []
for rid, r in d["races"].items():
    s = r.get("summary") or {}
    m = r.get("meta") or {}
    rows.append(dict(race=rid, state=rid.split("-")[0], office=("Senate" if "senate" in rid else "Governor"), dem=names.dem.get(rid, "Dem"), rep=names.rep.get(rid, "GOP"),
                     pct_in=round(s.get("pct_in") or 0, 1), median=round(s.get("median") or 0, 2), p10=round(s.get("p10") or 0, 2), p90=round(s.get("p90") or 0, 2),
                     win_prob=s.get("win_prob"), as_of=r.get("as_of") or d.get("updated")))
pd.DataFrame(rows).sort_values("race").to_csv(f"{out}/needle_now.csv", index=False)
lg = pd.read_csv(f"{repo}/data/needle_log.csv")
lg = lg[lg.timestamp >= "2026-11-03T22:00"]
lg.to_csv(f"{out}/needle_history.csv", index=False)
c = d.get("control", {})
cr = []
for ch, v in c.items():
    if isinstance(v, dict) and "dist" in v:
        cr.append(dict(chamber=ch, races=v.get("n"), expected_dem_wins=v.get("expected_dem_wins"), p_dem_majority=v.get("p_dem_majority"), as_of=d.get("updated")))
pd.DataFrame(cr).to_csv(f"{out}/needle_control.csv", index=False)
print(len(rows), "races;", len(lg), "history rows;", d.get("updated"))
