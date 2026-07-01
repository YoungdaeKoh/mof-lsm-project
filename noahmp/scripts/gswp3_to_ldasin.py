#!/usr/bin/env python
# Convert GSWP3 v1 0.5deg (CLM datm) forcing -> HRLDAS LDASIN files.
# One LDASIN file per 3-hourly timestep: YYYYMMDDHHMM.LDASIN_DOMAIN1
# Units already match HRLDAS -> only rename + V2D=0 (GSWP3 has total wind in WIND).
#
# Usage: python gswp3_to_ldasin.py YEAR MONTH OUTDIR [NDAYS]
#   NDAYS optional -> convert only first NDAYS days (testing). Default: whole month.
#
# Run on climate00 in conda base env (has netCDF4). GSWP3 at:
#   /data1/CESM2_INPUT/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v1.c170516
#
# NOTE: GSWP3 calendar is noleap (no Feb 29). Filenames here step on real calendar,
#       which is identical to noleap within any non-February month. For long cycling
#       spin-up crossing Feb 29, handle the leap-day gap separately.
import sys, os
from datetime import datetime, timedelta
import numpy as np
from netCDF4 import Dataset

GSWP3_DIR = "/data1/CESM2_INPUT/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v1.c170516"
TOKEN = {"TPHWL": "TPQWL", "Solar": "Solr", "Precip": "Prec"}

# (LDASIN name, subdir, GSWP3 var, units, description)
MAP = [
    ("T2D",      "TPHWL",  "TBOT",     "K",     "temperature"),
    ("Q2D",      "TPHWL",  "QBOT",     "kg/kg", "specific humidity"),
    ("U2D",      "TPHWL",  "WIND",     "m/s",   "zonal wind"),
    ("PSFC",     "TPHWL",  "PSRF",     "Pa",    "surface pressure"),
    ("LWDOWN",   "TPHWL",  "FLDS",     "W/m2",  "downward longwave radiation"),
    ("SWDOWN",   "Solar",  "FSDS",     "W/m2",  "downward shortwave radiation"),
    ("RAINRATE", "Precip", "PRECTmms", "mm/s",  "rain rate"),
]


def srcfile(sub, year, month):
    return os.path.join(GSWP3_DIR, sub,
                        "clmforc.GSWP3.c2011.0.5x0.5.%s.%04d-%02d.nc" % (TOKEN[sub], year, month))


def main():
    year, month, outdir = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    ndays = int(sys.argv[4]) if len(sys.argv) > 4 else None
    os.makedirs(outdir, exist_ok=True)

    files = {sub: Dataset(srcfile(sub, year, month)) for sub in TOKEN}
    nt = files["TPHWL"].dimensions["time"].size
    nlat = files["TPHWL"].dimensions["lat"].size
    nlon = files["TPHWL"].dimensions["lon"].size
    nmax = nt if ndays is None else min(nt, ndays * 8)

    start = datetime(year, month, 1, 0, 0)
    for t in range(nmax):
        dt = start + timedelta(hours=3 * t)
        out = os.path.join(outdir, dt.strftime("%Y%m%d%H") + ".LDASIN_DOMAIN1")
        o = Dataset(out, "w", format="NETCDF4")
        o.createDimension("west_east", nlon)
        o.createDimension("south_north", nlat)
        o.createDimension("Time", None)
        for ld, sub, gv, units, desc in MAP:
            v = o.createVariable(ld, "f4", ("Time", "south_north", "west_east"),
                                 zlib=True, complevel=1)
            v.description = desc
            v.units = units
            v[0, :, :] = files[sub].variables[gv][t, :, :]
        v2 = o.createVariable("V2D", "f4", ("Time", "south_north", "west_east"),
                              zlib=True, complevel=1)
        v2.description = "meridional wind"
        v2.units = "m/s"
        v2[0, :, :] = 0.0
        o.TITLE = "Created from GSWP3 v1 0.5deg (clmforc.GSWP3.c2011) by gswp3_to_ldasin.py"
        o.close()

    for ds in files.values():
        ds.close()
    print("wrote %d LDASIN files (%dx%d grid) to %s" % (nmax, nlat, nlon, outdir))


if __name__ == "__main__":
    main()
