"""Extract the LMWG (lnd_diag) standard diagnostic variable list.

Source: CESM_postprocessing-master/lnd_diag/
  - inputFiles/set*.txt      : which variables belong to which diagnostic set
  - inputFiles/variable_master4.3.ncl : per-variable metadata
                               (longName, nativeUnits, flux flag, derived flag)

Output (analysis/diag/):
  - lmwg_diag_variables.csv  : one row per (set, variable) with metadata
  - lmwg_diag_variables.md   : human-readable table grouped by diagnostic set

Why: the LMWG package is CLM-specific NCL and its observational climatology is
not distributed (kept on NCAR GLADE). The variable/set definitions, however, are
in the tarball and are usable as-is to define a common multi-LSM diagnostic
variable table (JULES / CLM5 / Noah-MP / LM4).
"""
import csv
import os
import re
from collections import OrderedDict

ROOT = "/Volumes/data01/MOF_LSM_project"
IN = os.path.join(ROOT, "CESM_postprocessing-master/lnd_diag/inputFiles")
OUT = os.path.join(ROOT, "analysis/diag")

# Diagnostic set descriptions, from the LMWG package output page (slide 7 of
# practical21-oleson.pdf) and the model-obs/set_*.ncl headers.
SET_DESC = OrderedDict([
    ("set1", "Global annual trends (energy balance, soil water/ice+T, runoff, snow, photosynthesis)"),
    ("set2", "Horizontal contour plots of DJF/MAM/JJA/SON/ANN means"),
    ("set3", "Monthly climatology, regional (air T, precip, runoff, snow depth, radiative+turbulent fluxes)"),
    ("set4", "Vertical profiles at land raobs stations (inactive)"),
    ("set5", "Tables of annual means"),
    ("set6", "Regional annual trends"),
    ("set7", "RTM/MOSART river flow and discharge to oceans"),
    ("set8", "Ocean/Land/Atmosphere CO2 exchange; annual cycle / zonal / trends"),
    ("set9", "Precip+temperature contours and statistics vs observations"),
    ("set10", "Seasonal mean contours zoomed on the Greenland ice sheet"),
    ("set11", "Seasonal mean contours zoomed on the Antarctic ice sheet"),
    ("set12", "Model vs observations at selected stations"),
])

# Which physical theme each inputFile covers (from its filename suffix).
THEME = {
    "hydro": "Hydrology", "turbFlx": "Turbulent fluxes", "radFlx": "Radiative fluxes",
    "landFlx": "Land fluxes", "moistEnergyFlx": "Moisture+energy fluxes",
    "snow": "Snow", "albedo": "Albedo", "fireFlx": "Fire fluxes",
    "cnFlx": "C/N fluxes", "cn_landFlx": "C/N land fluxes",
    "clampFlx": "CLAMP fluxes", "carbonStock": "Carbon stocks",
    "hydReg": "Hydrology (regional)", "clm": "CLM core", "cn": "CN (carbon-nitrogen)",
    "casa": "CASA", "c13": "C13 isotope", "clm-clamp": "CLM/CLAMP",
    "cn-clamp": "CN/CLAMP", "stationIds": "Station IDs",
    "ann_cycle": "Annual cycle", "ann_cycle_lnd": "Annual cycle (land)",
    "contour": "Contours", "contour_DJF-JJA": "Contours (DJF-JJA)",
    "trends": "Trends", "zonal": "Zonal means", "zonal_lnd": "Zonal means (land)",
}


def parse_variable_master(path):
    """Pull longName / nativeUnits / flux / derived out of the NCL master file.

    The file is a long if/else chain:
        if (varName .eq. "NEE") then
          info@flux=True
          info@longName="..."
          info@nativeUnits = "gC/m^2/s"
    so we track the current variable and attach attributes as we see them.
    """
    meta = OrderedDict()
    cur = None
    re_var = re.compile(r'varName\s+\.eq\.\s+"([^"]+)"')
    re_attr = re.compile(r'info@(\w+)\s*=\s*(.+?)\s*(?:;.*)?$')
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = re_var.search(line)
            if m:
                cur = m.group(1)
                meta.setdefault(cur, {"longName": "", "nativeUnits": "",
                                      "flux": "", "derived": ""})
                continue
            if cur is None:
                continue
            m = re_attr.search(line.strip())
            if not m:
                continue
            key, val = m.group(1), m.group(2).strip().strip('"')
            if key == "longName":
                meta[cur]["longName"] = val
            elif key == "nativeUnits":
                meta[cur]["nativeUnits"] = val
            elif key == "flux":
                meta[cur]["flux"] = "Y" if val.lower().startswith("true") else ""
            elif key == "derivedVariable":
                meta[cur]["derived"] = "Y" if val.lower().startswith("true") else ""
    return meta


def parse_set_files(indir):
    """Read inputFiles/set*.txt -> list of (set, theme, variable, avg_op)."""
    rows = []
    for fn in sorted(os.listdir(indir)):
        if not (fn.startswith("set") and fn.endswith(".txt")):
            continue
        stem = fn[:-4]
        setname, _, suffix = stem.partition("_")
        theme = THEME.get(suffix, suffix)
        # set4_stationIds.txt is a raobs station list (id + name), not variables.
        # Detect it by a numeric first column and skip it.
        with open(os.path.join(indir, fn), encoding="utf-8", errors="replace") as fh:
            lines = [l.split() for l in fh if len(l.split()) >= 2]
        if lines and lines[0][0].isdigit():
            print("skip (station list, not variables): %s" % fn)
            continue
        for parts in lines:
            op, var = parts[0], parts[1]
            rows.append((setname, theme, var, op, fn))
    return rows


def main():
    # variable_master4.3 covers CLM; the CASA masters define the CASA/CLAMP
    # carbon variables (CLOSS_*, BGTEMP, ...) that the set files also reference.
    meta = OrderedDict()
    for mf in ("variable_master4.3.ncl", "variable_master_CASA3.1.ncl",
               "variable_master_CASA3.0.ncl", "variable_master_CASA.ncl"):
        for var, m in parse_variable_master(os.path.join(IN, mf)).items():
            if var not in meta or not meta[var].get("longName"):
                meta[var] = m
    rows = parse_set_files(IN)
    print("variable_master: %d variables" % len(meta))
    print("set files      : %d (set, variable) entries" % len(rows))

    uniq = sorted({r[2] for r in rows})
    missing = [v for v in uniq if v not in meta]
    print("unique variables across sets: %d  (no metadata: %d)"
          % (len(uniq), len(missing)))
    if missing:
        print("  no-metadata examples:", ", ".join(missing[:10]))

    csv_path = os.path.join(OUT, "lmwg_diag_variables.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["set", "theme", "variable", "avg_op", "longName",
                    "nativeUnits", "flux", "derived", "source_file"])
        for setname, theme, var, op, fn in rows:
            m = meta.get(var, {})
            w.writerow([setname, theme, var, op, m.get("longName", ""),
                        m.get("nativeUnits", ""), m.get("flux", ""),
                        m.get("derived", ""), fn])
    print("wrote", csv_path)

    # Markdown: group by set, then by theme; de-duplicate variables within a set.
    md_path = os.path.join(OUT, "lmwg_diag_variables.md")
    by_set = OrderedDict()
    for setname, theme, var, op, fn in rows:
        by_set.setdefault(setname, OrderedDict()).setdefault(theme, [])
        if var not in by_set[setname][theme]:
            by_set[setname][theme].append(var)

    def setkey(s):
        return int(re.sub(r"\D", "", s) or 0)

    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("# LMWG (lnd_diag) 표준 진단 변수표\n\n")
        fh.write("출처: `CESM_postprocessing-master/lnd_diag/inputFiles/` "
                 "(set*.txt + variable_master4.3.ncl)\n\n")
        fh.write("생성: `analysis/diag/extract_lmwg_varlist.py`. "
                 "기계용 전체 표는 `lmwg_diag_variables.csv`.\n\n")
        fh.write("- 진단 세트 %d개 / 고유 변수 %d개 / (세트,변수) 항목 %d개\n\n"
                 % (len(by_set), len(uniq), len(rows)))
        for setname in sorted(by_set, key=setkey):
            desc = SET_DESC.get(setname, "")
            fh.write("## %s — %s\n\n" % (setname, desc))
            for theme, vlist in by_set[setname].items():
                fh.write("**%s** (%d)\n\n" % (theme, len(vlist)))
                fh.write("| 변수 | 설명 | 단위 |\n|---|---|---|\n")
                for v in vlist:
                    m = meta.get(v, {})
                    fh.write("| `%s` | %s | %s |\n"
                             % (v, m.get("longName", "—") or "—",
                                m.get("nativeUnits", "—") or "—"))
                fh.write("\n")
    print("wrote", md_path)


if __name__ == "__main__":
    main()
