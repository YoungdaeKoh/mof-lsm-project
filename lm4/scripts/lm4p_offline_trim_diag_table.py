"""Strip the AMIP diag_table down to the land streams.

With do_atmos=.false. and do_ocean=.false. the atmosphere is frozen at its
initial state and there is no ocean at all, so every atmos_*/ocean_*/aerosol_*
stream writes meaningless fields -- burning CPU on the diagnostic reductions and
filling disk (the same failure mode as the 4.3 TB mediator-history incident).

Format (FMS diag_manager):
  line 1        title
  line 2        base date
  file def      "name", freq, "units", format, "time_units", "time" [, ...]
  field entry   "module", "field", "output", "file", "sampling", reduc, "reg", pack
"""
import re
import sys

SRC = sys.argv[1]
DST = sys.argv[2]
KEEP_PREFIX = ("land",)
KEEP_EXACT = {"grid_spec"}          # grid metadata, needed to georeference output

lines = open(SRC).read().split("\n")
out = lines[:2]                      # title + base date

tok = re.compile(r'"([^"]*)"')
kept_files, dropped_files = set(), set()
n_field_keep = n_field_drop = 0

for ln in lines[2:]:
    s = ln.strip()
    if not s or s.startswith("#"):
        out.append(ln)
        continue
    q = tok.findall(s)
    if not q:
        out.append(ln)
        continue
    parts = [p.strip() for p in s.split(",")]
    is_filedef = len(parts) > 1 and re.fullmatch(r'-?\d+', parts[1]) is not None

    if is_filedef:
        name = q[0]
        if name.startswith(KEEP_PREFIX) or name in KEEP_EXACT:
            kept_files.add(name)
            out.append(ln)
        else:
            dropped_files.add(name)
    else:
        target = q[3] if len(q) > 3 else None
        if target in kept_files:
            out.append(ln)
            n_field_keep += 1
        else:
            n_field_drop += 1

open(DST, "w").write("\n".join(out))
print("kept files   (%d): %s" % (len(kept_files), " ".join(sorted(kept_files))))
print("dropped files(%d): %s" % (len(dropped_files),
                                 " ".join(sorted(dropped_files)[:14]) + " ..."))
print("fields kept=%d dropped=%d" % (n_field_keep, n_field_drop))
print("lines %d -> %d" % (len(lines), len(out)))
