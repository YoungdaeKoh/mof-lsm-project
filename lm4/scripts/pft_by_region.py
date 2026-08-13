"""Which species is producing the leaf area, region by region.

Southern South America carries a bias of +4.5 LAI against GIMMS -- 6.1 where the
observation says 1.6 -- and the residual after removing the model's general
tendency to over-green sparse vegetation is +3.5, five times any other region.
A grassland that the model has turned into forest would look exactly like that,
so the question is which species holds the canopy there.

Reported next to two controls: the Amazon, where the model is only ~30 % high and
should be tropical evergreen, and Siberia, where the model is closer to the
observation than its own global relationship predicts.

Species order is the field_table order (7 species):
  1 default  2 prioria (tropical evergreen)  3 picea (boreal evergreen needle)
  4 larix (boreal deciduous needle)  5 acer (temperate deciduous broadleaf)
  6 c4grass  7 c3grass

Run on climate00.  Output: /data2/ydkoh/lm4/pft_by_region.csv
"""
import numpy as np
from netCDF4 import Dataset

ARC = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive_c1"
GRID = "/data2/ydkoh/lm4/RUN/lm4_spinup30/INPUT/C96_grid.tile%d.nc"
STATIC = ARC + "/y1990/19900101.land_static.tile%d.nc"
YEAR = 2010
NX, FILL = 96, 1e19
SPECIES = ["default", "prioria", "picea", "larix", "acer", "c4grass", "c3grass"]
REGIONS = [("Amazon", (-10, 5, -70, -50)),
           ("S.SouthAmerica", (-35, -20, -65, -45)),
           ("Siberia", (55, 70, 60, 140))]

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
lon = np.concatenate(lon_all)
lon = np.where(lon > 180, lon - 360, lon)


def read(var):
    """(species, point) annual mean, species-summed quantities kept per species."""
    per_tile = []
    for t in range(1, 7):
        d = Dataset("%s/y%d/%d0101.land_month_by_species.tile%d.nc"
                    % (ARC, YEAR, YEAR, t))
        a = np.ma.filled(d.variables[var][:].astype("f8"), np.nan)
        a[np.abs(a) > FILL] = np.nan
        a[a < 0] = np.nan                      # _FillValue is -1 in this stream
        d.close()
        per_tile.append(np.nanmean(a, axis=0))  # mean over months -> (species, pt)
    return np.concatenate(per_tile, axis=1)


lai = read("lai")
nind = read("nindivs")
hgt = read("height_ave")
print("species x points:", lai.shape)

rows = []
for name, (la0, la1, lo0, lo1) in REGIONS:
    s = (lat >= la0) & (lat < la1) & (lon >= lo0) & (lon < lo1)
    tot = np.nansum(np.where(np.isfinite(lai[:, s]), lai[:, s], 0.0), axis=0)
    print("\n=== %s   %d points   total LAI %.3f ===" % (name, s.sum(), np.nanmean(tot)))
    print("%-10s %9s %8s %11s %10s" % ("species", "LAI", "% of LAI", "indiv/m2", "height m"))
    for k, sp in enumerate(SPECIES):
        v = np.nanmean(lai[k, s])
        if not np.isfinite(v) or v < 1e-4:
            continue
        share = 100 * v / np.nanmean(tot)
        print("%-10s %9.3f %7.1f%% %11.4g %10.2f"
              % (sp, v, share, np.nanmean(nind[k, s]), np.nanmean(hgt[k, s])))
        rows.append([name, sp, v, share, np.nanmean(nind[k, s]), np.nanmean(hgt[k, s])])

with open("/data2/ydkoh/lm4/pft_by_region.csv", "w") as f:
    f.write("region,species,lai,share_pct,nindivs,height_m\n")
    for r in rows:
        f.write("%s,%s,%.5f,%.2f,%.6g,%.3f\n" % tuple(r))
print("\nwrote /data2/ydkoh/lm4/pft_by_region.csv")
