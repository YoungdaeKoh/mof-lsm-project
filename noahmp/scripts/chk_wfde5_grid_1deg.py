"""grid-verify: WFDE5 CLM-format yearly file vs GSWP3 0.5deg vs Noah-MP 1deg setup.

Run on climate00 (anaconda python).  Prints only the numbers needed to decide
whether a stride-2 subsample of the WFDE5 file lands on the 1deg setup grid, and
how many 1deg land cells would receive WFDE5 ocean fill.
"""
import numpy as np
from netCDF4 import Dataset

WF = "/data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM_WFDE5/1979_wfde5.nc"
GS = ("/data1/CESM2_INPUT/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v1.c170516/"
      "TPHWL/clmforc.GSWP3.c2011.0.5x0.5.TPQWL.1981-01.nc")
SETUP = "/home/ydkoh/HRLDAS/forcing_GSWP3_1deg/init/HRLDAS_setup_GSWP3_1deg_d01.nc"

w = Dataset(WF)
print("WFDE5 dims:", {k: len(v) for k, v in w.dimensions.items()})
print("WFDE5 vars:", [v for v in w.variables])
t = w.variables["time"]
print("time units:", t.units, "calendar:", getattr(t, "calendar", "?"),
      "n=%d first=%s last=%s" % (len(t), t[0], t[-1]))
lat_w = np.array(w.variables["LATIXY"][:]); lon_w = np.array(w.variables["LONGXY"][:])
print("WFDE5 LATIXY[0,0],[−1,0]: %.3f %.3f  LONGXY[0,0],[0,−1]: %.3f %.3f"
      % (lat_w[0, 0], lat_w[-1, 0], lon_w[0, 0], lon_w[0, -1]))

g = Dataset(GS)
lat_g = np.array(g.variables["LATIXY"][:]); lon_g = np.array(g.variables["LONGXY"][:])
print("GSWP3 LATIXY[0,0],[−1,0]: %.3f %.3f  LONGXY[0,0],[0,−1]: %.3f %.3f"
      % (lat_g[0, 0], lat_g[-1, 0], lon_g[0, 0], lon_g[0, -1]))
print("max |lat diff| %.4f  max |lon diff| %.4f" %
      (np.abs(lat_w - lat_g).max(), np.abs(lon_w - lon_g).max()))

s = Dataset(SETUP)
xlat = np.array(s.variables["XLAT"][0]); xlon = np.array(s.variables["XLONG"][0])
ivg = np.array(s.variables["IVGTYP"][0])
print("setup dims:", xlat.shape, "XLAT[0,0] %.3f XLONG[0,0] %.3f" % (xlat[0, 0], xlon[0, 0]))
sub_lat = lat_w[::2, ::2]; sub_lon = lon_w[::2, ::2]
print("stride-2 WFDE5 vs setup: max |lat| %.4f max |lon| %.4f" %
      (np.abs(sub_lat - xlat).max(), np.abs(sub_lon - xlon).max()))

tb = np.array(w.variables["TBOT"][0])            # first 6h step
fillv = getattr(w.variables["TBOT"], "_FillValue", 1e20)
valid = np.isfinite(tb) & (tb < 1e19)
print("WFDE5 valid fraction 0.5deg: %.3f" % valid.mean())
sub_valid = valid[::2, ::2]
land = (ivg != 17) & (ivg != 21) & (ivg > 0)    # IGBP: 17 water, 21 lake? (checked below)
print("IVGTYP unique:", np.unique(ivg)[:25])
print("1deg land cells (IVGTYP not 17/21): %d ; of those WFDE5-fill: %d" %
      (land.sum(), (land & ~sub_valid).sum()))
ice = ivg == 15
print("  incl. ice cells: %d fill %d" % (ice.sum(), (ice & ~sub_valid).sum()))
print("TBOT range on valid: %.1f %.1f  FSDS max %.1f  PRECTmms max %.5f" %
      (tb[valid].min(), tb[valid].max(),
       np.array(w.variables["FSDS"][8])[valid].max(),
       np.array(w.variables["PRECTmms"][0])[valid].max()))
