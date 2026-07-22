"""Global land-mean monthly time series from the LM4 spin-up (1981-1982).

C96 is quasi-equal-area and land_area is zero in this diag, so an unweighted
cell mean over land points is used (see the land-mean comparability note). Each
year file holds 12 monthly records; concatenate y1981 + y1982 -> 24 months.

Emits a CSV of global land means, one row per month.
"""
import numpy as np
import netCDF4 as nc

ARCH = "/data2/ydkoh/lm4/RUN/lm4_spinup30/archive"
YEARS = [1981, 1982]
TILES = [1, 2, 3, 4, 5, 6]

# name -> (variable, layer_index or None for 2D). Chosen for spin-up + the
# quantities the project cares about (runoff, LAI, soil water, fluxes, carbon).
VARS = {
    "runoff":     ("frunf", None),      # liquid runoff, kg/m2/s
    "LAI":        ("lai", None),
    "GPP":        ("gpp", None),
    "NPP":        ("npp", None),
    "NEP":        ("nep", None),
    "evap":       ("evap_land", None),  # total land evap, kg/m2/s
    "sens":       ("sens", None),       # sensible heat, W/m2
    "soilT_2m":   ("soil_T", 12),       # ~2 m soil temperature (zfull idx 12)
    "theta_sfc":  ("theta_sfc", None),  # surface soil moisture, m3/m3
    "col_water":  ("water_soil", None), # column soil water, kg/m2
    "SWE":        ("snow", None),       # snow water equivalent, kg/m2
    "soilC":      ("tot_soil_C", None), # total soil carbon, kg C/m2
    "bwood":      ("bwood", None),      # wood biomass, kg C/m2
}

FILL = 1e30


def series(var, layer):
    rows = []
    for y in YEARS:
        tot = None
        cnt = None
        for t in TILES:
            f = "%s/y%d/%d0101.land_month.tile%d.nc" % (ARCH, y, y, t)
            d = nc.Dataset(f)
            if var not in d.variables:
                d.close()
                return None
            a = np.ma.filled(d.variables[var][:].astype("f8"), np.nan)
            a[np.abs(a) > FILL] = np.nan
            if layer is not None:
                a = a[:, layer, :]
            s = np.nansum(a, axis=1)
            c = np.sum(np.isfinite(a), axis=1).astype("f8")
            tot = s if tot is None else tot + s
            cnt = c if cnt is None else cnt + c
            d.close()
        rows.append(tot / np.where(cnt > 0, cnt, np.nan))
    return np.concatenate(rows)


cols = {}
for name, (var, layer) in VARS.items():
    v = series(var, layer)
    if v is not None:
        cols[name] = v
        print("%-10s months=%d  mean=%.4g  range=[%.4g, %.4g]" % (
            name, len(v), np.nanmean(v), np.nanmin(v), np.nanmax(v)))
    else:
        print("%-10s MISSING" % name)

nm = len(next(iter(cols.values())))
months = np.arange(1, nm + 1)
hdr = "month," + ",".join(cols.keys())
data = np.column_stack([months] + [cols[k] for k in cols])
np.savetxt("/data2/ydkoh/lm4/RUN/lm4_spinup30/monthly_1981_1982.csv",
           data, delimiter=",", header=hdr, comments="")
print("\nwrote monthly_1981_1982.csv  (%d months x %d vars)" % (nm, len(cols)))
