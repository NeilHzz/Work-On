"""
Combine 10 panels into a single Science Advances–ready figure.
Row 1 (A–C): highlighted_correlation Gallus / Anas / Columba  [+ shared legend]
Row 2 (D–F): 2d_enrichment G vs A / G vs C / A vs C            [+ shared legend]
Row 3 (G–J): glycan_profiling OVAL / OC116 / OC17 / TRFE       [+ shared legend]

Panel images sourced from _noleg.png variants; per-row shared legends drawn here.
Panel letter labels placed via ax.set_title() so they sit ABOVE each image, not inside.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle
from PIL import Image
from pathlib import Path

# Noleg images live in the source Figure folder
SRC_DIR = Path(r"e:\Data\Desktop\Work On\糖蛋白和蛋白联合分析\Figure")
OUT_DIR = Path(r"e:\Data\Desktop\Work On\Sci_Adv_Figure\PNG")
OUT_PNG = OUT_DIR / "Fig_combined_glycan_analysis.png"
OUT_PDF = OUT_DIR / "Fig_combined_glycan_analysis.pdf"

# Science Advances full-page width = 17.8 cm = 7.0 in
# Scale up 2× for higher resolution output
SCALE      = 2.0
FIG_W      = 7.0 * SCALE    # inches
DPI        = 300
MAIN_RATIO = 0.84   # fraction of width for panel images
LEG_RATIO  = 0.16   # fraction for shared legend column

matplotlib.rcParams.update({
    "font.family": "Arial",
    "font.size":   7,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
})

# ── Panel definitions (noleg variants) ───────────────────────────────────────
rows = [
    [   # Row 1
        ("A", "Fig_highlighted_correlation_Gallus_noleg.png"),
        ("B", "Fig_highlighted_correlation_Anas_noleg.png"),
        ("C", "Fig_highlighted_correlation_Columba_noleg.png"),
    ],
    [   # Row 2
        ("D", "Fig_2d_enrichment_Gallus_vs_Anas_noleg.png"),
        ("E", "Fig_2d_enrichment_Gallus_vs_Columba_noleg.png"),
        ("F", "Fig_2d_enrichment_Anas_vs_Columba_noleg.png"),
    ],
    [   # Row 3
        ("G", "Fig_glycan_profiling_OVAL_noleg.png"),
        ("H", "Fig_glycan_profiling_OC116_noleg.png"),
        ("I", "Fig_glycan_profiling_OC17_noleg.png"),
        ("J", "Fig_glycan_profiling_TRFE_noleg.png"),
    ],
]

# ── Color palettes ────────────────────────────────────────────────────────────
PROT_COLORS = {
    "OVAL":  "#E64B35",
    "OC116": "#4DBBD5",
    "TRFE":  "#00A087",
    "OC17":  "#3C5488",
}
GLYCAN_COLORS = {
    "High-Mannose": "#4DBBD5",
    "Neutral":      "#00A087",
    "Fucosylated":  "#F39B7F",
    "Sialylated":   "#E64B35",
    "Paucimannose": "#8491B4",
    "Other":        "#CCCCCC",
}

ncols = [len(r) for r in rows]   # [3, 3, 4]

# ── Fixed row heights (cm → inches, scaled) ─────────────────────────────────
ROW_HEIGHTS_CM = [3.6, 3.6, 4.2]   # ABC, DEF, GHIJ
row_heights = [h / 2.54 * SCALE for h in ROW_HEIGHTS_CM]

fig_h = sum(row_heights)

# ── Build figure: 3 rows × 2 cols (panels | legend) ──────────────────────────
fig = plt.figure(figsize=(FIG_W, fig_h))

outer_gs = gridspec.GridSpec(
    3, 2,
    figure=fig,
    height_ratios=row_heights,
    width_ratios=[MAIN_RATIO, LEG_RATIO],
    hspace=0.5,
    wspace=0.015,
)

inner_gs = [
    gridspec.GridSpecFromSubplotSpec(1, ncols[i],
                                     subplot_spec=outer_gs[i, 0],
                                     wspace=0.02)
    for i in range(3)
]

# Draw panel images with labels ABOVE (via set_title)
for ri, row in enumerate(rows):
    for ci, (label, fname) in enumerate(row):
        ax = fig.add_subplot(inner_gs[ri][ci])
        img = np.array(Image.open(SRC_DIR / fname).convert("RGB"))
        ax.imshow(img)
        ax.axis("off")
        ax.set_title(label, fontsize=9, fontweight="bold", loc="left",
                     pad=2, color="black")

# ── Shared legend drawing functions ──────────────────────────────────────────
LEG_FS = 6.0   # legend label font size

def draw_legend_row1(ax):
    """Row 1: Highlighted proteins (circles)."""
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.08, 0.97, "Proteins", fontsize=LEG_FS + 0.5,
            fontweight="bold", va="top", color="#333333")
    # items: list of (color, label, marker_size)
    items = [("#999999", "Other proteins", 30)] + [
        (c, n, 55) for n, c in PROT_COLORS.items()
    ]
    y = 0.86
    for color, label, s in items:
        ax.scatter([0.18], [y], c=color, s=s, zorder=5,
                   edgecolors="white", linewidths=0.4)
        ax.text(0.34, y, label, fontsize=LEG_FS, va="center", color="#333333")
        y -= 0.115

def draw_legend_row2(ax):
    """Row 2: 2D enrichment (circles + line + shaded regions)."""
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.08, 0.97, "Proteins", fontsize=LEG_FS + 0.5,
            fontweight="bold", va="top", color="#333333")
    prot_items = [("#999999", "Background")] + [
        (c, n) for n, c in PROT_COLORS.items() if n != "OC17"
    ]
    y = 0.87
    for color, name in prot_items:
        s = 28 if color == "#999999" else 50
        ax.scatter([0.18], [y], c=color, s=s, zorder=5,
                   edgecolors="white", linewidths=0.4)
        ax.text(0.34, y, name, fontsize=LEG_FS, va="center", color="#333333")
        y -= 0.105
    y -= 0.02
    ax.plot([0.04, 0.94], [y, y], color="#DDDDDD", lw=0.4)
    y -= 0.04
    ax.text(0.08, y, "Fold-change", fontsize=LEG_FS + 0.5,
            fontweight="bold", va="top", color="#333333")
    y -= 0.085
    ax.plot([0.06, 0.29], [y, y], "--", color="#666666", lw=1.1)
    ax.text(0.34, y, "y = x", fontsize=LEG_FS, va="center", color="#333333")
    y -= 0.09
    ax.add_patch(Rectangle((0.06, y - 0.026), 0.23, 0.052,
                            facecolor="#FDE8E4", edgecolor="#BBBBBB", lw=0.4))
    ax.text(0.34, y, "Suppressed\nin ref.", fontsize=LEG_FS,
            va="center", color="#333333")
    y -= 0.095
    ax.add_patch(Rectangle((0.06, y - 0.026), 0.23, 0.052,
                            facecolor="#E4F0FB", edgecolor="#BBBBBB", lw=0.4))
    ax.text(0.34, y, "Enriched\nin ref.", fontsize=LEG_FS,
            va="center", color="#333333")

def draw_legend_row3(ax):
    """Row 3: Glycan classification (colored bars)."""
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.08, 0.97, "Glycan\nClassification",
            fontsize=LEG_FS + 0.5, fontweight="bold", va="top", color="#333333",
            linespacing=1.3)
    y = 0.72
    for name, color in GLYCAN_COLORS.items():
        ax.add_patch(Rectangle((0.06, y - 0.029), 0.23, 0.058,
                                facecolor=color, edgecolor="white", lw=0.3))
        ax.text(0.34, y, name, fontsize=LEG_FS, va="center", color="#333333")
        y -= 0.115

# Add legend axes (right column of outer_gs)
draw_legend_row1(fig.add_subplot(outer_gs[0, 1]))
draw_legend_row2(fig.add_subplot(outer_gs[1, 1]))
draw_legend_row3(fig.add_subplot(outer_gs[2, 1]))

# ── Save ───────────────────────────────────────────────────────────────────────
fig.savefig(OUT_PNG, dpi=DPI, bbox_inches="tight", facecolor="white")
fig.savefig(OUT_PDF, bbox_inches="tight", facecolor="white")
print(f"Saved PNG : {OUT_PNG}")
print(f"Saved PDF : {OUT_PDF}")

from PIL import Image as _PIL
im = _PIL.open(OUT_PNG)
w, h = im.size
print(f"Output size: {w}×{h} px  ({w/DPI*2.54:.1f} × {h/DPI*2.54:.1f} cm @ {DPI} dpi, scale={SCALE}×)")
