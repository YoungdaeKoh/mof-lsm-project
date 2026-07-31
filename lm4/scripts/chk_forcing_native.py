"""Forcing delivery check on the model's OWN grid — no re-binning.

The first version put both fields into 1-degree boxes.  In complex terrain a
1-degree box often holds a single C96 point, so its centre elevation was being
compared against the box-mean elevation of the 0.5-degree source; that mismatch
alone produced +-1 K and was mistaken for a delivery error.

Here the source is bilinearly interpolated to the exact C96 cell centres
instead, so model and source are evaluated at the same location and the only
remaining difference is what the model actually received.  Bilinear
interpolation is linear, so interpolating the annual mean equals the annual mean
of the interpolated field -- comparing annual means is exact, not an
approximation.

Points whose four source neighbours are not all valid (coastlines, where the
land-only source has fill) are reported separately rather than silently filled.

Output: /data2/ydkoh/lm4/forcing_native_1990.npz
"""
import numpy as np
from netCDF4 import Dataset

LF = "/data2/ydkoh/lm4/RERUN/wA/archive/y1990/19900101.land_forcing.tile%d.nc"
LD = "/data2/ydkoh/lm4/RERUN/wA/archive/y1990/19900101.land_daily.tile%d.nc"
STATIC = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive/y1990/19900101.land_static.tile%d.nc"
GRID = "/data2/ydkoh/lm4/RUN/lm4_spinup30/INPUT/C96_grid.tile%d.nc"
SRC = "/data2/ydkoh/lm4/forcing_WFDE5_lm4p/wfde5_atm_1990.nc"
OUT = "/data2/ydkoh/lm4/forcing_native_1990.npz"
NX, BIG, GUST = 96, 1e19, 3.0

# ------------------------------------------------ model, at C96 cell centres --
lat, lon = [], []
mod = {k: [] for k in ("t", "q", "ps", "wind", "pr")}
for t in range(1, 7):
    st = Dataset(STATIC % t)
    gi = st.variables["grid_index"][:].astype(int)
    st.close()
    g = Dataset(GRID % t)
    X, Y = g.variables["x"][:], g.variables["y"][:]
    g.close()
    j, i = gi // NX, gi % NX
    lat.append(Y[1::2, 1::2][j, i])
    lon.append(X[1::2, 1::2][j, i])

    d = Dataset(LF % t)
    n = d.dimensions["time"].size
    for key, var in (("t", "t_atm"), ("q", "q_atm"), ("ps", "ps"), ("wind", "wind")):
        s = np.zeros((NX, NX))
        for i0 in range(0, n, 200):
            a = np.ma.filled(d.variables[var][i0:i0 + 200].astype("f8"), np.nan)
            a[np.abs(a) > BIG] = np.nan
            s += np.nansum(a, axis=0)
        mod[key].append((s / n)[j, i])
    d.close()

    d = Dataset(LD % t)                      # precip lives in land_daily
    a = np.ma.filled(d.variables["precip"][:].astype("f8"), np.nan)
    a[np.abs(a) > BIG] = np.nan
    mod["pr"].append(np.nanmean(a, axis=0))
    d.close()
    print("tile %d done" % t)

lat = np.concatenate(lat)
lon = np.concatenate(lon)
for k in mod:
    mod[k] = np.concatenate(mod[k])
print("C96 land points: %d" % lat.size)

# ------------------------------------------------------ source, annual mean --
d = Dataset(SRC)
slat = np.array(d.variables["lat"][:], dtype="f8")
slon = np.array(d.variables["lon"][:], dtype="f8")
tv = d.variables["time"][:]
idx = np.where((tv >= 0) & (tv < 365))[0]


def src_mean(names):
    s = None
    n = 0
    for i0 in range(idx[0], idx[-1] + 1, 100):
        i1 = min(i0 + 100, idx[-1] + 1)
        a = None
        for nm in names:
            b = np.ma.filled(d.variables[nm][i0:i1].astype("f8"), np.nan)
            b[np.abs(b) > BIG] = np.nan
            a = b if a is None else a + b
        s = np.nansum(a, axis=0) if s is None else s + np.nansum(a, axis=0)
        n += i1 - i0
    return s / n


SRCF = {"t": src_mean(["t_bot"]), "q": src_mean(["sphum_bot"]),
        "ps": src_mean(["p_surf"]), "wind": np.abs(src_mean(["u_bot"])),
        "pr": src_mean(["lprec", "fprec"])}
d.close()
print("source records used: %d" % idx.size)

# --------------------------------------------- bilinear onto the C96 points --
# the source is a regular lat-lon grid; build the weights once and reuse them
asc = slat[1] > slat[0]
LA = slat if asc else slat[::-1]
qlon = np.mod(lon, 360.0) if slon.max() > 180.0 else np.where(lon > 180, lon - 360, lon)
qlat = np.clip(lat, LA[0], LA[-1])

dlon = slon[1] - slon[0]
fx = (qlon - slon[0]) / dlon
i0 = np.floor(fx).astype(int) % slon.size
i1 = (i0 + 1) % slon.size                     # wrap in longitude
wx = fx - np.floor(fx)

j0 = np.searchsorted(LA, qlat, side="right") - 1
j0 = np.clip(j0, 0, LA.size - 2)
wy = (qlat - LA[j0]) / (LA[j0 + 1] - LA[j0])
j1 = j0 + 1


def interp(field):
    f = field if asc else field[::-1]
    c00, c10 = f[j0, i0], f[j0, i1]
    c01, c11 = f[j1, i0], f[j1, i1]
    bad = ~(np.isfinite(c00) & np.isfinite(c10) &
            np.isfinite(c01) & np.isfinite(c11))
    v = ((1 - wx) * (1 - wy) * c00 + wx * (1 - wy) * c10 +
         (1 - wx) * wy * c01 + wx * wy * c11)
    v[bad] = np.nan
    return v, bad


SR = {}
for k, f in SRCF.items():
    SR[k], bad = interp(f)
    if k == "t":
        print("points dropped for incomplete source neighbours: %d of %d (%.1f%%)"
              % (bad.sum(), bad.size, 100 * bad.mean()))

np.savez(OUT, lat=lat, lon=lon,
         **{"mod_%s" % k: v for k, v in mod.items()},
         **{"src_%s" % k: v for k, v in SR.items()})

# ------------------------------------------------------------------ report ---
print("\n1990 annual mean at C96 cell centres (no re-binning)")
print("%-12s %11s %11s %11s %9s %8s %8s %8s"
      % ("field", "model", "source", "bias", "rel%", "r", "sd(diff)", "p99|d|"))
for k, sc, unit, src in (("t", 1.0, "K", None), ("q", 1e3, "g/kg", None),
                         ("ps", 1e-2, "hPa", None), ("pr", 86400.0, "mm/day", None),
                         ("wind", 1.0, "m/s", "gust")):
    a = mod[k] * sc
    b = SR[k] * sc
    if src == "gust":
        b = np.sqrt(b ** 2 + GUST ** 2)
    ok = np.isfinite(a) & np.isfinite(b)
    dd = a[ok] - b[ok]
    print("%-12s %11.4f %11.4f %+11.5f %8.3f%% %8.5f %8.4f %8.4f"
          % (k, a[ok].mean(), b[ok].mean(), dd.mean(),
             dd.mean() / abs(b[ok].mean()) * 100,
             np.corrcoef(a[ok], b[ok])[0, 1], dd.std(),
             np.percentile(np.abs(dd), 99)))
print("\nwrote %s" % OUT)
