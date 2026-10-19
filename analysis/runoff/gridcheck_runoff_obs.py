# grid-verify: G-RUN ENSEMBLE MMM and GRDC/UNH composite runoff (0.5 deg) before any regional statistic.
# Checks: coordinate metadata, units/fill, raw index-space image, known boxes, cross-dataset spatial r with shifts.
import numpy as np, xarray as xr
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

GR = "/Volumes/data02/runoff/GRUN/G-RUN_ENSEMBLE_MMM.nc"
CP = "/Volumes/data02/GRDC/processed/GRDC_UNH_composite_runoff_0.5deg.nc"
OUT = "/private/tmp/claude-501/-Volumes-data01-MOF-LSM-project/7ddc294b-f224-4bd0-b2ea-5dd0b742d675/scratchpad/"

g = xr.open_dataset(GR); c = xr.open_dataset(CP)
gr = g["Runoff"]
print("G-RUN attrs:", {k: gr.attrs.get(k) for k in ("units", "long_name", "_FillValue", "missing_value")})
print(f"  dims {dict(gr.sizes)}  Y {float(g.Y[0])}->{float(g.Y[-1])}  X {float(g.X[0])}->{float(g.X[-1])}  "
      f"time {str(g.time.values[0])[:7]}..{str(g.time.values[-1])[:7]}")
print("composite cmp_ro attrs:", {k: c["cmp_ro"].attrs.get(k) for k in ("units", "_FillValue")},
      "dims", dict(c["cmp_ro"].sizes))
latn = [d for d in c["cmp_ro"].dims if "lat" in d.lower()][0]; lonn = [d for d in c["cmp_ro"].dims if "lon" in d.lower()][0]
print(f"  lat {float(c[latn][0])}->{float(c[latn][-1])}  lon {float(c[lonn][0])}->{float(c[lonn][-1])}")

# 2001-2019 mean annual G-RUN (mm/day if units say so), composite annual mm/yr -> mm/day
sel = gr.sel(time=slice("2001-01-01", "2019-12-31"))
print(f"  G-RUN 2001-2019 months: {sel.time.size}")
ga = sel.mean("time").values.astype("f8")
ca = (c["cmp_ro_ann"].values / 365.0).astype("f8")
for name, a in (("G-RUN 2001-2019 mean", ga), ("composite ann/365", ca)):
    print(f"  {name}: min {np.nanmin(a):.3g} max {np.nanmax(a):.3g} valid% {100*np.isfinite(a).mean():.1f}")

fig, ax = plt.subplots(1, 2, figsize=(14, 4))
ax[0].imshow(ga, aspect="auto", vmin=0, vmax=3); ax[0].set_title("G-RUN 2001-19 mean RAW index (row0=Y[0])")
ax[1].imshow(ca, aspect="auto", vmin=0, vmax=3); ax[1].set_title("composite ann RAW index (row0=lat[0])")
plt.savefig(OUT + "_gridcheck_runoff.png", dpi=70)

G = xr.DataArray(ga, dims=("lat", "lon"), coords=dict(lat=g.Y.values, lon=g.X.values % 360)).sortby("lon").sortby("lat")
C = xr.DataArray(ca, dims=("lat", "lon"), coords=dict(lat=c[latn].values, lon=c[lonn].values % 360)).sortby("lon").sortby("lat")
bx = lambda d, a0, a1, o0, o1: float(d.sel(lat=slice(a0, a1), lon=slice(o0, o1)).mean())
for lab, b in [("Amazon 5S-0 300-310E", (-5, 0, 300, 310)), ("Congo 0-5N 15-25E", (0, 5, 15, 25)),
               ("Sahara 20-25N 0-10E", (20, 25, 0, 10)), ("W-Siberia 55-60N 70-80E", (55, 60, 70, 80)),
               ("Norway coast 60-65N 5-10E", (60, 65, 5, 10)), ("Yangtze 28-32N 110-120E", (28, 32, 110, 120))]:
    print(f"  {lab:26s} G-RUN {bx(G, *b):6.3f}  composite {bx(C, *b):6.3f} mm/day")

# common grid (both 0.5 deg?) -> spatial r and shift test
Ci = C.interp(lat=G.lat, lon=G.lon, method="nearest")
a, b = G.values, Ci.values
k = np.isfinite(a) & np.isfinite(b)
print(f"  same centres? max|dlat| {np.abs(C.lat.values[:, None] - G.lat.values[None, :]).min(0).max():.3f}")
for s, lab in [((0, 0), "as-is"), ((0, 1), "lon+0.5"), ((1, 0), "lat+0.5"), ((0, 4), "lon+2"), ((4, 0), "lat+2")]:
    bb = np.roll(np.roll(b, s[0], 0), s[1], 1); kk = k & np.isfinite(bb)
    print(f"  shift {lab:8s} r(G-RUN, composite) = {np.corrcoef(a[kk], bb[kk])[0, 1]:.3f} (n={kk.sum()})")
