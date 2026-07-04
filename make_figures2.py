#!/usr/bin/env python3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

INDIGO="#4B48F8"; MAGENTA="#DC267F"; AMBER="#F0A202"; NAVY="#06122A"; GREY="#8A93A6"
plt.rcParams.update({"font.size":9,"axes.spines.top":False,"axes.spines.right":False})

# ---------- FIGURE 3: real RQ3 conflict rates ----------
labels=["Intra-agent\n(same agent)","Cross-agent\n(different agents)"]
p=np.array([0.198,0.417]); lo=np.array([0.168,0.331]); hi=np.array([0.232,0.509])
ks=["119/601","48/115"]
yerr=np.vstack([p-lo,hi-p])
fig,ax=plt.subplots(figsize=(5.0,3.6))
bars=ax.bar(labels,p*100,yerr=yerr*100,capsize=7,color=[INDIGO,MAGENTA],
            edgecolor="white",width=0.62,error_kw=dict(ecolor=NAVY,lw=1.4))
for i,b in enumerate(bars):
    ax.text(b.get_x()+b.get_width()/2,hi[i]*100+2.2,f"{p[i]*100:.1f}%",ha="center",
            fontweight="bold",fontsize=11)
    ax.text(b.get_x()+b.get_width()/2,4,ks[i],ha="center",color="white",fontsize=8.5,fontweight="bold")
ax.set_ylabel("Textual merge-conflict rate (%)")
ax.set_ylim(0,62)
ax.set_title("RQ3: Conflict rate among co-active agentic PR pairs\n(real 3-way git merge-tree replay; 95% Wilson CI, N=716)",fontsize=9.5)
plt.tight_layout(); plt.savefig("/mnt/user-data/outputs/figure3_rq3_REAL.png",dpi=160,bbox_inches="tight")
print("wrote figure3_rq3_REAL.png")

# ---------- FIGURE 4: real taxonomy ----------
fig,(ax1,ax2)=plt.subplots(1,2,figsize=(9.6,3.7))

# (a) conflict TYPE
types=["content","modify/delete","add/add","other"]
tv=np.array([57.6,26.8,15.1,0.5])
cols=[INDIGO,MAGENTA,AMBER,GREY]
y=np.arange(len(types))[::-1]
ax1.barh(y,tv,color=cols,edgecolor="white",height=0.66)
for yi,v in zip(y,tv): ax1.text(v+1,yi,f"{v:.1f}%",va="center",fontsize=9,fontweight="bold")
ax1.set_yticks(y); ax1.set_yticklabels(types)
ax1.set_xlim(0,68); ax1.set_xlabel("% of conflict signals")
ax1.set_title("(a) Conflict type (from git merge-tree)",fontsize=9.5)

# (b) conflicted-FILE category
cats=["Source\nCode","Other /\nAssets","Config\n& CI","Manifest &\nLockfile","Docs &\nText"]
cv=np.array([84.4,5.1,4.0,3.9,2.6])
yc=np.arange(len(cats))[::-1]
ax2.barh(yc,cv,color=NAVY,edgecolor="white",height=0.66)
for yi,v in zip(yc,cv): ax2.text(v+1.4,yi,f"{v:.1f}%",va="center",fontsize=9,fontweight="bold")
ax2.set_yticks(yc); ax2.set_yticklabels(cats)
ax2.set_xlim(0,98); ax2.set_xlabel("% of conflicted files")
ax2.set_title("(b) Conflicted file category",fontsize=9.5)

fig.suptitle("RQ3 taxonomy: what agentic PRs actually collide on (167 conflicting pairs, 1,646 files)",
             fontsize=10,y=1.03)
plt.tight_layout(); plt.savefig("/mnt/user-data/outputs/figure4_taxonomy_REAL.png",dpi=160,bbox_inches="tight")
print("wrote figure4_taxonomy_REAL.png")
