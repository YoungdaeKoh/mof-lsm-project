#!/usr/bin/env python3
"""
Download ESA CCI soil moisture (C3S satellite-soil-moisture), COMBINED, monthly average, global 0.25 deg.
CDS dataset satellite-soil-moisture, type_of_record cdr, version v202505.
Variables: surface_soil_moisture_volumetric (+ root_zone_soil_moisture_volumetric if VARS includes it).
One request per year (zip of monthly files) -> unzipped into /Volumes/data02/SoilMoisture/ESACCI_C3S_v202505_monthly/<var>/
Usage: python3 download_esacci_sm_monthly.py Y0 Y1 [var ...]     (re-runs skip finished years)
"""
import os, re, sys, zipfile
import ecmwf.datastores as ed

Y0, Y1 = int(sys.argv[1]), int(sys.argv[2])
VARS = sys.argv[3:] or ["surface_soil_moisture_volumetric"]
OUT = "/Volumes/data02/SoilMoisture/ESACCI_C3S_v202505_monthly"
rc = open(os.path.expanduser("~/.cdsapirc")).read()
client = ed.Client(url=re.search(r"url:\s*(\S+)", rc).group(1), key=re.search(r"key:\s*(\S+)", rc).group(1))
for v in VARS:
    os.makedirs(f"{OUT}/{v}", exist_ok=True)
    for y in range(Y0, Y1 + 1):
        done = f"{OUT}/{v}/.done_{y}"
        if os.path.exists(done):
            print(f"[skip] {v} {y}", flush=True); continue
        z = f"{OUT}/{v}/tmp_{y}.zip"
        client.retrieve("satellite-soil-moisture", {
            "variable": [v], "type_of_sensor": ["combined"], "time_aggregation": ["month_average"],
            "year": [str(y)], "month": [f"{m:02d}" for m in range(1, 13)], "day": ["01"],
            "type_of_record": ["cdr"], "version": ["v202505"]}, z + ".part")
        os.replace(z + ".part", z)
        with zipfile.ZipFile(z) as f:
            names = f.namelist(); f.extractall(f"{OUT}/{v}")
        os.remove(z); open(done, "w").write("\n".join(names))
        print(f"[done] {v} {y}: {len(names)} files", flush=True)
print("ALLDONE")
