"""
Venn diagram for three-species orthogroup analysis.
Species: Gallus, Anas, Columba
"""

import os
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _save import save_fig
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker
from matplotlib.patches import Circle

# ── Colors ────────────────────────────────────────────────────────────────────
COLORS = {
    "Gallus":  "#B54664",
    "Anas":    "#7895C1",
    "Columba": "#F0C284",
}

# ── Parse Orthogroups ─────────────────────────────────────────────────────────
ortho_file = r"D:\system_folder\Desktop\Work On\01_数据与计算\Ortho\Orthogroups.txt.gz.txt"

gallus_groups  = set()
anas_groups    = set()
columba_groups = set()

with open(ortho_file, "r") as fh:
    for idx, line in enumerate(fh):
        line = line.strip()
        if not line:
            continue
        if "Gallus|"  in line: gallus_groups.add(idx)
        if "Anas|"    in line: anas_groups.add(idx)
        if "Columba|" in line: columba_groups.add(idx)

only_A  = gallus_groups  - anas_groups  - columba_groups
only_B  = anas_groups    - gallus_groups - columba_groups
only_C  = columba_groups - gallus_groups - anas_groups
AB_only = (gallus_groups & anas_groups)    - columba_groups
AC_only = (gallus_groups & columba_groups) - anas_groups
BC_only = (anas_groups   & columba_groups) - gallus_groups
ABC     = gallus_groups & anas_groups & columba_groups

n_only_A = len(only_A);  n_only_B = len(only_B);  n_only_C = len(only_C)
n_AB = len(AB_only);     n_AC = len(AC_only);      n_BC = len(BC_only)
n_ABC = len(ABC)
total_G = len(gallus_groups); total_A = len(anas_groups); total_C = len(columba_groups)

print(f"Gallus only:{n_only_A}, Anas only:{n_only_B}, Columba only:{n_only_C}")
print(f"G+A:{n_AB}, G+C:{n_AC}, A+C:{n_BC}, All three:{n_ABC}")
print(f"Total G={total_G}, A={total_A}, C={total_C}")

# ── Figure ────────────────────────────────────────────────────────────────────
matplotlib.rcParams.update({
    "font.family":       "Times New Roman",
    "font.size":          9,
    "pdf.fonttype":       42,
    "svg.fonttype":       "none",
})

fig = plt.figure(figsize=(5.0, 7.5))
gs  = gridspec.GridSpec(3, 1, figure=fig, height_ratios=[5.5, 2, 1], hspace=0.50)

# ── Panel A: Equal-circle Venn ────────────────────────────────────────────────
ax_venn = fig.add_subplot(gs[0])
ax_venn.set_aspect("equal")
ax_venn.axis("off")
ax_venn.set_xlim(-1.55, 1.55)
ax_venn.set_ylim(-1.55, 1.25)

r = 0.82
cx_G, cy_G = -0.42,  0.28
cx_A, cy_A =  0.42,  0.28
cx_C, cy_C =  0.00, -0.50
alpha = 0.55

for cx, cy, sp in [(cx_G, cy_G, "Gallus"), (cx_A, cy_A, "Anas"), (cx_C, cy_C, "Columba")]:
    ax_venn.add_patch(Circle((cx, cy), r, fc=COLORS[sp], ec="white",
                             linewidth=1.2, alpha=alpha, zorder=2))

lbl_kw = dict(fontsize=10, fontweight="bold", color="white",
              ha="center", va="center", zorder=5)
ax_venn.text(cx_G - 0.50, cy_G + 0.32, str(n_only_A), **lbl_kw)
ax_venn.text(cx_A + 0.50, cy_A + 0.32, str(n_only_B), **lbl_kw)
ax_venn.text(cx_C,        cy_C - 0.42, str(n_only_C), **lbl_kw)
ax_venn.text( 0.00,  0.60, str(n_AB),  **lbl_kw)
ax_venn.text(-0.42, -0.18, str(n_AC),  **lbl_kw)
ax_venn.text( 0.42, -0.18, str(n_BC),  **lbl_kw)
ax_venn.text( 0.00,  0.08, str(n_ABC), **lbl_kw)

sp_kw = dict(ha="center", va="center", fontsize=11, fontweight="bold", zorder=6)
ax_venn.text(cx_G - 0.90, cy_G + 0.88, "Gallus",  color=COLORS["Gallus"],  **sp_kw)
ax_venn.text(cx_A + 0.90, cy_A + 0.88, "Anas",    color=COLORS["Anas"],    **sp_kw)
ax_venn.text(cx_C,        cy_C - 1.02, "Columba", color=COLORS["Columba"], **sp_kw)

# ── Panel B: Bar chart ────────────────────────────────────────────────────────
ax_bar = fig.add_subplot(gs[1])
species_names = ["Gallus", "Anas", "Columba"]
totals        = [total_G, total_A, total_C]
bar_colors    = [COLORS[s] for s in species_names]
bar_x         = np.arange(len(species_names))

bars = ax_bar.bar(bar_x, totals, color=bar_colors, width=0.55, edgecolor="none", zorder=3)
for bar, val in zip(bars, totals):
    ax_bar.text(bar.get_x() + bar.get_width()/2, bar.get_height()*0.5,
                str(val), ha="center", va="center", fontsize=8, color="white", fontweight="bold")

ax_bar.set_xticks(bar_x)
ax_bar.set_xticklabels(species_names, fontsize=9)
ax_bar.set_ylabel("No. of orthogroups", fontsize=8)
ax_bar.set_title("Size of each list", fontsize=8, style="italic", pad=3)
ax_bar.set_ylim(0, max(totals) * 1.15)
ax_bar.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax_bar.spines[["right", "top"]].set_visible(False)
ax_bar.tick_params(axis="both", labelsize=8)
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
for i, (val, col, lbl) in enumerate(zip(shared_values, shared_colors, shared_labels)):
    ax_hbar.barh(0, val, left=left, color=col, height=0.5, edgecolor="none")
    if val > 0:
        # Last segment: left-align label so it doesn't overflow
        if i == len(shared_values) - 1:
            ax_hbar.text(left + val * 0.05, 0, lbl,
                         ha="left", va="center", fontsize=7, color="#444444", fontweight="bold")
        else:
            ax_hbar.text(left + val/2, 0, lbl,
                         ha="center", va="center", fontsize=7, color="#444444", fontweight="bold")
    left += val

ax_hbar.set_xlim(0, left * 1.06)
ax_hbar.set_yticks([])
ax_hbar.set_xlabel("Number of shared orthogroups", fontsize=8)
ax_hbar.set_title("Number of elements: specific (1) or shared by 2, 3, ... lists",
                  fontsize=7.5, style="italic", pad=3)
ax_hbar.spines[["right", "top", "left"]].set_visible(False)
ax_hbar.tick_params(axis="x", labelsize=8)

# ── Save ───────────────────────────────────────────────────────────────────────
save_fig(fig, "Fig2A")
plt.close()
