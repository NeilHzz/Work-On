"""
Venn diagram for three-species orthogroup analysis.
Species: Gallus, Anas, Columba
Style: Nature Communications publication quality
"""

import tarfile
import os
import re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import Circle
from matplotlib.colors import to_rgba

# ── Color scheme ──────────────────────────────────────────────────────────────
COLORS = {
    "Gallus":  "#B54664",
    "Anas":    "#7895C1",
    "Columba": "#F0C284",
}

# ── Parse Orthogroups.txt.gz.txt ───────────────────────────────────────────────
ortho_file = os.path.join(os.path.dirname(__file__), "Orthogroups.txt.gz.txt")

gallus_groups  = set()
anas_groups    = set()
columba_groups = set()

with open(ortho_file, "r") as fh:
    for idx, line in enumerate(fh):
        line = line.strip()
        if not line:
            continue
        has_gallus  = "Gallus|"  in line
        has_anas    = "Anas|"    in line
        has_columba = "Columba|" in line
        if has_gallus:
            gallus_groups.add(idx)
        if has_anas:
            anas_groups.add(idx)
        if has_columba:
            columba_groups.add(idx)

# Venn regions
only_A   = gallus_groups  - anas_groups  - columba_groups
only_B   = anas_groups    - gallus_groups - columba_groups
only_C   = columba_groups - gallus_groups - anas_groups
AB_only  = (gallus_groups & anas_groups)    - columba_groups
AC_only  = (gallus_groups & columba_groups) - anas_groups
BC_only  = (anas_groups   & columba_groups) - gallus_groups
ABC      = gallus_groups & anas_groups & columba_groups

n_only_A  = len(only_A)
n_only_B  = len(only_B)
n_only_C  = len(only_C)
n_AB      = len(AB_only)
n_AC      = len(AC_only)
n_BC      = len(BC_only)
n_ABC     = len(ABC)

total_G = len(gallus_groups)
total_A = len(anas_groups)
total_C = len(columba_groups)

print(f"Gallus only:  {n_only_A}")
print(f"Anas only:    {n_only_B}")
print(f"Columba only: {n_only_C}")
print(f"G+A only:     {n_AB}")
print(f"G+C only:     {n_AC}")
print(f"A+C only:     {n_BC}")
print(f"All three:    {n_ABC}")
print(f"Total G={total_G}, A={total_A}, C={total_C}")

# ── Figure layout ─────────────────────────────────────────────────────────────
matplotlib.rcParams.update({
    "font.family":       "Arial",
    "font.size":         7,
    "axes.linewidth":    0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size":  2.5,
    "ytick.major.size":  2.5,
    "pdf.fonttype":      42,
    "svg.fonttype":      "none",
})

fig = plt.figure(figsize=(3.5, 5.4))

gs = gridspec.GridSpec(
    3, 1,
    figure=fig,
    height_ratios=[5.5, 2, 1],
    hspace=0.50,
)

# ── Panel A: Manual Venn diagram (equal circles) ───────────────────────────────
ax_venn = fig.add_subplot(gs[0])
ax_venn.set_aspect("equal")
ax_venn.axis("off")
ax_venn.set_xlim(-1.3, 1.3)
ax_venn.set_ylim(-1.15, 1.1)

# Circle centers – equilateral triangle layout (same as reference image)
r = 0.62                       # radius of each circle
cx_G = -0.35                   # Gallus  (top-left)
cy_G =  0.22
cx_A =  0.35                   # Anas    (top-right)
cy_A =  0.22
cx_C =  0.00                   # Columba (bottom)
cy_C = -0.38

alpha = 0.55

# Draw filled circles in order (back→front) so overlaps blend naturally
for (cx, cy, sp) in [(cx_G, cy_G, "Gallus"),
                      (cx_A, cy_A, "Anas"),
                      (cx_C, cy_C, "Columba")]:
    circ = Circle((cx, cy), r, fc=COLORS[sp], ec="white",
                  linewidth=0.9, alpha=alpha, zorder=2)
    ax_venn.add_patch(circ)

# ── Number labels in each region ──────────────────────────────────────────────
# Approximate centroids of each region
lbl_kw = dict(fontsize=6.5, fontweight="bold", color="white",
              ha="center", va="center", zorder=5)

# Gallus only (top-left arc)
ax_venn.text(cx_G - 0.38, cy_G + 0.15, str(n_only_A),  **lbl_kw)
# Anas only (top-right arc)
ax_venn.text(cx_A + 0.38, cy_A + 0.15, str(n_only_B),  **lbl_kw)
# Columba only (bottom arc)
ax_venn.text(cx_C,        cy_C - 0.38, str(n_only_C),  **lbl_kw)
# G+A (top centre)
ax_venn.text(0.00,  0.58, str(n_AB),   **lbl_kw)
# G+C (left)
ax_venn.text(-0.38, -0.22, str(n_AC),  **lbl_kw)
# A+C (right)
ax_venn.text( 0.38, -0.22, str(n_BC),  **lbl_kw)
# All three (centre)
ax_venn.text(0.00,  0.05, str(n_ABC),  **lbl_kw)

# Species name labels
sp_lbl_kw = dict(ha="center", va="center", fontsize=7.5, fontweight="bold", zorder=6)
ax_venn.text(cx_G - 0.52, cy_G + 0.52, "Gallus",
             color=COLORS["Gallus"],  **sp_lbl_kw)
ax_venn.text(cx_A + 0.52, cy_A + 0.52, "Anas",
             color=COLORS["Anas"],    **sp_lbl_kw)
ax_venn.text(cx_C,        cy_C - 0.72, "Columba",
             color=COLORS["Columba"], **sp_lbl_kw)

# ── Panel B: Bar chart – total per species ─────────────────────────────────────
ax_bar = fig.add_subplot(gs[1])

species_names = ["Gallus", "Anas", "Columba"]
totals        = [total_G, total_A, total_C]
bar_colors    = [COLORS[s] for s in species_names]
bar_x         = np.arange(len(species_names))

bars = ax_bar.bar(
    bar_x, totals,
    color=bar_colors,
    width=0.55,
    edgecolor="none",
    zorder=3,
)

for bar, val in zip(bars, totals):
    ax_bar.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() * 0.5,
        str(val),
        ha="center", va="center",
        fontsize=6, color="white", fontweight="bold",
    )

ax_bar.set_xticks(bar_x)
ax_bar.set_xticklabels(species_names, fontsize=7)
ax_bar.set_ylabel("No. of orthogroups", fontsize=6.5)
ax_bar.set_title("Size of each list", fontsize=7, style="italic", pad=3)
ax_bar.set_ylim(0, max(totals) * 1.15)
ax_bar.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
    lambda x, _: f"{int(x):,}"
))
ax_bar.spines[["right", "top"]].set_visible(False)
ax_bar.tick_params(axis="both", labelsize=6)
ax_bar.set_axisbelow(True)
ax_bar.yaxis.grid(True, linewidth=0.4, color="#dddddd", zorder=0)

# ── Panel C: Horizontal stacked bar ───────────────────────────────────────────
ax_hbar = fig.add_subplot(gs[2])

n_shared3 = n_ABC
n_shared2 = n_AB + n_AC + n_BC
n_shared1 = n_only_A + n_only_B + n_only_C

shared_values = [n_shared3, n_shared2, n_shared1]
shared_colors = ["#A89BC8", "#C8B8DC", "#E8D8F0"]
shared_labels = [f"{n_shared3}", f"{n_shared2}", f"1 ({n_shared1})"]

left = 0
for val, col, lbl in zip(shared_values, shared_colors, shared_labels):
    ax_hbar.barh(0, val, left=left, color=col, height=0.5, edgecolor="none")
    if val > 0:
        ax_hbar.text(
            left + val / 2, 0, lbl,
            ha="center", va="center",
            fontsize=6, color="#444444", fontweight="bold",
        )
    left += val

ax_hbar.set_xlim(0, left)
ax_hbar.set_yticks([])
ax_hbar.set_xlabel("Number of shared orthogroups", fontsize=6.5)
ax_hbar.set_title(
    "Number of elements: specific (1) or shared by 2, 3, ... lists",
    fontsize=6.5, style="italic", pad=3,
)
ax_hbar.spines[["right", "top", "left"]].set_visible(False)
ax_hbar.tick_params(axis="x", labelsize=6)

# ── Save ───────────────────────────────────────────────────────────────────────
out_dir = os.path.dirname(__file__)
out_pdf = os.path.join(out_dir, "Fig_venn_orthogroups.pdf")
out_svg = os.path.join(out_dir, "Fig_venn_orthogroups.svg")
out_png = os.path.join(out_dir, "Fig_venn_orthogroups.png")

fig.savefig(out_pdf, dpi=300, bbox_inches="tight")
fig.savefig(out_svg, bbox_inches="tight")
fig.savefig(out_png, dpi=300, bbox_inches="tight")
print(f"\nSaved: {out_pdf}\n        {out_svg}\n        {out_png}")
plt.show()


# ── Color scheme ──────────────────────────────────────────────────────────────
COLORS = {
    "Gallus":  "#B54664",
    "Anas":    "#7895C1",
    "Columba": "#F0C284",
}

# ── Parse Orthogroups.txt.gz.txt ───────────────────────────────────────────────
ortho_file = os.path.join(os.path.dirname(__file__), "Orthogroups.txt.gz.txt")

gallus_groups  = set()
anas_groups    = set()
columba_groups = set()

with open(ortho_file, "r") as fh:
    for idx, line in enumerate(fh):
        line = line.strip()
        if not line:
            continue
        has_gallus  = "Gallus|"  in line
        has_anas    = "Anas|"    in line
        has_columba = "Columba|" in line
        if has_gallus:
            gallus_groups.add(idx)
        if has_anas:
            anas_groups.add(idx)
        if has_columba:
            columba_groups.add(idx)

# Venn regions (abc notation: Gallus=A, Anas=B, Columba=C)
only_A   = gallus_groups  - anas_groups  - columba_groups        # Gallus only
only_B   = anas_groups    - gallus_groups - columba_groups        # Anas only
only_C   = columba_groups - gallus_groups - anas_groups           # Columba only
AB_only  = (gallus_groups & anas_groups)    - columba_groups      # G+A not C
AC_only  = (gallus_groups & columba_groups) - anas_groups         # G+C not A
BC_only  = (anas_groups   & columba_groups) - gallus_groups       # A+C not G
ABC      = gallus_groups & anas_groups & columba_groups            # all three

# Counts
n_only_A  = len(only_A)
n_only_B  = len(only_B)
n_only_C  = len(only_C)
n_AB      = len(AB_only)
n_AC      = len(AC_only)
n_BC      = len(BC_only)
n_ABC     = len(ABC)

total_G = len(gallus_groups)
total_A = len(anas_groups)
total_C = len(columba_groups)

print(f"Gallus only:  {n_only_A}")
print(f"Anas only:    {n_only_B}")
print(f"Columba only: {n_only_C}")
print(f"G+A only:     {n_AB}")
print(f"G+C only:     {n_AC}")
print(f"A+C only:     {n_BC}")
print(f"All three:    {n_ABC}")
print(f"Total G={total_G}, A={total_A}, C={total_C}")

# ── Figure layout ─────────────────────────────────────────────────────────────
matplotlib.rcParams.update({
    "font.family":      "Arial",
    "font.size":        7,
    "axes.linewidth":   0.6,
    "xtick.major.width":0.6,
    "ytick.major.width":0.6,
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "pdf.fonttype":     42,
    "svg.fonttype":     "none",
})

fig = plt.figure(figsize=(3.5, 5.4))  # single-column width for NatComms

gs = gridspec.GridSpec(
    3, 1,
    figure=fig,
    height_ratios=[5.5, 2, 1],
    hspace=0.50,
)

# ── Panel A: Venn diagram ─────────────────────────────────────────────────────
ax_venn = fig.add_subplot(gs[0])
ax_venn.set_aspect("equal")
ax_venn.axis("off")

# matplotlib_venn: subsets order = (Abc, aBc, ABc, abC, AbC, aBC, ABC)
subsets = (n_only_A, n_only_B, n_AB, n_only_C, n_AC, n_BC, n_ABC)

v = venn3(
    subsets=subsets,
    set_labels=("", "", ""),  # We will add custom labels manually
    alpha=0.55,
    ax=ax_venn,
)

# Apply colors
patch_ids = ["100", "010", "001"]
species_order = ["Gallus", "Anas", "Columba"]
for pid, sp in zip(patch_ids, species_order):
    p = v.get_patch_by_id(pid)
    if p:
        p.set_facecolor(COLORS[sp])
        p.set_edgecolor("none")

# Mixed patches – blend adjacent colors slightly or use neutral
mixed_ids = ["110", "101", "011", "111"]
mixed_colors = [
    "#9A7C95",  # G+A
    "#C07874",  # G+C
    "#A3B4A4",  # A+C
    "#B09080",  # All
]
for pid, col in zip(mixed_ids, mixed_colors):
    p = v.get_patch_by_id(pid)
    if p:
        p.set_facecolor(col)
        p.set_edgecolor("none")

# Circle outlines
c = venn3_circles(subsets=subsets, ax=ax_venn, linewidth=0.8, color="white")

# Label text font
label_ids = ["100", "010", "001", "110", "101", "011", "111"]
for lid in label_ids:
    lbl = v.get_label_by_id(lid)
    if lbl:
        lbl.set_fontsize(6.5)
        lbl.set_fontweight("bold")
        lbl.set_color("white")

# Expand axis to avoid clipping the AB-only region at top
xlim = ax_venn.get_xlim()
ylim = ax_venn.get_ylim()
x_pad = (xlim[1] - xlim[0]) * 0.08
y_pad_top = (ylim[1] - ylim[0]) * 0.12
y_pad_bot = (ylim[1] - ylim[0]) * 0.08
ax_venn.set_xlim(xlim[0] - x_pad, xlim[1] + x_pad)
ax_venn.set_ylim(ylim[0] - y_pad_bot, ylim[1] + y_pad_top)

# Species name labels – positioned just outside each circle
label_positions = {
    "Gallus":  (-0.50,  0.45),
    "Anas":    ( 0.50,  0.45),
    "Columba": ( 0.00, -0.62),
}
for sp, (dx, dy) in label_positions.items():
    ax_venn.text(
        dx, dy, sp,
        ha="center", va="center",
        fontsize=7.5, fontweight="bold",
        color=COLORS[sp],
        transform=ax_venn.transData,
    )

# ── Panel B: Bar chart – total per species ─────────────────────────────────────
ax_bar = fig.add_subplot(gs[1])

species_names  = ["Gallus", "Anas", "Columba"]
totals         = [total_G, total_A, total_C]
bar_colors     = [COLORS[s] for s in species_names]
bar_x          = np.arange(len(species_names))

bars = ax_bar.bar(
    bar_x, totals,
    color=bar_colors,
    width=0.55,
    edgecolor="none",
    zorder=3,
)

# Value labels inside bars
for bar, val in zip(bars, totals):
    ax_bar.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() * 0.5,
        str(val),
        ha="center", va="center",
        fontsize=6, color="white", fontweight="bold",
    )

ax_bar.set_xticks(bar_x)
ax_bar.set_xticklabels(species_names, fontsize=7)
ax_bar.set_ylabel("No. of orthogroups", fontsize=6.5)
ax_bar.set_title("Size of each list", fontsize=7, style="italic", pad=3)
ax_bar.set_ylim(0, max(totals) * 1.15)
ax_bar.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
    lambda x, _: f"{int(x):,}"
))
ax_bar.spines[["right", "top"]].set_visible(False)
ax_bar.tick_params(axis="both", labelsize=6)
ax_bar.set_axisbelow(True)
ax_bar.yaxis.grid(True, linewidth=0.4, color="#dddddd", zorder=0)

# ── Panel C: Horizontal stacked bar – shared by 1/2/3 species ─────────────────
ax_hbar = fig.add_subplot(gs[2])

# Count orthogroups shared by exactly 1, 2, 3 species
n_shared3 = n_ABC
n_shared2 = n_AB + n_AC + n_BC
n_shared1 = n_only_A + n_only_B + n_only_C

shared_values  = [n_shared3, n_shared2, n_shared1]
shared_colors  = ["#A89BC8", "#C8B8DC", "#E8D8F0"]
shared_labels  = [f"{n_shared3}", f"{n_shared2}", f"1 ({n_shared1})"]

left = 0
for val, col, lbl in zip(shared_values, shared_colors, shared_labels):
    ax_hbar.barh(
        0, val,
        left=left,
        color=col,
        height=0.5,
        edgecolor="none",
    )
    if val > 0:
        ax_hbar.text(
            left + val / 2, 0,
            lbl,
            ha="center", va="center",
            fontsize=6, color="#444444", fontweight="bold",
        )
    left += val

ax_hbar.set_xlim(0, left)
ax_hbar.set_yticks([])
ax_hbar.set_xlabel("Number of shared orthogroups", fontsize=6.5)
ax_hbar.set_title(
    "Number of elements: specific (1) or shared by 2, 3, ... lists",
    fontsize=6.5, style="italic", pad=3,
)
ax_hbar.spines[["right", "top", "left"]].set_visible(False)
ax_hbar.tick_params(axis="x", labelsize=6)

# ── Save ───────────────────────────────────────────────────────────────────────
out_dir = os.path.dirname(__file__)
out_pdf = os.path.join(out_dir, "Fig_venn_orthogroups.pdf")
out_svg = os.path.join(out_dir, "Fig_venn_orthogroups.svg")
out_png = os.path.join(out_dir, "Fig_venn_orthogroups.png")

fig.savefig(out_pdf, dpi=300, bbox_inches="tight")
fig.savefig(out_svg, bbox_inches="tight")
fig.savefig(out_png, dpi=300, bbox_inches="tight")
print(f"\nSaved: {out_pdf}\n        {out_svg}\n        {out_png}")
plt.show()
