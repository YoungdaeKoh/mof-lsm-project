import numpy as np
from netCDF4 import Dataset
G="/data1/CESM2_INPUT/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v1.c170516/Precip"
f0=Dataset(f"{G}/clmforc.GSWP3.c2011.0.5x0.5.Prec.1981-01.nc")
LAT=np.array(f0.variables['LATIXY'][:,0]); f0.close()
W=np.cos(np.deg2rad(LAT))[:,None]
rows=[]; vf=None
for y in range(1981,2011):
    ms=[]
    for m in range(1,13):
        nc=Dataset(f"{G}/clmforc.GSWP3.c2011.0.5x0.5.Prec.{y}-{m:02d}.nc")
        p=np.array(nc.variables['PRECTmms'][::8],dtype=float); nc.close()  # daily subsample
        p[p>1e10]=np.nan
        mm=np.nanmean(p,axis=0)
        valid=~np.isnan(mm)
        if vf is None: vf=valid.mean()
        ms.append(np.nansum(mm*W)/(W*valid).sum())
    a=np.mean(ms)*86400.0
    rows.append((y,a)); print(y,round(a,3),flush=True)
print("valid fraction (1=global,~0.3=land):",round(vf,2))
with open('/data2/ydkoh/gswp3_precip_annual.csv','w') as o:
    o.write('year,precip_mm_day\n')
    for y,a in rows: o.write(f'{y},{a:.4f}\n')
print("saved gswp3_precip_annual.csv")
