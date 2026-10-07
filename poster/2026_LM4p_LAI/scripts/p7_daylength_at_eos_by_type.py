#!/usr/bin/env python3
"""Day length at the observed EOS, split by dominant vegetation type (and latitude band).

Cells: 1 deg, north of 20N, GIMMS LAI4g 1982-2010 climatology with seasonal amplitude >= 0.5
(same EOS and day-length calculation as p6_daylength_at_eos_percell.py).
Vegetation type: CLM5 surface dataset PFT fractions (../data/clm5_surfdata_pft_0.9x1.25_simyr2000.nc,
nearest cell), grouped into evergreen needleleaf, deciduous needleleaf (larch), deciduous broadleaf,
shrub, C3 grass, crop; a cell counts for a type when that type covers >= 50 % of its vegetated area.
Output: ../data/eos_daylength_by_type.txt
"""
import numpy as np
import netCDF4 as nc

D = np.arange(1, 366.0)
MID = np.array([15.5, 45, 74.5, 105, 135.5, 166, 196.5, 227.5, 258, 288.5, 319, 349.5])
g = nc.Dataset("../data/gimms_lai_clim_1982_2010.nc")
clim = np.ma.filled(g["clim"][:].astype("f8"), np.nan)
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

# CLM5 PFT groups, nearest cell onto the 1-deg grid
c = nc.Dataset("../data/clm5_surfdata_pft_0.9x1.25_simyr2000.nc")
p = np.asarray(c["pct_pft"][:], "f8"); crop = np.asarray(c["pct_crop"][:], "f8")
clat = np.asarray(c["lat"][:]); clon = np.asarray(c["lon"][:])
ii = np.abs(clat[:, None] - lat[None, :]).argmin(0)
jj = np.abs(((clon[:, None] - (lon[None, :] % 360) + 180) % 360 - 180)).argmin(0)
groups = [("evergreen needleleaf (picea)", [1, 2]), ("deciduous needleleaf / larch (larix)", [3]),
          ("deciduous broadleaf (acer)", [6, 7, 8]), ("shrub", [9, 10, 11]), ("C3 grass incl. arctic (c3grass)", [12, 13]), ("crop", None)]
veg = p[1:].sum(0) + crop
share = {}
for name, ks in groups:
    x = crop if ks is None else p[ks].sum(0)
    share[name] = (x / np.where(veg > 0, veg, np.nan))[np.ix_(ii, jj)]

out = ["Day length on the observed EOS date by dominant vegetation type (CLM5 PFT >= 50 % of vegetated area), GIMMS 1982-2010 climatology, 1 deg, 20N+",
       "day length (h): median [p25-p75]; EOS = 50 % amplitude; n = cells", ""]
bands = [(20, 40), (40, 50), (50, 60), (60, 72)]
out.append("%-40s %-28s " % ("type", "all cells") + " ".join("%-26s" % ("%d-%dN" % b) for b in bands))
for name, _ in groups:
    sel = (share[name] >= 0.5) & np.isfinite(dl)
    def cell(mask):
        v = dl[mask]
        return "%5.2f [%5.2f-%5.2f] n%5d" % (np.median(v), *np.percentile(v, [25, 75]), v.size) if v.size >= 15 else "%-26s" % "(n<15)"
    row = cell(sel)
    for a, b in bands:
        row += " " + cell(sel & (lat[:, None] >= a) & (lat[:, None] < b))
    out.append("%-40s %s" % (name, row))
out += ["", "same, EOS day of year median by type and band"]
for name, _ in groups:
    sel = (share[name] >= 0.5) & np.isfinite(dl)
    row = " ".join("%-26s" % ("%5.1f n%5d" % (np.median(eos[sel & (lat[:, None] >= a) & (lat[:, None] < b)]), (sel & (lat[:, None] >= a) & (lat[:, None] < b)).sum())
                   if (sel & (lat[:, None] >= a) & (lat[:, None] < b)).sum() >= 15 else "(n<15)") for a, b in bands)
    out.append("%-40s %-28s %s" % (name, "", row))
open("../data/eos_daylength_by_type.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out[3:]))
