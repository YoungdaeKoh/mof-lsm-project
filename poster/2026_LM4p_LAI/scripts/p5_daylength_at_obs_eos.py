#!/usr/bin/env python3
"""Day length on the observed end-of-season date, by AR6 region (basis of the experiment-4 thresholds).

Inputs (both produced earlier in this folder's pipeline):
  ../data/lai_regional_sos_eos.txt   GIMMS EOS day of year per region, 1982-2010 mean, from
                                     p3_regional_seasonal_sos_eos.py (50 % amplitude, monthly
                                     means linearly interpolated to days, per year, then averaged)
  ../data/gimms_lai_clim_1982_2010.nc  only to find the valid 1-deg cells for the regional mean latitude
Steps:
  1. regional mean latitude = cos(lat)-weighted mean over the region's valid 1-deg cells
  2. solar declination (Cooper 1969): decl = 23.44 deg * sin(2 pi (284 + doy) / 365)
  3. day length = 24/pi * acos(-tan(lat) tan(decl)), clipped for polar day/night
  4. day length evaluated on the GIMMS EOS day of year
Output: ../data/eos_daylength_at_obs.txt (overwrites the earlier inline-script version)
Caveats: one latitude per region; EOS is the mid-point of the decline, not its onset;
         the 365-day declination formula is approximate (about 1 degree near the equinoxes).
"""
import re
import warnings
import datetime as dt
import numpy as np
import netCDF4 as nc
import regionmask

REG = ["NWN", "ESB", "RFE", "ENA", "WCE", "EAS"]
D = np.arange(1, 366.0)


def dayl(lat_deg, doy):
    decl = np.radians(23.44) * np.sin(2 * np.pi * (284 + doy) / 365)
    return 24 / np.pi * np.arccos(np.clip(-np.tan(np.radians(lat_deg)) * np.tan(decl), -1, 1))


def date(doy):
    return (dt.date(2010, 1, 1) + dt.timedelta(int(round(doy)) - 1)).strftime("%m/%d")


# observed EOS per region from the SOS/EOS table
eos, name = {}, None
for line in open("../data/lai_regional_sos_eos.txt"):
    m = re.search(r"\((\w{3})\)\s+\(\d+ cells\)", line)
    if m:
        name = m.group(1)
    m = re.match(r"\s+GIMMS\s+SOS\s+[\d.]+\s+\+-\s+[\d.]+\s+\(\S+\)\s+EOS\s+([\d.]+)", line)
    if m and name:
        eos[name] = float(m.group(1))

# regional mean latitude over the valid 1-deg cells
g = nc.Dataset("../data/gimms_lai_clim_1982_2010.nc")
lat = np.asarray(g["lat"][:]); lon = np.asarray(g["lon"][:])
ok = np.isfinite(np.ma.filled(g["clim"][:].astype("f8"), np.nan)).all(0)
W = np.cos(np.radians(lat))[:, None] * np.ones((1, lon.size))
ar6 = regionmask.defined_regions.ar6.land
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    m3 = ar6.mask_3D(lon, lat)

out = ["Day length on the observed EOS date (GIMMS LAI4g, 1982-2010 mean EOS from lai_regional_sos_eos.txt), AR6 regions, at the regional mean latitude",
       "and the date a day-length rule would fire for thresholds 12, 13, 14 h (after the solstice); script p5_daylength_at_obs_eos.py", ""]
vals = []
for ab in REG:
    w = W * (ok & m3.sel(region=ar6.map_keys(ab)).values.astype(bool))
    phi = (lat[:, None] * w).sum() / w.sum()
    e = eos[ab]; dl = dayl(phi, D)
    fire = lambda thr: date(D[[k for k in range(172, 365) if dl[k] < thr][0]])
    vals.append(dayl(phi, e))
    out.append("%s lat %4.1fN  obs EOS %s (doy %5.1f)  day length %5.2f h | rule fires: 12 h %s  13 h %s  14 h %s"
               % (ab, phi, date(e), e, vals[-1], fire(12), fire(13), fire(14)))
out.append("range of day length at obs EOS: %.2f-%.2f h (spread %.2f h)" % (min(vals), max(vals), max(vals) - min(vals)))
open("../data/eos_daylength_at_obs.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out[3:]))
