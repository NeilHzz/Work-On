"""
Venn diagram for three-species orthogroup analysis – manual equal circles.
Nature Communications publication quality.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker
from matplotlib.patches import Circle

# ── Colors ────────────────────────────────────────────────────────────────────
COLORS = {"Gallus": "#B54664", "Anas": "#7895C1", "Columba": "#F0C284"}

# ── Parse Orthogroups ─────────────────────────────────────────────────────────
ortho_file = os.path.join(os.path.dirname(__file__), "Orthogroups.txt.gz.txt")
G, A, C = set(), set(), set()
with open(ortho_file) as fh:
    for i, line in enumerate(fh):
        if "Gallus|"  in line: G.add(i)
        if "Anas|"    in line: A.add(i)
        if "Columba|" in line: C.add(i)

n_G   = len(G - A - C)
n_A   = len(A - G - C)
n_C   = len(C - G - A)
n_GA  = len((G & A) - C)
n_GC  = len((G & C) - A)
n_AC  = len((A & C) - G)
n_all = len(G & A & C)
tot_G, tot_A, tot_C = len(G), len(A), len(C)

# ── Style ─────────────────────────────────────────────────────────────────────
matplotlib.rcParams.update({
    "font.family": "Arial", "font.size": 7, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "pdf.fonttype": 42, "svg.fonttype": "none",
})

fig = plt.figure(figsize=(3.5, 5.4))
gs  = gridspec.GridSpec(3, 1, figure=fig, height_ratios=[5.5, 2, 1], hspace=0.50)

# ── Panel A: Venn ─────────────────────────────────────────────────────────────
ax = fig.add_subplot(gs[0])
ax.set_aspect("equal"); ax.axis("off")
ax.set_xlim(-1.3, 1.3); ax.set_ylim(-1.15, 1.1)

r = 0.62
# Equilateral triangle centers
cx_G, cy_G = -0.35,  0.22
cx_A, cy_A =  0.35,  0.22
cx_C, cy_C =  0.00, -0.38

for cx, cy, sp in [(cx_G, cy_G, "Gallus"), (cx_A, cy_A, "Anas"), (cx_C, cy_C, "Columba")]:
    ax.add_patch(Circle((cx, cy), r, fc=COLORS[sp], ec="white",
                        linewidth=0.9, alpha=0.55, zorder=2))

# Region number labels
lkw = dict(fontsize=6.5, fontweight="bold", color="white",
           ha="center", va="center", zorder=5)
ax.text(cx_G - 0.37, cy_G + 0.12, str(n_G),   **lkw)   # Gallus only
ax.text(cx_A + 0.37, cy_A + 0.12, str(n_A),   **lkw)   # Anas only
ax.text(cx_C,        cy_C - 0.36, str(n_C),   **lkw)   # Columba only
ax.text( 0.00,  0.58, str(n_GA),  **lkw)                # G+A
ax.text(-0.37, -0.22, str(n_GC),  **lkw)                # G+C
ax.text( 0.37, -0.22, str(n_AC),  **lkw)                # A+C
ax.text( 0.00,  0.03, str(n_all), **lkw)                # All three

# Species name labels outside the circles
skw = dict(ha="center", va="center", fontsize=7.5, fontweight="bold", zorder=6)
ax.text(cx_G - 0.55, cy_G + 0.52, "Gallus",  color=COLORS["Gallus"],  **skw)
ax.text(cx_A + 0.55, cy_A + 0.52, "Anas",    color=COLORS["Anas"],    **skw)
ax.text(cx_C,        cy_C - 0.70, "Columba", color=COLORS["Columba"], **skw)

# ── Panel B: Bar chart ────────────────────────────────────────────────────────
ax2 = fig.add_subplot(gs[1])
bx  = np.arange(3)
tots = [tot_G, tot_A, tot_C]
bcs  = [COLORS[s] for s in ("Gallus", "Anas", "Columba")]

bars = ax2.bar(bx, tots, color=bcs, width=0.55, edgecolor="none", zorder=3)
for b, v in zip(bars, tots):
    ax2.text(b.get_x() + b.get_width()/2, b.get_height()*0.5, str(v),
             ha="center", va="center", fontsize=6, color="white", fontweight="bold")

ax2.set_xticks(bx)
ax2.set_xticklabels(["Gallus", "Anas", "Columba"], fontsize=7)
ax2.set_ylabel("No. of orthogroups", fontsize=6.5)
ax2.set_title("Size of each list", fontsize=7, style="italic", pad=3)
ax2.set_ylim(0, max(tots) * 1.15)
ax2.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax2.spines[["right", "top"]].set_visible(False)
ax2.tick_params(labelsize=6)
ax2.set_axisbelow(True)
ax2.yaxis.grid(True, linewidth=0.4, color="#dddddd", zorder=0)

# ── Panel C: Horizontal stacked bar ──────────────────────────────────────────
ax3 = fig.add_subplot(gs[2])
sv = [n_all, n_GA + n_GC + n_AC, n_G + n_A + n_C]
sc = ["#A89BC8", "#C8B8DC", "#E8D8F0"]
sl = [str(sv[0]), str(sv[1]), f"1 ({sv[2]})"]

left = 0
for v, c, l in zip(sv, sc, sl):
    ax3.barh(0, v, left=left, color=c, height=0.5, edgecolor="none")
    if v > 0:
        ax3.text(left + v/2, 0, l, ha="center", va="center",
                 fontsize=6, color="#444444", fontweight="bold")
    left += v

ax3.set_xlim(0, left)
ax3.set_yticks([])
ax3.set_xlabel("Number of shared orthogroups", fontsize=6.5)
ax3.set_title("Number of elements: specific (1) or shared by 2, 3, ... lists",
              fontsize=6.5, style="italic", pad=3)
ax3.spines[["right", "top", "left"]].set_visible(False)
ax3.tick_params(axis="x", labelsize=6)

# ── Save ──────────────────────────────────────────────────────────────────────
base = os.path.join(os.path.dirname(__file__), "Fig_venn_orthogroups")
fig.savefig(base + ".pdf", dpi=300, bbox_inches="tight")
fig.savefig(base + ".svg", bbox_inches="tight")
fig.savefig(base + ".png", dpi=300, bbox_inches="tight")
print(f"Saved {base}.pdf / .svg / .png")
