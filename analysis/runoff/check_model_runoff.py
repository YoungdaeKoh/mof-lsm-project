# Sanity check of extracted model runoff (2001-2023 monthly): time, grid, units, ranges, known boxes, liquid/solid split.
# All converted to mm/day of LIQUID total runoff (memory lsm-runoff-definition-mismatch).
import glob
import numpy as np, xarray as xr

D = "/Volumes/data02/MOF_LSM_model_results/runoffdiag/"
S = 86400.0

def norm(da):
    return da.assign_coords(lon=da.lon % 360).sortby("lon").sortby("lat")

def fill(a):
    a = np.asarray(a, dtype="f8")
    return np.where(np.abs(a) > 1e19, np.nan, a)

def load(name):
    """dict of (time, lat, lon) mm/day DataArrays: total (liquid), and components where available"""
    if name == "LM4p":
        ds = xr.open_dataset(D + "lm4p_runoff_2001_2023.nc")
        runf, frunf = fill(ds.runf.values) * S, fill(ds.frunf.values) * S
        mk = lambda a: norm(xr.DataArray(a, dims=ds.runf.dims, coords=ds.runf.coords))
        return {"total": mk(runf - frunf), "runf_incl_solid": mk(runf), "solid": mk(frunf)}
    if name == "CLM5":
        ds = xr.open_dataset(D + "clm5_runoff_2001_2023.nc")
        return {k: norm(xr.DataArray(fill(ds[v].values) * S, dims=ds[v].dims, coords=ds[v].coords))
                for k, v in (("total", "QRUNOFF"), ("surface", "QOVER"), ("subsurface", "QDRAI"))}
    if name == "NoahMP":
        ds = xr.open_dataset(D + "noahmp_runoff_2001_2023.nc")
        sf, ug = fill(ds.SFCRNOFF.values), fill(ds.UGDRNOFF.values)       # already mm/day
        mk = lambda a: norm(xr.DataArray(a, dims=ds.SFCRNOFF.dims, coords=ds.SFCRNOFF.coords))
        return {"total": mk(sf + ug), "surface": mk(sf), "subsurface": mk(ug)}
    if name == "JULES":
        fs = sorted(glob.glob(D + "jules_yearly/jules_runoff.*.nc"))
        ds = xr.open_mfdataset(fs, combine="nested", concat_dim="time", data_vars="minimal", coords="minimal",
                               compat="override", decode_times=False)
        lat = ds.latitude.isel(y=0).values; lon = ds.longitude.isel(y=0).values % 360
        glat = np.arange(-89.5, 90, 1.0); glon = np.arange(0.0, 360, 1.0)   # CDO r360x180
        iy = np.round(lat - glat[0]).astype(int); ix = np.round(lon - glon[0]).astype(int)
        assert np.allclose(glat[iy], lat) and np.allclose(glon[ix], lon)
        out = {}
        for k, v in (("total", "runoff"), ("surface", "surf_roff"), ("subsurface", "sub_surf_roff")):
            a = fill(ds[v].isel(y=0).values) * S
            g = np.full((a.shape[0], glat.size, glon.size), np.nan); g[:, iy, ix] = a
            out[k] = xr.DataArray(g, dims=("time", "lat", "lon"), coords=dict(lat=glat, lon=glon))
        return out

def box(da, a0, a1, o0, o1):
    return float(da.sel(lat=slice(a0, a1), lon=slice(o0, o1)).mean())

BOX = [("Amazon", -5, 0, 300, 310), ("Congo", 0, 5, 15, 25), ("Sahara", 20, 25, 0, 10),
       ("W-Siberia", 55, 60, 70, 80), ("Norway", 60, 65, 5, 10), ("Yangtze", 28, 32, 110, 120)]

if __name__ == "__main__":
    # observations for the same boxes (2001-2019 G-RUN; composite climatology)
    g = xr.open_dataset("/Volumes/data02/runoff/GRUN/G-RUN_ENSEMBLE_MMM.nc")["Runoff"].sel(
        time=slice("2001", "2019")).mean("time").rename(Y="lat", X="lon")
    g = norm(g)
    print("obs G-RUN 01-19 :", "  ".join(f"{b[0]} {box(g, *b[1:]):.2f}" for b in BOX))
    for name in ["LM4p", "CLM5", "NoahMP", "JULES"]:
        r = load(name); t = r["total"]
        print(f"== {name}: n_time {t.sizes['time']}, lat {float(t.lat[0]):.2f}..{float(t.lat[-1]):.2f} (n={t.lat.size}), "
              f"lon {float(t.lon[0]):.2f}..{float(t.lon[-1]):.2f} (n={t.lon.size})")
        m = t.isel(time=slice(0, 228)).mean("time")                      # 2001-2019
        a = t.values
        w = np.cos(np.deg2rad(t.lat.values))[:, None] * np.isfinite(m.values)
        gm = np.nansum(w * m.values) / w.sum()
        print(f"   total liquid mm/day: min {np.nanmin(a):.3g} max {np.nanmax(a):.3g} neg-share {100*np.nanmean(a < 0):.2f}% "
              f"| 2001-19 land mean (cos-lat, all land incl. ice) {gm:.3f}")
        print("   boxes 2001-19 :", "  ".join(f"{b[0]} {box(m, *b[1:]):.2f}" for b in BOX))
        for k in r:
            if k != "total":
                mk = r[k].isel(time=slice(0, 228)).mean("time").values
                print(f"   {k:16s} land mean {np.nansum(w * mk) / w.sum():.3f} ({100 * np.nansum(w * mk) / np.nansum(w * m.values):.0f}% of total)")
