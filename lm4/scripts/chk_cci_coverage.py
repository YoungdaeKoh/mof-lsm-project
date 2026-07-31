"""Is ESA CCI soil moisture usable over 1982-1996?

Our window sits in the early satellite era (SMMR, SSM/I, ERS), which is sparser
and noisier than the present, and the retrieval fails outright under dense
canopy, snow and frozen ground.  Before building any comparison, count how many
of the 75 MJJAS months actually carry data in each cell.

A cell is called usable when at least 60 of the 75 months are valid, i.e. four
of the five MJJAS months in a typical year.

Input : ESACCI_SM_v202505_combined_monthly_197811-202412.nc  (0.25 deg monthly)
Output: figures/cci_coverage_1982_1996.png
"""
import numpy as np
import netCDF4 as nc
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

F = ("/Users/youngdaekoh/data2/SoilMoisture/ESACCI_SM_v9/"
     "ESACCI_SM_v202505_combined_monthly_197811-202412.nc")
YEARS = range(1982, 1997)
MONTHS = (5, 6, 7, 8, 9)

d = nc.Dataset(F)
clat = np.array(d.variables["lat"][:], "f8")
clon = np.array(d.variables["lon"][:], "f8")
tv = d.variables["time"]
dates = nc.num2date(tv[:], tv.units, only_use_cftime_datetimes=False)
idx = [i for i, t in enumerate(dates) if t.year in YEARS and t.month in MONTHS]
print("CCI grid: lat %d %.3f..%.3f   lon %d %.3f..%.3f"
      % (clat.size, clat[0], clat[-1], clon.size, clon[0], clon[-1]))
print("MJJAS months in 1982-1996: %d (expected 75)" % len(idx))

valid = np.zeros((clat.size, clon.size))
for k in idx:
    a = d.variables["sm"][k]
    valid += (~np.ma.getmaskarray(a)) & np.isfinite(np.ma.filled(a, np.nan))
d.close()
frac = valid / len(idx)

# 0.25 -> 1 degree
NLAT, NLON = 180, 360
f1 = frac.reshape(NLAT, 4, NLON, 4).mean(axis=(1, 3))
lat1 = 89.5 - np.arange(NLAT)
lon1 = -179.5 + np.arange(NLON)

W = np.cos(np.deg2rad(lat1))[:, None] * np.ones((1, NLON))
land = f1 > 0
usable = f1 >= 0.8                       # >=60 of 75 months
print("\ncells with any data      : %6d" % land.sum())
print("cells >=80 %% of months   : %6d  (%.1f %% of those)"
      % (usable.sum(), 100 * usable.sum() / land.sum()))
print("area-weighted mean coverage over cells with data: %.1f %%"
      % (100 * np.nansum(np.where(land, f1, 0) * W) / np.where(land, W, 0).sum()))
print("\nzonal coverage [%]")
for a0, a1 in ((60, 85), (30, 60), (0, 30), (-30, 0), (-60, -30)):
    s = land & (lat1[:, None] >= a0) & (lat1[:, None] < a1)
    if s.sum():
        ww = np.where(s, W, 0.0)
        print("  %4d..%-4d  %5.1f %%   usable cells %5.1f %%"
              % (a0, a1, 100 * np.nansum(np.where(s, f1, 0) * ww) / ww.sum(),
                 100 * (usable & s).sum() / s.sum()))

proj = ccrs.PlateCarree()
fig = plt.figure(figsize=(14, 7))
ax = fig.add_subplot(1, 1, 1, projection=proj)
ax.set_extent([-180, 180, -58, 84], crs=proj)
ax.add_feature(cfeature.COASTLINE, lw=0.5)
lv = np.array([0, 0.2, 0.4, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0]) * 100
im = ax.contourf(lon1, lat1, np.where(land, f1 * 100, np.nan), levels=lv,
                 cmap="YlGnBu", extend="min", transform=proj)
gl = ax.gridlines(draw_labels=True, lw=0.3, alpha=0.4)
gl.top_labels = False
gl.right_labels = False
gl.xlabel_style = {"size": 11}
gl.ylabel_style = {"size": 11}
cb = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.06, shrink=0.65,
                  ticks=lv, aspect=40)
cb.set_label("share of the 75 MJJAS months with data [%]", fontsize=12)
cb.ax.tick_params(labelsize=10)
ax.set_title("ESA CCI soil moisture coverage, MJJAS 1982–1996\n"
             "white = no retrieval at all (dense canopy, desert-edge, frozen)",
             fontsize=14)
fig.tight_layout()
fig.savefig("figures/cci_coverage_1982_1996.png", dpi=150)
print("\nwrote figures/cci_coverage_1982_1996.png")
