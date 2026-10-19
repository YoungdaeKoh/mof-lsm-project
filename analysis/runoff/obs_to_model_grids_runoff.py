# Area-average runoff references onto each LSM's native grid (cos-lat weighted, snowlib.Binner), mm/day.
#   G-RUN ENSEMBLE MMM   monthly 2001-2019 (0.5 deg)                      obs-based (ML on gauges)
#   ERA5-Land ro         monthly 2001-2019 (0.1 deg, m/day x1000)          reanalysis LSM (reference, not obs)
#   GRDC/UNH composite   12-month climatology (0.5 deg, mm/month / days)  + gauged share (obs_ro present)
# Plus the common IGBP ice share already on each grid (snowdiag/obs_on_<model>_2001_2023.nc).
# Output: runoffdiag/obs_on_<model>_runoff_2001_2019.nc
import sys
import numpy as np, xarray as xr
sys.path.insert(0, "/Volumes/data01/MOF_LSM_project/analysis/snow")
from snowlib import model_grid, Binner

D = "/Volumes/data02/MOF_LSM_model_results/runoffdiag/"
SD = "/Volumes/data02/MOF_LSM_model_results/snowdiag/"
YEARS = range(2001, 2020)
DAYS = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31], "f8")   # composite mm/month -> mm/day (noleap)

g = xr.open_dataset("/Volumes/data02/runoff/GRUN/G-RUN_ENSEMBLE_MMM.nc")["Runoff"].sel(time=slice("2001-01-01", "2019-12-31"))
assert g.sizes["time"] == 228
G_LAT, G_LON = g.Y.values, g.X.values
c = xr.open_dataset("/Volumes/data02/GRDC/processed/GRDC_UNH_composite_runoff_0.5deg.nc")
C_LAT, C_LON = c.lat.values, c.lon.values
cmp = c.cmp_ro.values.astype("f8") / DAYS[:, None, None]
gauged = np.isfinite(c.obs_ro_ann.values) & (c.obs_ro_ann.values >= 0)
e0 = xr.open_dataset("/Volumes/data02/ERA5/ERA5_Land/runoff_global/ERA5L_runoff_monthly_global_2001.nc")
E_LAT, E_LON = e0.latitude.values, e0.longitude.values

for name in ["LM4p", "CLM5", "NoahMP", "JULES"]:
    mlat, mlon = model_grid(name)
    bg, bc, be = Binner(G_LAT, G_LON, mlat, mlon), Binner(C_LAT, C_LON, mlat, mlon), Binner(E_LAT, E_LON, mlat, mlon)
    shape = (mlat.size, mlon.size)
    grun = np.stack([bg(g.isel(time=i).values) for i in range(228)])
    era = []
    for y in YEARS:
        ds = xr.open_dataset(f"/Volumes/data02/ERA5/ERA5_Land/runoff_global/ERA5L_runoff_monthly_global_{y}.nc")
        era += [be(ds.ro.isel(valid_time=i).values * 1000.0) for i in range(12)]
    era = np.stack(era)
    comp = np.stack([bc(cmp[i]) for i in range(12)])
    gshare = bc(np.where(np.isfinite(cmp[0]), gauged.astype("f8"), np.nan), minvalid=0.0)
    ice = xr.open_dataset(SD + f"obs_on_{name}_2001_2023.nc").icefrac_igbp.values
    times = [np.datetime64(f"{y}-{m:02d}-15") for y in YEARS for m in range(1, 13)]
    out = xr.Dataset(
        dict(grun=(("time", "lat", "lon"), grun.astype("f4"), dict(units="mm/day", source="G-RUN ENSEMBLE MMM v1.0")),
             era5l=(("time", "lat", "lon"), era.astype("f4"), dict(units="mm/day", source="ERA5-Land ro x1000")),
             composite=(("month", "lat", "lon"), comp.astype("f4"), dict(units="mm/day", source="GRDC/UNH cmp_ro / days")),
             gauged_share=(("lat", "lon"), gshare.astype("f4"), dict(long_name="share of composite cells with obs_ro (gauged)")),
             icefrac_igbp=(("lat", "lon"), ice.astype("f4"))),
        coords=dict(time=times, month=np.arange(1, 13), lat=mlat, lon=mlon),
        attrs=dict(method="cos-lat weighted mean of fine pixels in each model cell (snowlib.Binner, >=50% valid)",
                   script="analysis/runoff/obs_to_model_grids_runoff.py"))
    out.to_netcdf(D + f"obs_on_{name}_runoff_2001_2019.nc")
    print(f"{name}: wrote, grid {shape}, gauged cells (share>=0.5) {int(np.nansum(gshare >= 0.5))}", flush=True)
