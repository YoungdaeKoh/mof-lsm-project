#!/usr/bin/env python3
"""Day length on the observed EOS date, computed cell by cell (replaces the one-latitude-per-region shortcut).

For every 1-deg cell north of 20N with a clear seasonal cycle (GIMMS LAI4g 1982-2010 climatology,
max - min >= 0.5), the climatological monthly curve is interpolated to days, EOS is the 50 % amplitude
crossing after the peak, and the day length on that day is computed at the cell's own latitude
(Cooper declination + sunrise equation).  Outputs the distribution per AR6 region and per 5-degree
latitude band, and a linear fit of day length at EOS against latitude.
Output: ../data/eos_daylength_percell.txt
"""
import warnings
import numpy as np
import netCDF4 as nc
import regionmask

D = np.arange(1, 366.0)
MID = np.array([15.5, 45, 74.5, 105, 135.5, 166, 196.5, 227.5, 258, 288.5, 319, 349.5])
import sys
# optional: <monthly 1-deg file> <its first year> <y0> <y1> <tag> -> climatology of y0..y1 from that product,
# output eos_daylength_percell_<tag>.txt (no arguments = original GIMMS 1982-2010 climatology)
if len(sys.argv) == 6:
    fn, fy, A, B, TAG = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    g = nc.Dataset(fn)
    name = [v for v in g.variables if g.variables[v].ndim == 3][0]
    x = np.ma.filled(g[name][(A - fy) * 12:(B - fy + 1) * 12].astype("f8"), np.nan)
    x[np.abs(x) > 100] = np.nan
    clim = x.reshape(B - A + 1, 12, *x.shape[1:]).mean(0)
    SRC = "%s %d-%d" % (TAG, A, B)
else:
    g = nc.Dataset("../data/gimms_lai_clim_1982_2010.nc")
    clim = np.ma.filled(g["clim"][:].astype("f8"), np.nan)
    TAG, SRC = None, "GIMMS LAI4g climatology 1982-2010"
lat = np.asarray(g["lat"][:]); lon = np.asarray(g["lon"][:])
ok = np.isfinite(clim).all(0) & (lat[:, None] > 20) & ((clim.max(0) - clim.min(0)) >= 0.5)

eos = np.full(ok.shape, np.nan); dl = np.full(ok.shape, np.nan)
for i, j in zip(*np.where(ok)):
    m = clim[:, i, j]
    c = np.interp(D, np.r_[MID[-1] - 365, MID, MID[0] + 365], np.r_[m[-1], m, m[0]])
    thr = c.min() + 0.5 * (c.max() - c.min()); ip = int(c.argmax())
    dn = [k for k in range(ip, 364) if c[k] >= thr > c[k + 1]]
    if not dn:
        continue
    k = dn[0]; e = D[k] + (c[k] - thr) / (c[k] - c[k + 1])
    decl = np.radians(23.44) * np.sin(2 * np.pi * (284 + e) / 365)
    eos[i, j] = e; dl[i, j] = 24 / np.pi * np.arccos(np.clip(-np.tan(np.radians(lat[i])) * np.tan(decl), -1, 1))

W = np.cos(np.radians(lat))[:, None] * np.ones((1, lon.size))
ar6 = regionmask.defined_regions.ar6.land
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    m3 = ar6.mask_3D(lon, lat)


def stats(mask):
    v = dl[mask & np.isfinite(dl)]; e = eos[mask & np.isfinite(dl)]
    if v.size < 20:
        return None
    q = np.percentile(v, [10, 25, 50, 75, 90])
    return "n %5d | day length at EOS (h): p10 %5.2f p25 %5.2f median %5.2f p75 %5.2f p90 %5.2f | EOS doy median %5.1f" % (v.size, *q, np.median(e))


out = ["Day length on the observed EOS date, cell by cell (%s, 1 deg, cells north of 20N with seasonal amplitude >= 0.5)" % SRC,
       "EOS = 50 %% amplitude crossing after the peak of the climatological curve (monthly means interpolated to days); %d cells" % np.isfinite(dl).sum(), "",
       "AR6 regions"]
for ab in ("NWN", "NEN", "ESB", "RFE", "WSB", "ENA", "WCE", "EEU", "NEU", "EAS"):
    s = stats(m3.sel(region=ar6.map_keys(ab)).values.astype(bool))
    if s:
        out.append("  %-4s %s" % (ab, s))
out += ["", "5-degree latitude bands (all longitudes)"]
for a in range(20, 75, 5):
    s = stats((lat[:, None] >= a) & (lat[:, None] < a + 5) & np.ones_like(ok))
    if s:
        out.append("  %2d-%2dN %s" % (a, a + 5, s))
v = np.isfinite(dl); la = (lat[:, None] * np.ones((1, lon.size)))[v]
p = np.polyfit(la, dl[v], 1)
out += ["", "linear fit over all cells: day length at EOS = %.3f + %.4f x latitude (h)  ->  40N %.2f h, 50N %.2f h, 60N %.2f h, 70N %.2f h"
        % (p[1], p[0], *(p[1] + p[0] * x for x in (40, 50, 60, 70))),
        "for comparison Birch et al. 2021 (CLM5): 11 h at 45N rising linearly to 15 h at 65N"]
open("../data/eos_daylength_percell%s.txt" % ("_" + TAG if TAG else ""), "w").write("\n".join(out) + "\n")
print("\n".join(out[3:]))
