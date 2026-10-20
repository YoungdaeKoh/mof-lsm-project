import numpy as np, netCDF4 as nc, regionmask, warnings
D=np.arange(1,366.0); MID=np.array([15.5,45,74.5,105,135.5,166,196.5,227.5,258,288.5,319,349.5])
F={}
for n,f,y0 in [("GIMMS","gimms_lai_mon_1982_2020.nc",1982),("AVHRR","gimms_solely_lai_mon_1982_2015.nc",1982),("GLASS","glass_lai_modis_monthly_1deg_2001_2020.nc",2001)]:
    with nc.Dataset("../../../poster/2026_LM4p_LAI/data/"+f) as A:
        i0=(2010-y0)*12; F[n]=np.ma.filled(A["lai"][i0:i0+12].astype("f8"),np.nan); lat=np.asarray(A["lat"][:]); lon=np.asarray(A["lon"][:])
for n,k in [("CTRL","base"),("DL","dayl")]:
    with nc.Dataset("../../../poster/2026_LM4p_LAI/data/%s.lai.2010-2010.1deg.nc"%k) as A: F[n]=np.ma.filled(A["lai"][:].astype("f8"),np.nan)
for v in F.values(): v[np.abs(v)>100]=np.nan
S=np.load("../../../poster/2026_LM4p_LAI/data/model_species_dominance_1deg_2010.npz",allow_pickle=True)
assert np.allclose(S["lat"],lat) and np.allclose(S["lon"],lon), (S["lat"][:3],lat[:3],S["lon"][:3],lon[:3])
sp=list(S["species"]); acer=S["share"][sp.index("acer")]
def eos(m):
    if not np.isfinite(m).all() or np.ptp(m)<0.3: return np.nan
    c=np.interp(D,np.r_[MID[-1]-365,MID,MID[0]+365],np.r_[m[-1],m,m[0]]); thr=c.min()+0.5*np.ptp(c); ip=int(c.argmax())
    dn=[k for k in range(ip,364) if c[k]>=thr>c[k+1]]
    return D[dn[0]]+(c[dn[0]]-thr)/(c[dn[0]]-c[dn[0]+1]) if dn else np.nan
LA=lat[:,None]*np.ones((1,360))
base=(LA>20)&np.isfinite(acer)&(np.ptp(F["GIMMS"],0)>=0.5)&np.all([np.isfinite(v).all(0) for v in F.values()],0)
E={n:np.full(base.shape,np.nan) for n in F}
for i,j in zip(*np.where(base)):
    for n in F: E[n][i,j]=eos(F[n][:,i,j])
W=np.cos(np.radians(LA))
with warnings.catch_warnings():
    warnings.simplefilter("ignore"); m3=regionmask.defined_regions.ar6.land.mask_3D(lon,lat)
ar6=regionmask.defined_regions.ar6.land
def row(lab,msk):
    ok=msk&np.all([np.isfinite(E[n]) for n in E],0)
    if ok.sum()<10: return "%-28s n %4d (too few)"%(lab,ok.sum())
    w=W[ok]; mean=lambda x:(x[ok]*w).sum()/w.sum()
    o=[mean(E[n]) for n in ("GIMMS","AVHRR","GLASS")]; om=np.mean(o)
    c=mean(E["CTRL"]); d=mean(E["DL"])
    return "%-28s n %4d acer %.2f | obs EOS %5.1f (spread %4.1f) | CTRL %+5.1f  DL13/12 %+5.1f  change %+5.1f | cells DL earlier %3.0f %%"%(
        lab,ok.sum(),(acer[ok]*w).sum()/w.sum(),om,np.ptp(o),c-om,d-om,d-c,100*np.mean(E["DL"][ok]<E["CTRL"][ok]-1))
out=["EOS 2010 bias vs mean of GIMMS/AVHRR/GLASS (days, cos-lat), monthly interp 50 %; acer = July leaf-area share (base 2010)"]
for th in (0.3,0.5,0.7):
    out.append(row("acer >= %.1f, 20-90N"%th, base&(acer>=th)))
out.append(row("acer < 0.1, 20-90N (ref)", base&(acer<0.1)))
for a,b in ((20,30),(30,40),(40,50),(50,60)):
    out.append(row("acer>=0.5 %d-%dN"%(a,b), base&(acer>=0.5)&(LA>=a)&(LA<b)))
for r in ("ENA","WCE","EAS","EEU","CNA","WNA"):
    rm=m3.sel(region=ar6.map_keys(r)).values.astype(bool)
    out.append(row("acer>=0.5 %s"%r, base&(acer>=0.5)&rm))
    out.append(row("all cells %s"%r, base&rm))
open("../data/acer_eos_ctrl_vs_dl_2010.txt","w").write("\n".join(out)+"\n")
print("\n".join(out))
