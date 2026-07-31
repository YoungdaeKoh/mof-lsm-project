"""How LM4+ was run offline: the AMIP configuration with the atmosphere put into
forcing mode.

Every value drawn here is read from the run configurations, not paraphrased:
  KIOST-ESM2_AMIP/input.nml   and   RUN/lm4_spinup30/input.nml
    do_atmos / do_ocean / do_ice / do_land are coupler_nml switches
    (coupler/full/coupler_main.F90:484-490, ".not.do_atmos" branch at 1383/1492)
  atmos_model_init is gated on Atm%pe, not do_atmos -> the atmosphere is still
  initialised, only its time stepping is skipped
  flux_down_from_atmos is called outside the if(do_atmos) block -> the forcing
  injection hook stays alive, which is what makes the whole approach work

Output: figures/lm4p_offline_schematic.png
"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

C_ATM = "#4a7fb5"
C_ICE = "#7fc9d9"
C_LND = "#4a9a5f"
C_OFF = "#c9c9c9"
C_FRC = "#e08a33"
C_TXT = "#1a1a1a"


def box(ax, x, y, w, h, label, sub, face, dashed=False, alpha=1.0, bold=True):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.02",
                       linewidth=2.0 if not dashed else 1.6,
                       linestyle="--" if dashed else "-",
                       edgecolor="#444444", facecolor=face, alpha=alpha, zorder=3)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h * (0.62 if sub else 0.5), label, ha="center",
            va="center", fontsize=11 if bold else 10,
            fontweight="bold" if bold else "normal", color=C_TXT, zorder=4)
    if sub:
        ax.text(x + w / 2, y + h * 0.26, sub, ha="center", va="center",
                fontsize=7.6, style="italic", color="#333333", zorder=4)


def arrow(ax, xy, xytext, color="#555555", lw=1.6, style="<->", dashed=False):
    ax.add_patch(FancyArrowPatch(xytext, xy, arrowstyle=style, mutation_scale=13,
                                 lw=lw, color=color, zorder=2,
                                 linestyle="--" if dashed else "-",
                                 shrinkA=2, shrinkB=2))


def panel(ax, mode):
    """mode: 'amip' or 'offline'"""
    off = mode == "offline"
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # --- atmosphere -----------------------------------------------------------
    box(ax, 0.26, 0.80, 0.48, 0.135,
        "AM4.5 atmosphere  (FV3, C96)",
        "initialised, NOT time-stepped" if off else "prognostic",
        C_OFF if off else C_ATM, dashed=off, alpha=0.55 if off else 1.0)

    # --- coupler --------------------------------------------------------------
    box(ax, 0.10, 0.475, 0.80, 0.115, "FMS coupler  /  exchange grid",
        "coupler_main.F90  do_* switches", "#f0ede4", bold=True)

    # --- land -----------------------------------------------------------------
    box(ax, 0.26, 0.135, 0.48, 0.145, "LM4 land",
        "PPA cohorts, dynamic vegetation", C_LND, alpha=0.95)

    # --- ice / ocean ----------------------------------------------------------
    box(ax, 0.015, 0.655, 0.30, 0.105, "SIS2 sea ice",
        "SPECIFIED_ICE (obs)", C_ICE, bold=False)
    box(ax, 0.685, 0.655, 0.30, 0.105, "MOM6 ocean", "off", C_OFF,
        dashed=True, alpha=0.55, bold=False)
    ax.text(0.952, 0.708, "✕", ha="center", va="center", fontsize=17,
            color="#8b0000", zorder=5)
    # the atmosphere is deliberately NOT crossed out: it is not removed,
    # it is demoted to prescribed forcing

    # --- connections ----------------------------------------------------------
    arrow(ax, (0.50, 0.80), (0.50, 0.59), dashed=off,
          color="#aaaaaa" if off else "#555555")
    arrow(ax, (0.50, 0.475), (0.50, 0.28))
    arrow(ax, (0.165, 0.655), (0.30, 0.565), lw=1.2)
    arrow(ax, (0.835, 0.655), (0.70, 0.565), lw=1.2, color="#bbbbbb", dashed=True)

    # --- prescribed forcing (offline only) ------------------------------------
    if off:
        box(ax, 0.005, 0.245, 0.275, 0.145, "WFDE5 forcing",
            "0.5° land-mask mesh", C_FRC, alpha=0.92)
        arrow(ax, (0.42, 0.505), (0.285, 0.33), color=C_FRC, lw=2.4, style="->")
        ax.text(0.345, 0.428, "data_table\n↓\nflux_down_from_atmos",
                ha="center", va="center", fontsize=7.2, color="#7a4a10",
                fontweight="bold", zorder=6,
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=C_FRC, lw=0.9))

    cap = ("do_atmos = .false.  —  the same namelist switch, one notch further"
           if off else
           "do_ocean = .false.  —  AMIP had already switched the ocean off")
    ax.text(0.50, 0.045, cap, ha="center", va="center", fontsize=9.5,
            fontweight="bold", color="#8b0000" if off else "#333333")


fig = plt.figure(figsize=(15.5, 8.6))
axL = fig.add_axes([0.025, 0.315, 0.45, 0.585])
axR = fig.add_axes([0.525, 0.315, 0.45, 0.585])
panel(axL, "amip")
panel(axR, "offline")
axL.set_title("KIOST-ESM2  AMIP   (starting point)", fontsize=13,
              fontweight="bold", pad=10)
axR.set_title("LM4+ offline   (atmosphere in forcing mode)", fontsize=13,
              fontweight="bold", pad=10)

fig.add_artist(FancyArrowPatch((0.483, 0.60), (0.518, 0.60),
                               arrowstyle="-|>", mutation_scale=26, lw=3,
                               color="#8b0000", transform=fig.transFigure))

# ------------------------------------------------------------------- table ---
axT = fig.add_axes([0.06, 0.045, 0.50, 0.20])
axT.set_xlim(0, 1)
axT.set_ylim(0, 1)          # fix limits BEFORE plotting: the rule below would
axT.set_autoscale_on(False)  # otherwise autoscale the axis and throw the rows out
axT.axis("off")
rows = [("do_atmos", ".true.", ".false."), ("do_ocean", ".false.", ".false."),
        ("do_ice", ".true.", ".true."), ("do_land", ".true.", ".true."),
        ("do_flux", ".true.", ".true.")]
axT.text(0.0, 1.02, "coupler_nml switches", fontsize=10.5, fontweight="bold",
         family="monospace")
for j, h in enumerate(("switch", "AMIP", "offline")):
    axT.text(0.02 + j * 0.30, 0.84, h, fontsize=9.5, fontweight="bold",
             family="monospace")
axT.plot([0.0, 0.92], [0.79, 0.79], color="#888888", lw=0.9)
for i, (a, b, c) in enumerate(rows):
    y = 0.66 - i * 0.145
    hot = a == "do_atmos"
    axT.text(0.02, y, a, fontsize=9.2, family="monospace")
    axT.text(0.32, y, b, fontsize=9.2, family="monospace")
    axT.text(0.62, y, c, fontsize=9.2, family="monospace",
             color="#c0392b" if hot else "black",
             fontweight="bold" if hot else "normal")

axN = fig.add_axes([0.58, 0.045, 0.40, 0.20])
axN.set_xlim(0, 1)
axN.set_ylim(0, 1)
axN.axis("off")
axN.text(0.0, 1.02, "why it works", fontsize=10.5, fontweight="bold")
notes = [
    "• atmos_model_init is gated on Atm%pe, not do_atmos",
    "   → the atmosphere is still initialised (AMIP INPUT still required);",
    "     only update_atmos_model_* is skipped",
    "• flux_down_from_atmos sits OUTSIDE the if(do_atmos) block",
    "   → the forcing injection hook survives — this is the crux",
    "• no new driver: namelist + data_table.  Two coupler lines were",
    "   patched so leftover radiation would stop running (0.000 s after).",
]
for i, t in enumerate(notes):
    axN.text(0.0, 0.84 - i * 0.135, t, fontsize=8.2,
             color="#222222" if t.startswith("•") else "#444444")

fig.suptitle("Carving LM4+ out of the coupled ESM — the atmosphere is not removed, "
             "it is put into forcing mode", fontsize=14.5, y=0.985)
fig.savefig("figures/lm4p_offline_schematic.png", dpi=150, facecolor="white")
print("wrote figures/lm4p_offline_schematic.png")
