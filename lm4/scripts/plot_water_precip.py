import csv, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
g=[(int(r[0]),float(r[3])) for r in csv.reader(open('/tmp/global.csv'))]; g.sort()
water=[r[1] for r in g]; x=list(range(1,len(g)+1))
p={int(r[0]):float(r[1]) for r in csv.reader(open('/tmp/gswp3_precip_annual.csv')) if not r[0].startswith('year')}
pvals=[p[y] for y in sorted(p)]   # 1981..2010 (30)
prec=[pvals[min((i%29)+1,len(pvals)-1)] for i in range(len(g))]  # tile: cycle pos -> forcing yr
fig,ax=plt.subplots(figsize=(13,4.5))
ax.plot(x,water,"k-",lw=1.5)
ax.set_ylabel("Global column soil water (kg m$^{-2}$)"); ax.set_xlabel("cumulative spin-up year")
ax2=ax.twinx(); ax2.plot(x,prec,"-",color="tab:blue",lw=1,alpha=.65)
ax2.set_ylabel("GSWP3 precip (mm/day, cycled)",color="tab:blue"); ax2.tick_params(axis='y',colors='tab:blue')
ax.set_title("Global column soil water (black) vs GSWP3 precip (blue, 1981-2010 cycled)",fontsize=11)
fig.tight_layout(); fig.savefig("/Volumes/data01/MOF_LSM_project/figures/lm4_water_vs_precip.png",dpi=140,bbox_inches="tight")
print("precip range:",round(min(pvals),3),"-",round(max(pvals),3),"mm/day; saved")
