#!/usr/bin/env python3
"""Build the reduced diag_tables for the offline speed tests (EXP-DIAG, EXP-CONS; LM4 notes 13.71).

Input : lm4/config/diag_table.ctl   (copy of the production ctl diag_table, read-only)
Output: lm4/config/diag_table.offline_min         keeps only what the offline LAI/phenology/water analyses use
        lm4/config/diag_table.offline_min_nocons  same minus water_cons/carbon_cons (EXP-CONS: switches off the
                                                  per-tile conservation bookkeeping, land_model.F90:1602-1604)
        lm4/config/diag_table_removed.txt         every removed field, by stream, for the record
Rules: streams in KEEP_ALL are kept whole; land_month keeps only KEEP_LAND_MONTH; every other stream is dropped
(incl. its file definition). Header, grid_spec and static streams are kept.
"""
import re

SRC = "../config/diag_table.ctl"
KEEP_ALL = {"grid_spec", "land_static", "land_static_sg", "land_month_by_species", "land_static_cmip", "land_month_cmip",
            "land_daily", "land_daily_cmip", "river_month"}
KEEP_LAND_MONTH = set("""geolon_t geolat_t area_ntrl soil_ice soil_liq soil_psi soil_T swdn_dif swdn_dir swup_dif swup_dir
evap evap_soil transp sens fco2 flw fsw lwdn grnd_flux hevap precip runf frunf hrunf FWS FWSv LWS LWSv melt snow snow_soil
snow_depth snow_frac snow_ice snow_liq Tca Tgrnd Trad temp qca water_soil water_lake soil_fsat fsc ssc tot_soil_C litterfall_C
rsoil gpp npp nep resp lai sai bl br bsw bwood bseed nsc btot height height_ave ncohorts nindivs nlayers dbh crownarea species
gdd tc_pheno theta_phen bl_max br_max theta tsoil_av stomatal_cond soil_water_supply PAR_dn PAR_net lai_ntrl height_ntrl
csmoke_rate fevapv levapv levapg fevapg levaps fevaps water_cons carbon_cons""".split())
CONS = {"water_cons", "carbon_cons", "nitrogen_cons"}

field_re = re.compile(r'^\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,')   # module, field, outname, file
file_re = re.compile(r'^\s*"([^"]+)"\s*,\s*-?\d+\s*,\s*"(months|days|hours|minutes|seconds)"')

lines = open(SRC).read().splitlines()
kept_streams = set(KEEP_ALL) | {"land_month"}
removed = {}


def build(keep_lm):
    out = []
    for ln in lines:
        m = field_re.match(ln)
        if m:
            mod, fld, outn, stream = m.groups()
            keep = stream in KEEP_ALL or (stream == "land_month" and fld in keep_lm)
            if not keep:
                removed.setdefault(stream, []).append(fld)
                continue
        else:
            f = file_re.match(ln)
            if f and f.group(1) not in kept_streams:
                continue
        out.append(ln)
    return out


mini = build(KEEP_LAND_MONTH)
open("../config/diag_table.offline_min", "w").write("\n".join(mini) + "\n")
removed_min = {k: list(v) for k, v in removed.items()}
removed.clear()
nocons = build(KEEP_LAND_MONTH - CONS)
open("../config/diag_table.offline_min_nocons", "w").write("\n".join(nocons) + "\n")

nf = lambda L: sum(1 for ln in L if field_re.match(ln))
with open("../config/diag_table_removed.txt", "w") as f:
    f.write("Fields removed from the ctl diag_table in diag_table.offline_min (EXP-DIAG). %d -> %d field lines.\n" % (nf(lines), nf(mini)))
    f.write("Streams dropped whole: %s\n" % ", ".join(sorted(k for k in removed_min if k != "land_month")))
    for k in sorted(removed_min):
        f.write("\n[%s] %d removed:\n  %s\n" % (k, len(removed_min[k]), " ".join(removed_min[k])))
    f.write("\ndiag_table.offline_min_nocons (EXP-CONS) additionally removes: %s\n" % " ".join(sorted(CONS & KEEP_LAND_MONTH)))
print("ctl field lines %d | offline_min %d | nocons %d" % (nf(lines), nf(mini), nf(nocons)))
print("land_month kept %d of %d" % (sum(1 for ln in mini if field_re.match(ln) and field_re.match(ln).group(4) == "land_month"),
                                    sum(1 for ln in lines if field_re.match(ln) and field_re.match(ln).group(4) == "land_month")))
print("streams dropped:", ", ".join(sorted(k for k in removed_min if k != "land_month")))

# ---- production default for offline runs (2026-10-08): offline_min + river_daily (daily discharge for GRDC)
KEEP_ALL.add("river_daily"); kept_streams.add("river_daily"); removed.clear()
fast = build(KEEP_LAND_MONTH)
open("../config/diag_table.offline_fast", "w").write("\n".join(fast) + "\n")
print("offline_fast %d field lines (offline_min + river_daily)" % nf(fast))
