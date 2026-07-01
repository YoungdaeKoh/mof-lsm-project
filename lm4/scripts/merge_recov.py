import os
main="/data2/ydkoh/lm4/region_spinup.csv"; recov="/data2/ydkoh/lm4/region_recov.csv"
rows={}
for f in [main, recov]:
    if os.path.exists(f):
        for l in open(f):
            if l.startswith("year"): continue
            c=l.strip().split(","); rows[(int(c[0]),c[1])]=(c[2],c[3],c[4])
with open(main,"w") as o:
    o.write("year,region,deepT,colWater,snowWat\n")
    for k in sorted(rows): v=rows[k]; o.write(f"{k[0]},{k[1]},{v[0]},{v[1]},{v[2]}\n")
print("merged rows:", len(rows))
