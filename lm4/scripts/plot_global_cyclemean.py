import csv, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
r=[(int(x[0]),float(x[2]),float(x[3]),float(x[4])) for x in csv.reader(open('/tmp/global.csv'))]; r.sort()
T=np.array([v[1] for v in r]); W=np.array([v[2] for v in r]); S=np.array([v[3] for v in r])
n=len(r); cyc=29  # 각 cycle = 29 연간점
# cycle별 평균 (마지막 불완전 그룹 포함)
def cmean(a): 
    out=[]; 
    for i in range(0,n,cyc): out.append(a[i:i+cyc].mean())
    return np.array(out)
Tc,Wc,Sc=cmean(T),cmean(W),cmean(S)
xc=[(i+0.5)*30 for i in range(len(Tc))]  # cycle 중심 (모델연수)
fig,ax=plt.subplots(1,3,figsize=(14,4.3))
for a,(dc,dj,ttl,u) in zip(ax,[(Tc,T,"Deep soil T @ 8.75 m","K"),(Wc,W,"Column soil water","kg m$^{-2}$"),(Sc,S,"Snow water","kg m$^{-2}$")]):
    a.plot(range(1,n+1),dj,"-",color="0.75",lw=0.7,label="Jan-1 (annual)")  # 옅은 원본
    a.plot(xc,dc,"o-",color="k",lw=2,ms=5,label="cycle mean (30yr)")
    a.set_title(f"{ttl} ({u})"); a.set_xlabel("cumulative spin-up year"); a.grid(alpha=.3)
ax[0].legend(fontsize=8)
fig.suptitle("LM4 static-veg spin-up — GLOBAL (cycle-mean, smooth convergence)",fontweight="bold")
fig.tight_layout(rect=[0,0,1,0.95])
fig.savefig("/Volumes/data01/MOF_LSM_project/figures/lm4_global_cyclemean.png",dpi=150,bbox_inches="tight")
print("cycle means:",len(Tc),"| final cycle: T=%.2f W=%.0f S=%.1f"%(Tc[-1],Wc[-1],Sc[-1]))
print("last 3 cycle dW:",[round(Wc[i]-Wc[i-1],1) for i in range(len(Wc)-3,len(Wc))])
