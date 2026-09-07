"""Extend the AMIP sea-ice and SST boundary files past 2022 with a climatology.

The production run died in December 2022 because the PCMDI AMIP boundary files
(1870-01 to 2022-12) ran out while the coupler still had do_ice=.true. and was
asking data_override for a sea-ice concentration one hour past the last record.

The values themselves do not matter here.  This is a land-only configuration --
do_atmos=.false., the land is forced directly from WFDE5 through data_table --
so sea ice and SST live on ocean cells and never reach the land.  The evidence
is in the forcing-transfer check (NOTES 13.42): temperature, humidity, shortwave
and precipitation arrive at the land identical to WFDE5, r = 1.00000, which they
could not do if the ocean state were feeding back.  The same configuration
already prescribes sea-ice thickness as a bare constant of 2.0 m in data_table
for exactly this reason.

So the extension is a placeholder that keeps the coupler fed: the 2013-2022
mean for each calendar month, repeated through 2025.  Ten years is long enough
to average out individual years and short enough to sit near the present state.

The originals are symlinks into the KIOST-ESM2_AMIP case and are never touched.
New files are written under lm4/INPUT_amip_ext with the end year in the name, so
that `ls -l INPUT` in the run directory shows what is actually being read.

Note on the values: these are "bcs" fields, mid-month adjusted so that linear
interpolation reproduces the observed monthly mean, which is why the sea-ice
percentages run outside 0-100.  Averaging the adjusted values keeps that
property approximately, and exactly enough for a field nothing reads.

Run on climate00.
"""
import os
import numpy as np
import netCDF4 as nc

SRC = "/home/ydkoh/KIOST-ESM2_AMIP/INPUT"
DST = "/data2/ydkoh/lm4/INPUT_amip_ext"
FILES = [("amipbc_sic_PCMDI-AMIP-1-1-10.nc", "siconcbcs"),
         ("amipbc_sst_PCMDI-AMIP-1-1-10.nc", "tosbcs")]
CLIM = (2013, 2022)          # years averaged, by calendar month
END_YEAR = 2025              # extend through December of this year

os.makedirs(DST, exist_ok=True)

for fname, var in FILES:
    src = os.path.join(SRC, fname)
    out = os.path.join(DST, fname.replace(".nc", "_ext%d.nc" % END_YEAR))
    print("\n=== %s -> %s" % (fname, os.path.basename(out)))

    d = nc.Dataset(src)
    tv = d.variables["time"]
    units, cal = tv.units, tv.calendar
    dates = nc.num2date(tv[:], units, calendar=cal)
    years = np.array([x.year for x in dates])
    months = np.array([x.month for x in dates])
    last = dates[-1]
    print("  source: %d records, %s .. %s"
          % (len(dates), dates[0].strftime("%Y-%m"), last.strftime("%Y-%m")))

    # monthly climatology over CLIM, from the adjusted values themselves
    sel = (years >= CLIM[0]) & (years <= CLIM[1])
    clim = np.stack([np.ma.filled(d.variables[var][(months == m) & sel]
                                  .astype("f8"), np.nan).mean(axis=0)
                     for m in range(1, 13)])
    print("  climatology %d-%d: %d years, range %.2f .. %.2f"
          % (CLIM[0], CLIM[1], sel.sum() // 12,
             np.nanmin(clim), np.nanmax(clim)))

    # months to add: everything after the last record through END_YEAR-12
    add = [(y, m) for y in range(last.year, END_YEAR + 1)
           for m in range(1, 13)
           if (y, m) > (last.year, last.month)]
    print("  appending %d months: %04d-%02d .. %04d-%02d"
          % (len(add), add[0][0], add[0][1], add[-1][0], add[-1][1]))

    # copy the file, then append along the unlimited time axis
    o = nc.Dataset(out, "w", format="NETCDF4_CLASSIC")
    for name, dim in d.dimensions.items():
        o.createDimension(name, None if dim.isunlimited() else len(dim))
    for name, v in d.variables.items():
        nv = o.createVariable(name, v.dtype, v.dimensions,
                              zlib=True, complevel=1,
                              fill_value=getattr(v, "_FillValue", None))
        for a in v.ncattrs():
            if a != "_FillValue":
                nv.setncattr(a, getattr(v, a))
        if "time" not in v.dimensions:
            nv[:] = v[:]
    for a in d.ncattrs():
        o.setncattr(a, getattr(d, a))
    o.setncattr("history_extension",
                "months after %s are the %d-%d climatology for that calendar "
                "month; land-only run, these fields do not reach the land"
                % (last.strftime("%Y-%m"), CLIM[0], CLIM[1]))

    n = len(dates)
    # copy the existing time-varying records in blocks, to keep memory sane
    for v in ("time", "time_bnds", var):
        src_v, dst_v = d.variables[v], o.variables[v]
        for i0 in range(0, n, 120):
            dst_v[i0:min(i0 + 120, n)] = src_v[i0:min(i0 + 120, n)]

    # append: time is the exact midpoint of the month bounds, as in the source
    for k, (y, m) in enumerate(add):
        import datetime as _dt
        b0 = nc.date2num(_dt.datetime(y, m, 1), units, calendar=cal)
        ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
        b1 = nc.date2num(_dt.datetime(ny, nm, 1), units, calendar=cal)
        o.variables["time_bnds"][n + k, :] = [b0, b1]
        o.variables["time"][n + k] = 0.5 * (b0 + b1)
        o.variables[var][n + k] = clim[m - 1]
    o.close()
    d.close()

    # verify what was written
    c = nc.Dataset(out)
    tv = c.variables["time"]
    dd = nc.num2date(tv[:], tv.units, calendar=tv.calendar)
    print("  written: %d records, %s .. %s  (%.1f MB)"
          % (len(dd), dd[0].strftime("%Y-%m"), dd[-1].strftime("%Y-%m"),
             os.path.getsize(out) / 1e6))
    a_old = np.ma.filled(c.variables[var][n - 1].astype("f8"), np.nan)
    a_new = np.ma.filled(c.variables[var][-1].astype("f8"), np.nan)
    print("  last original month mean %.3f   last appended month mean %.3f"
          % (np.nanmean(a_old), np.nanmean(a_new)))
    c.close()
