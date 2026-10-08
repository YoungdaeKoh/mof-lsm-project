# Seasonal SWE / SCF metrics of four LSMs vs ERA5-Land / MODIS on each model's native grid (2001-2023).
# Domain: NH land 20-90N minus common ice mask (MCD12C1 IGBP snow-and-ice share of land >= 0.5).
# Fairness: model months are masked wherever the observation is missing (MODIS polar night, clouds).
# Metrics: cos(lat)-weighted mean, bias, bias %, RMSE, weighted spatial r of the seasonal climatology.
# Output: snowdiag/snow_metrics_2001_2023.txt (full table) + snowdiag/snow_seasonal_cycle_2001_2023.nc
import numpy as np, xarray as xr

D = "/Volumes/data02/MOF_LSM_model_results/snowdiag/"
MODEL = {"LM4p": ("lm4p", "snow", "snow_frac"), "CLM5": ("clm5", "H2OSNO", "FSNO"),
         "NoahMP": ("noahmp", "SNEQV", "FSNO"), "JULES": (None, "snow_mass_gb", "snow_frac")}
SEAS = {"DJF": (12, 1, 2), "MAM": (3, 4, 5), "SON": (9, 10, 11)}
REG = {"NH": lambda lat, lon: lat >= 20,
       "EUR": lambda lat, lon: (lat >= 20) & ((lon >= 340) | (lon < 190)),
       "NAM": lambda lat, lon: (lat >= 20) & (lon >= 190) & (lon < 340)}
ICE_THR = 0.5
# perennial-snow mask: ERA5-Land Aug climatological SWE above this (mm) is excluded for every model.
# IGBP alone misses partly glaciated cells (Greenland margin, Canadian Arctic, Alaska, HMA; median ice share 0.16)
# that carry 87 % of the NH SON obs mean (2026-10-08 diagnosis).
import os
PERM_THR = float(os.environ.get("PERM_THR", "100"))

def load_model(name):
    """Monthly (276, lat, lon) SWE and SCF, lon 0..360 ascending, lat ascending."""
    if name == "JULES":
        from check_model_snow import jules_gridded  # same scatter as the verified check
        ds = jules_gridded()
    else:
        ds = xr.open_dataset(D + f"{MODEL[name][0]}_snow_2001_2023.nc")
    ds = ds.assign_coords(lon=ds.lon % 360).sortby("lon").sortby("lat")
    f = lambda v: np.where(np.abs(ds[v].values) > 1e19, np.nan, ds[v].values).astype(np.float64)
    return ds.lat.values, ds.lon.values, np.maximum(f(MODEL[name][1]), 0.0), np.clip(f(MODEL[name][2]), 0, 1)

def seas_clim(a, months):
    """Seasonal climatology: mean over all valid months of the season (2001-2023); NaN if < 50 % valid."""
    mi = np.array([(i % 12) + 1 in months for i in range(a.shape[0])])
    s = a[mi]
    n = np.isfinite(s).sum(0)
    with np.errstate(invalid="ignore"):
        c = np.nanmean(s, 0)
    c[n < 0.5 * s.shape[0]] = np.nan
    return c

def stats(m, o, w):
    k = np.isfinite(m) & np.isfinite(o) & (w > 0)
    m, o, w = m[k], o[k], w[k]
    W = w.sum(); mm = (w * m).sum() / W; om = (w * o).sum() / W
    rmse = np.sqrt((w * (m - o) ** 2).sum() / W)
    r = (w * (m - mm) * (o - om)).sum() / np.sqrt((w * (m - mm) ** 2).sum() * (w * (o - om) ** 2).sum())
    return dict(n=int(k.sum()), mod=mm, obs=om, bias=mm - om, biasp=100 * (mm - om) / om if om else np.nan,
                rmse=rmse, r=r)

rows, cyc = [], {}
for name in MODEL:
    lat, lon, swe, scf = load_model(name)
    ob = xr.open_dataset(D + f"obs_on_{name}_2001_2023.nc")
    assert np.allclose(ob.lat.values, lat) and np.allclose(ob.lon.values, lon), f"{name}: obs/model grid mismatch"
    oswe, oscf = ob.swe_era5l.values.astype(np.float64), ob.scf_modis.values.astype(np.float64)
    aug = np.nanmean(oswe[7::12], 0)
    maug = np.nanmean(swe[7::12], 0)
    ice_obs = (ob.icefrac_igbp.values >= ICE_THR) | (aug > PERM_THR)
    spur = (maug > PERM_THR) & ~ice_obs  # model-only perennial snow (e.g. JULES bare-soil frac cells) -> reported
    ice = ice_obs | spur
    print(f"{name}: spurious model-perennial-snow cells (Aug SWE>{PERM_THR} mm, not obs ice) "
          f"NH {int((spur & (ob.lat.values[:, None] >= 20)).sum())}, global {int(spur.sum())}")
    LAT, LON = np.meshgrid(lat, lon, indexing="ij")
    w0 = np.cos(np.deg2rad(LAT)) * ~ice
    scf_m = np.where(np.isfinite(oscf), scf, np.nan)          # same months/cells as MODIS
    swe_m = np.where(np.isfinite(oswe), swe, np.nan)
    oswe = np.where(np.isfinite(swe), oswe, np.nan)
    oscf = np.where(np.isfinite(scf), oscf, np.nan)
    print(f"{name}: ice-masked cells {int(ice.sum())}, NH land cells {int((np.isfinite(swe[0]) & (LAT >= 20)).sum())}")
    for rg, f in REG.items():
        w = w0 * f(LAT, LON)
        for sn, mo in SEAS.items():
            for var, mdl, obs in (("SWE", swe_m, oswe), ("SCF", scf_m, oscf)):
                s = stats(seas_clim(mdl, mo), seas_clim(obs, mo), w)
                rows.append((name, rg, sn, var, s))
    # seasonal climatology maps (for bias-map figures), masked cells NaN
    mp = {}
    for sn, mo in SEAS.items():
        for var, mdl, obs in (("SWE", swe_m, oswe), ("SCF", scf_m, oscf)):
            for src, a in (("model", mdl), ("obs", obs)):
                mp[f"{var}_{sn}_{src}"] = (("lat", "lon"), np.where(ice, np.nan, seas_clim(a, mo)).astype(np.float32))
    xr.Dataset(mp, coords=dict(lat=lat, lon=lon)).to_netcdf(D + f"snow_seasclim_{name}_perm{int(PERM_THR)}.nc")
    # NH monthly climatology (for the seasonal-cycle figure), same masking
    w = w0 * REG["NH"](LAT, LON)
    for var, mdl, obs in (("SWE", swe_m, oswe), ("SCF", scf_m, oscf)):
        mc = np.array([[np.nansum(w * mdl[i]) / np.nansum(w * np.isfinite(mdl[i]) * np.isfinite(obs[i]))
                        if np.isfinite(mdl[i]).any() else np.nan for i in range(m - 1, 276, 12)] for m in range(1, 13)])
        oc = np.array([[np.nansum(w * obs[i]) / np.nansum(w * np.isfinite(mdl[i]) * np.isfinite(obs[i]))
                        for i in range(m - 1, 276, 12)] for m in range(1, 13)])
        cyc[(name, var)] = (np.nanmean(mc, 1), np.nanmean(oc, 1))  # nanmean: 5 MODIS months missing

tag = f"_perm{int(PERM_THR)}"
with open(D + f"snow_metrics_2001_2023{tag}.txt", "w") as fo:
    fo.write("# model region season var n_cells model_mean obs_mean bias bias% RMSE spatial_r  "
             f"(SWE mm, SCF 0-1; NH land 20-90N, IGBP ice>={ICE_THR} or ERA5L Aug SWE>{PERM_THR} mm masked, "
             "cos-lat weighted, 2001-2023)\n")
    for name, rg, sn, var, s in rows:
        fo.write(f"{name:7s} {rg:3s} {sn} {var} {s['n']:6d} {s['mod']:8.3f} {s['obs']:8.3f} {s['bias']:+8.3f} "
                 f"{s['biasp']:+7.1f} {s['rmse']:8.3f} {s['r']:6.3f}\n")

xr.Dataset({f"{n}_{v}_{k}": (("month",), cyc[(n, v)][j]) for (n, v) in cyc for j, k in enumerate(("model", "obs"))},
           coords=dict(month=np.arange(1, 13))).to_netcdf(D + f"snow_seasonal_cycle_2001_2023{tag}.nc")

# console: NH only, compact
print("\nNH 20-90N | season var | model: bias (bias%) r")
for sn in SEAS:
    for var in ("SWE", "SCF"):
        line = " ".join(f"{n}: {s['bias']:+.3g} ({s['biasp']:+.0f}%) r={s['r']:.2f}"
                        for n, rg, ss, vv, s in rows if rg == "NH" and ss == sn and vv == var)
        obs = [s["obs"] for n, rg, ss, vv, s in rows if rg == "NH" and ss == sn and vv == var]
        print(f"{sn} {var} obs~{np.mean(obs):.3g} | {line}")
