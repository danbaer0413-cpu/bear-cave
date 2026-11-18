"""Needle files for the app from the needle repo: current state of every race + the election-night history."""
import json, sys, pandas as pd
repo, out = sys.argv[1], sys.argv[2]
d = json.load(open(f"{repo}/data/latest.json"))
names = pd.read_csv(f"{repo}/config/candidates.csv").set_index("id")
rows = []
for rid, r in d["races"].items():
    s = r.get("summary") or {}
    m = r.get("meta") or {}
    rows.append(dict(race=rid, state=rid.split("-")[0], office=("Senate" if "senate" in rid else f"House {rid.rsplit('-', 1)[1]} runoff (Dec 12)" if "-house-" in rid else "Governor"), dem=names.dem.get(rid, "Dem"), rep=names.rep.get(rid, "GOP"),
                     pct_in=round(s.get("pct_in") or 0, 1), median=round(s.get("median") or 0, 2), p10=round(s.get("p10") or 0, 2), p90=round(s.get("p90") or 0, 2),
                     win_prob=s.get("win_prob"), as_of=r.get("as_of") or d.get("updated")))
# a called race is decided: the model's leftover count uncertainty should not show as a live chance
import os
_sc = f"{repo}/data/senate_called.csv"
_called = dict(pd.read_csv(_sc, dtype=str).iloc[:, :2].values) if os.path.exists(_sc) else {}
for r_ in rows:
    if r_["race"] in _called: r_["win_prob"] = 1.0 if _called[r_["race"]] == "D" else 0.0
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
# ---- forecast check: keep the locked Nov 2 forecast, refresh the result side from the latest count
import os
fcp = f"{out}/forecast_2026.csv"
if os.path.exists(fcp):
    fc = pd.read_csv(fcp); now = pd.DataFrame(rows).set_index("race")
    called = set()
    sc = f"{repo}/data/senate_called.csv"
    if os.path.exists(sc): called = set(pd.read_csv(sc, dtype=str).iloc[:, 0])
    for i, r in fc.iterrows():
        if r.race not in now.index: continue
        n = now.loc[r.race]
        fc.loc[i, "result_margin"] = round(float(n["median"]), 1); fc.loc[i, "pct_in"] = n.pct_in
        fc.loc[i, "status"] = ("called" if r.race in called else "ranked choice count Nov 18" if r.race.startswith("AK-") else "final count" if n.pct_in >= 99.5 else "near final")
    fc.to_csv(fcp, index=False); print("forecast check refreshed")
