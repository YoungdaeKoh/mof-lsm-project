#!/usr/bin/env python3
"""Global-mean monthly CO2 (CMIP7, the same series KIOST-ESM2 historical restores its atmosphere to) spread onto a
coarse lat-lon grid, for the offline LM4p data_override of the bottom-level atmospheric CO2:
    data_table:  "ATM", "co2_bot", "co2", "./INPUT/co2_latlon.nc", "bilinear", 1.0e-6
(atm_land_ice_flux_exchange.F90:897 overrides Atm%tr_bot(co2) in DRY vmr and converts to moist mmr itself.)
Source: co2_gblannualdata.nc (monthly 1750-01 .. 2022-12 + a pad record at 2024-01-01 repeating 2022-12).
2023-2024 (not in the source): 2022 monthly values + n x mean annual growth of the last 3 years (user decision (a),
2026-10-10). Output covers 1978-01 .. 2024-12 (mid-month, noleap, days since 1750-01-01).
"""
import numpy as np, netCDF4 as nc

SRC = "/Volumes/data02/LM4P/forcing_co2/co2_gblannualdata.nc"
OUT = "/Volumes/data02/LM4P/forcing_co2/co2_latlon_cmip7_1978_2024.nc"

d = nc.Dataset(SRC)
t = np.asarray(d["time"][:], "f8"); c = np.asarray(d["co2"][:], "f8")
t, c = t[:-1], c[:-1]                                  # drop the 2024-01-01 pad record
yr = 1750 + np.floor(t / 365).astype(int)
assert (yr == 2022).sum() == 12 and yr.max() == 2022
ann = {y: c[yr == y].mean() for y in (2019, 2022)}
g = (ann[2022] - ann[2019]) / 3.0
k22 = yr == 2022
t_ext = np.concatenate([t[k22] + 365.0, t[k22] + 730.0])
c_ext = np.concatenate([c[k22] + g, c[k22] + 2 * g])
keep = yr >= 1978
T = np.concatenate([t[keep], t_ext]); C = np.concatenate([c[keep], c_ext])
assert np.all(np.diff(T) > 0) and T.size == (2024 - 1978 + 1) * 12

lat = np.arange(-89.0, 90.0, 2.0); lon = np.arange(1.0, 360.0, 2.0)
o = nc.Dataset(OUT, "w", format="NETCDF4_CLASSIC")
o.createDimension("time", None); o.createDimension("lat", lat.size); o.createDimension("lon", lon.size)
v = o.createVariable("time", "f8", ("time",)); v[:] = T
v.units = "days since 1750-01-01 00:00:00"; v.calendar = "noleap"; v.axis = "T"; v.standard_name = "time"
v = o.createVariable("lat", "f8", ("lat",)); v[:] = lat; v.units = "degrees_north"; v.axis = "Y"
v = o.createVariable("lon", "f8", ("lon",)); v[:] = lon; v.units = "degrees_east"; v.axis = "X"
v = o.createVariable("co2", "f4", ("time", "lat", "lon"))
v[:] = np.broadcast_to(C[:, None, None], (C.size, lat.size, lon.size))
v.units = "ppm"; v.long_name = "global-mean atmospheric CO2, dry mole fraction (spatially uniform)"
o.title = "CMIP7 monthly global CO2 for offline LM4p co2_bot data_override"
o.history = f"from {SRC}; 2023-2024 = 2022 monthly + n*{g:.3f} ppm/yr (mean 2019->2022 growth); make_co2_latlon.py"
o.close()
print(f"wrote {OUT}: {T.size} months, growth {g:.3f} ppm/yr; 1979-01 {C[12]:.2f}, 2022-12 {C[-25]:.2f}, "
      f"2023 mean {C[-24:-12].mean():.2f}, 2024 mean {C[-12:].mean():.2f}")
