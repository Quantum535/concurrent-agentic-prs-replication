import json, subprocess, tempfile, shutil, csv
DN=subprocess.DEVNULL
RES="/mnt/user-data/outputs/rq3_merge_replay_full.csv"
miss=json.load(open("/home/claude/cands_missing.json"))
def run(cmd,cwd,t):
    try: return subprocess.run(cmd,cwd=cwd,stdin=DN,capture_output=True,text=True,timeout=t)
    except Exception: return None
def parse_conflict(s):
    lines=s.split("\n"); files=set(); types=[]
    for ln in lines[1:]:
        if ln=="": break
        if "\t" in ln: files.add(ln.split("\t",1)[1])
    for ln in lines:
        if ln.startswith("CONFLICT ("): types.append(ln[10:].split(")",1)[0])
    return files,types
def label(fn,a,b):
    d=tempfile.mkdtemp()
    try:
        run(["git","init","-q"],d,20); run(["git","remote","add","origin","https://github.com/%s.git"%fn],d,20)
        f=run(["git","-c","protocol.version=2","fetch","-q","--no-tags","--depth","80","origin","refs/pull/%s/head:pra"%a,"refs/pull/%s/head:prb"%b],d,90)
        if f is None or f.returncode!=0: return ("UNAVAIL_fetch",0,"","")
        mb=run(["git","merge-base","pra","prb"],d,15)
        if mb is None or not mb.stdout.strip(): return ("UNAVAIL_nobase",0,"","")
        mt=run(["git","merge-tree","--write-tree","pra","prb"],d,60)
        if mt is None: return ("UNAVAIL_timeout",0,"","")
        if mt.returncode==0: return ("CLEAN",0,"","")
        if mt.returncode==1:
            files,types=parse_conflict(mt.stdout); return ("CONFLICT",len(files),"|".join(sorted(files)),"|".join(types))
        return ("ERR%d"%mt.returncode,0,"","")
    finally: shutil.rmtree(d,ignore_errors=True)
for c in miss:
    st,fn,a,b,aga,agb=c
    lab,nf,files,types=label(fn,a,b)
    with open(RES,"a",newline="") as f:
        csv.writer(f).writerow([st,fn,a,b,aga,agb,lab,nf,files,types])
    print(st,fn,a,b,"->",lab,nf)
print("done")
