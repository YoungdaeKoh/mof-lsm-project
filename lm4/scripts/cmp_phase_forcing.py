"""Compare the two LM4p forcings of one year: ramp phase split (wfde5_atm_<y>.nc) vs WFDE5 phase (_phasewfde5).

Checks: every non-precip field identical; fprec + lprec identical (same total); snowfall difference by latitude band
and by WFDE5 grid altitude (ASurf), Oct-May. Run on the server (anaconda python).
usage: python cmp_phase_forcing.py <year>
"""
import sys
import numpy as np
import netCDF4 as nc

Y = int(sys.argv[1])
D = "/data2/ydkoh/lm4/forcing_WFDE5_lm4p/"
A, B = nc.Dataset(D + "wfde5_atm_%d.nc" % Y), nc.Dataset(D + "wfde5_atm_%d_phasewfde5.nc" % Y)
lat = A["lat"][:]; lon = A["lon"][:]
with nc.Dataset("/data2/ydkoh/WFDE5_6h/ASurf/ASurf_WFDE5_CRU_v3.0.nc") as G:
    z = np.ma.filled(G["ASurf"][:].astype("f8"), np.nan)
    k = int(np.argmin(np.abs(G["lon"][:] - lon[0]))); z = np.roll(z, -k, axis=1)
land = np.isfinite(z)
for v in ("t_bot", "sphum_bot", "p_surf", "u_bot", "flux_lw", "flux_sw", "coszen"):
    d = max(float(np.nanmax(np.abs(A[v][s:min(s + 200, 1460)] - B[v][s:min(s + 200, 1460)]))) for s in range(0, 1460, 200))
    print("%-9s max |old-new| %.3g" % (v, d))
oct_may = np.r_[0:151 * 4, 273 * 4:1460]                 # Jan-May + Oct-Dec steps (noleap)
fa = fb = pa = pb = 0.0
fa = np.zeros(land.shape); fb = np.zeros(land.shape); pt = np.zeros(land.shape); dp = 0.0
for s in range(0, 1460, 200):
    idx = [i for i in range(s, min(s + 200, 1460)) if i in set(oct_may)]
    if not idx:
        continue
    a_f, b_f = A["fprec"][idx], B["fprec"][idx]; a_l, b_l = A["lprec"][idx], B["lprec"][idx]
    dp = max(dp, float(np.nanmax(np.abs((a_f + a_l) - (b_f + b_l)))))
    fa += a_f.sum(0); fb += b_f.sum(0); pt += (a_f + a_l).sum(0)
print("fprec+lprec max |old-new| %.3g kg/m2/s" % dp)
LA = lat[:, None] * np.ones((1, lon.size)); W = np.cos(np.radians(LA))
print("Oct-May snowfall, ramp vs WFDE5 phase (land, cos-lat): snow share of precip and ramp/WFDE5 ratio")
for name, m in [("30-45N", (LA >= 30) & (LA < 45)), ("45-60N", (LA >= 45) & (LA < 60)), ("60-75N", (LA >= 60) & (LA < 75)),
                ("NH z<500m", (LA >= 30) & (z < 500)), ("NH 500-1500m", (LA >= 30) & (z >= 500) & (z < 1500)), ("NH >1500m", (LA >= 30) & (z >= 1500))]:
    m = m & land
    sa, sb, sp = (fa[m] * W[m]).sum(), (fb[m] * W[m]).sum(), (pt[m] * W[m]).sum()
    print("  %-13s cells %5d  share ramp %.3f  WFDE5 %.3f  ratio ramp/WFDE5 %.3f" % (name, m.sum(), sa / sp, sb / sp, sa / sb))
