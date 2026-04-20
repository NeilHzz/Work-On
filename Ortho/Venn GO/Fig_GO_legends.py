#!/usr/bin/env python3
"""
单独生成 GO 图例：
1. GO Category 图例（BP / CC / MF）
2. P-value 颜色条 — pairwise（50~175）
3. P-value 颜色条 — single species（2~35）
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.cm import ScalarMappable

CAT_COLORS = {
    "BP": "#809EC0",
    "CC": "#D9A96C",
    "MF": "#7EAF82",
}

# ═══════════════════════════════════════
# 1) GO Category 图例
# ═══════════════════════════════════════
fig_leg, ax_leg = plt.subplots(figsize=(3.2, 1.2))
ax_leg.axis("off")
legend_patches = [
    Patch(facecolor=CAT_COLORS["BP"], edgecolor="white", label="BP (Biological Process)"),
    Patch(facecolor=CAT_COLORS["CC"], edgecolor="white", label="CC (Cellular Component)"),
    Patch(facecolor=CAT_COLORS["MF"], edgecolor="white", label="MF (Molecular Function)"),
]
leg = ax_leg.legend(handles=legend_patches, loc="center",
                    fontsize=10, frameon=True, edgecolor="#cccccc", fancybox=False,
                    title="GO Category", title_fontsize=11)
leg.get_frame().set_linewidth(0.6)
fig_leg.savefig("Legend_GO_Category.png", dpi=300, bbox_inches="tight", pad_inches=0.1)
fig_leg.savefig("Legend_GO_Category.pdf", bbox_inches="tight", pad_inches=0.1)
plt.close(fig_leg)
print("Done: Legend_GO_Category.png / .pdf")

# ═══════════════════════════════════════
# 2) P-value 颜色条 — pairwise (50~175)
# ═══════════════════════════════════════
gray_cmap = LinearSegmentedColormap.from_list("pv", ["#f0f0f0", "#333333"], N=256)

fig_cb1, ax_cb1 = plt.subplots(figsize=(0.6, 2.5))
ax_cb1.axis("off")
cax1 = fig_cb1.add_axes([0.15, 0.08, 0.25, 0.82])
sm1 = ScalarMappable(cmap=gray_cmap, norm=Normalize(vmin=50, vmax=175))
sm1.set_array([])
cb1 = fig_cb1.colorbar(sm1, cax=cax1, orientation="vertical")
cb1.ax.tick_params(labelsize=8)
cb1.set_label("$-\\log_{10}$(P value)", fontsize=10, labelpad=6)
fig_cb1.savefig("Legend_Pvalue_pairwise.png", dpi=300, bbox_inches="tight", pad_inches=0.15)
fig_cb1.savefig("Legend_Pvalue_pairwise.pdf", bbox_inches="tight", pad_inches=0.15)
plt.close(fig_cb1)
print("Done: Legend_Pvalue_pairwise.png / .pdf")

# ═══════════════════════════════════════
# 3) P-value 颜色条 — single species (2~35)
# ═══════════════════════════════════════
fig_cb2, ax_cb2 = plt.subplots(figsize=(0.6, 2.5))
ax_cb2.axis("off")
cax2 = fig_cb2.add_axes([0.15, 0.08, 0.25, 0.82])
sm2 = ScalarMappable(cmap=gray_cmap, norm=Normalize(vmin=2, vmax=35))
sm2.set_array([])
cb2 = fig_cb2.colorbar(sm2, cax=cax2, orientation="vertical")
cb2.ax.tick_params(labelsize=8)
cb2.set_label("$-\\log_{10}$(P value)", fontsize=10, labelpad=6)
fig_cb2.savefig("Legend_Pvalue_single.png", dpi=300, bbox_inches="tight", pad_inches=0.15)
fig_cb2.savefig("Legend_Pvalue_single.pdf", bbox_inches="tight", pad_inches=0.15)
plt.close(fig_cb2)
print("Done: Legend_Pvalue_single.png / .pdf")
