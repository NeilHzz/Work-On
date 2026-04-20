#!/usr/bin/env python3
"""
单物种 GO 富集热图 — 正方形色块拼接（展示所有 GO 条目）
横轴: GO terms（BP → CC → MF）
纵轴: Gallus, Anas, Columba（3行）
颜色: 由 GO 分类决定色相，P 值大→深，P 值小→浅，无数据留白
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
from matplotlib.colors import LinearSegmentedColormap, to_rgb, Normalize
from matplotlib.cm import ScalarMappable

# ── 分类配色（柔和度对齐 Gallus #B54664 / Anas #7895C1 / Columba #F0C284）──
CAT_COLORS = {
    "BP": "#809EC0",
    "CC": "#D9A96C",
    "MF": "#7EAF82",
}

def make_cmap(hex_color):
    """白色 → 目标色"""
    return LinearSegmentedColormap.from_list("c", [np.ones(3), to_rgb(hex_color)], N=256)

CAT_CMAPS = {k: make_cmap(v) for k, v in CAT_COLORS.items()}

# ── 读取数据 ──
df = pd.read_excel("GO_Enrichment_Summary.xlsx")

single_groups = ["Gallus (chicken only)", "Anas (duck only)", "Columba (pigeon only)"]
group_labels = ["Gallus", "Anas", "Columba"]
group_map = dict(zip(single_groups, group_labels))

ds = df[df["Group"].isin(single_groups)].copy()

cat_order = [
    ("biological_process",  "BP"),
    ("cellular_component",  "CC"),
    ("molecular_function",  "MF"),
]

# ── 每个分类中，展示所有 GO 条目 ──
all_terms = []       # (x_index, description, cat_tag)
cat_ranges = {}      # {tag: (start_x, end_x)}
cat_data = {}        # {cat_tag: (plot_df, desc_to_x)}
x_pos = 0

for cat_key, cat_tag in cat_order:
    sub = ds[ds["Category"] == cat_key].copy()
    if sub.empty:
        continue

    # 所有条目，按最小 p_value 排序
    desc_sorted = (
        sub.groupby("Description")["p_value"]
        .min()
        .sort_values()
        .index
        .tolist()
    )

    start_x = x_pos
    desc_to_x = {}
    for d in desc_sorted:
        desc_to_x[d] = x_pos
        all_terms.append((x_pos, d, cat_tag))
        x_pos += 1

    cat_ranges[cat_tag] = (start_x, x_pos - 1)
    cat_data[cat_tag] = (sub, desc_to_x)

total_terms = x_pos
n_groups = len(group_labels)
grp_idx = {g: i for i, g in enumerate(group_labels)}

# 全局 p_value 范围（-log10 显示范围裁剪到 2~35）
disp_lo = 2     # -log10(P) 显示下限
disp_hi = 35    # -log10(P) 显示上限
pv_min_log = -disp_hi
pv_max_log = -disp_lo
pv_range = pv_max_log - pv_min_log if pv_max_log != pv_min_log else 1.0

# ── 绘图 ──
cell = 1.0
fig, ax = plt.subplots(figsize=(18, 6))

# 绘制正方形色块
for cat_tag, (plot_df, desc_to_x) in cat_data.items():
    cmap = CAT_CMAPS[cat_tag]
    for _, row in plot_df.iterrows():
        g_label = group_map[row["Group"]]
        desc = row["Description"]
        if desc not in desc_to_x:
            continue
        col = desc_to_x[desc]
        row_i = grp_idx[g_label]
        pv = row["p_value"]

        # P 值大 → 深色 (alpha=1)，P 值小 → 浅色 (alpha 低)
        norm_val = (np.log10(pv) - pv_min_log) / pv_range
        norm_val = np.clip(norm_val, 0, 1)
        alpha = 0.1 + 0.9 * (norm_val ** 0.5)  # 透明度 0.1~1.0

        color = to_rgb(CAT_COLORS[cat_tag])
        rect = Rectangle(
            (col, row_i), cell, cell,
            facecolor=color, alpha=alpha, edgecolor="white", linewidth=1.5, zorder=2,
        )
        ax.add_patch(rect)

# 分类分隔线
for cat_tag, (sx, ex) in cat_ranges.items():
    if sx > 0:
        ax.axvline(sx, color="grey", linewidth=0.8, linestyle="--", alpha=0.5, zorder=1)

# ── 坐标轴 ──
CAT_LABEL_COLOR = {
    "BP": "#5A7EA0",
    "CC": "#B08540",
    "MF": "#4E8A55",
}

x_labels = [t[1] for t in all_terms]
x_cats   = [t[2] for t in all_terms]

ax.set_xticks([i + 0.5 for i in range(total_terms)])
ax.set_xticklabels(x_labels, rotation=-45, ha="left", fontsize=9,
                   rotation_mode="anchor", fontweight="bold")
for tick_label, cat in zip(ax.get_xticklabels(), x_cats):
    tick_label.set_color(CAT_LABEL_COLOR[cat])

ax.set_yticks([i + 0.5 for i in range(n_groups)])
ax.set_yticklabels(group_labels, fontsize=12, fontweight="bold")

ax.set_xlim(0, total_terms)
ax.set_ylim(0, n_groups)
ax.set_box_aspect(n_groups / total_terms)

ax.invert_yaxis()

ax.set_title("GO Enrichment — Species-Specific Orthologs", fontsize=14,
             fontweight="bold", pad=20)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.tick_params(left=False, bottom=False)
ax.tick_params(axis='x', pad=4)

plt.subplots_adjust(right=0.95, bottom=0.35)
plt.savefig("Fig_GO_heatmap_single_species.png", dpi=300, bbox_inches="tight", pad_inches=0.3)
plt.savefig("Fig_GO_heatmap_single_species.pdf", bbox_inches="tight", pad_inches=0.3)
plt.close()
print("Done: Fig_GO_heatmap_single_species.png / .pdf")
