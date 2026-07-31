"""Radiation delivery check — the piece land_forcing could not give us.

land_forcing registers lwdn_sfc/swdn_* but writes them as fill under
do_atmos=.false.  land_month carries the same quantities and does write them:

    swdn_dir(time, band, grid_index)  swdn_dif(time, band, grid_index)
    lwdn(time, grid_index)

so total downward shortwave is the sum over bands of direct plus diffuse.
Monthly means are combined with day weights from time_bnds (noleap months are
not equal length), then compared at the C96 cell centres against the source
interpolated bilinearly to the same points -- the same recipe as
chk_forcing_native.py.
"""
import numpy as np
from netCDF4 import Dataset

LM = "/data2/ydkoh/lm4/RERUN/wA/archive/y1990/19900101.land_month.tile%d.nc"
STATIC = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive/y1990/19900101.land_static.tile%d.nc"
GRID = "/data2/ydkoh/lm4/RUN/lm4_spinup30/INPUT/C96_grid.tile%d.nc"
SRC = "/data2/ydkoh/lm4/forcing_WFDE5_lm4p/wfde5_atm_1990.nc"
NPZ = "/data2/ydkoh/lm4/forcing_native_1990.npz"
NX, BIG = 96, 1e19

lat, lon, sw, lw = [], [], [], []
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

    d = Dataset(LM % t)
    tb = d.variables["time_bnds"][:]
    wgt = np.array(tb[:, 1] - tb[:, 0], dtype="f8")     # days per month
    wgt = wgt / wgt.sum()
    if t == 1:
        print("bands = %d, months = %d, day weights sum = %.3f"
              % (d.dimensions["band"].size, wgt.size, wgt.sum() * 1))

    def rd(name):
        a = np.ma.filled(d.variables[name][:].astype("f8"), np.nan)
        a[np.abs(a) > BIG] = np.nan
        return a

    s = rd("swdn_dir") + rd("swdn_dif")        # (time, band, pts)
    s = np.nansum(s, axis=1)                   # sum the bands
    sw.append(np.einsum("m,mp->p", wgt, s))
    lw.append(np.einsum("m,mp->p", wgt, rd("lwdn")))
    d.close()
    print("tile %d done" % t)

lat = np.concatenate(lat)
lon = np.concatenate(lon)
sw = np.concatenate(sw)
lw = np.concatenate(lw)

# ------------------------------------------------------ source, annual mean --
d = Dataset(SRC)
slat = np.array(d.variables["lat"][:], dtype="f8")
slon = np.array(d.variables["lon"][:], dtype="f8")
tv = d.variables["time"][:]
idx = np.where((tv >= 0) & (tv < 365))[0]


def src_mean(nm):
    s = None
    n = 0
    for i0 in range(idx[0], idx[-1] + 1, 100):
        i1 = min(i0 + 100, idx[-1] + 1)
        b = np.ma.filled(d.variables[nm][i0:i1].astype("f8"), np.nan)
        b[np.abs(b) > BIG] = np.nan
        s = np.nansum(b, axis=0) if s is None else s + np.nansum(b, axis=0)
        n += i1 - i0
    return s / n


F = {"sw": src_mean("flux_sw"), "lw": src_mean("flux_lw")}
d.close()

asc = slat[1] > slat[0]
LA = slat if asc else slat[::-1]
qlon = np.mod(lon, 360.0) if slon.max() > 180.0 else np.where(lon > 180, lon - 360, lon)
qlat = np.clip(lat, LA[0], LA[-1])
dlon = slon[1] - slon[0]
fx = (qlon - slon[0]) / dlon
i0 = np.floor(fx).astype(int) % slon.size
i1 = (i0 + 1) % slon.size
wx = fx - np.floor(fx)
j0 = np.clip(np.searchsorted(LA, qlat, side="right") - 1, 0, LA.size - 2)
wy = (qlat - LA[j0]) / (LA[j0 + 1] - LA[j0])
j1 = j0 + 1


def interp(field):
    f = field if asc else field[::-1]
    c = [f[j0, i0], f[j0, i1], f[j1, i0], f[j1, i1]]
    bad = ~np.all([np.isfinite(x) for x in c], axis=0)
    v = ((1 - wx) * (1 - wy) * c[0] + wx * (1 - wy) * c[1] +
         (1 - wx) * wy * c[2] + wx * wy * c[3])
    v[bad] = np.nan
    return v


SR = {k: interp(v) for k, v in F.items()}

z = dict(np.load(NPZ))
z["mod_sw"], z["mod_lw"] = sw, lw
z["src_sw"], z["src_lw"] = SR["sw"], SR["lw"]
np.savez(NPZ, **z)

print("\n1990 annual mean at C96 cell centres, W/m2")
print("%-6s %11s %11s %11s %9s %8s %9s"
      % ("field", "model", "source", "bias", "rel%", "r", "sd(diff)"))
for k in ("sw", "lw"):
    a, b = z["mod_%s" % k], z["src_%s" % k]
    ok = np.isfinite(a) & np.isfinite(b)
    dd = a[ok] - b[ok]
    print("%-6s %11.4f %11.4f %+11.5f %8.3f%% %8.5f %9.5f"
          % (k, a[ok].mean(), b[ok].mean(), dd.mean(),
             dd.mean() / abs(b[ok].mean()) * 100,
             np.corrcoef(a[ok], b[ok])[0, 1], dd.std()))
