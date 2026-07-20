"""Grid-safety check on the ATM-ready file before wiring it into data_table.

Checks that would catch the failure modes that matter here:
  - coordinates actually present and CF-readable by data_override
  - no remaining missing values anywhere (the whole point of the ocean fill)
  - fields still physical after fill + derivation
  - lprec+fprec conserves the original PRECTmms
  - coszen has a real diurnal cycle and is zero at night
  - the fill did not move land values (land cells must be untouched)
"""
import numpy as np
import netCDF4 as nc

NEW = "/data2/ydkoh/lm4/forcing_WFDE5_lm4p/wfde5_atm_1981.nc"
SRC = "/data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM_WFDE5/1981_wfde5.nc"

d = nc.Dataset(NEW)
s = nc.Dataset(SRC)

print("=== coordinates ===")
for c in ("lat", "lon", "time"):
    v = d.variables[c]
    print("%-5s n=%-5d %12.4f -> %10.4f  units=%s" % (
        c, len(v), v[0], v[-1], getattr(v, "units", "-")))
print("lat direction:", "ascending" if d.variables["lat"][1] > d.variables["lat"][0]
      else "DESCENDING")
print("calendar:", getattr(d.variables["time"], "calendar", "-"))

print("\n=== fields: full-year min/max and missing count ===")
ranges = {"t_bot": (180, 340), "sphum_bot": (0, 0.05), "p_surf": (4e4, 1.1e5),
          "u_bot": (0, 80), "flux_lw": (30, 600), "flux_sw": (0, 1400),
          "lprec": (0, 0.02), "fprec": (0, 0.02), "coszen": (0, 1)}
bad = 0
for name, (lo, hi) in ranges.items():
    v = d.variables[name]
    vmin, vmax, nmiss = np.inf, -np.inf, 0
    for s0 in range(0, v.shape[0], 200):
        a = v[s0:s0 + 200, :, :]
        nmiss += int(np.isnan(a).sum())
        vmin = min(vmin, float(np.nanmin(a)))
        vmax = max(vmax, float(np.nanmax(a)))
    ok = (vmin >= lo) and (vmax <= hi) and (nmiss == 0)
    bad += 0 if ok else 1
    print("%-10s min=%12.5g max=%12.5g  NaN=%d   %s" % (
        name, vmin, vmax, nmiss, "OK" if ok else "*** CHECK ***"))

print("\n=== precip phase split conserves total ===")
p0 = np.ma.filled(s.variables["PRECTmms"][0:40, :, :], np.nan)
tot = d.variables["lprec"][0:40, :, :] + d.variables["fprec"][0:40, :, :]
land = ~np.isnan(p0)
err = np.abs(tot[land] - p0[land])
print("max |lprec+fprec - PRECTmms| over land = %.3e kg/m2/s" % err.max())

print("\n=== fill did not disturb land cells ===")
t0src = np.ma.filled(s.variables["TBOT"][0, :, :], np.nan)
t0new = d.variables["t_bot"][0, :, :]
lm = ~np.isnan(t0src)
print("max |t_bot_new - TBOT| on land = %.3e K" % np.abs(t0new[lm] - t0src[lm]).max())
print("ocean cells now filled: %d (was missing)" % int((~lm).sum()))

print("\n=== coszen diurnal sanity (equator, day 172 ~ Jun solstice) ===")
lat = d.variables["lat"][:]
lon = d.variables["lon"][:]
je = int(np.argmin(np.abs(lat - 0.0)))
i0 = int(np.argmin(np.abs(lon - 0.0)))
k0 = 171 * 4
cz = d.variables["coszen"][k0:k0 + 4, je, i0]
print("lat=%.2f lon=%.2f  coszen over one day (00,06,12,18 UTC): %s" % (
    lat[je], lon[i0], np.array2string(cz, precision=3)))
print("global coszen==0 fraction (night+polar):",
      "%.3f" % float((d.variables["coszen"][k0, :, :] == 0).mean()))

print("\nRESULT:", "PASS" if bad == 0 else "%d field(s) need review" % bad)
d.close()
s.close()
