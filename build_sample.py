#!/usr/bin/env python3
"""Build the stratified co-active-pair sample for the large-scale merge replay (RQ3).
One pair per distinct repository, per stratum. Cross-agent is capped by reality
(~122 repos have any cross-agent co-activity), so we take ALL available cross repos
and a seeded random 625 for intra. Outputs /home/claude/rq3_sample_full.csv + cands.json."""
import pandas as pd, numpy as np, json, csv

U="/mnt/user-data/uploads/"
df=pd.read_parquet(U+"pull_request.parquet")
repo=pd.read_parquet(U+"repository.parquet")
id2name=repo.set_index("id")["full_name"].to_dict()

for c in ("created_at","closed_at","merged_at"):
    df[c]=pd.to_datetime(df[c],errors="coerce",utc=True)
gmax=pd.concat([df["closed_at"],df["merged_at"],df["created_at"]]).max()
df["start"]=df["created_at"]
df["end"]=df["closed_at"].fillna(df["merged_at"]).fillna(gmax)
df=df.dropna(subset=["start"]).copy()
df["end"]=df["end"].fillna(gmax)
df=df[["repo_id","number","agent","start","end"]]

def first_overlap(rows, want_cross):
    """Sweep PRs sorted by start; return first overlapping pair matching the
    intra/cross requirement, or None. rows: list of (start,end,agent,number)."""
    rows=sorted(rows,key=lambda r:r[0])
    active=[]  # (end,agent,number)
    for s,e,ag,num in rows:
        active=[a for a in active if a[0]>=s]   # keep still-open
        for ae,aag,anum in active:
            if want_cross and aag!=ag:   return (anum,num,aag,ag)
            if (not want_cross) and aag==ag: return (anum,num,aag,ag)
        active.append((e,ag,num))
    return None

intra_rows=[]; cross_rows=[]
n_repos_intra=0; n_repos_cross=0
for rid,g in df.groupby("repo_id"):
    if len(g)<2: continue
    fn=id2name.get(rid)
    if not fn: continue
    recs=list(zip(g["start"],g["end"],g["agent"],g["number"]))
    # intra: any repo can have one
    pi=first_overlap(recs,False)
    if pi:
        n_repos_intra+=1
        intra_rows.append(("same",fn,pi[0],pi[1],pi[2],pi[3]))
    # cross: only if >=2 distinct agents present
    if g["agent"].nunique()>=2:
        pc=first_overlap(recs,True)
        if pc:
            n_repos_cross+=1
            cross_rows.append(("cross",fn,pc[0],pc[1],pc[2],pc[3]))

print(f"repos with an intra-agent co-active pair: {n_repos_intra}")
print(f"repos with a cross-agent co-active pair : {n_repos_cross}")

rng=np.random.default_rng(42)
# take ALL cross (reality-capped), seeded 625 intra
if len(intra_rows)>625:
    idx=rng.choice(len(intra_rows),625,replace=False)
    intra_sel=[intra_rows[i] for i in sorted(idx)]
else:
    intra_sel=intra_rows
cross_sel=cross_rows

sample=cross_sel+intra_sel
with open("/home/claude/rq3_sample_full.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["stratum","repo","prA","prB","agentA","agentB"])
    w.writerows(sample)
json.dump([list(r) for r in sample],open("/home/claude/cands_full.json","w"))

print(f"\nSAMPLE BUILT: intra={len(intra_sel)}  cross={len(cross_sel)}  total={len(sample)}")
print("saved /home/claude/rq3_sample_full.csv and cands_full.json")
