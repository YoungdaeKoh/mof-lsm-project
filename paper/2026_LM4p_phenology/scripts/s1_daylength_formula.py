#!/usr/bin/env python3
"""SI figure: the day-length terms of the phenology patch (vegn_dynamics.F90, lm4P.phenology_autumn_daylength.diff).

    decl       = 23.44 deg * sin(2 pi (284 + doy) / 365)              solar declination (Cooper 1969)
    dayl       = 24/pi * acos( clip(-tan(lat) tan(decl), -1, 1) )     day length, hours (polar day/night clipped)
    shortening = lat * cos(2 pi (284 + doy) / 365) < 0                 days getting shorter (NH: Jun 21 - Dec 21)
(a) declination over the year; (b) day length at 30-70N (and 40S) with the 13 h leaf-off and 12 h winter-hold lines,
the shortening half-year shaded for the NH, and the date each latitude crosses 13 h while shortening.
output: ../figures/s1_daylength_formula.png
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

doy = np.arange(1, 366)
decl = np.radians(23.44) * np.sin(2 * np.pi * (284 + doy) / 365)


def dayl(lat):
    return 24 / np.pi * np.arccos(np.clip(-np.tan(np.radians(lat)) * np.tan(decl), -1, 1))


def shortening(lat):
    return lat * np.cos(2 * np.pi * (284 + doy) / 365) < 0


fig, (a, b) = plt.subplots(1, 2, figsize=(13, 4.6), gridspec_kw={"width_ratios": (1, 1.6), "wspace": 0.18})
a.plot(doy, np.degrees(decl), color="#c0392b", lw=2)
a.axhline(0, color="k", lw=0.6)
for d, lab in ((80, "Mar equinox"), (172, "Jun solstice"), (266, "Sep equinox"), (355, "Dec solstice")):
    a.axvline(d, color="0.6", lw=0.7, ls=":"); a.text(d + 2, -26, lab, fontsize=7.5, rotation=90, va="bottom", color="0.4")
a.set_ylabel("Solar declination (°)"); a.set_ylim(-27, 27)
a.set_title("(a) decl = 23.44° × sin[2π(284 + doy)/365]", loc="left", fontsize=10)

b.axvspan(172, 355, color="#fde2c4", alpha=0.6, lw=0)
b.text(263, 23.2, "NH: days shortening (shortening = .true.)", ha="center", fontsize=8.5, color="#a0522d")
cols = {30: "#2c7fb8", 40: "#41ab5d", 50: "#d95f0e", 60: "#7570b3", 70: "#e7298a", -40: "0.45"}
for lat, col in cols.items():
    L = dayl(lat)
    b.plot(doy, L, color=col, lw=2 if lat > 0 else 1.2, ls="-" if lat > 0 else "--", label="%d°%s" % (abs(lat), "N" if lat > 0 else "S"))
    hit = np.where(shortening(lat) & (L < 13))[0]
    if hit.size and lat > 0:
        d0 = doy[hit[0]]; b.plot(d0, 13, "o", color=col, ms=6, zorder=5)
        b.annotate("doy %d" % d0, (d0, 13), xytext=(d0 + 4, 13.6 + 0.55 * (lat - 30) / 10), fontsize=7.5, color=col)
b.axhline(13, color="k", lw=1, ls="--"); b.text(3, 13.25, "13 h: autumn leaf-off (larch, C3 grass)", fontsize=8)
b.axhline(12, color="k", lw=0.8, ls=":"); b.text(3, 11.3, "12 h: winter hold / acer leaf-off", fontsize=8)
b.set_xticks([1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]); b.set_xticklabels(list("JFMAMJJASOND"))
b.set_xlim(1, 365); b.set_ylim(0, 24.5); b.set_ylabel("Day length (h)")
b.set_title("(b) dayl = 24/π × acos[−tan(lat) tan(decl)]  (dots: first day < 13 h while shortening)", loc="left", fontsize=10)
b.legend(fontsize=8, ncol=6, loc="lower center", frameon=False)
for ax in (a, b):
    ax.grid(alpha=0.25)
a.set_xticks([1, 91, 182, 274, 365]); a.set_xticklabels(["Jan", "Apr", "Jul", "Oct", "Jan"]); a.set_xlim(1, 365)
fig.savefig("../figures/s1_daylength_formula.png", dpi=200, bbox_inches="tight")
for lat in (40, 50, 60, 70):
    L = dayl(lat); h = np.where(shortening(lat) & (L < 13))[0]
    print("%dN: max %.1f h, below 13 h while shortening from doy %d" % (lat, L.max(), doy[h[0]]))
