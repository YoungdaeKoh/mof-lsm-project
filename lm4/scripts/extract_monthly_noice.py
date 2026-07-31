"""Monthly global land-mean, ice sheets removed, for every archived LM4 year.

Mask, built once and applied to every variable:
  soil_area > 0          -- drops Antarctica outright (0 points south of 60S)
  minus Greenland itself -- the Natural Earth outline, not a lat/lon box.  The
                            box used first (lat>59, 73W..11W) reached across
                            Baffin Bay and removed 87 Canadian Arctic points;
                            the outline also makes the Iceland exception
                            unnecessary.  See greenland_mask.py

Needed because lai/water_soil/tot_soil_C ride on soil_area while
snow/runf/evap_land ride on land_area, so an unmasked figure averages the water
panels over a different land than the carbon panels.  The offline model has no
glacier dynamics, so those columns only accumulate.

y1990 is read from the re-run (12 months); every other year has Jan-Nov.
"""
import glob
import os
import numpy as np
from netCDF4 import Dataset
from netCDF4 import num2date
from greenland_mask import in_greenland

MAIN = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive"
RERUN = "/data2/ydkoh/lm4/RERUN/wA/archive"
TILES = [1, 2, 3, 4, 5, 6]
FILL = 1e30
OUT = "/data2/ydkoh/lm4/monthly_noice_16yr.csv"

VARS = {
    "runoff":    ("runf", None),
    "baseflow":  ("soil_rbf", None),
    "LAI":       ("lai", None),
    "GPP":       ("gpp", None),
    "NPP":       ("npp", None),
    "NEP":       ("nep", None),
    "evap":      ("evap_land", None),
    "sens":      ("sens", None),
    "theta_sfc": ("theta_sfc", None),
    "col_water": ("water_soil", None),
    "SWE":       ("snow", None),
    "soilC":     ("tot_soil_C", None),
    "bwood":     ("bwood", None),
    "soilT_2m":  ("soil_T", 12),
}

years = sorted(int(os.path.basename(d)[1:]) for d in glob.glob(MAIN + "/y[0-9]*"))

MASK = {}
ngrn = 0
for t in TILES:
    d = Dataset("%s/y1990/19900101.land_month.tile%d.nc" % (RERUN, t))
    a = np.ma.filled(d.variables["lai"][0].astype("f8"), np.nan)
    a[np.abs(a) > FILL] = np.nan
    soil = np.isfinite(a)
    lat = np.array(d.variables["geolat_t"][:])
    lon = np.array(d.variables["geolon_t"][:])
    d.close()
    grn = in_greenland(lat, lon)
    ngrn += (soil & grn).sum()
    MASK[t] = soil & ~grn
print("non-ice land points: %d   (Greenland cut removed %d)"
      % (sum(m.sum() for m in MASK.values()), ngrn))

rows = []
for y in years:
    root = RERUN if y == 1990 else MAIN
    acc = {k: [None, None] for k in VARS}
    months = None
    for t in TILES:
        f = "%s/y%d/%d0101.land_month.tile%d.nc" % (root, y, y, t)
        d = Dataset(f)
        tv = d.variables["time"]
        months = np.array([x.month for x in
                           num2date(tv[:], tv.units,
                                    getattr(tv, "calendar", "noleap"))])
        for k, (var, layer) in VARS.items():
            a = np.ma.filled(d.variables[var][:].astype("f8"), np.nan)
            a[np.abs(a) > FILL] = np.nan
            if layer is not None:
                a = a[:, layer, :]
            a = np.where(MASK[t][None, :], a, np.nan)
            s = np.nansum(a, axis=1)
            c = np.sum(np.isfinite(a), axis=1).astype("f8")
            acc[k][0] = s if acc[k][0] is None else acc[k][0] + s
            acc[k][1] = c if acc[k][1] is None else acc[k][1] + c
        d.close()
    for i, m in enumerate(months):
        rows.append([y, m] + [acc[k][0][i] / acc[k][1][i] for k in VARS])

np.savetxt(OUT, np.array(rows), delimiter=",",
           header="year,month," + ",".join(VARS), comments="", fmt="%.8f")
print("wrote %s (%d rows, %d years)" % (OUT, len(rows), len(years)))
