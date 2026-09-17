"""Sanity check: same date, GSWP3 1deg/3h LDASIN vs WFDE5 1deg/6h LDASIN (land mean)."""
import numpy as np
from netCDF4 import Dataset
G = "/home/ydkoh/HRLDAS/forcing_GSWP3_1deg/LDASIN/"
W = "/home/ydkoh/HRLDAS/forcing_WFDE5_1deg/LDASIN_test/"
s = Dataset("/home/ydkoh/HRLDAS/forcing_GSWP3_1deg/init/HRLDAS_setup_GSWP3_1deg_d01.nc")
ivg = np.array(s.variables["IVGTYP"][0]); s.close()
land = (ivg != 17) & (ivg != 21) & (ivg > 0)
def lm(path, v):
    a = np.array(Dataset(path).variables[v][0], "f8"); return a[land].mean()
print("%-9s %12s %12s" % ("var", "GSWP3 00+06Z", "WFDE5 03Z"))
for v in ["T2D", "Q2D", "U2D", "PSFC", "LWDOWN", "SWDOWN", "RAINRATE"]:
    g = 0.5 * (lm(G + "1981010100.LDASIN_DOMAIN1", v) + lm(G + "1981010106.LDASIN_DOMAIN1", v))
    w = lm(W + "1981010103.LDASIN_DOMAIN1", v)
    print("%-9s %12.4g %12.4g" % (v, g, w))
d = np.array(Dataset(W + "1981010103.LDASIN_DOMAIN1").variables["T2D"][0], "f8")
print("WFDE5 T2D ocean-fill check (min over all cells, must be < 400): %.1f" % d.max())
