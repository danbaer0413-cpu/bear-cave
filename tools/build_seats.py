"""Seat files for the app: House (called.csv + newest night file for leaders), Senate (holdovers + 2026 races)."""
import glob, json, os, sys
import pandas as pd
repo, app = sys.argv[1], sys.argv[2]
called = pd.read_csv(f"{repo}/data/house/called.csv", dtype=str)
called["district"] = called.district.str.lstrip("0").replace("", "1")
nights = sorted(glob.glob(f"{repo}/data/night/house_*.csv"), key=os.path.getmtime)
live = pd.concat([pd.read_csv(f, dtype=str).assign(_f=os.path.basename(f)) for f in nights]) if nights else pd.DataFrame()
live["district"] = live.district.str.lstrip("0").replace("", "1")
live = live.groupby(["state", "district"]).tail(1).set_index(["state", "district"])
c = pd.read_csv(f"{app}/contests.csv", dtype=str)
h24 = c[(c.year == "2024") & (c.office == "U.S. House") & (c.election_type == "general")].copy()
h24["district"] = h24.district.replace("AT-LARGE", "1")
w24 = dict(zip(zip(h24.state_po, h24.district), h24.winner_party))
# seat list = every district NBC lists (called + live) ; fall back to 2024 districts
keys = set(zip(called.state, called.district)) | set(live.index)
rows = []
for st, d in sorted(keys, key=lambda k: (k[0], int(k[1]) if k[1].isdigit() else 0)):
    note = ""
    cl = called[(called.state == st) & (called.district == d)]
    lv = live.loc[(st, d)] if (st, d) in live.index else None
    if len(cl):
        party, status = ("DEMOCRAT" if cl.winner.iloc[0] == "D" else "REPUBLICAN"), "called"
        lead, margin, pin = "", None, None
    else:
        dp = float(lv.dem_pct) if lv is not None and str(lv.dem_pct) not in ("", "nan") else 0.0
        rp = float(lv.rep_pct) if lv is not None and str(lv.rep_pct) not in ("", "nan") else 0.0
        party = "DEMOCRAT" if dp >= rp else "REPUBLICAN"; status = "leading"
        lead = (lv.dem_name if party == "DEMOCRAT" else lv.rep_name) if lv is not None else ""
        margin = round(dp - rp, 1); pin = lv.pct_in if lv is not None else None
        # top-two states: only one name listed means both finalists are from that party, so the D-minus-R gap is meaningless
        one = lv is not None and (str(lv.dem_pct) in ("", "nan")) != (str(lv.rep_pct) in ("", "nan"))
        if st in ("CA", "WA") and one:
            margin = None; note = "both finalists " + ("Democrats" if party == "DEMOCRAT" else "Republicans")
    prev = w24.get((st, d), "")
    rows.append(dict(key=f"{st}-{d}", state_po=st, district=d, party=party, status=status, leader=lead if isinstance(lead, str) else "",
                     margin=margin, pct_in=pin, note=note, party_2024=prev, flip=bool(prev) and prev in ("DEMOCRAT", "REPUBLICAN") and prev != party))
h = pd.DataFrame(rows)
h.to_csv(f"{app}/house_seats.csv", index=False)
print("house", len(h), h.groupby(["party", "status"]).size().to_dict(), "flips vs 2024 district:", int(h.flip.sum()))
# Senate: holdovers from config, 2026 races from contests + senate calls
cfg = json.load(open(f"{repo}/config/senate_seats.json"))
s26 = c[(c.year == "2026") & (c.office == "U.S. Senate")].copy()
uncalled = {"MS", "AK"}
srows = [dict(key=f"hold-D-{i}", state_po="", seat="not up in 2026", party="DEMOCRAT", status="holdover", candidate="", margin=None, pct_in=None) for i in range(cfg["holdover_D"])]
srows += [dict(key=f"hold-R-{i}", state_po="", seat="not up in 2026", party="REPUBLICAN", status="holdover", candidate="", margin=None, pct_in=None) for i in range(cfg["holdover_R"])]
for _, r in s26.iterrows():
    p = r.winner_party if r.winner_party in ("DEMOCRAT", "REPUBLICAN") else "INDEPENDENT"
    srows.append(dict(key=f"{r.state_po}-{r.election_type}", state_po=r.state_po, seat=("special" if "special" in r.election_type else "regular"), party=p,
                      status="leading" if r.state_po in uncalled else "called", candidate=r.winner, margin=r.margin, pct_in=None))
s = pd.DataFrame(srows)
s.to_csv(f"{app}/senate_seats.csv", index=False)
print("senate", len(s), s.groupby(["party", "status"]).size().to_dict())
