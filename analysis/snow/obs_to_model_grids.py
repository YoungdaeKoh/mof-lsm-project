# Area-average fine-resolution snow observations onto each LSM's native grid (2001-2023, monthly).
#   ERA5-Land SWE (0.1 deg, m w.e. -> mm), MODIS MOD10CM SCF (0.05 deg, % -> 0-1),
#   MODIS MCD12C1 2010 IGBP "snow and ice" fraction of land (0.05 deg) for the common ice mask.
# Each fine pixel is assigned to the model cell containing its centre; cos(lat)-weighted mean;
# a model cell is NaN if < 50 % of its (weighted) pixels are valid.
# Output: /Volumes/data02/MOF_LSM_model_results/snowdiag/obs_on_<model>_2001_2023.nc
import glob, time
import numpy as np, xarray as xr
from pyhdf.SD import SD, SDC

D = "/Volumes/data02/MOF_LSM_model_results/snowdiag/"
E5 = "/Volumes/data02/ERA5/ERA5L_SWE_monthly/ERA5m-land_{:04d}{:02d}.nc"
MN = "/Volumes/data02/snow/modis/data/nc/MOD10CM.v061.{:04d}.{:02d}.nc"
LC = "/Volumes/data02/MODIS/MCD12C1_v061_hdf/MCD12C1.A2010001.061.2022161022952.hdf"
YEARS = range(2001, 2024)
from snowlib import model_grid, Binner, MINVALID  # moved to snowlib.py (2026-10-08) for reuse

# fine grids (verified in notes/findings.md, 2026-10-08)
e0 = xr.open_dataset(E5.format(2001, 1)); E_LAT, E_LON = e0.latitude.values, e0.longitude.values
m0 = xr.open_dataset(MN.format(2001, 1)); M_LAT, M_LON = m0.lat.values, m0.lon.values
C_LAT = np.linspace(89.975, -89.975, 3600); C_LON = np.linspace(-179.975, 179.975, 7200)  # MCD12C1 CMG

# IGBP snow/ice share of land, 0.05 deg
h = SD(LC, SDC.READ); pct = h.select("Land_Cover_Type_1_Percent")
water = pct[:, :, 0].astype(np.float64); ice = pct[:, :, 15].astype(np.float64)
bad = (water > 100) | (ice > 100); water[bad] = np.nan; ice[bad] = np.nan
land = 100.0 - water

models = ["LM4p", "CLM5", "NoahMP", "JULES"]
B = {}
for mname in models:
    mlat, mlon = model_grid(mname)
    B[mname] = dict(lat=mlat, lon=mlon, e=Binner(E_LAT, E_LON, mlat, mlon), m=Binner(M_LAT, M_LON, mlat, mlon),
                    c=Binner(C_LAT, C_LON, mlat, mlon))
    print(f"{mname}: grid {mlat.size}x{mlon.size}, binners ready", flush=True)

times = [np.datetime64(f"{y:04d}-{m:02d}-15") for y in YEARS for m in range(1, 13)]
out = {k: dict(swe=np.full((len(times),) + (B[k]["lat"].size, B[k]["lon"].size), np.nan, np.float32),
               scf=np.full((len(times),) + (B[k]["lat"].size, B[k]["lon"].size), np.nan, np.float32)) for k in models}
t0 = time.time()
for it, t in enumerate(times):
    y, m = int(str(t)[:4]), int(str(t)[5:7])
    swe = xr.open_dataset(E5.format(y, m))["sd"].isel(time=0).values * 1000.0  # m w.e. -> mm
    try:  # 5 months have no MOD10CM granule (2001-06, 2002-03, 2003-12, 2016-02, 2022-10) -> stay NaN
        scf = xr.open_dataset(MN.format(y, m))["snow"].isel(time=0).values / 100.0  # % -> 0-1
    except FileNotFoundError:
        scf = None; print(f"  MODIS missing {y}-{m:02d} -> NaN", flush=True)
    for k in models:
        out[k]["swe"][it] = B[k]["e"](swe)
        if scf is not None:
            out[k]["scf"][it] = B[k]["m"](scf)
    if m == 12:
        print(f"  {y} done ({time.time()-t0:.0f} s)", flush=True)

for k in models:
    # ice share of land: sum(ice%) / sum(land%) within the model cell (no validity threshold beyond data presence)
    icef = B[k]["c"](ice, minvalid=0.0) / B[k]["c"](land, minvalid=0.0)
    ds = xr.Dataset(
        dict(swe_era5l=(("time", "lat", "lon"), out[k]["swe"], dict(units="mm", source="ERA5-Land sd (m w.e.) x1000")),
             scf_modis=(("time", "lat", "lon"), out[k]["scf"], dict(units="1", source="MOD10CM v061 QA==0, /100")),
             icefrac_igbp=(("lat", "lon"), icef.astype(np.float32),
                           dict(units="1", long_name="IGBP snow-and-ice share of land, MCD12C1 2010"))),
        coords=dict(time=times, lat=B[k]["lat"], lon=B[k]["lon"]),
        attrs=dict(method="cos(lat)-weighted mean of fine pixels whose centre lies in the model cell; "
                          f"NaN if valid weight share < {MINVALID}", script="analysis/snow/obs_to_model_grids.py"))
    ds.to_netcdf(D + f"obs_on_{k}_2001_2023.nc")
    print(f"wrote obs_on_{k}_2001_2023.nc  ice cells(>=0.5)={int((icef >= 0.5).sum())}", flush=True)
