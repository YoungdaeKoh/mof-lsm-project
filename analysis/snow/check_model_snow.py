# Sanity check of extracted model SWE / snow cover fraction (2001-2023): time, grid orientation, units, ranges, known boxes
import glob
import numpy as np, xarray as xr

D = "/Volumes/data02/MOF_LSM_model_results/snowdiag/"
SPEC = {  # model: (file, SWE var, SCF var)
    "LM4p":   (D + "lm4p_snow_2001_2023.nc",   "snow",   "snow_frac"),
    "CLM5":   (D + "clm5_snow_2001_2023.nc",   "H2OSNO", "FSNO"),
    "NoahMP": (D + "noahmp_snow_2001_2023.nc", "SNEQV",  "FSNO"),
}

def jules_gridded():
    """Scatter the JULES land-point vector (y=1, x=npts) onto a regular lat-lon grid."""
    ds = xr.open_mfdataset(sorted(glob.glob(D + "jules_yearly/jules_snow.*.nc")), combine="nested",
                           concat_dim="time", data_vars="minimal", coords="minimal", compat="override", decode_times=False)
    lat = ds.latitude.isel(y=0).values; lon = ds.longitude.isel(y=0).values % 360
    dlat = np.diff(np.unique(lat)).min(); dlon = np.diff(np.unique(lon)).min()
    print(f"  JULES points={lat.size}, unique dlat={dlat}, dlon={dlon}, lat {lat.min()}..{lat.max()}, lon {lon.min()}..{lon.max()}")
    glat = np.arange(-89.5, 90, 1.0); glon = np.arange(0.0, 360, 1.0)  # CDO r360x180 (forcing remapcon target): lon centres on integers
    iy = np.round((lat - glat[0]) / 1.0).astype(int); ix = np.round((lon - glon[0]) / 1.0).astype(int)
    assert np.allclose(glat[iy], lat) and np.allclose(glon[ix], lon), "JULES points are not on 1-deg centres"
    assert len(set(zip(iy, ix))) == lat.size, "duplicate JULES points"
    out = {}
    for v in ("snow_mass_gb", "snow_frac"):
        a = ds[v].isel(y=0).values  # (time, x)
        g = np.full((a.shape[0], glat.size, glon.size), np.nan, np.float32); g[:, iy, ix] = a
        out[v] = xr.DataArray(g, dims=("time", "lat", "lon"), coords=dict(lat=glat, lon=glon), attrs=ds[v].attrs)
    t = ds.time
    print(f"  JULES time units: {t.attrs.get('units')}, n={t.size}, first={float(t[0])}, last={float(t[-1])}")
    return xr.Dataset(out)

def norm(ds):
    """lon -> 0..360 and both axes ascending (LM4p is -180..180; Noah-MP lon wraps 179.25 -> -179.75)."""
    return ds.assign_coords(lon=ds.lon % 360).sortby("lon").sortby("lat")

def box(da, la0, la1, lo0, lo1):
    s = da.sel(lat=slice(la0, la1), lon=slice(lo0, lo1))
    return float(s.mean())

if __name__ == "__main__":  # jules_gridded() is imported by snow_metrics.py
  for name in ["LM4p", "CLM5", "NoahMP", "JULES"]:
    print(f"== {name}")
    if name == "JULES":
        ds = jules_gridded(); vs, vf = "snow_mass_gb", "snow_frac"
    else:
        f, vs, vf = SPEC[name]; ds = xr.open_dataset(f)
        print(f"  time n={ds.time.size}, first={ds.time.values[0]}, last={ds.time.values[-1]}")
    lat, lon = ds.lat.values, ds.lon.values
    print(f"  raw lat {lat[0]:.2f}->{lat[-1]:.2f} (n={lat.size}), lon {lon[0]:.2f}->{lon[-1]:.2f} (n={lon.size})")
    ds = norm(ds)
    for v in (vs, vf):
        a = ds[v].values
        a = np.where(np.abs(a) > 1e19, np.nan, a)
        print(f"  {v:13s} units={ds[v].attrs.get('units')!s:10s} min={np.nanmin(a):.4g} max={np.nanmax(a):.4g} "
              f"valid%={100*np.isfinite(a[0]).mean():.1f}")
    jan = ds.isel(time=slice(0, None, 12)).mean("time")  # Jan climatology (records start in Jan 2001)
    jul = ds.isel(time=slice(6, None, 12)).mean("time")
    print(f"  Jan SWE: Sahara {box(jan[vs],20,25,0,10):.1f}  W-Siberia {box(jan[vs],55,60,70,80):.1f}  "
          f"Canada {box(jan[vs],55,60,260,270):.1f} | Jul W-Siberia {box(jul[vs],55,60,70,80):.2f}")
    print(f"  Jan SCF: Sahara {box(jan[vf],20,25,0,10):.3f}  W-Siberia {box(jan[vf],55,60,70,80):.3f}  "
          f"Canada {box(jan[vf],55,60,260,270):.3f}")
