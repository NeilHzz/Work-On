"""
CAFE5 Gene Family Expansion/Contraction Phylogenetic Tree Visualization
Style: Nature Communications publication quality

Data source: cafe5.tar.gz  (Base_asr.tre, Base_clade_results.txt)
Tree: ((Gallus:83.3749, Anas:83.3749):7.46473, Columba:90.8397)
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle
import numpy as np
import os
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _save import save_fig

WORK_DIR = os.path.dirname(__file__)

# ── Colors ────────────────────────────────────────────────────────────────────
SP_COLORS  = {"Gallus": "#B54664", "Anas": "#7895C1", "Columba": "#F0C284"}
EXP_COLOR  = "#D56661"
CON_COLOR  = "#4D9A94"
TREE_COLOR = "#999999"

# ── Tree topology (from CAFE5 Base_asr.tre, ultrametric in MYA) ───────────────
ROOT_AGE = 90.8397   # root → tips total branch length = age of root
N3_AGE   = 83.3749   # Gallus-Anas ancestor age (= 90.84 − 7.46)

# ── Species data ──────────────────────────────────────────────────────────────
# Values from summary_statistics.csv / reference figure
EC = {
    "Gallus":  {"exp": 6,  "con": 64},
    "Anas":    {"exp": 14, "con": 30},
    "Columba": {"exp": 75, "con": 8},
}

# Tip y-positions (arbitrary layout units)
Y = {"Gallus": 3.0, "Anas": 2.0, "Columba": 1.0}
Y_N3   = (Y["Gallus"] + Y["Anas"]) / 2   # 2.5
Y_ROOT = (Y_N3 + Y["Columba"]) / 2       # 1.75

# ── Figure ────────────────────────────────────────────────────────────────────
matplotlib.rcParams.update({
    "font.family": "Times New Roman",
    "font.size":    7,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
})

BG_COLOR = "white"

fig = plt.figure(figsize=(8.5, 2.8), facecolor=BG_COLOR)

# ── Tree axis ─────────────────────────────────────────────────────────────────
ax = fig.add_axes([0.03, 0.10, 0.55, 0.80], facecolor=BG_COLOR)
# tree tips land at x=0; labels placed right of x=0 (negative data coords = right)
ax.set_xlim(ROOT_AGE + 3, -32)   # left = oldest, right = space for labels & pies
ax.set_ylim(0.2, 3.9)
ax.axis("off")

# ── Time ruler (top) ─────────────────────────────────────────────────────────
TICKS = [80, 60, 40, 20, 0]
RULER_Y = 3.70
TICK_H  = 0.06
ruler_kw = dict(color="#555555", linewidth=0.7)

# ruler spans from root age (left) to 0 (right), aligned with tree
ax.plot([ROOT_AGE, 0], [RULER_Y, RULER_Y], **ruler_kw)
for t in TICKS:
    ax.plot([t, t], [RULER_Y, RULER_Y + TICK_H], **ruler_kw)
    ax.text(t, RULER_Y + TICK_H + 0.05, str(t),
            ha="center", va="bottom", fontsize=6.5, color="#444444")

# "Million Years Ago" placed 5 MYA to the right of 0 for clear separation
ax.text(-5, RULER_Y + TICK_H + 0.05, "Million Years Ago",
        ha="left", va="bottom", fontsize=6.5, color="#555555",
        style="italic")

# ── Tree branches ─────────────────────────────────────────────────────────────
bkw = dict(color=TREE_COLOR, linewidth=1.1, solid_capstyle="round", zorder=2)

# Root vertical clade bar (connects Columba y and N3 y)
ax.plot([ROOT_AGE, ROOT_AGE], [Y["Columba"], Y_N3], **bkw)
# Root → N3 horizontal
ax.plot([ROOT_AGE, N3_AGE], [Y_N3, Y_N3], **bkw)
# Root → Columba horizontal
ax.plot([ROOT_AGE, 0], [Y["Columba"], Y["Columba"]], **bkw)
# N3 vertical clade bar (connects Gallus y and Anas y)
ax.plot([N3_AGE, N3_AGE], [Y["Anas"], Y["Gallus"]], **bkw)
# N3 → Gallus horizontal
ax.plot([N3_AGE, 0], [Y["Gallus"], Y["Gallus"]], **bkw)
# N3 → Anas horizontal
ax.plot([N3_AGE, 0], [Y["Anas"],   Y["Anas"]],   **bkw)

# Internal node circles – use scatter for display-coord consistency (no distortion)
for nx, ny in [(ROOT_AGE, Y_ROOT), (N3_AGE, Y_N3)]:
    ax.scatter([nx], [ny], s=55, zorder=5,
               color="white", edgecolors=TREE_COLOR, linewidths=0.8)

# ── Species labels – placed at x = 1.5 (just right of tip, in data coords) ───
# tree lines end at x=0; negative data coords are to the right
for sp, ypos in Y.items():
    ax.text(-1.5, ypos, sp, ha="left", va="center",
            fontsize=8.5, style="italic", color="#333333")

# ── Pie charts + annotation (placed as inset axes) ───────────────────────────
PIE_R = 0.080   # inset size in figure-fraction units (radius)

for sp, ypos in Y.items():
    # Convert data-coord of pie center to figure fractions
    pie_cx_data = -20.0  # data x position for pie center (right of species labels)
    disp = ax.transData.transform((pie_cx_data, ypos))
    fig_cx, fig_cy = fig.transFigure.inverted().transform(disp)

    ax_pie = fig.add_axes([fig_cx - PIE_R, fig_cy - PIE_R,
                           2 * PIE_R, 2 * PIE_R],
                          facecolor=BG_COLOR)
    exp_v = EC[sp]["exp"]
    con_v = EC[sp]["con"]

    ax_pie.pie(
        [exp_v, con_v],
        colors=[EXP_COLOR, CON_COLOR],
        startangle=90,
        counterclock=False,
        wedgeprops=dict(linewidth=0.5, edgecolor="white"),
    )
    ax_pie.set_aspect("equal")
    ax_pie.set_facecolor(BG_COLOR)

    # +exp / -con text to the right of the pie
    txt_x_data = -27.5
    disp2 = ax.transData.transform((txt_x_data, ypos))
    fig_tx, fig_ty = fig.transFigure.inverted().transform(disp2)

    fig.text(fig_tx, fig_ty,
             f"+{exp_v} / -{con_v}",
             ha="left", va="center",
             fontsize=7, color="#333333",
             fontfamily="Times New Roman")

# ── Legend ────────────────────────────────────────────────────────────────────
leg_x = 0.60  # figure fraction
leg_y = 0.90
patch_w = 0.020
patch_h = 0.050
gap = 0.010

for i, (label, color) in enumerate([("Expansion", EXP_COLOR),
                                      ("Contraction", CON_COLOR)]):
    lx = leg_x + i * (patch_w + gap + 0.072)
    rect = mpatches.FancyBboxPatch((lx, leg_y - patch_h / 2),
                                    patch_w, patch_h,
                                    boxstyle="round,pad=0.002",
                                    facecolor=color, edgecolor="none",
                                    transform=fig.transFigure,
                                    clip_on=False)
    fig.add_artist(rect)
    fig.text(lx + patch_w + 0.006, leg_y,
             label, ha="left", va="center",
             fontsize=7, color="#333333", transform=fig.transFigure)

# ── Save ──────────────────────────────────────────────────────────────────────
save_fig(fig, "Fig2G")
