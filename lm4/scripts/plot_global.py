import csv, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
rows=[(int(r[0]),float(r[2]),float(r[3]),float(r[4])) for r in csv.reader(open('/tmp/global.csv'))]
rows.sort()
x=list(range(1,len(rows)+1))
T=[r[1] for r in rows]; W=[r[2] for r in rows]; S=[r[3] for r in rows]
fig,ax=plt.subplots(1,3,figsize=(14,4.3))
for a,(d,ttl,u) in zip(ax,[(T,"Deep soil T @ 8.75 m","K"),(W,"Column soil water","kg m$^{-2}$"),(S,"Snow water","kg m$^{-2}$")]):
    a.plot(x,d,"-",color="k",lw=2)
    a.set_title(f"{ttl} ({u})"); a.set_xlabel("cumulative spin-up year"); a.grid(alpha=.3)
fig.suptitle(f"LM4 static-veg spin-up — GLOBAL mean (through {len(rows)} yr)",fontweight="bold")
fig.tight_layout(rect=[0,0,1,0.95])
fig.savefig("/Volumes/data01/MOF_LSM_project/figures/lm4_global_spinup.png",dpi=150,bbox_inches="tight")
print("saved, n=",len(rows),"final deepT/water/snow:",round(T[-1],2),round(W[-1],0),round(S[-1],1))
