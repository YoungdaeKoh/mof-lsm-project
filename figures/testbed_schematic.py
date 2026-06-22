#!/usr/bin/env python3
"""Multi-LSM offline testbed schematic: forcing -> LSMs -> validation obs."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib
matplotlib.rcParams['font.family'] = 'AppleGothic'
matplotlib.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(15, 8))
ax.set_xlim(0, 15); ax.set_ylim(0, 10); ax.axis('off')

def box(x, y, w, h, text, fc, ec, fs=11, bold=False):
    b = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.12",
                       linewidth=1.4, facecolor=fc, edgecolor=ec)
    ax.add_patch(b)
    ax.text(x+w/2, y+h/2, text, ha='center', va='center', fontsize=fs,
            fontweight='bold' if bold else 'normal', color='#1a1a1a')

# column headers
ax.text(2.3, 9.5, "① 대기강제력 (입력)", ha='center', fontsize=15, fontweight='bold', color='#1f4e79')
ax.text(7.5, 9.5, "② 다중 LSM (offline)", ha='center', fontsize=15, fontweight='bold', color='#2e6b2e')
ax.text(12.6, 9.5, "③ 검증 관측/재분석", ha='center', fontsize=15, fontweight='bold', color='#b5651d')

# --- forcing (left) ---
F = '#dbe9f6'; FE = '#1f4e79'
forc = [
    ("ERA5\n0.25°, 1940–현재 (재분석)", 8.0),
    ("GSWP3\n0.5°, 1901–2014 (LSM 표준)", 6.9),
    ("Sheffield / PGF\n0.5°, 1901–2012", 5.8),
    ("CMFD\n0.1°, 1979–2018 · 동아시아 관측동화", 4.7),
    ("[미래] CMIP7 / ISIMIP\nSSP 시나리오 (3년차~)", 3.5),
]
for t, y in forc:
    fc = '#f0e2c0' if '미래' in t else F
    ec = '#a07d2c' if '미래' in t else FE
    box(0.5, y, 3.6, 0.95, t, fc, ec, fs=10)

# --- LSMs (middle) ---
G = '#dceede'; GE = '#2e6b2e'
ax.text(7.5, 8.65, "공통 강제력으로 각 모델 단독 적분\n(NASA LIS 프레임워크, 전구 0.5°, 1979–현재)",
        ha='center', fontsize=9.5, style='italic', color='#333')
lsm_done = ["Noah-3.3", "Noah-MP", "Mosaic", "CLSM"]
lsm_todo = ["JULES", "GFDL LM4"]
y0 = 7.4
for i, m in enumerate(lsm_done):
    box(5.9+ (i%2)*1.7, y0 - (i//2)*1.0, 1.55, 0.8, m, G, GE, fs=10, bold=True)
ax.text(7.5, 5.55, "구축 완료", ha='center', fontsize=9, color='#2e6b2e')
for i, m in enumerate(lsm_todo):
    box(5.9 + i*1.7, 4.3, 1.55, 0.8, m, '#eFcfcf', '#a33', fs=10, bold=True)
ax.text(7.5, 4.0, "구축 중 / 예정", ha='center', fontsize=9, color='#a33')

# --- validation (right) ---
O = '#f6e4cf'; OE = '#b5651d'
val = [
    ("토양수분 : ESA CCI (위성)", 8.0),
    ("유출 : GRUN (관측기반 ML)", 6.9),
    ("증발산 : GLEAM / FLUXNET", 5.8),
    ("식생 LAI : GIMMS / GLASS", 4.7),
    ("적설 SWE : GlobSnow / ERA5-Land", 3.6),
]
for t, y in val:
    box(10.7, y, 3.7, 0.9, t, O, OE, fs=10)

# arrows between columns
ar = dict(arrowstyle='-|>', color='#555', lw=2.2, mutation_scale=22)
ax.add_patch(FancyArrowPatch((4.2, 5.8), (5.8, 6.0), **ar))
ax.add_patch(FancyArrowPatch((9.2, 6.0), (10.6, 6.0), **ar))
ax.text(5.0, 6.25, "구동", ha='center', fontsize=10, color='#555')
ax.text(9.9, 6.3, "성능 진단\n(비교)", ha='center', fontsize=9.5, color='#555')

ax.text(7.5, 2.2, "목적 : 강제력 불확실성  vs  모델 구조오차 분리 → 지역·계절별 성능 진단",
        ha='center', fontsize=12, fontweight='bold', color='#1a1a1a',
        bbox=dict(boxstyle='round,pad=0.5', fc='#fff7e6', ec='#caa', lw=1))

plt.tight_layout()
out = "/Volumes/data01/MOF_LSM_project/figures/testbed_schematic.png"
fig.savefig(out, dpi=150, bbox_inches='tight'); print("saved", out)
