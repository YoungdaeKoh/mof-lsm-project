# Is the common mountain SWE deficit forcing-driven?  Snowfall by elevation band, on each model's native grid.
#   ERA5 sf (0.25 deg, ERA5-Land's precipitation source)  vs  WFDE5 v3.0 Snowf (0.5 deg, the LSM forcing)
#   + model-received snowfall after each model's own rain/snow split (LM4p fprec_l, CLM5 SNOW, Noah-MP ACSNOW;
#     JULES writes only total precip)
# Accumulation season = Oct-May mean (mm/day), 2001-2023. Same NH land 20-90N + ice/perennial mask as snow_metrics.py
# (cells where the MAM SWE climatology map is finite). Elevation: ETOPO2 1deg nearest to model cell.
# Output: snowdiag/snowfall_by_elev_2001_2023.txt
import numpy as np, xarray as xr
from snowlib import D, model_grid, Binner

SF = D + "snowfall/"
TOPO = "/Volumes/data02/ETOPO2/ETOPO2_GLOBAL_2_ELEVATION_1x1.nc"
ACC = [9, 10, 11, 0, 1, 2, 3, 4]          # month index (0=Jan) of Oct..May
BANDS = [(-1e9, 500, "<500 m"), (500, 1500, "500-1500 m"), (1500, 1e9, ">1500 m")]
MSF = {"LM4p": ("lm4p_snowfall_2001_2023.nc", "fprec_l", 86400.0),   # kg m-2 s-1 -> mm/day
       "CLM5": ("clm5_snowfall_2001_2023.nc", "SNOW", 86400.0),      # mm/s -> mm/day
       "NoahMP": ("noahmp_snowfall_2001_2023.nc", "ACSNOW", 1.0)}    # already mm/day

def accmean(a):
    """Oct-May climatological mean of a (276, ...) monthly array."""
    idx = [i for i in range(a.shape[0]) if i % 12 in ACC]
    return np.nanmean(a[idx], 0)

era = xr.open_dataset(SF + "ERA5_sf_mon_200101-202312.nc")
wfd = xr.open_dataset(SF + "WFDE5_Snowf_mon_200101-202312.nc")
elat, elon = era.latitude.values if "latitude" in era else era.lat.values, \
             era.longitude.values if "longitude" in era else era.lon.values
wlat, wlon = wfd.lat.values, wfd.lon.values
era_acc = accmean(era["sf"].values.astype(np.float64))
wfd_acc = accmean(wfd["Snowf"].values.astype(np.float64))
# total precipitation: ERA5 tp; WFDE5 Rainf+Snowf (= PRECTmms that LM4p/CLM5 receive)
erp_acc = accmean(xr.open_dataset(SF + "ERA5_tp_mon_200101-202312.nc")["tp"].values.astype(np.float64))
wfp_acc = wfd_acc + accmean(xr.open_dataset(SF + "WFDE5_Rainf_mon_200101-202312.nc")["Rainf"].values.astype(np.float64))
topo = xr.open_dataset(TOPO)["ELEV"]

rows = []
for name in ["LM4p", "CLM5", "NoahMP", "JULES"]:
    mlat, mlon = model_grid(name)
    be, bw = Binner(elat, elon, mlat, mlon), Binner(wlat, wlon, mlat, mlon)
    e, w = be(era_acc), bw(wfd_acc)
    ep, wp = be(erp_acc), bw(wfp_acc)
    s = xr.open_dataset(D + f"snow_seasclim_{name}_perm100.nc")
    assert np.allclose(s.lat.values, mlat) and np.allclose(s.lon.values, mlon)
    ok = np.isfinite(s.SWE_MAM_model.values) & np.isfinite(s.SWE_MAM_obs.values) & (mlat[:, None] >= 20)
    swe_b = (s.SWE_MAM_model - s.SWE_MAM_obs).values
    if name in MSF:
        f, v, k = MSF[name]
        ds = xr.open_dataset(D + f).assign_coords(lon=lambda d: d.lon % 360).sortby("lon").sortby("lat")
        a = np.where(np.abs(ds[v].values) > 1e19, np.nan, ds[v].values).astype(np.float64) * k
        m = accmean(a)
    else:
        m = np.full(e.shape, np.nan)
    el = topo.interp(lat=mlat, lon=mlon, method="nearest").values
    cw = np.cos(np.deg2rad(mlat))[:, None] * np.ones_like(el)
    for lo, hi, lab in BANDS:
        k = ok & (el >= lo) & (el < hi) & np.isfinite(e) & np.isfinite(w)
        wm = lambda x: np.nansum(cw[k] * x[k]) / np.sum(cw[k] * np.isfinite(x[k]))
        rows.append((name, lab, int(k.sum()), wm(e), wm(w), wm(m), wm(swe_b), wm(ep), wm(wp)))

hdr = (f"{'model':7s} {'band':11s} {'n':>5s} {'ERA5':>6s} {'WFDE5':>6s} {'W-E%':>6s} "
       f"{'model':>6s} {'M-W%':>6s} {'M-E%':>6s} | {'P_ERA5':>6s} {'P_WFD':>6s} {'P W-E%':>7s} | "
       f"{'fsn_E':>5s} {'fsn_W':>5s} {'fsn_M':>5s} | MAM SWE bias mm")
lines = [hdr]
pc = lambda a, b: 100 * (a - b) / b
for name, lab, n, e, w, m, b, ep, wp in rows:
    lines.append(f"{name:7s} {lab:11s} {n:5d} {e:6.3f} {w:6.3f} {pc(w, e):+6.1f} {m:6.3f} {pc(m, w):+6.1f} "
                 f"{pc(m, e):+6.1f} | {ep:6.3f} {wp:6.3f} {pc(wp, ep):+7.1f} | {e/ep:5.2f} {w/wp:5.2f} {m/wp:5.2f} "
                 f"| {b:+6.1f}")
open(D + "snowfall_by_elev_2001_2023.txt", "w").write(
    "# Oct-May means (mm/day) 2001-2023, NH land 20-90N, ice/perennial masked, cos-lat weighted, model grid\n"
    "# snowfall: ERA5 sf, WFDE5 Snowf, model-received (LM4p fprec_l, CLM5 SNOW, Noah-MP ACSNOW; JULES none)\n"
    "# W-E% WFDE5 vs ERA5; M-W% model vs WFDE5 Snowf (split effect); M-E% model vs ERA5\n"
    "# P = total precip (ERA5 tp; WFDE5 Rainf+Snowf = PRECTmms); fsn = snowfall / total precip (E: ERA5, W: WFDE5, "
    "M: model snowfall / WFDE5 P)\n"
    + "\n".join(lines) + "\n")
print("\n".join(lines))
