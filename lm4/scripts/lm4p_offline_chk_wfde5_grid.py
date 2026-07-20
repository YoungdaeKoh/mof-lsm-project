"""Grid-safety check on WFDE5 forcing before wiring it into FMS data_override.

Question that matters for Route B: data_override interpolates the 0.5x0.5 source
onto C96 with "bilinear". If WFDE5 is land-only (ocean = _FillValue), bilinear
stencils near coasts mix fill values into land cells. Quantify the exposure.
"""
import numpy as np
import netCDF4 as nc

F = "/data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM_WFDE5/1981_wfde5.nc"
d = nc.Dataset(F)

# CLM forcing format: 2D LATIXY/LONGXY only, no 1D coordinate variables.
# FMS data_override needs CF 1D lat/lon with units to interpolate -> must rewrite.
print("1D coord vars present:", [v for v in ("lat", "lon") if v in d.variables])
lat = d.variables["LATIXY"][:, 0]
lon = d.variables["LONGXY"][0, :]
print("lat: n=%d  %.4f -> %.4f  (%s)" % (
    len(lat), lat[0], lat[-1], "ascending" if lat[1] > lat[0] else "DESCENDING"))
print("lon: n=%d  %.4f -> %.4f  (%s)" % (
    len(lon), lon[0], lon[-1], "0-360" if lon.max() > 180 else "-180-180"))

for v in ["TBOT", "PRECTmms", "FSDS"]:
    a = d.variables[v][0, :, :]
    m = np.ma.getmaskarray(a)
    valid = (~m).sum()
    print("\n%s  units=%s" % (v, d.variables[v].units))
    print("  valid cells %d / %d  (%.1f%% = land fraction)" % (
        valid, m.size, 100.0 * valid / m.size))
    if valid:
        print("  min=%.4g  max=%.4g  mean=%.4g" % (a.min(), a.max(), a.mean()))

# Coastal exposure: land cells with >=1 masked neighbour in the 4-neighbourhood.
# These are exactly the cells a bilinear stencil can contaminate.
a = d.variables["TBOT"][0, :, :]
land = ~np.ma.getmaskarray(a)
nb_missing = np.zeros_like(land, dtype=int)
for ax, sh in ((0, 1), (0, -1), (1, 1), (1, -1)):
    nb_missing += (~np.roll(land, sh, axis=ax)).astype(int)
coastal = land & (nb_missing > 0)
print("\nland cells        : %d" % land.sum())
print("coastal land cells: %d  (%.1f%% of land)" % (
    coastal.sum(), 100.0 * coastal.sum() / land.sum()))
print("\ntime: n=%d  units=%s  calendar=%s" % (
    len(d.variables["time"]), d.variables["time"].units,
    d.variables["time"].calendar))
d.close()
