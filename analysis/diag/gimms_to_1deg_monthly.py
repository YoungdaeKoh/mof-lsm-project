"""Aggregate GIMMS LAI4g (0.5 deg monthly) onto a common 1 deg grid.

Prepares the observational half of the LMWG-style comparison so that the model
side only has to be binned to the same grid. Output keeps every month
(1982-01..2020-12) rather than a fixed climatology, so any period can be
selected later.

Grid notes (verified 2026-07-30, see LM4_SPINUP_NOTES 13.23):
  - source latitude is ASCENDING, 361 points from -90 to +90 inclusive, i.e.
    points ON the poles. That is not 180x2, so a reshape would silently
    mis-align; each source point is binned by its own coordinate instead.
  - source longitude is 0..359.5. The target grid uses -179.5..179.5 to match
    analysis/diag/lai_metrics_1deg.py, so longitudes above 180 are shifted.
  - _FillValue is 65535; values above 100 are treated as missing.

Output: /Volumes/data02/LAI/derived/gimms_lai4g_1deg_monthly_1982_2020.npz
  lai   (nmonth, 180, 360) float32, NaN where no valid source cell
  lat   (180,)  cell centres -89.5 .. 89.5
  lon   (360,)  cell centres -179.5 .. 179.5
  year, month (nmonth,)
"""
import os
import numpy as np
import netCDF4 as nc

SRC = "/Volumes/data02/LAI/GIMMS_LAI4g_V1.2_1982_2020.nc"
OUTDIR = "/Volumes/data02/LAI/derived"
OUT = os.path.join(OUTDIR, "gimms_lai4g_1deg_monthly_1982_2020.npz")

lat1 = np.arange(-89.5, 90.0, 1.0)      # 180
lon1 = np.arange(-179.5, 180.0, 1.0)    # 360


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    d = nc.Dataset(SRC)
    slat = d.variables["latitude"][:].astype("f8")
    slon = d.variables["longitude"][:].astype("f8")
    tvar = d.variables["time"]
    dts = nc.num2date(tvar[:], tvar.units,
                      calendar=getattr(tvar, "calendar", "standard"))
    nt = len(dts)

    # bin index per source point, from the coordinate itself
    slon180 = np.where(slon > 180.0, slon - 360.0, slon)
    ilat = np.clip(np.floor(slat + 90.0).astype(int), 0, 179)
    ilon = np.clip(np.floor(slon180 + 180.0).astype(int), 0, 359)
    print("source %d x %d -> target %d x %d" % (len(slat), len(slon), 180, 360))
    print("lat bins used: %d..%d   lon bins used: %d..%d"
          % (ilat.min(), ilat.max(), ilon.min(), ilon.max()))

    # flat index for np.add.at, built once
    IJ = (ilat[:, None] * 360 + ilon[None, :]).ravel()

    out = np.full((nt, 180 * 360), np.nan, dtype="f4")
    for k in range(nt):
        a = np.ma.filled(d.variables["lai"][k].astype("f8"), np.nan)
        a[a > 100.0] = np.nan                      # _FillValue 65535 and friends
        good = np.isfinite(a).ravel()
        s = np.zeros(180 * 360)
        c = np.zeros(180 * 360)
        np.add.at(s, IJ[good], a.ravel()[good])
        np.add.at(c, IJ[good], 1.0)
        m = c > 0
        row = np.full(180 * 360, np.nan)
        row[m] = s[m] / c[m]
        out[k] = row.astype("f4")
        if k % 60 == 0 or k == nt - 1:
            print("  %s  valid 1deg cells=%5d  mean=%.3f"
                  % (dts[k].strftime("%Y-%m"), m.sum(), np.nanmean(row)))
    d.close()

    lai = out.reshape(nt, 180, 360)
    year = np.array([x.year for x in dts])
    month = np.array([x.month for x in dts])
    np.savez_compressed(OUT, lai=lai, lat=lat1, lon=lon1, year=year, month=month)
    print("\nwrote %s  (%.1f MB)" % (OUT, os.path.getsize(OUT) / 1e6))

    # sanity: seasonal contrast should flip between hemispheres
    nh = (lat1 > 30) & (lat1 < 70)
    sh = (lat1 < -10) & (lat1 > -40)
    for name, sel in (("NH 30-70N", nh), ("SH 10-40S", sh)):
        jja = np.nanmean(lai[np.isin(month, [6, 7, 8])][:, sel, :])
        djf = np.nanmean(lai[np.isin(month, [12, 1, 2])][:, sel, :])
        print("%-10s JJA=%.3f  DJF=%.3f  (JJA-DJF=%+.3f)"
              % (name, jja, djf, jja - djf))


if __name__ == "__main__":
    main()
