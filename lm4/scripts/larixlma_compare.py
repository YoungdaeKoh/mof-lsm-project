#!/usr/bin/env python3
"""larixlma_d (larix LMA 0.076 -> 0.038 kgC/m2) vs replant1y_np48_d baseline, 2010 one-year runs from the same IC.

Input: land_month_by_species (grid-cell means per species, compressed land grid_index), 6 tiles per run.
Region: 50-75N cells where the baseline has larix individuals in January (C96 ~ equal area -> unweighted mean).
Per species: annual-mean GPP/NPP (kgC/m2/yr), July LAI, and December carbon pools / crown area / individuals.
usage: python3 larixlma_compare.py -> ../data/replant/larixlma_compare.txt
"""
import os
import numpy as np
from netCDF4 import Dataset

ROOT = "/Volumes/data02/LM4P/cases/larixlma"
RUNS = (("base", "base_2011"), ("lma", "larixlma_2011"))
SPECIES = {"picea": 1, "larix": 2, "acer": 3}            # 0-based index in species_names
# gpp/npp are already kgC/m2/yr in this file


def load(sub):
    out = {}
    for n in range(1, 7):
        with Dataset(os.path.join(ROOT, sub, "20100101.land_month_by_species.tile%d.nc" % n)) as A:
            lat = A.variables["geolat_t"][:]
            for k in ("gpp", "npp", "lai", "nsc", "bseed", "bl_max", "crownarea", "nindivs", "bwood"):
                v = np.ma.filled(A.variables[k][:].astype(float), np.nan)     # (time, species, grid_index)
                out.setdefault(k, []).append(v)
            out.setdefault("lat", []).append(np.ma.filled(lat, np.nan))
    return {k: np.concatenate(v, axis=-1) for k, v in out.items()}


d = {r: load(s) for r, s in RUNS}
b = d["base"]
mask = (b["lat"] >= 50) & (b["lat"] <= 75) & (np.nan_to_num(b["nindivs"][0, SPECIES["larix"]]) > 0)
print("cells 50-75N with larix:", mask.sum())

rows = [("GPP yr", lambda x, s: np.nanmean(x["gpp"][:, s], axis=0)),
        ("NPP yr", lambda x, s: np.nanmean(x["npp"][:, s], axis=0)),
        ("LAI Jul", lambda x, s: x["lai"][6, s]),
        ("NSC Dec", lambda x, s: x["nsc"][11, s]),
        ("bseed Dec", lambda x, s: x["bseed"][11, s]),
        ("bl_max Dec", lambda x, s: x["bl_max"][11, s]),
        ("bwood Dec", lambda x, s: x["bwood"][11, s]),
        ("crownA Dec", lambda x, s: x["crownarea"][11, s]),
        ("nindiv Dec", lambda x, s: x["nindivs"][11, s])]
lines = ["larixlma_d vs replant1y_np48_d (2010, same IC), 50-75N cells with larix (n=%d), unweighted cell means" % mask.sum(),
         "%-6s %-11s %11s %11s %8s" % ("sp", "var", "base", "larixLMA", "diff%")]
for sp, s in SPECIES.items():
    for name, f in rows:
        vb = np.nanmean(f(d["base"], s)[mask]); vl = np.nanmean(f(d["lma"], s)[mask])
        lines.append("%-6s %-11s %11.4g %11.4g %8.1f" % (sp, name, vb, vl, 100 * (vl - vb) / vb if vb else np.nan))
# larix monthly LAI cycle
for r in ("base", "lma"):
    lines.append("larix LAI monthly %-4s: " % r + " ".join("%.2f" % np.nanmean(d[r]["lai"][m, SPECIES["larix"]][mask]) for m in range(12)))
os.makedirs("../data/replant", exist_ok=True)
open("../data/replant/larixlma_compare.txt", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
