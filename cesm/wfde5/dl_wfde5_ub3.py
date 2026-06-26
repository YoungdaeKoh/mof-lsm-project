import cdsapi, os
DEST="/mnt/data2/WFDE5"
c = cdsapi.Client(); months=[f"{m:02d}" for m in range(1,13)]
for var in ["near_surface_specific_humidity","surface_air_pressure"]:
    for y in range(1979,2010):
        out=f"{DEST}/wfde5_{var}_{y}.zip"
        if os.path.exists(out) and os.path.getsize(out)>1000000: print("skip",out); continue
        try:
            c.retrieve("derived-near-surface-meteorological-variables",
                {"product":"wfde5","variable":var,"reference_dataset":"cru","version":"3_0","year":str(y),"month":months}, out)
            print("OK",var,y)
        except Exception as e: print("FAIL",var,y,str(e)[:80])
