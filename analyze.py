#!/usr/bin/env python3
import pandas as pd, math, os, re, csv
from collections import Counter

def wilson(k,n,z=1.96):
    if n==0: return (float('nan'),)*3
    p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d; h=(z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)))/d
    return p,max(0,c-h),min(1,c+h)

d=pd.read_csv("/mnt/user-data/outputs/rq3_merge_replay_full.csv")
print("="*64)
print("TOTAL pairs attempted:",len(d))
print("label distribution:"); print(d.label.value_counts().to_string())

ev=d[d.label.isin(["CLEAN","CONFLICT"])].copy()
print("\n"+"="*64+"\nRQ3 TEXTUAL CONFLICT RATES (evaluable = CLEAN+CONFLICT)")
summ=[]
for s in ["same","cross"]:
    g=ev[ev.stratum==s]; k=int((g.label=="CONFLICT").sum()); n=len(g)
    p,lo,hi=wilson(k,n)
    att=int((d.stratum==s).sum()); una=att-n
    print(f"  {s:5s}: {k}/{n} = {p*100:.1f}%  95% CI [{lo*100:.1f}, {hi*100:.1f}]   (attempted {att}, unavailable {una})")
    summ.append([s,k,n,round(p,4),round(lo,4),round(hi,4),att,una])
# pooled
k=int((ev.label=="CONFLICT").sum()); n=len(ev); p,lo,hi=wilson(k,n)
print(f"  POOL : {k}/{n} = {p*100:.1f}%  95% CI [{lo*100:.1f}, {hi*100:.1f}]")
summ.append(["__pool__",k,n,round(p,4),round(lo,4),round(hi,4),len(d),len(d)-n])
pd.DataFrame(summ,columns=["stratum","conflicts","evaluable","rate","ci_low","ci_high","attempted","unavailable"]).to_csv("/mnt/user-data/outputs/rq3_rates_full.csv",index=False)

# ---------- TAXONOMY ----------
MANIFEST_BASE={"package.json","package-lock.json","yarn.lock","pnpm-lock.yaml","npm-shrinkwrap.json",
 "cargo.toml","cargo.lock","go.mod","go.sum","poetry.lock","pipfile","pipfile.lock","uv.lock",
 "gemfile","gemfile.lock","pom.xml","composer.json","composer.lock","pubspec.yaml","pubspec.lock",
 "mix.exs","mix.lock","podfile","podfile.lock","bun.lock","bun.lockb","packages.lock.json","gradle.lockfile"}
def is_manifest(b,p):
    if b in MANIFEST_BASE: return True
    if b.startswith("requirements") and b.endswith(".txt"): return True
    if b.endswith(".csproj") or b.endswith(".gemspec"): return True
    if re.search(r"build\.gradle(\.kts)?$",b): return True
    return False
CONFIG_BASE={"dockerfile","makefile","tsconfig.json",".gitignore",".dockerignore",".npmrc",
 ".eslintrc",".eslintrc.js",".eslintrc.json",".prettierrc",".editorconfig","vite.config.js",
 "vite.config.ts","webpack.config.js","rollup.config.js","next.config.js","next.config.mjs",
 "jest.config.js","babel.config.js",".env",".env.example"}
SRC_EXT={".py",".js",".jsx",".mjs",".cjs",".ts",".tsx",".go",".rs",".java",".kt",".kts",".c",
 ".cc",".cpp",".cxx",".h",".hpp",".rb",".php",".cs",".swift",".scala",".m",".mm",".dart",".ex",
 ".exs",".lua",".r",".jl",".vue",".svelte",".sh",".bash",".ps1",".sql",".pl",".clj",".hs",".elm"}
DOC_EXT={".md",".mdx",".rst",".txt",".adoc"}
CFG_EXT={".yml",".yaml",".json",".toml",".ini",".cfg",".conf",".properties",".xml",".env"}
def categorize(path):
    b=path.rsplit("/",1)[-1].lower()
    ext="."+b.rsplit(".",1)[-1] if "." in b else ""
    if is_manifest(b,path): return "Manifest & Lockfile"
    if b in CONFIG_BASE or "/.github/" in "/"+path.lower() or path.lower().startswith(".github/"): return "Config & CI"
    if ext in SRC_EXT: return "Source Code"
    if ext in DOC_EXT or b in ("license","changelog","readme"): return "Docs & Text"
    if ext in CFG_EXT: return "Config & CI"
    return "Other / Assets"

conf=d[d.label=="CONFLICT"].copy()
file_cat=Counter(); pairs_with_cat=Counter(); type_ctr=Counter()
n_conf_pairs=len(conf); total_files=0
for _,r in conf.iterrows():
    files=str(r.files).split("|") if pd.notna(r.files) and r.files else []
    cats=set()
    for fp in files:
        if not fp: continue
        c=categorize(fp); file_cat[c]+=1; cats.add(c); total_files+=1
    for c in cats: pairs_with_cat[c]+=1
    for t in (str(r.types).split("|") if pd.notna(r.types) and r.types else []):
        if t: type_ctr[t]+=1

print("\n"+"="*64+"\nCONFLICT TAXONOMY")
print(f"conflicting pairs: {n_conf_pairs} | total conflicted files: {total_files}")
print("\nA) By conflicted FILE (each conflicted file assigned one category):")
tax=[]
for c,n in file_cat.most_common():
    print(f"   {c:22s} {n:4d}  ({n/total_files*100:.1f}%)")
    tax.append([c,n,round(n/total_files*100,1)])
pd.DataFrame(tax,columns=["category","conflicted_files","pct_of_files"]).to_csv("/mnt/user-data/outputs/rq3_taxonomy_full.csv",index=False)

print("\nB) Share of conflicting PAIRS that touch each category (a pair can touch several):")
for c,n in pairs_with_cat.most_common():
    print(f"   {c:22s} {n:4d}/{n_conf_pairs}  ({n/n_conf_pairs*100:.1f}% of conflicting pairs)")

print("\nC) git conflict TYPE (from merge-tree messages):")
tt=sum(type_ctr.values())
for t,n in type_ctr.most_common():
    print(f"   {t:18s} {n:4d}  ({n/tt*100:.1f}%)")

print("\nsaved: rq3_rates_full.csv, rq3_taxonomy_full.csv")
