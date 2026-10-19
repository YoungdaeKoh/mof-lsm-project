# Observed: is 2010 summer dry in WSB/ESB bands, and do drier cells have earlier GLASS EOS?
import glob, numpy as np, netCDF4 as nc, regionmask, warnings
warnings.filterwarnings("ignore")
SM = "/Volumes/data02/SoilMoisture/ESACCI_C3S_v202505_monthly/surface_soil_moisture_volumetric/"
def sm1deg(y, mo):
    with nc.Dataset(glob.glob(SM + "*MONTHLY-%d%02d01*" % (y, mo))[0]) as A:
        x = np.ma.filled(A["sm"][0].astype("f8"), np.nan)[::-1]          # lat descending -> ascending
    return np.nanmean(x.reshape(180, 4, 360, 4), axis=(1, 3))              # 0.25 -> 1 deg block mean
months = (5, 6, 7, 8, 9)
s10 = np.array([sm1deg(2010, m) for m in months])
clim = np.array([[sm1deg(y, m) for m in months] for y in range(2001, 2021)])
cm = np.nanmean(clim, 0)
d = np.load("/Volumes/data01/MOF_LSM_project/poster/2026_LM4p_LAI/data/sos_eos_maps_2010.npz")
lat, lon = d["lat"], d["lon"]
# GLASS EOS 2010 (same method as p25)
D = np.arange(1, 366.0); MID = np.array([15.5,45,74.5,105,135.5,166,196.5,227.5,258,288.5,319,349.5])
with nc.Dataset("/Volumes/data01/MOF_LSM_project/poster/2026_LM4p_LAI/data/glass_lai_modis_monthly_1deg_2001_2020.nc") as A:
    gl = np.ma.filled(A["lai"][108:120].astype("f8"), np.nan)
def eos_of(m):
    c = np.interp(D, np.r_[MID[-1]-365, MID, MID[0]+365], np.r_[m[-1], m, m[0]])
    thr = c.min() + 0.5*(c.max()-c.min()); ip = int(c.argmax())
    dn = [k for k in range(ip, 364) if c[k] >= thr > c[k+1]]
    return (D[dn[0]] + (c[dn[0]]-thr)/(c[dn[0]]-c[dn[0]+1]) if dn else np.nan), D[ip]
reg = regionmask.defined_regions.ar6.land.mask(lon, lat).values
print("band       cells | ESA SM 2010 May Jun Jul Aug Sep (m3/m3) | 2010-clim JJA | GLASS peak doy, EOS | r(EOS, JA SM) | EOS dry1/3 vs wet1/3")
for r, b0, b1 in (("WSB",45,55),("WSB",55,65),("ESB",45,55),("ESB",55,65)):
    m = (reg == regionmask.defined_regions.ar6.land.map_keys(r)) & (lat[:, None] >= b0) & (lat[:, None] < b1)
    m &= np.isfinite(s10).all(0) & np.isfinite(gl).all(0) & ((gl.max(0)-gl.min(0)) >= 0.5)
    ii, jj = np.where(m)
    ep = np.array([eos_of(gl[:, i, j]) for i, j in zip(ii, jj)]); e, pk = ep[:, 0], ep[:, 1]
    ja = s10[2:4, ii, jj].mean(0); ok = np.isfinite(e)
    rr = np.corrcoef(e[ok], ja[ok])[0, 1]
    q1, q2 = np.percentile(ja[ok], [33.3, 66.7])
    an = (s10[1:4] - cm[1:4])[:, ii, jj].mean()
    print("%s %d-%dN %5d | %s | %+6.3f | %5.0f %5.0f | %+5.2f | %5.0f vs %5.0f" % (r, b0, b1, m.sum(),
          " ".join("%.2f" % np.nanmean(s10[k, ii, jj]) for k in range(5)), an, np.median(pk), np.nanmean(e), rr,
          np.nanmean(e[ok][ja[ok] <= q1]), np.nanmean(e[ok][ja[ok] >= q2])))
