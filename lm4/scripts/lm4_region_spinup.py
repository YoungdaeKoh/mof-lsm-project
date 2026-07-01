#!/usr/bin/env python3
"""
lm4_region_spinup.py — 대표 지역별 spin-up 수렴 추적.

각 cycle은 시계를 1981로 리셋(restart=1982..2010)하므로, --base_year(이 cycle 전까지 누적연수)를
주어 **누적연수로 라벨링**해 master CSV에 append → 전체 spin-up 궤적을 쌓는다.

지역별로 deep soil T / column soil water / snow water 의 land-mean을 연도별로 계산.
좌표: soil.res tile_index(compress="tile lat lon") 분해 → cpl.hi.lnd 의 lndExp_lon/lat[tile,j,i].

사용 (서버 anaconda):
  python lm4_region_spinup.py --rundir <RUNDIR> --base_year 30 \
      --csv /data2/ydkoh/lm4/region_spinup.csv --png /data2/ydkoh/lm4/region_spinup.png
"""
import argparse, glob, os, re
import numpy as np
from netCDF4 import Dataset
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REGIONS = {  # name: (lat0, lat1, lon0, lon1)  (lon -180..180)
    "Amazon":     (-10,  5, -70, -50),
    "Sahara":     ( 18, 28,   0,  25),
    "Siberia":    ( 55, 68,  90, 130),
    "Tibet":      ( 28, 42,  75, 105),
    "Central US": ( 35, 45,-100, -90),
    "Sahel":      ( 10, 17,   0,  30),
}
NX = 96


def coords(rundir):
    f = sorted(glob.glob(f"{rundir}/ufs.cpld.cpl.hi.lnd.*.nc"))[0]
    c = Dataset(f); LON = np.array(c.variables["lndExp_lon"][0]); LAT = np.array(c.variables["lndExp_lat"][0]); c.close()
    return LON, LAT


def region_means(rundir, year, LON, LAT):
    """한 해 restart → 지역별 (deepT, colWater, snowWat) dict."""
    glon, glat, dT, sw, snw = [], [], [], [], []
    for t in range(1, 7):
        s = Dataset(f"{rundir}/RESTART/{year}0101.000000.soil.res.tile{t}.nc")
        gi = np.array(s.variables["tile_index"][:]).astype(int)
        temp = np.array(s.variables["temp"][:], float)
        wl = np.array(s.variables["wl"][:], float); ws = np.array(s.variables["ws"][:], float)
        s.close()
        pos = gi % (NX * NX)            # tile lat lon -> 공간위치 (subtile offset 제거)
        j, i = pos // NX, pos % NX
        lon = LON[t-1, j, i]; lat = LAT[t-1, j, i]
        lon = np.where(lon > 180, lon - 360, lon)
        glon.append(lon); glat.append(lat)
        dT.append(temp[-1])
        sw.append(np.where(wl < 1e30, wl, 0).sum(0) + np.where(ws < 1e30, ws, 0).sum(0))
        n = Dataset(f"{rundir}/RESTART/{year}0101.000000.snow.res.tile{t}.nc")
        nwl = np.array(n.variables["wl"][:], float); nws = np.array(n.variables["ws"][:], float); n.close()
        snw.append(np.where(nwl < 1e30, nwl, 0).sum(0) + np.where(nws < 1e30, nws, 0).sum(0))
    glon = np.concatenate(glon); glat = np.concatenate(glat)
    dT = np.concatenate(dT); sw = np.concatenate(sw); snw = np.concatenate(snw)
    out = {}
    for name, (la0, la1, lo0, lo1) in REGIONS.items():
        m = (glat >= la0) & (glat < la1) & (glon >= lo0) & (glon < lo1) & (dT < 1e30)
        if m.sum() == 0:
            out[name] = (np.nan, np.nan, np.nan)
        else:
            out[name] = (float(dT[m].mean()), float(sw[m].mean()), float(snw[m].mean()))
    g = (dT < 1e30) & np.isfinite(dT)            # Global = 전 land point 평균
    out["Global"] = (float(dT[g].mean()), float(sw[g].mean()), float(snw[g].mean()))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rundir", default=None)
    p.add_argument("--base_year", type=int, default=0, help="이 cycle 전까지 누적 모델연수")
    p.add_argument("--plot_only", action="store_true", help="CSV만으로 재plot (restart 계산 건너뜀)")
    p.add_argument("--depth", default="8.75 m", help="deep soil T 층 깊이 라벨")
    p.add_argument("--csv", required=True)
    p.add_argument("--png", required=True)
    a = p.parse_args()

    # 기존 CSV 읽기 (항상)
    rows = {}
    if os.path.exists(a.csv):
        for line in open(a.csv):
            if line.startswith("year"):
                continue
            c = line.strip().split(",")
            rows[(int(c[0]), c[1])] = (float(c[2]), float(c[3]), float(c[4]))

    # 새 cycle restart 계산 → CSV append (plot_only면 건너뜀)
    if not a.plot_only:
        LON, LAT = coords(a.rundir)
        years = sorted({m.group(1) for f in os.listdir(f"{a.rundir}/RESTART")
                        if "soil.res.tile1" in f for m in [re.match(r"(\d{4})", f)] if m})
        for k, y in enumerate(years):
            cum = a.base_year + k + 1
            rm = region_means(a.rundir, y, LON, LAT)
            for name, (dT, sw, snw) in rm.items():
                rows[(cum, name)] = (dT, sw, snw)
        with open(a.csv, "w") as f:
            f.write("year,region,deepT,colWater,snowWat\n")
            for (cum, name) in sorted(rows):
                v = rows[(cum, name)]
                f.write(f"{cum},{name},{v[0]:.4f},{v[1]:.3f},{v[2]:.3f}\n")

    # plot: x축은 **연속 순번(rank)** — 절대연수 gap 무시, 1년 간격 균일
    yrs = sorted({k[0] for k in rows})
    x = list(range(1, len(yrs) + 1))            # 1,2,3,... 연속
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.8))
    titles = [f"Deep soil T @ {a.depth} (K)", "Column soil water (kg m$^{-2}$)", "Snow water (kg m$^{-2}$)"]
    plot_names = list(REGIONS) + ["Global"]
    for vi, ttl in enumerate(titles):
        for name in plot_names:
            ser = [rows.get((yy, name), (np.nan,) * 3)[vi] for yy in yrs]
            if name == "Global":
                ax[vi].plot(x, ser, "-", color="k", lw=2.4, zorder=5, label="Global")
            else:
                ax[vi].plot(x, ser, "o-", ms=3, lw=1.3, label=name)
        ax[vi].set_title(ttl); ax[vi].set_xlabel("cumulative spin-up year"); ax[vi].grid(alpha=.3)
    # deep soil T: legend가 곡선과 안 겹치게 y축 위 공간 확보
    y0, y1 = ax[0].get_ylim()
    ax[0].set_ylim(y0, y1 + 0.42 * (y1 - y0))
    ax[0].legend(fontsize=8, ncol=4, loc="upper center")
    fig.suptitle(f"LM4 static-veg spin-up by region (through {len(yrs)} yr)", fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(a.png, dpi=140, bbox_inches="tight")
    print(f"csv={a.csv} ({len(rows)} rows), png={a.png}, n_points={len(yrs)}")


if __name__ == "__main__":
    main()
