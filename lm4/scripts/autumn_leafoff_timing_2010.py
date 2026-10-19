# dayl_d 2010, WSB/ESB bands: when does the autumn leaf-off rule fire, and when does cell LAI actually fall?
# Rule (vegn_dynamics.F90 + phenoff patch), larix/c3grass: leaf-off if tc_pheno < 5 C  OR
#   (shortening .and. dayl < 13 h .and. tc_pheno < 20 C); acer: 10 C / 12 h / 20 C. Drought ignored (see notes).
# tc_pheno reconstructed as 20-day EMA (0.95/0.05) of daily canopy Tmean (as spring_gate_diag.py).
import glob, numpy as np
from netCDF4 import Dataset
run = "/Volumes/data02/LM4P/cases/phentest_2010/dayl_d"
L, Lo, lai, tx, tn, tr = [], [], [], [], [], []
for f in sorted(glob.glob(run + "/*.land_daily.tile*.nc")):
    with Dataset(f) as A:
        A.set_auto_mask(False)
        la = A["geolat_t"][:].ravel(); lo = A["geolon_t"][:].ravel()
        m = (la >= 45) & (la < 65) & (lo >= 60) & (lo < 130)
        L.append(la[m]); Lo.append(lo[m])
        for lst, k in ((lai, "lai"), (tx, "vegn_temp_max"), (tn, "vegn_temp_min"), (tr, "t_ref_max")):
            x = A[k][:].astype("f8"); lst.append(x.reshape(x.shape[0], -1)[:, m])
la = np.concatenate(L); lo = np.concatenate(Lo)
lai, tx, tn = (np.concatenate(v, -1) for v in (lai, tx, tn))
nt = lai.shape[0]; doy = np.arange(1, nt + 1)
ok = np.all((lai >= 0) & (lai < 1e10), 0) & np.all((tx > 100) & (tx < 400), 0) & (lai.max(0) - lai.min(0) > 0.3)
tm = (tx + tn) / 2 - 273.15
tc = np.empty_like(tm); tc[0] = tm[:31].mean(0)
for t in range(1, nt):
    tc[t] = 0.95 * tc[t - 1] + 0.05 * tm[t]
rl = np.radians(la)[None, :]; d = doy[:, None]
decl = np.radians(23.44) * np.sin(2 * np.pi * (284 + d) / 365)
dayl = 24 / np.pi * np.arccos(np.clip(-np.tan(rl) * np.tan(decl), -1, 1))
shorten = (rl * np.cos(2 * np.pi * (284 + d) / 365)) < 0
after = (d > 172)
def first(c):
    c = c & after
    return np.where(c.any(0), np.argmax(c, 0) + 1, np.nan)
cold5 = first(tc < 5); dl13 = first(shorten & (dayl < 13) & (tc < 20))
off = np.fmin(cold5, dl13)
cold10 = first(tc < 10); dl12 = first(shorten & (dayl < 12) & (tc < 20)); off_acer = np.fmin(cold10, dl12)
pk = np.argmax(np.where(doy[:, None] > 120, lai, -1), 0)
thr = lai.min(0) + 0.5 * (lai.max(0) - lai.min(0))
e50 = np.array([pk[i] + 1 + np.argmax(lai[pk[i]:, i] < thr[i]) for i in range(la.size)], float)
d13 = lambda lat: 1 + np.argmax([(24/np.pi*np.arccos(np.clip(-np.tan(np.radians(lat))*np.tan(np.radians(23.44)*np.sin(2*np.pi*(284+x)/365)),-1,1)) < 13) & (x > 172) for x in range(1, 366)])
print("band        cells | peak  | larix/grass: DL13  cold5  off  dl-binding%% | acer off | LAI50 down | off->LAI50 | T(raw) at off | doy(dayl<13 h) at band mid")
for r, l0, l1 in (("WSB", 60, 90), ("ESB", 90, 130)):
    for b0, b1 in ((45, 55), (55, 65)):
        m = ok & (lo >= l0) & (lo < l1) & (la >= b0) & (la < b1)
        md = lambda a: np.nanmedian(a[m])
        toff = np.array([tm[int(off[i]) - 1, i] for i in np.where(m)[0] if np.isfinite(off[i])])
        print("%s %d-%dN %5d | %5.0f | %5.0f %6.0f %5.0f %6.0f | %8.0f | %10.0f | %10.0f | %10.1f C | %5d" % (
            r, b0, b1, m.sum(), md(pk + 1), md(dl13), md(cold5), md(off), 100 * np.mean((dl13 <= cold5)[m]), md(off_acer),
            md(e50), md(e50 - off), np.median(toff), d13((b0 + b1) / 2)))

# WSB 45-55N: cells whose LAI falls to 50 % before the autumn rule (summer dip) - do they re-green?
m = ok & (lo >= 60) & (lo < 90) & (la >= 45) & (la < 55)
early = m & (e50 < off - 5)
mo = lambda a, i: a[[0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365][i]:[0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365][i + 1]].mean(0)
print("\nWSB 45-55N: summer-dip cells %d of %d (%.0f %%), median lat %.1f" % (early.sum(), m.sum(), 100 * early.mean() / m.mean(), np.median(la[early])))
for name, s in (("dip", early), ("other", m & ~early)):
    print("  %-5s monthly LAI May-Oct: %s | Jun-Aug Tmean %.1f C" % (name, " ".join("%.2f" % np.median(mo(lai, k)[s]) for k in range(4, 10)),
          np.median(tm[151:243][:, s])))
