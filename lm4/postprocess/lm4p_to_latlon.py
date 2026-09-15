#!/usr/bin/env python3
"""Turn LM4P land output into something you can open in ncview.

LM4P writes its land fields on an unstructured grid: one dimension, `grid_index`,
holding only the land points of one C96 cubed-sphere tile, with no latitude or
longitude attached.  Six such files make a globe.  Nothing standard will plot
that, which is why every analysis so far has had to rebuild the coordinates from
scratch.  This does it once and writes a regular lat-lon netCDF.

Two steps, and the first is the one that goes wrong silently:

1. Recover coordinates.  `grid_index` is a flat index into the tile's 96x96 cell
   array, so cell (j,i) = (gi // 96, gi % 96).  The C96_grid files store a 193x193
   *supergrid* -- corners and midpoints interleaved -- so the centre of cell (j,i)
   is at supergrid [2j+1, 2i+1].  Taking [j,i] straight from the supergrid would
   silently give you cell corners, shifted half a cell, and every map would look
   almost right.

2. Bin to lat-lon.  C96 cells are ~1 degree, so a 1-degree target is close to
   one-to-one and a simple average of the points falling in each cell is honest.
   Cells with no land point stay missing rather than being interpolated into
   existence.

    A WORD ON WHAT THIS IS FOR.  Regridding is for looking and for sharing.  For
    model-observation comparison, do the comparison on the model grid and bring
    the observations to it -- putting both onto some third grid manufactures
    error that is not in either field (see grid-compare-on-model-grid).  This
    file exists so you can see the field, not so you can score it.

Usage:
    python lm4p_to_latlon.py --case /Volumes/data02/LM4P/cases/lm4p_ctl_1979-2024 \
                             --years 1982 2023 --vars lai --res 1.0
    python lm4p_to_latlon.py --list-vars          # what is in a land_month file

Output: <case>/../../postprocess/latlon/<casename>.<var>.<y0>-<y1>.<res>deg.nc
        dims (time, lat, lon), monthly, CF-ish attributes kept from the source.
"""

import argparse
import glob
import os
import sys

import numpy as np
from netCDF4 import Dataset

NX = 96                      # C96: 96x96 cells per tile, 6 tiles
NTILE = 6
GRIDDIR_DEFAULT = "/Volumes/data02/LM4P/postprocess/grid"
FILL = np.float32(1.0e20)


# --------------------------------------------------------------------------
def tile_coords(griddir, tile):
    """Centre lat/lon of every cell in one C96 tile, as flat 96*96 arrays.

    The supergrid is 193x193 = 2*96+1 in each direction: corners at even indices,
    cell centres at odd.  [1::2, 1::2] is the centres.
    """
    path = os.path.join(griddir, "C96_grid.tile%d.nc" % tile)
    with Dataset(path) as g:
        x = np.asarray(g.variables["x"][:])      # lon, degrees east, 0..360
        y = np.asarray(g.variables["y"][:])      # lat, degrees north
    return y[1::2, 1::2].ravel(), x[1::2, 1::2].ravel()


def land_coords(case, year, griddir):
    """lat/lon of every land point, in the order the land files store them."""
    lats, lons = [], []
    for t in range(1, NTILE + 1):
        static = "%s/archive/y%d/%d0101.land_static.tile%d.nc" % (case, year, year, t)
        if not os.path.exists(static):
            raise SystemExit("missing %s\n  (is the transfer finished?)" % static)
        with Dataset(static) as s:
            gi = np.asarray(s.variables["grid_index"][:]).astype(int)
        lat_t, lon_t = tile_coords(griddir, t)
        lats.append(lat_t[gi])
        lons.append(lon_t[gi])
    lat = np.concatenate(lats)
    lon = np.concatenate(lons)
    lon = np.where(lon > 180.0, lon - 360.0, lon)   # 0..360 -> -180..180
    return lat, lon


# --------------------------------------------------------------------------
def read_var(case, year, var):
    """One year of a land_month variable, concatenated over the six tiles.

    Returns (nmonth, npoint).  Raises if a tile is short of twelve months --
    a truncated year is the one thing that would quietly bias an annual mean.
    """
    pieces = []
    for t in range(1, NTILE + 1):
        f = "%s/archive/y%d/%d0101.land_month.tile%d.nc" % (case, year, year, t)
        with Dataset(f) as d:
            if var not in d.variables:
                raise SystemExit("'%s' not in %s\n  try --list-vars" % (var, f))
            v = d.variables[var]
            a = np.ma.filled(v[:].astype("f8"), np.nan)
            if a.shape[0] != 12:
                raise SystemExit("%s has %d months, expected 12" % (f, a.shape[0]))
            attrs = {k: v.getncattr(k) for k in v.ncattrs()
                     if k not in ("_FillValue", "missing_value")}
        pieces.append(a)
    return np.concatenate(pieces, axis=1), attrs


def target_grid(res):
    nlat = int(round(180.0 / res))
    nlon = int(round(360.0 / res))
    lat_c = -90.0 + res * (np.arange(nlat) + 0.5)
    lon_c = -180.0 + res * (np.arange(nlon) + 0.5)
    return lat_c, lon_c


def _xyz(lat, lon):
    """Unit vectors on the sphere, so that 'nearest' means nearest on the globe
    and not nearest in degrees -- the two stop agreeing near the poles, which is
    exactly where this grid needs to behave."""
    la = np.deg2rad(lat); lo = np.deg2rad(lon)
    c = np.cos(la)
    return np.column_stack([c * np.cos(lo), c * np.sin(lo), np.sin(la)])


def regrid(values, lat, lon, res, how="nearest", maxdist_km=120.0):
    """Scattered C96 land points -> regular lat-lon.

    how='bin'      average the points that fall inside each target cell.
                   Honest where the target is coarser than C96, but C96 cells are
                   already about a degree, so at one degree many high-latitude
                   target cells catch no point at all: a 1-degree longitude box
                   shrinks with cos(lat) while a C96 cell does not.  The result
                   is a field that looks fine in the tropics and turns into
                   speckle with holes through the whole boreal forest -- which is
                   the region most of the LAI questions are about.

    how='nearest'  give each target cell the nearest land point on the sphere,
                   and leave it missing if that point is farther than maxdist_km.
                   No holes, no values invented from nothing: every cell carries
                   a real model value, just possibly its neighbour's.  120 km is
                   a little over one C96 cell (~100 km), so ocean stays empty.

    Returns (nmonth, nlat, nlon), lat_c, lon_c.
    """
    lat_c, lon_c = target_grid(res)
    nlat, nlon = lat_c.size, lon_c.size
    nm = values.shape[0]

    if how == "bin":
        jj = np.clip(((lat + 90.0) / res).astype(int), 0, nlat - 1)
        ii = np.clip(((lon + 180.0) / res).astype(int), 0, nlon - 1)
        flat = jj * nlon + ii
        out = np.full((nm, nlat * nlon), np.nan)
        for m in range(nm):
            v = values[m]
            ok = np.isfinite(v)
            tot = np.bincount(flat[ok], weights=v[ok], minlength=nlat * nlon)
            cnt = np.bincount(flat[ok], minlength=nlat * nlon)
            nz = cnt > 0
            out[m, nz] = tot[nz] / cnt[nz]
        return out.reshape(nm, nlat, nlon), lat_c, lon_c

    if how != "nearest":
        raise SystemExit("how must be 'bin' or 'nearest'")

    from scipy.spatial import cKDTree
    tree = cKDTree(_xyz(lat, lon))
    LO, LA = np.meshgrid(lon_c, lat_c)
    # chord length on the unit sphere for the great-circle cutoff
    R = 6371.0
    cutoff = 2.0 * np.sin(0.5 * maxdist_km / R)
    dist, idx = tree.query(_xyz(LA.ravel(), LO.ravel()), k=1)
    far = dist > cutoff

    out = np.empty((nm, nlat * nlon))
    for m in range(nm):
        out[m] = values[m][idx]
        out[m][far] = np.nan
    return out.reshape(nm, nlat, nlon), lat_c, lon_c


# --------------------------------------------------------------------------
def write_nc(path, var, data, lat_c, lon_c, years, attrs, case, res, regrid_note):
    nm = data.shape[0]
    with Dataset(path, "w", format="NETCDF4") as o:
        o.createDimension("time", nm)
        o.createDimension("lat", lat_c.size)
        o.createDimension("lon", lon_c.size)

        # "months since" is only legal with a 360_day calendar under CF, and
        # netCDF4/xarray/CDO refuse to decode it with noleap.  Encode each
        # record as the middle of its month in days, on the noleap calendar
        # the model actually uses.
        mlen = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31], float)
        mstart = np.concatenate(([0.0], np.cumsum(mlen)[:-1]))
        yy, mm = np.divmod(np.arange(nm), 12)
        t = o.createVariable("time", "f8", ("time",))
        t.units = "days since %d-01-01 00:00:00" % years[0]
        t.calendar = "noleap"
        t.long_name = "time"
        t[:] = yy * 365.0 + mstart[mm] + mlen[mm] / 2.0

        la = o.createVariable("lat", "f8", ("lat",))
        la.units = "degrees_north"; la.long_name = "latitude"; la[:] = lat_c
        lo = o.createVariable("lon", "f8", ("lon",))
        lo.units = "degrees_east"; lo.long_name = "longitude"; lo[:] = lon_c

        v = o.createVariable(var, "f4", ("time", "lat", "lon"),
                             zlib=True, complevel=4, fill_value=FILL)
        for k, val in attrs.items():
            try:
                v.setncattr(k, val)
            except Exception:
                pass
        v[:] = np.where(np.isfinite(data), data, FILL).astype("f4")

        o.title = "LM4P %s regridded from C96 land points" % var
        o.source_case = case
        o.regridding = regrid_note
        o.caveat = ("For model-observation comparison use the native C96 output "
                    "and bring observations to it; comparing two fields on a "
                    "third grid invents error that is in neither.")
        o.history = "created by lm4/postprocess/lm4p_to_latlon.py"


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True, help="case dir holding archive/yYYYY/")
    ap.add_argument("--years", nargs=2, type=int, metavar=("Y0", "Y1"))
    ap.add_argument("--vars", nargs="+", default=["lai"])
    ap.add_argument("--res", type=float, default=1.0, help="target degrees")
    ap.add_argument("--how", default="nearest", choices=["nearest", "bin"],
                    help="nearest: no holes (default); bin: cell average, holes at high lat")
    ap.add_argument("--maxdist", type=float, default=120.0,
                    help="km; nearest point farther than this leaves the cell missing")
    ap.add_argument("--griddir", default=GRIDDIR_DEFAULT)
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--list-vars", action="store_true")
    a = ap.parse_args()

    if a.list_vars:
        f = sorted(glob.glob("%s/archive/y*/*.land_month.tile1.nc" % a.case))
        if not f:
            raise SystemExit("no land_month files under %s/archive" % a.case)
        with Dataset(f[0]) as d:
            names = [k for k, v in d.variables.items() if "grid_index" in v.dimensions]
            for n in sorted(names):
                ln = getattr(d.variables[n], "long_name", "")
                un = getattr(d.variables[n], "units", "")
                print("  %-22s %-34s %s" % (n, ln[:34], un))
        print("\n%d variables on grid_index in %s" % (len(names), os.path.basename(f[0])))
        return

    if not a.years:
        raise SystemExit("--years Y0 Y1 required (or --list-vars)")
    y0, y1 = a.years
    case = a.case.rstrip("/")
    name = os.path.basename(case)
    outdir = a.outdir or os.path.join(os.path.dirname(os.path.dirname(case)),
                                      "postprocess", "latlon")
    os.makedirs(outdir, exist_ok=True)

    print("coordinates from %s (C96 supergrid centres)" % a.griddir)
    lat, lon = land_coords(case, y0, a.griddir)
    print("  %d land points, lat %.2f..%.2f, lon %.2f..%.2f"
          % (lat.size, lat.min(), lat.max(), lon.min(), lon.max()))

    for var in a.vars:
        stack = []
        for y in range(y0, y1 + 1):
            vals, attrs = read_var(case, y, var)
            stack.append(vals)
            print("  %s %d  mean %.4g" % (var, y, np.nanmean(vals)), flush=True)
        vals = np.concatenate(stack, axis=0)

        grid, lat_c, lon_c = regrid(vals, lat, lon, a.res, a.how, a.maxdist)
        filled = np.isfinite(grid[0]).sum()
        print("  -> %d x %d grid, %d cells with land (%.1f%%)"
              % (lat_c.size, lon_c.size, filled, 100.0 * filled / grid[0].size))

        out = os.path.join(outdir, "%s.%s.%d-%d.%gdeg.nc"
                           % (name, var, y0, y1, a.res))
        note = ("%s regridding of C96 land points onto a %.2f deg lat-lon grid"
                % (a.how, a.res))
        if a.how == "nearest":
            note += "; cell takes its nearest land point within %.0f km, else missing" % a.maxdist
        else:
            note += "; cell-mean of contained points, empty cells missing"
        write_nc(out, var, grid, lat_c, lon_c, (y0, y1), attrs, name, a.res, note)
        print("  wrote %s (%.1f MB)" % (out, os.path.getsize(out) / 1e6))


if __name__ == "__main__":
    sys.exit(main())
