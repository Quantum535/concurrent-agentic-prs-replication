#!/usr/bin/env python3
"""Large-scale merge replay over the 747-pair stratified sample.
Real 3-way git merge-tree per pair. Resumable, time-boxed, threaded.
On CONFLICT, records the conflicted file paths and git's conflict TYPES."""
import json, subprocess, tempfile, shutil, time, csv, os, threading, queue
t0=time.time(); BUDGET=140; DN=subprocess.DEVNULL; WORKERS=8
RES="/mnt/user-data/outputs/rq3_merge_replay_full.csv"
HEADER=["stratum","repo","prA","prB","agentA","agentB","label","n_files","files","types"]
cands=json.load(open("/home/claude/cands_full.json"))

if not os.path.exists(RES):
    with open(RES,"w",newline="") as f: csv.writer(f).writerow(HEADER)
done=set()
with open(RES) as f:
    for r in csv.DictReader(f): done.add((r["stratum"],r["repo"],str(r["prA"]),str(r["prB"])))
todo=[c for c in cands if (c[0],c[1],str(c[2]),str(c[3])) not in done]
q=queue.Queue()
for c in todo: q.put(c)
wlock=threading.Lock(); counters={"n":0}
print("to process this batch: %d (already done: %d)"%(len(todo),len(done)))

def run(cmd,cwd,t):
    try: return subprocess.run(cmd,cwd=cwd,stdin=DN,capture_output=True,text=True,timeout=t)
    except Exception: return None

def parse_conflict(stdout):
    lines=stdout.split("\n"); files=set(); types=[]
    for ln in lines[1:]:
        if ln=="": break
        if "\t" in ln: files.add(ln.split("\t",1)[1])
    for ln in lines:
        if ln.startswith("CONFLICT ("): types.append(ln[10:].split(")",1)[0])
    return files,types

def label(fn,a,b):
    d=tempfile.mkdtemp()
    try:
        run(["git","init","-q"],d,20)
        run(["git","remote","add","origin","https://github.com/%s.git"%fn],d,20)
        f=run(["git","-c","protocol.version=2","fetch","-q","--no-tags","--depth","80","origin",
               "refs/pull/%s/head:pra"%a,"refs/pull/%s/head:prb"%b],d,90)
        if f is None or f.returncode!=0: return ("UNAVAIL_fetch",0,"","")
        mb=run(["git","merge-base","pra","prb"],d,15)
        if mb is None or not mb.stdout.strip():
            run(["git","-c","protocol.version=2","fetch","-q","--no-tags","--depth","600","origin",
                 "refs/pull/%s/head:pra"%a,"refs/pull/%s/head:prb"%b],d,150)
            mb=run(["git","merge-base","pra","prb"],d,15)
            if mb is None or not mb.stdout.strip(): return ("UNAVAIL_nobase",0,"","")
        mt=run(["git","merge-tree","--write-tree","pra","prb"],d,60)
        if mt is None: return ("UNAVAIL_timeout",0,"","")
        if mt.returncode==0: return ("CLEAN",0,"","")
        if mt.returncode==1:
            files,types=parse_conflict(mt.stdout)
            return ("CONFLICT",len(files),"|".join(sorted(files)),"|".join(types))
        return ("ERR%d"%mt.returncode,0,"","")
    finally: shutil.rmtree(d,ignore_errors=True)

def worker():
    while True:
        if time.time()-t0>BUDGET: return
        try: c=q.get_nowait()
        except queue.Empty: return
        st,fn,a,b,aga,agb=c
        lab,nf,files,types=label(fn,a,b)
        with wlock:
            with open(RES,"a",newline="") as f:
                csv.writer(f).writerow([st,fn,a,b,aga,agb,lab,nf,files,types])
            counters["n"]+=1
            if counters["n"]%25==0: print("  ...%d done (%ds)"%(counters["n"],time.time()-t0))
        q.task_done()

ths=[threading.Thread(target=worker) for _ in range(WORKERS)]
for t in ths: t.start()
for t in ths: t.join()
print("BATCH done=%d  remaining=%d  elapsed=%ds"%(counters["n"],q.qsize(),time.time()-t0))
