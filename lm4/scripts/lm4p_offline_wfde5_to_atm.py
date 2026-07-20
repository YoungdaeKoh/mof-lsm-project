"""Build an ATM-ready forcing file for offline lm4P from CLM-format WFDE5.

FMS data_override is a plain file reader: it interpolates in time and space but
derives nothing. Everything CDEPS/DATM used to compute must be produced here.

Three jobs:
  1. CF coordinates. The CLM files carry only 2D LATIXY/LONGXY, so "bilinear"
     in data_table cannot read them. Write real 1D lat/lon with units.
  2. Ocean fill. WFDE5 is land-only (35.8% valid); 8.5% of land cells touch a
     missing neighbour, so a bilinear stencil would mix _FillValue into land --
     East Asian coasts above all. Extrapolate outward (nearest valid, wrapping
     in longitude) so the stencil never sees a gap.
  3. Derived fields. lprec/fprec (phase split) and coszen (solar geometry)
     cannot be expressed as a data_table scale factor, so they are written out.

Fields that ARE expressible as a factor stay out of the file: p_bot reuses
p_surf, and the four shortwave components are FSDS * 0.25 in data_table.
Constants (v_bot, z_bot, gust, slp) live in data_table too.

Usage: python wfde5_to_lm4p_atm.py <year>
"""
import sys
import numpy as np
import netCDF4 as nc
from scipy.ndimage import distance_transform_edt

YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 1981
SRC = "/data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM_WFDE5/%d_wfde5.nc" % YEAR
DST = "/data2/ydkoh/lm4/forcing_WFDE5_lm4p/wfde5_atm_%d.nc" % YEAR

TFRZ = 273.15
SNOW_RAMP = 2.0   # all snow at/below TFRZ, all rain at TFRZ+SNOW_RAMP


def fill_indices(land):
    """Nearest-valid-cell index map, wrapping in longitude.

    distance_transform_edt has no periodic mode, so tile 3x in lon, solve on
    the wide array, then crop the middle third back out.
    """
    ny, nx = land.shape
    wide = np.concatenate([land, land, land], axis=1)
    idx = distance_transform_edt(~wide, return_distances=False,
                                 return_indices=True)
    jj = idx[0][:, nx:2 * nx]
    ii = idx[1][:, nx:2 * nx] % nx          # fold tiled lon back into range
    return jj, ii


def main():
    src = nc.Dataset(SRC)
    lat = src.variables["LATIXY"][:, 0].astype("f8")
    lon = src.variables["LONGXY"][0, :].astype("f8")
    tvar = src.variables["time"]
    nt, ny, nx = src.variables["TBOT"].shape

    # Land mask is time-invariant, so solve the fill geometry once.
    t0 = src.variables["TBOT"][0, :, :]
    land = ~np.ma.getmaskarray(t0)
    jj, ii = fill_indices(land)
    print("land cells %d / %d (%.1f%%)" % (land.sum(), land.size,
                                           100.0 * land.sum() / land.size))

    dst = nc.Dataset(DST, "w", format="NETCDF4")
    dst.createDimension("time", None)
    dst.createDimension("lat", ny)
    dst.createDimension("lon", nx)

    v = dst.createVariable("lat", "f8", ("lat",))
    v.units = "degrees_north"
    v.long_name = "latitude"
    v[:] = lat
    v = dst.createVariable("lon", "f8", ("lon",))
    v.units = "degrees_east"
    v.long_name = "longitude"
    v[:] = lon
    v = dst.createVariable("time", "f8", ("time",))
    v.units = tvar.units
    v.calendar = tvar.calendar
    v[:] = tvar[:].astype("f8")

    def out(name, units, long_name):
        return dst.createVariable(name, "f4", ("time", "lat", "lon"),
                                  zlib=True, complevel=1,
                                  chunksizes=(1, ny, nx))

    spec = [("t_bot", "TBOT", "K", "temperature at lowest atm level"),
            ("sphum_bot", "QBOT", "kg/kg", "specific humidity at lowest atm level"),
            ("p_surf", "PSRF", "Pa", "surface pressure"),
            ("u_bot", "WIND", "m/s", "zonal wind (scalar WIND; v_bot=0 keeps |V|)"),
            ("flux_lw", "FLDS", "W/m2", "downward longwave at surface"),
            ("flux_sw", "FSDS", "W/m2", "downward shortwave at surface (total)")]

    vout = {}
    for name, _, units, ln in spec:
        vv = out(name, units, ln)
        vv.units = units
        vv.long_name = ln
        vout[name] = vv
    for name, units, ln in [("lprec", "kg/m2/s", "liquid precipitation"),
                            ("fprec", "kg/m2/s", "frozen precipitation"),
                            ("coszen", "1", "cosine of solar zenith angle")]:
        vv = out(name, units, ln)
        vv.units = units
        vv.long_name = ln
        vout[name] = vv

    # Solar geometry, evaluated at each timestamp. FSDS is a 6-hour mean while
    # this is instantaneous at the interval start, which is the usual offline
    # approximation -- the dataset carries no sub-6h information anyway.
    lat2d = np.deg2rad(lat)[:, None] * np.ones((1, nx))
    lon2d = np.ones((ny, 1)) * lon[None, :]

    days = tvar[:].astype("f8")
    CH = 200                                  # time chunk
    for s in range(0, nt, CH):
        e = min(s + CH, nt)
        for name, srcname, _, _ in spec:
            a = np.ma.filled(src.variables[srcname][s:e, :, :], np.nan)
            a = a[:, jj, ii]                  # nearest-valid extrapolation
            vout[name][s:e, :, :] = a

        tb = np.ma.filled(src.variables["TBOT"][s:e, :, :], np.nan)[:, jj, ii]
        pr = np.ma.filled(src.variables["PRECTmms"][s:e, :, :], np.nan)[:, jj, ii]
        fsnow = np.clip((TFRZ + SNOW_RAMP - tb) / SNOW_RAMP, 0.0, 1.0)
        vout["fprec"][s:e, :, :] = pr * fsnow
        vout["lprec"][s:e, :, :] = pr * (1.0 - fsnow)

        d = days[s:e]
        doy = np.floor(d) + 1.0
        hutc = (d - np.floor(d)) * 24.0
        dec = np.deg2rad(-23.44) * np.cos(np.deg2rad(360.0 / 365.0) * (doy + 10.0))
        cz = np.empty((e - s, ny, nx), dtype="f4")
        for k in range(e - s):
            lst = hutc[k] + lon2d / 15.0
            ha = np.deg2rad(15.0 * (lst - 12.0))
            cz[k] = (np.sin(lat2d) * np.sin(dec[k]) +
                     np.cos(lat2d) * np.cos(dec[k]) * np.cos(ha))
        vout["coszen"][s:e, :, :] = np.clip(cz, 0.0, 1.0)
        print("  %d/%d" % (e, nt), flush=True)

    dst.source = "WFDE5 (CLM format) reprocessed for FMS data_override"
    dst.notes = ("ocean cells filled by nearest valid land (lon-periodic); "
                 "snow fraction = clip((%.2f-T)/%.1f,0,1); "
                 "coszen instantaneous at timestamp" % (TFRZ + SNOW_RAMP, SNOW_RAMP))
    dst.close()
    src.close()
    print("wrote", DST)


if __name__ == "__main__":
    main()
