"""Is the grass layer at its ceiling, or is something limiting it?

C4 grass carries LAI 3.07 in the Amazon and 3.10 in southern South America --
the same number under a closed 14 m canopy as in open subtropical grassland.
Light competition should not allow that, so either the grass is not being shaded
or it is not being limited at all and simply grows to whatever maximum leaf
biomass its allometry allows.

bl_max is that maximum.  If LAI/bl_max sits near its ceiling everywhere, the
grass layer is allometry-limited rather than resource-limited, and the
over-greening of sparse vegetation is a parameter problem rather than a regional
one.  If the ratio varies with climate, something is limiting it and the
question moves elsewhere.

w_scale is carried alongside: it is the model's own water-stress multiplier, so
if the grass in a dry region is unstressed the water limitation is not biting.

Run on climate00.  Output: /data2/ydkoh/lm4/grass_blmax.csv
"""
import numpy as np
from netCDF4 import Dataset

ARC = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive_c1"
GRID = "/data2/ydkoh/lm4/RUN/lm4_spinup30/INPUT/C96_grid.tile%d.nc"
STATIC = ARC + "/y1990/19900101.land_static.tile%d.nc"
YEAR, NX = 2010, 96
KGRASS = 5          # zero-based index of C4 grass (field_table position 6)
KTREE = 0           # zero-based index of the tropical broadleaf (position 1)
REGIONS = [("Amazon", (-10, 5, -70, -50)),
           ("S.SouthAmerica", (-35, -20, -65, -45)),
           ("Australia", (-35, -15, 115, 150)),
           ("Sahel", (10, 18, -15, 35)),
           ("Siberia", (55, 70, 60, 140)),
           ("East Asia", (20, 50, 100, 145))]

lat_all, lon_all = [], []
for t in range(1, 7):
    st = Dataset(STATIC % t)
    gi = st.variables["grid_index"][:].astype(int)
    st.close()
    g = Dataset(GRID % t)
    X, Y = g.variables["x"][:], g.variables["y"][:]
    g.close()
    j, i = gi // NX, gi % NX
    lat_all.append(Y[1::2, 1::2][j, i])
    lon_all.append(X[1::2, 1::2][j, i])
lat = np.concatenate(lat_all)
lon = np.where(np.concatenate(lon_all) > 180,
               np.concatenate(lon_all) - 360, np.concatenate(lon_all))


def read(var, k):
    per = []
    for t in range(1, 7):
        d = Dataset("%s/y%d/%d0101.land_month_by_species.tile%d.nc"
                    % (ARC, YEAR, YEAR, t))
        a = np.ma.filled(d.variables[var][:, k, :].astype("f8"), np.nan)
        a[a < 0] = np.nan
        d.close()
        per.append(a)
    return np.concatenate(per, axis=1)          # (month, point)


# leafarea is the grass canopy's own leaf area; lai is its contribution to the
# cell.  bl_max is a biomass ceiling, so compare it against leaf biomass bl.
lai_g = read("lai", KGRASS)
blmax = read("bl_max", KGRASS)
wsc = read("w_scale", KGRASS)
lai_t = read("lai", KTREE)
print("months x points:", lai_g.shape)

# annual maximum of the grass canopy, the month it is actually at its fullest
gmax = np.nanmax(lai_g, axis=0)
bmax = np.nanmean(blmax, axis=0)
wmin = np.nanmin(wsc, axis=0)
tmean = np.nanmean(lai_t, axis=0)

print("\n%-16s %6s %8s %8s %9s %9s %9s" %
      ("region", "cells", "grassLAI", "bl_max", "LAI/blmax", "w_scale", "treeLAI"))
rows = []
for name, (la0, la1, lo0, lo1) in REGIONS:
    s = ((lat >= la0) & (lat < la1) & (lon >= lo0) & (lon < lo1)
         & np.isfinite(gmax) & (gmax > 0.01))
    if s.sum() < 20:
        continue
    r = gmax[s] / bmax[s]
    print("%-16s %6d %8.3f %8.3f %9.3f %9.3f %9.3f"
          % (name, s.sum(), np.nanmean(gmax[s]), np.nanmean(bmax[s]),
             np.nanmean(r), np.nanmean(wmin[s]), np.nanmean(tmean[s])))
    rows.append([name, s.sum(), np.nanmean(gmax[s]), np.nanmean(bmax[s]),
                 np.nanmean(r), np.nanmean(wmin[s]), np.nanmean(tmean[s])])

ok = np.isfinite(gmax) & np.isfinite(bmax) & (gmax > 0.01)
r = gmax[ok] / bmax[ok]
print("\nglobal grass LAI/bl_max: p10 %.3f  p50 %.3f  p90 %.3f  (n=%d)"
      % (*np.percentile(r, [10, 50, 90]), ok.sum()))
print("global grass w_scale (annual minimum): p10 %.3f  p50 %.3f  p90 %.3f"
      % tuple(np.percentile(wmin[ok][np.isfinite(wmin[ok])], [10, 50, 90])))

with open("/data2/ydkoh/lm4/grass_blmax.csv", "w") as f:
    f.write("region,cells,grass_lai_max,bl_max,ratio,w_scale_min,tree_lai\n")
    for x in rows:
        f.write("%s,%d,%.5f,%.5f,%.5f,%.5f,%.5f\n" % tuple(x))
print("wrote /data2/ydkoh/lm4/grass_blmax.csv")
