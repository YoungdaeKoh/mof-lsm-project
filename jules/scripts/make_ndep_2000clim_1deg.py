#!/usr/bin/env python3
"""Total nitrogen deposition, year-2000 monthly climatology, on the JULES 1-deg grid.

Source = the file CLM5 uses (CMIP6 historical CESM2-WACCM ensemble mean, 1849-2015
monthly, 0.9x1.25, kg/m2/s); CLM5 production cycles its year 2000
(stream_year_first/last_ndep = 2000), so JULES gets the same year.
Total = dry + wet of NHx and NOy (all "as N").  JULES reads it as `deposition_n`
(kg/m2/s) through &jules_prescribed_dataset with is_climatology=.true.
(rose-stem loobos_jules_cn / gswp2_es_1p1 pattern).  Not used by any run yet:
prepared for a later JULES nitrogen-on sensitivity experiment.

Steps: (1) year-2000 sum on the source grid  (2) cdo remapcon -> r360x180,
which is the grid_info_1deg.nc layout (lon 0..359, lat -89.5..89.5)
(3) grid-verify: coordinates vs grid_info, global/land totals before and after,
value range, regional sign checks, index-space map (written as PNG).
"""
import os
import subprocess
import numpy as np
from netCDF4 import Dataset, num2date

SRC = ("/data1/CESM2_INPUT/lnd/clm2/ndepdata/fndep_clm_hist_b.e21.BWHIST.f09_g17."
       "CMIP6-historical-WACCM.ensmean_1849-2015_monthly_0.9x1.25_c180926.nc")
D = "/data2/ydkoh/jules_ndep"
MID = D + "/ndep_total_2000clim_0.9x1.25.nc"
OUT = D + "/ndep_2000clim_1deg.nc"
GI = "/home/ydkoh/JULES_runs/ancil/global_1deg/grid_info_1deg.nc"
CDO = "/usr/local/cdo/1.9.3_gcc85/bin/cdo"
VARS = ["dry_deposition_NHx_as_N", "dry_deposition_NOy_as_N",
        "wet_deposition_NHx_as_N", "wet_deposition_NOy_as_N"]
SPY = 365 * 86400.0
R_E = 6.371e6
os.makedirs(D, exist_ok=True)


def cell_area(lat, lon):
    """area (m2) of a regular lat/lon grid from centre coordinates"""
    dlon = np.deg2rad(np.abs(np.diff(lon).mean()))
    latb = np.concatenate([[-90.0], 0.5 * (lat[1:] + lat[:-1]), [90.0]])
    band = np.sin(np.deg2rad(latb[1:])) - np.sin(np.deg2rad(latb[:-1]))
    return (R_E ** 2 * dlon * band)[:, None] * np.ones((1, lon.size))


# ---- (1) year-2000 total on the source grid ----
with Dataset(SRC) as s:
    s.set_auto_mask(False)
    t = s.variables["time"]
    dates = num2date(t[:], t.units, getattr(t, "calendar", "noleap"))
    idx = [i for i, d in enumerate(dates) if d.year == 2000]
    print("source: %s ... months of 2000: %s" % (s.dimensions["time"].size, [dates[i].month for i in idx]))
    lat = s.variables["lat"][:].astype("f8"); lon = s.variables["lon"][:].astype("f8")
    tot = sum(s.variables[v][idx].astype("f8") for v in VARS)       # (12, lat, lon)
print("source grid: lat %.3f..%.3f (%d), lon %.3f..%.3f (%d)" % (lat[0], lat[-1], lat.size, lon[0], lon[-1], lon.size))
with Dataset(MID, "w", format="NETCDF4_CLASSIC") as o:
    o.createDimension("time", None); o.createDimension("lat", lat.size); o.createDimension("lon", lon.size)
    v = o.createVariable("time", "f8", ("time",)); v[:] = np.arange(12) * 30.4 + 15
    v.units = "days since 2000-01-01 00:00:00"; v.calendar = "noleap"
    v = o.createVariable("lat", "f8", ("lat",)); v[:] = lat; v.units = "degrees_north"
    v = o.createVariable("lon", "f8", ("lon",)); v[:] = lon; v.units = "degrees_east"
    v = o.createVariable("deposition_n", "f4", ("time", "lat", "lon")); v[:] = tot
    v.units = "kg/m2/s"; v.long_name = "total N deposition (dry+wet NHx+NOy), year-2000 monthly"

# ---- (2) conservative remap to the JULES 1-deg grid ----
env = dict(os.environ, LD_LIBRARY_PATH="/usr/local/netcdf/4.6.1_gcc85/lib:/usr/local/hdf5/1.10.5_gcc85/lib")
subprocess.run([CDO, "-s", "remapcon,r360x180", MID, OUT], check=True, env=env)

# ---- (3) grid-verify ----
with Dataset(OUT) as o, Dataset(GI) as g:
    o.set_auto_mask(False); g.set_auto_mask(False)
    la, lo = o.variables["lat"][:], o.variables["lon"][:]
    nd = o.variables["deposition_n"][:].astype("f8")
    gla, glo = g.variables["lat"][:], g.variables["lon"][:]
    land = g.variables["land_fraction"][:] > 0
    print("1deg grid: lat %.2f..%.2f (%d) lon %.2f..%.2f (%d) | identical to grid_info: lat %s lon %s"
          % (la[0], la[-1], la.size, lo[0], lo[-1], lo.size, np.allclose(la, gla), np.allclose(lo, glo)))
    print("records %d, NaN/fill %d, min %.3e max %.3e kg/m2/s" % (nd.shape[0], int((~np.isfinite(nd) | (np.abs(nd) > 1e19)).sum()), nd.min(), nd.max()))
    A0, A1 = cell_area(lat, lon), cell_area(la, lo)
    g0 = (tot.mean(0) * A0).sum() * SPY / 1e9      # kg -> Tg
    g1 = (nd.mean(0) * A1).sum() * SPY / 1e9
    l1 = (nd.mean(0) * A1 * land).sum() * SPY / 1e9
    print("global total: source %.2f TgN/yr, 1deg %.2f TgN/yr (diff %.3f %%) | on JULES land %.2f TgN/yr"
          % (g0, g1, 100 * (g1 - g0) / g0, l1))
    ann = nd.mean(0) * SPY * 1000                  # gN/m2/yr
    def box(la0, la1, lo0, lo1):
        m = (la[:, None] >= la0) & (la[:, None] <= la1) & (lo[None, :] >= lo0) & (lo[None, :] <= lo1) & land
        return ann[m].mean()
    print("regional land means (gN/m2/yr): E China %.2f | W Europe %.2f | E USA %.2f | Sahara %.2f | Amazon %.2f | Siberia %.2f"
          % (box(25, 40, 110, 122), box(45, 55, 0, 15), box(33, 43, 270, 285), box(18, 28, 0, 30),
             box(-10, 0, 295, 310), box(60, 70, 90, 130)))
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(12, 3.4))
    ax[0].imshow(np.log10(np.maximum(tot.mean(0) * SPY * 1000, 1e-3)), origin="lower", aspect="auto"); ax[0].set_title("source 0.9x1.25, RAW index space, log10 gN/m2/yr")
    ax[1].imshow(np.log10(np.maximum(ann, 1e-3)), origin="lower", aspect="auto"); ax[1].set_title("JULES 1deg, RAW index space")
    ax[1].contour(land.astype(float), [0.5], colors="k", linewidths=0.3)
    fig.tight_layout(); fig.savefig(D + "/gridcheck_ndep.png", dpi=90)
    print("wrote", OUT, "and", D + "/gridcheck_ndep.png")
