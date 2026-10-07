#!/usr/bin/env python3
"""Replanting step 3: relabel cohort species in a copy of the restart according to the observation-based map.

Rules (decided 2026-10-07, LM4 notes 13.70):
  - tree cohorts (prioria, picea, larix, acer) on natural (3) and secondary (4) tiles -> the map's dominant
    tree species of the nearest CLM5 cell; left unchanged where the map has no trees
  - grass cohorts (c4grass, c3grass) on every tile -> the map's dominant grass species; unchanged where none
  - trees on crop/pasture tiles, sizes, biomass, densities and all other variables: unchanged
Only vegn2.res.tile*.nc 'species' is written, in a COPY of the restart directory; the source is never touched.
usage: python replant_step3_relabel.py <src_restart_dir> <dst_restart_dir> <decoded.npz> <species_map.nc>
"""
import os
import shutil
import sys
import numpy as np
from netCDF4 import Dataset

src, dst, dec, mapf = sys.argv[1:5]
if os.path.exists(dst) and os.listdir(dst):
    sys.exit("destination exists and is not empty: " + dst)
os.makedirs(dst, exist_ok=True)
for f in sorted(os.listdir(src)):
    if ".res" in f:
        shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
print("copied %d restart files to %s" % (len([f for f in os.listdir(dst)]), dst))

D = np.load(dec, allow_pickle=True); names = list(D["species_names"])
M = Dataset(mapf); mlat = np.asarray(M["lat"][:]); mlon = np.asarray(M["lon"][:])
dom_tree = np.asarray(M["dom_tree"][:]); dom_grass = np.asarray(M["dom_grass"][:])
assert M.species_names.split(", ") == names[:6], "species order differs between map and restart"
ii = np.abs(mlat[:, None] - D["lat"][None, :]).argmin(0)
jj = np.abs(((mlon[:, None] - (D["lon"][None, :] % 360) + 180) % 360 - 180)).argmin(0)
dt = dom_tree[ii, jj]; dg = dom_grass[ii, jj]
sp = D["species"].copy(); new = sp.copy()
is_tree = sp <= 3; is_grass = (sp == 4) | (sp == 5); natural = np.isin(D["landuse"], (3, 4))
tsel = is_tree & natural & (dt >= 0); gsel = is_grass & (dg >= 0)
new[tsel] = dt[tsel]; new[gsel] = dg[gsel]
changed = new != sp
print("cohorts %d | tree cohorts on natural/secondary tiles %d (relabelled %d, no-tree map %d) | grass cohorts %d (relabelled %d) | changed %d"
      % (sp.size, (is_tree & natural).sum(), (tsel & changed).sum(), (is_tree & natural & (dt < 0)).sum(), is_grass.sum(), (gsel & changed).sum(), changed.sum()))
for k, nm in enumerate(names):
    print("  %-8s before %7d  after %7d" % (nm, (sp == k).sum(), (new == k).sum()))

# write back per face, in the same cohort order the decode step read them
start = 0
for n in range(1, 7):
    f = os.path.join(dst, "vegn2.res.tile%d.nc" % n)
    with Dataset(f, "r+") as A:
        A.set_auto_mask(False)
        nco = A.variables["species"].shape[0]
        assert np.array_equal(A.variables["species"][:], sp[start:start + nco]), "cohort order mismatch on face %d" % n
        A.variables["species"][:] = new[start:start + nco]
        A.replant_note = "species relabelled from the CLM5-based map (replant_step3_relabel.py, 2026-10-07); all other variables unchanged"
    start += nco
assert start == sp.size
np.savez(os.path.join(dst, "relabel_record.npz"), species_before=sp, species_after=new, dom_tree=dt, dom_grass=dg)
print("written; record saved to relabel_record.npz")
