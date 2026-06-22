#!/usr/bin/env python3
"""Draw a presentation-quality flowchart of the ERA5 -> CLM forcing pipeline."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.font_manager import FontProperties

plt.rcParams["font.family"] = ["AppleGothic", "Malgun Gothic", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(11, 14))
ax.set_xlim(0, 10); ax.set_ylim(0, 20); ax.axis("off")

NAVY = "#10314b"; BLUE = "#2f5597"; ORANGE = "#ed7d31"
GREEN = "#548235"; GREY = "#5a6b7a"; PEACH = "#fbe5d6"

def box(x, y, w, h, text, fc, ec=NAVY, fs=11, tc="white", bold=True):
    p = FancyBboxPatch((x-w/2, y-h/2), w, h, boxstyle="round,pad=0.08,rounding_size=0.12",
                       fc=fc, ec=ec, lw=1.5, zorder=2)
    ax.add_patch(p)
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, color=tc,
            fontweight="bold" if bold else "normal", zorder=3)

def arrow(x, y0, y1):
    ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle="-|>", mutation_scale=22,
                                 lw=2, color=NAVY, zorder=1))

CX = 5.0

# Input
box(CX, 19, 8.8, 1.2,
    "[ INPUT ]  ERA5 Hourly 0.25°\nt2m · d2m · sp · u10 · v10 · avg_sdswrf · avg_sdlwrf · tp",
    NAVY, fs=10.5)
arrow(CX, 18.4, 17.7)

# Step 1
box(CX, 16.9, 9.0, 1.5,
    "Step 1.  Load & Pre-process\n• addfiles 일괄읽기 + short2flt 언패킹\n"
    "• 위도 역순(::-1, →S→N)  • 윤일(Feb29) 제거 (noleap)",
    BLUE, fs=10)
arrow(CX, 16.15, 15.2)

# Step 2 header
box(CX, 14.5, 9.2, 0.85, "Step 2.  변수 계산 & 시간집계 (→ 7 CLM 변수)", GREEN, fs=11)
# variable rows
vars_ = [
    ("TBOT", "t2m  (그대로)"),
    ("PSRF", "sp  (그대로)"),
    ("QBOT", "d2m + sp → 수증기압 e → 비습 q"),
    ("FLDS", "avg_sdlwrf  (그대로, 6h avg)"),
    ("FSDS", "avg_sdswrf → 6시간 평균 (dim_avg)"),
    ("PRECTmms", "tp → 6시간 누적 (dim_sum) → kg/m²/s"),
    ("WIND", "√(u10² + v10²)"),
]
y = 13.65
for name, conv in vars_:
    box(2.0, y, 2.4, 0.62, name, ORANGE, fs=10, tc=NAVY)
    ax.text(3.45, y, "←  " + conv, ha="left", va="center", fontsize=9.5, color=NAVY)
    y -= 0.78
arrow(CX, 8.0, 7.2)

# Step 3
box(CX, 6.5, 9.0, 1.3,
    "Step 3.  공간 Regridding\n"
    "Target = GSWP3 0.5° 2D격자 (LATIXY/LONGXY)\n"
    "area_conserve_remap_Wrap  (0.25° → 0.5°, 보존)",
    BLUE, fs=10)
arrow(CX, 5.85, 5.05)

# Step 4
box(CX, 4.3, 9.0, 1.3,
    "Step 4.  Metadata & Time축\n"
    "6-hourly time (ispan·0.25+0.125, noleap)\n"
    "setmeta: 1D좌표 제거 + CLM5 변수명/단위",
    BLUE, fs=10)
arrow(CX, 3.65, 2.85)

# Output
box(CX, 2.05, 9.2, 1.5,
    "[ OUTPUT ]  NetCDF4Classic   yyyy_era5.nc\n"
    "7 기상변수 + 2D격자/경계(LONGXY/LATIXY/EDGE) + time(noleap)\n"
    "★ NetCDF4Classic 필수 (datm 호환 · NC_CHAR calendar)",
    NAVY, fs=9.5)

ax.text(CX, 0.6, "ERA5 → CLM5 대기강제력 생성 (era5_to_clm5.ncl, NCL)",
        ha="center", fontsize=12, fontweight="bold", color=NAVY)

fig.tight_layout()
out = "/Volumes/data01/MOF_LSM_project/figures/forcing_flowchart.png"
fig.savefig(out, dpi=140, bbox_inches="tight")
print("saved:", out)
