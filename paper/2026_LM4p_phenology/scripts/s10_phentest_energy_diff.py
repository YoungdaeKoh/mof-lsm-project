# CTRL(base) vs DL13/12(dayl_d) 2010 land_month: surface energy & temperature response, land-area weighted
import netCDF4 as nc, numpy as np
R="/Volumes/data02/LM4P/cases/phentest_2010"
def load(case):
    out={}
    for t in range(1,7):
        f=nc.Dataset(f"{R}/{case}/20100101.land_month.tile{t}.nc")
        g=nc.Dataset(f"{R}/{case}/20100101.grid_spec.tile{t}.nc")
        gi=f["grid_index"][:].astype(int)
        if t==1 and case=="base": print("grid_index attrs:",f["grid_index"].ncattrs(), gi.min(), gi.max())
        area=g["area"][:].ravel(); lm=g["land_mask"][:].ravel()
        d={"lat":f["geolat_t"][:],"w":area[gi]*lm[gi]}
        for v in ["Tgrnd","vegn_T","t_ref","sens","shflx","evap_land","grnd_flux","lwdn","lai","snow_frac"]:
            d[v]=np.ma.filled(f[v][:].astype(float),np.nan)
        d["swdn"]=np.ma.filled(f["swdn_dir"][:].astype(float),np.nan).sum(1)+np.ma.filled(f["swdn_dif"][:].astype(float),np.nan).sum(1)
        d["swup"]=np.ma.filled(f["swup_dir"][:].astype(float),np.nan).sum(1)+np.ma.filled(f["swup_dif"][:].astype(float),np.nan).sum(1)
        for k in d: out.setdefault(k,[]).append(d[k])
    return {k:np.concatenate(v,axis=-1) for k,v in out.items()}
b=load("base"); d=load("dayl_d")
assert np.allclose(b["lat"],d["lat"])
b["netsw"]=b["swdn"]-b["swup"]; d["netsw"]=d["swdn"]-d["swup"]
b["LE"]=b["evap_land"]*2.5e6; d["LE"]=d["evap_land"]*2.5e6
for lo,hi in [(50,70),(40,50)]:
    m=(b["lat"]>=lo)&(b["lat"]<hi)&(b["w"]>0)
    print(f"\n== {lo}-{hi}N  cells={m.sum()}")
    print("mon  LAI b/d   alb b->d   netSW   sens   LE   grnd_flux   Tgrnd   vegn_T   t_ref   snowfrac")
    for mo in range(7,13):
        i=mo-1; w=b["w"][m]
        def avg(x,k): 
            a=x[k][i][m]; ok=np.isfinite(a); return np.nansum(a[ok]*w[ok])/w[ok].sum()
        alb_b=avg(b,"swup")/avg(b,"swdn"); alb_d=avg(d,"swup")/avg(d,"swdn")
        dd=lambda k: avg(d,k)-avg(b,k)
        print(f"{mo:2d}  {avg(b,'lai'):.2f}/{avg(d,'lai'):.2f}  {alb_b:.3f}->{alb_d:.3f}  {dd('netsw'):+.2f}  {dd('sens'):+.2f}  {dd('LE'):+.2f}  {dd('grnd_flux'):+.2f}  {dd('Tgrnd'):+.3f}  {dd('vegn_T'):+.3f}  {dd('t_ref'):+.3f}  {avg(b,'snow_frac'):.3f}/{avg(d,'snow_frac'):.3f}")
    # sign fraction of Tgrnd diff in Oct
    i=9; a=(d["Tgrnd"][i]-b["Tgrnd"][i])[m]; a=a[np.isfinite(a)]
    print(f"Oct dTgrnd: mean {a.mean():+.3f} min {a.min():+.2f} max {a.max():+.2f} neg frac {np.mean(a<0):.2f}  |d|>0.1 frac {np.mean(np.abs(a)>0.1):.2f}")
