#!/usr/bin/env python3
"""Double-logistic LAI seasonal curve (Beck et al. 2006 RSE 100:321 form) and SOS/EOS from it.

    y(t) = w + (m - w) * ( 1/(1+exp(-kS (t - S))) + 1/(1+exp( kA (t - A))) - 1 )
w winter floor, m summer plateau, S/A spring/autumn inflection dates (doy), kS/kA slopes (1/day).
fit(t, y)  : least squares with bounds; t in day of year (may extend past 365 for wrap), y LAI samples of any spacing
             (8-day, half-monthly, monthly, daily). Returns params or None if the fit fails or the amplitude is < amp_min.
curve(p, t): fitted values.
dates(p)   : SOS/EOS at 50 % of the fitted amplitude (= inflection points S and A of this form), plus the 20 % points,
             the fitted peak-plateau midpoint and the amplitude. Used identically on observations and model.
"""
import numpy as np
from scipy.optimize import curve_fit

DOY = np.arange(1, 366.0)


def model(t, w, m, S, kS, A, kA):
    return w + (m - w) * (1.0 / (1.0 + np.exp(-kS * (t - S))) + 1.0 / (1.0 + np.exp(kA * (t - A))) - 1.0)


def fit(t, y, amp_min=0.3):
    t = np.asarray(t, float); y = np.asarray(y, float)
    k = np.isfinite(t) & np.isfinite(y)
    t, y = t[k], y[k]
    if t.size < 6 or (y.max() - y.min()) < amp_min:
        return None
    w0, m0 = np.percentile(y, 5), np.percentile(y, 95)
    ip = t[np.argmax(y)]
    half = w0 + 0.5 * (m0 - w0)
    up = t[(t < ip) & (y >= half)]; dn = t[(t > ip) & (y >= half)]
    S0 = up.min() if up.size else ip - 40; A0 = dn.max() if dn.size else ip + 40
    p0 = [w0, m0, S0, 0.1, A0, 0.1]
    lo = [-0.5, w0, 1, 0.01, 100, 0.01]; hi = [m0, 12, 250, 1.0, 400, 1.0]
    try:
        p, _ = curve_fit(model, t, y, p0=p0, bounds=(lo, hi), maxfev=20000)
    except Exception:
        return None
    if p[1] - p[0] < amp_min or not (p[2] < p[4]):
        return None
    return p


def curve(p, t=DOY):
    return model(np.asarray(t, float), *p)


def dates(p, frac=(0.5, 0.2)):
    """threshold crossings on the fitted daily curve; 50 % = S and A for this functional form (checked numerically)."""
    c = curve(p); lo, hi = c.min(), c.max(); ip = int(c.argmax()); out = {"amp": hi - lo, "peak": DOY[ip]}
    for f in frac:
        thr = lo + f * (hi - lo)
        up = np.where((c[:-1] < thr) & (c[1:] >= thr))[0]; dn = np.where((c[:-1] >= thr) & (c[1:] < thr))[0]
        up = up[up < ip]; dn = dn[dn >= ip]
        s = DOY[up[-1]] + (thr - c[up[-1]]) / (c[up[-1] + 1] - c[up[-1]]) if up.size else np.nan
        e = DOY[dn[0]] + (c[dn[0]] - thr) / (c[dn[0]] - c[dn[0] + 1]) if dn.size else np.nan
        out["sos%d" % round(100 * f)] = s; out["eos%d" % round(100 * f)] = e
    return out
