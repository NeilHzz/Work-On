#!/usr/bin/env python3
"""
GO 富集可视化 — Nature Communications 风格
============================================
合并自 nc_visualization.py + plot_venn_go_style.py

默认执行模式：自动生成全套 6 张 NC 风格图表
  Fig1 – 水平条形图面板（6 个物种/组合）
  Fig2 – 单物种气泡图（Gallus / Anas / Columba）
  Fig3 – 两物种共有气泡图（A&C / G&C / G&A）
  Fig4 – 韦恩图（三物种 GO term 重叠，分 BP/MF/CC）
  Fig5 – GO term 数量汇总堆叠条形图
  Fig6 – 热图总览（top 20 全局最显著 GO terms）

命令行模式（传入参数时启用，来自原 plot_venn_go_style.py）：
  python Fig_venn_go_visualization.py --help
"""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

# ─── Nature Communications 全局样式 ─────────────────────────────────────────
NC_STYLE = {
    "font.family": "Times New Roman",
    "font.sans-serif":       ["Times New Roman", "DejaVu Sans"],
    "font.size":             8,
    "axes.titlesize":        9,
    "axes.labelsize":        8,
    "xtick.labelsize":       7,
    "ytick.labelsize":       7,
    "legend.fontsize":       7,
    "legend.title_fontsize": 7.5,
    "axes.linewidth":        0.8,
    "xtick.major.width":     0.8,
    "ytick.major.width":     0.8,
    "xtick.major.size":      3.0,
    "ytick.major.size":      3.0,
    "xtick.direction":       "out",
    "ytick.direction":       "out",
    "axes.spines.top":       False,
    "axes.spines.right":     False,
    "axes.grid":             False,
    "figure.dpi":            300,
    "savefig.dpi":           300,
    "savefig.bbox":          "tight",
    "pdf.fonttype":          42,
    "svg.fonttype":          "none",
}
plt.rcParams.update(NC_STYLE)

# ─── 颜色方案 ────────────────────────────────────────────────────────────────
ONTOLOGY_COLOR = {
    "biological_process": "#4DBBD5",
    "molecular_function": "#E64B35",
    "cellular_component": "#00A087",
}
ONTOLOGY_ABBR = {
    "biological_process": "BP",
    "molecular_function": "MF",
    "cellular_component": "CC",
}
GROUP_COLOR = {
    "Gallus":  "#B54664",
    "Anas":    "#7895C1",
    "Columba": "#F0C284",
    "A&C":     "#3C5488",
    "G&C":     "#F39B7F",
    "G&A":     "#8491B4",
}
GROUP_LABEL = {
    "Gallus":  "Gallus",
    "Anas":    "Anas",
    "Columba": "Columba",
    "A&C":     "Anas \u2229 Columba",
    "G&C":     "Gallus \u2229 Columba",
    "G&A":     "Gallus \u2229 Anas",
}

# ─── 路径 ────────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).parent
DATA_DIR = Path(r"D:\system_folder\Desktop\Work On/Ortho/Venn GO")
OUT_DIR  = Path(r"D:\system_folder\Desktop\Work On\Figure\png")
OUT_DIR.mkdir(exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
# 共用：数据读取
# ══════════════════════════════════════════════════════════════════════════════
def read_enrichment(path: Path) -> pd.DataFrame:
    """读取富集结果 tsv，统一格式并计算 -log10(p)"""
    df = pd.read_csv(path, sep="\t", header=None)
    if df.shape[1] < 5:
        raise ValueError(f"文件列数不足5列: {path}")
    df = df.iloc[:, :5].copy()
    df.columns = ["go_id", "count", "term", "ontology", "p_value"]
    df["count"]   = pd.to_numeric(df["count"],   errors="coerce")
    df["p_value"] = pd.to_numeric(df["p_value"], errors="coerce")
    df = df.dropna(subset=["count", "p_value", "term", "ontology"])
    df = df[df["p_value"] > 0]
    df["neglog10p"] = -np.log10(df["p_value"])
    return df


def load_all(data_dir: Path) -> dict:
    """加载全部6组富集文件"""
    files = {
        "Gallus":  "Gallus_enrichment.txt",
        "Anas":    "Anas_enrichment.txt",
        "Columba": "Columba_enrichment.txt",
        "A&C":     "A&C_enrichment.txt",
        "G&C":     "G&C_enrichment.txt",
        "G&A":     "G&A_enrichment.txt",
    }
    return {k: read_enrichment(data_dir / v) for k, v in files.items()}


# 别名（兼容 plot_venn_go_style 的调用方式）
load_frames = load_all


def wrap_term(term: str, maxlen: int = 34) -> str:
    """超长 GO term 末尾截断并加省略号"""
    return term if len(term) <= maxlen else term[:maxlen - 1] + "\u2026"


def format_p_ticks_from_log10(ticks):
    """将 -log10(p) 刻度格式化为科学计数法"""
    labels = []
    for t in ticks:
        p = 10 ** (-t)
        exp = int(np.floor(np.log10(p))) if p > 0 else 0
        coeff = p / (10 ** exp)
        if abs(coeff - 1) < 1e-6:
            labels.append(rf"$1\times10^{{{exp}}}$")
        else:
            labels.append(rf"${coeff:.1f}\times10^{{{exp}}}$")
    return labels


# ══════════════════════════════════════════════════════════════════════════════
# NC 风格自动生成：Fig 1 — 水平条形图面板（6 组）
# ══════════════════════════════════════════════════════════════════════════════
def plot_hbar_panel(frames: dict, out: Path, top_n: int = 8):
    group_order = ["Gallus", "Anas", "Columba", "A&C", "G&C", "G&A"]
    fig, axes = plt.subplots(2, 3, figsize=(180 / 25.4, 145 / 25.4))
    axes = axes.flatten()

    for ax_idx, grp in enumerate(group_order):
        ax = axes[ax_idx]
        df = (frames[grp]
              .sort_values("neglog10p", ascending=False)
              .drop_duplicates(subset="term")
              .head(top_n)
              .sort_values("neglog10p", ascending=True))

        colors_bar = [ONTOLOGY_COLOR.get(o, "#aaaaaa") for o in df["ontology"]]
        y_pos = np.arange(len(df))
        ax.barh(y_pos, df["neglog10p"], color=colors_bar, height=0.62,
                edgecolor="white", linewidth=0.3, zorder=3)
        ax.set_yticks(y_pos)
        ax.set_yticklabels([wrap_term(t, 30) for t in df["term"]], fontsize=6)
        ax.set_xlabel("\u2212log\u2081\u2080(P)", fontsize=7)
        ax.set_title(GROUP_LABEL[grp], fontsize=8.5, fontweight="bold",
                     color=GROUP_COLOR[grp], pad=3)
        ax.tick_params(axis="x", labelsize=6.5)
        ax.set_xlim(left=0)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.xaxis.grid(True, color="#ebebeb", linewidth=0.5, zorder=0)
        ax.set_axisbelow(True)
        for bar, v in zip(ax.patches, df["neglog10p"]):
            ax.text(v + 0.05, bar.get_y() + bar.get_height() / 2,
                    f"{v:.1f}", va="center", fontsize=5.5, color="#555555")

    legend_patches = [
        mpatches.Patch(facecolor=ONTOLOGY_COLOR[o],
                       label=ONTOLOGY_ABBR[o], linewidth=0)
        for o in ["biological_process", "molecular_function", "cellular_component"]
    ]
    fig.legend(handles=legend_patches, title="Ontology",
               loc="lower center", ncol=3, frameon=False,
               fontsize=7, title_fontsize=7.5,
               bbox_to_anchor=(0.5, -0.01))
    plt.tight_layout(rect=[0, 0.05, 1, 1], w_pad=2.2, h_pad=2.0)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    print(f"  \u2713 {out.name}")


# ══════════════════════════════════════════════════════════════════════════════
# NC 风格自动生成：Fig 2 & 3 — GO 富集气泡图
# ══════════════════════════════════════════════════════════════════════════════
def plot_bubble_panel(frames: dict, groups: list, out: Path,
                      top_n_per_group: int = 8, title: str = ""):
    rows = []
    for grp in groups:
        df = (frames[grp]
              .sort_values("neglog10p", ascending=False)
              .drop_duplicates(subset="term")
              .head(top_n_per_group)
              .copy())
        df["group"] = grp
        rows.append(df)
    combined = pd.concat(rows, ignore_index=True)
    if combined.empty:
        print(f"  \u26a0 {out.name} \u2014 \u65e0\u6570\u636e\uff0c\u8df3\u8fc7")
        return

    term_order = (combined.groupby("term")["neglog10p"].max()
                  .sort_values(ascending=True).index.tolist())
    x_map = {g: i for i, g in enumerate(groups)}
    y_map = {t: i for i, t in enumerate(term_order)}
    combined["x"] = combined["group"].map(x_map)
    combined["y"] = combined["term"].map(y_map)

    vmin = combined["neglog10p"].min()
    vmax = combined["neglog10p"].max()
    if np.isclose(vmin, vmax):
        vmax = vmin + 1

    cmax  = float(combined["count"].max())
    s_arr = (combined["count"] / cmax) * 240 + 12
    n_terms = len(term_order)
    n_grps  = len(groups)
    fig_h   = max(3.0, n_terms * 0.34 + 1.8)
    fig_w   = max(4.0, n_grps  * 0.65 + 4.5)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    sc = ax.scatter(combined["x"], combined["y"], s=s_arr,
                    c=combined["neglog10p"], cmap="RdBu_r",
                    vmin=vmin, vmax=vmax,
                    alpha=0.88, edgecolors="white", linewidths=0.3, zorder=3)
    for row in combined.itertuples():
        ax.scatter(row.x, row.y, marker="s", s=4.5,
                   c=ONTOLOGY_COLOR.get(row.ontology, "#999"),
                   zorder=4, alpha=0.7)

    ax.set_xticks(range(n_grps))
    ax.set_xticklabels([GROUP_LABEL[g] for g in groups],
                       fontsize=7.5, fontstyle="italic")
    ax.set_yticks(range(n_terms))
    ax.set_yticklabels([wrap_term(t, 38) for t in term_order], fontsize=6.5)
    ax.set_xlim(-0.65, n_grps - 0.35)
    ax.set_ylim(-0.6, n_terms - 0.4)
    ax.grid(True, color="#ebebeb", linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    if title:
        ax.set_title(title, fontsize=9, fontweight="bold", pad=5)

    cbar = fig.colorbar(sc, ax=ax, fraction=0.025, pad=0.02, shrink=0.45,
                        anchor=(0.0, 1.0))
    cbar.ax.set_title("\u2212log\u2081\u2080(P)", fontsize=7, pad=3)
    cbar.ax.tick_params(labelsize=6)

    count_vals = np.unique(combined["count"].astype(int))
    idxs = np.unique(np.round(np.linspace(0, len(count_vals) - 1, 4)).astype(int))
    c_levels = count_vals[idxs]
    handles_c = [
        Line2D([0], [0], marker="o", ls="none",
               markerfacecolor="#888888", markeredgecolor="none",
               markersize=np.sqrt((c / cmax) * 240 + 12) * 0.85)
        for c in c_levels
    ]
    ax.legend(handles_c, [str(int(c)) for c in c_levels],
              title="Count", frameon=False, fontsize=6.5, title_fontsize=7,
              loc="upper left", bbox_to_anchor=(1.14, 0.60),
              handletextpad=0.5, labelspacing=0.7)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    print(f"  [OK] {out.name}")


# ══════════════════════════════════════════════════════════════════════════════
# NC 风格自动生成：Fig 4 — 韦恩图
# ══════════════════════════════════════════════════════════════════════════════
def _venn3_draw(counts: dict, labels: list, colors: list, ax, title: str = ""):
    from matplotlib.patches import Circle
    r = 0.34
    centers = [(-0.20, 0.14), (0.20, 0.14), (0.0, -0.17)]
    for i, (cx, cy) in enumerate(centers):
        ax.add_patch(Circle((cx, cy), r, alpha=0.28,
                            facecolor=colors[i], edgecolor=colors[i],
                            linewidth=1.2))
    ax.set_xlim(-0.65, 0.65)
    ax.set_ylim(-0.62, 0.62)
    ax.set_aspect("equal")
    ax.axis("off")
    ann = dict(ha="center", va="center", fontweight="bold")
    ax.text(-0.36,  0.28,  str(counts["only_A"]), fontsize=9, color=colors[0], **ann)
    ax.text( 0.36,  0.28,  str(counts["only_B"]), fontsize=9, color=colors[1], **ann)
    ax.text( 0.00, -0.48,  str(counts["only_C"]), fontsize=9, color=colors[2], **ann)
    ax.text( 0.00,  0.28,  str(counts["AB_C"]),   fontsize=8, color="#444444",  **ann)
    ax.text(-0.18, -0.10,  str(counts["AC_B"]),   fontsize=8, color="#444444",  **ann)
    ax.text( 0.18, -0.10,  str(counts["BC_A"]),   fontsize=8, color="#444444",  **ann)
    ax.text( 0.00,  0.07,  str(counts["ABC"]),    fontsize=10, color="#111111", **ann)
    ax.text(-0.50,  0.52, labels[0], color=colors[0], fontsize=8,
            fontweight="bold", ha="center", fontstyle="italic")
    ax.text( 0.50,  0.52, labels[1], color=colors[1], fontsize=8,
            fontweight="bold", ha="center", fontstyle="italic")
    ax.text( 0.00, -0.60, labels[2], color=colors[2], fontsize=8,
            fontweight="bold", ha="center", fontstyle="italic")
    if title:
        ax.set_title(title, fontsize=9, fontweight="bold", pad=4)


def plot_venn_panel(frames: dict, out: Path):
    ont_list  = [("biological_process", "BP"),
                 ("molecular_function", "MF"),
                 ("cellular_component", "CC")]
    species   = ["Gallus", "Anas", "Columba"]
    sp_colors = [GROUP_COLOR[s] for s in species]
    fig, axes = plt.subplots(1, 3, figsize=(180 / 25.4, 68 / 25.4))

    for ax, (ont, abbr) in zip(axes, ont_list):
        def n(grp):
            return int((frames[grp]["ontology"] == ont).sum())
        counts = dict(only_A=n("Gallus"), only_B=n("Anas"), only_C=n("Columba"),
                      AB_C=n("G&A"), AC_B=n("G&C"), BC_A=n("A&C"), ABC=0)
        if sum(counts.values()) == 0:
            ax.axis("off"); ax.set_title(abbr, fontsize=9, fontweight="bold"); continue
        _venn3_draw(counts, species, sp_colors, ax=ax, title=abbr)

    plt.tight_layout(w_pad=0.5)
    fig.savefig(out, dpi=300)
    plt.close(fig)
    print(f"  [OK] {out.name}")


# ══════════════════════════════════════════════════════════════════════════════
# NC 风格自动生成：Fig 5 — 汇总堆叠条形图
# ══════════════════════════════════════════════════════════════════════════════
def plot_summary_bar(frames: dict, out: Path):
    group_order = ["Gallus", "Anas", "Columba", "A&C", "G&C", "G&A"]
    ont_list    = ["biological_process", "molecular_function", "cellular_component"]
    data   = {grp: {ont: int((frames[grp]["ontology"] == ont).sum()) for ont in ont_list}
              for grp in group_order}
    df_plot = pd.DataFrame(data, index=ont_list).T
    fig, ax = plt.subplots(figsize=(88 / 25.4, 68 / 25.4))
    bottom  = np.zeros(len(group_order))
    x_pos   = np.arange(len(group_order))
    for ont in ont_list:
        vals = df_plot[ont].values.astype(float)
        ax.bar(x_pos, vals, bottom=bottom, color=ONTOLOGY_COLOR[ont],
               label=ONTOLOGY_ABBR[ont], width=0.58, edgecolor="white", linewidth=0.4)
        for xi, (v, b) in enumerate(zip(vals, bottom)):
            if v > 0:
                ax.text(xi, b + v / 2, str(int(v)),
                        ha="center", va="center", fontsize=6,
                        color="white", fontweight="bold")
        bottom += vals
    ax.set_xticks(x_pos)
    ax.set_xticklabels([GROUP_LABEL[g] for g in group_order],
                       rotation=35, ha="right", fontsize=6.5, fontstyle="italic")
    ax.set_ylabel("Enriched GO terms (n)", fontsize=7)
    ax.yaxis.grid(True, color="#ebebeb", linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.spines["left"].set_linewidth(0.8)
    ax.legend(title="Ontology", frameon=False,
              fontsize=6.5, title_fontsize=7, loc="upper right")
    plt.tight_layout()
    fig.savefig(out, dpi=300)
    plt.close(fig)
    print(f"  [OK] {out.name}")


# ══════════════════════════════════════════════════════════════════════════════
# NC 风格自动生成：Fig 6 — 热图总览
# ══════════════════════════════════════════════════════════════════════════════
def plot_heatmap_overview(frames: dict, out: Path, top_n: int = 20):
    group_order = ["Gallus", "Anas", "Columba", "A&C", "G&C", "G&A"]
    all_df = pd.concat([frames[g].assign(group=g) for g in group_order], ignore_index=True)
    top_terms = (all_df.groupby("term")["p_value"].min()
                 .sort_values().head(top_n).index.tolist())
    mat = pd.DataFrame(0.0, index=top_terms, columns=group_order)
    for grp in group_order:
        sub    = frames[grp].set_index("term")["neglog10p"]
        common = sub.index.intersection(top_terms)
        mat.loc[common, grp] = sub[common]

    n_terms = len(top_terms)
    n_grps  = len(group_order)
    fig_h   = max(3.5, n_terms * 0.29 + 1.8)
    fig_w   = max(4.0, n_grps  * 0.62 + 4.2)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    cmap = plt.cm.YlOrRd
    norm = mcolors.PowerNorm(gamma=0.55, vmin=0, vmax=max(mat.values.max(), 1))
    im   = ax.imshow(mat.values, aspect="auto", cmap=cmap, norm=norm)
    ax.set_xticks(range(n_grps))
    ax.set_xticklabels([GROUP_LABEL[g] for g in group_order],
                       rotation=35, ha="right", fontsize=7, fontstyle="italic")
    ax.set_yticks(range(n_terms))
    ax.set_yticklabels([wrap_term(t, 40) for t in top_terms], fontsize=6.5)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)
    for i in range(n_terms):
        for j in range(n_grps):
            v = mat.iloc[i, j]
            if v > 0:
                ax.text(j, i, f"{v:.0f}", ha="center", va="center",
                        fontsize=5.5,
                        color="white" if v > mat.values.max() * 0.55 else "#555555")
    cbar = fig.colorbar(im, ax=ax, fraction=0.028, pad=0.02, shrink=0.5)
    cbar.ax.set_title("\u2212log\u2081\u2080(P)", fontsize=7, pad=3)
    cbar.ax.tick_params(labelsize=6)
    ax.set_title(f"Top {top_n} GO terms \u2014 enrichment overview",
                 fontsize=9, fontweight="bold", pad=5)
    plt.tight_layout()
    fig.savefig(out, dpi=300)
    plt.close(fig)
    print(f"  [OK] {out.name}")


# ══════════════════════════════════════════════════════════════════════════════
# 扩展模式（原 plot_venn_go_style.py）：可配置气泡图
# ══════════════════════════════════════════════════════════════════════════════
def prepare_plot_df(frames, ontology: str, top_n: int, per_file_top: bool = False,
                    group_subset: list = None):
    """\u6309\u672c\u4f53\u548c\u7ec4\u7b5b\u9009 GO terms\uff0c\u8fd4\u56de\u53ef\u7ed8\u56fe\u7684 DataFrame"""
    all_group_order = ["Gallus", "A&C", "Anas", "G&C", "Columba", "G&A"]
    label_map = {
        "Gallus": "Gallus", "A&C": "A\u2229C",
        "Anas": "Anas",     "G&C": "G\u2229C",
        "Columba": "Columba", "G&A": "G\u2229A",
    }
    group_order = [g for g in all_group_order
                   if (group_subset is None or g in group_subset)]
    filtered = {k: frames[k][frames[k]["ontology"] == ontology].copy()
                for k in group_order}
    combined = pd.concat([filtered[g].assign(group=g) for g in group_order],
                         ignore_index=True)
    if combined.empty:
        raise ValueError(f"ontology={ontology} 下无数据")

    term_rank = (combined.groupby("term", as_index=False)
                 .agg(total_count=("count", "sum"), p_value=("p_value", "min"))
                 .sort_values(["p_value", "total_count"], ascending=[True, False]))

    if (top_n is None or top_n <= 0):
        top_terms = term_rank["term"].tolist()
    elif per_file_top:
        sel = set()
        for g in group_order:
            sel.update(filtered[g].sort_values(["p_value", "count"],
                                                ascending=[True, False])
                       .head(top_n)["term"].tolist())
        top_terms = term_rank[term_rank["term"].isin(sel)]["term"].tolist()
    else:
        top_terms = term_rank.head(top_n)["term"].tolist()

    records = []
    for term in top_terms:
        for g in group_order:
            hit = filtered[g][filtered[g]["term"] == term]
            if hit.empty:
                continue
            hit = hit.sort_values("p_value").iloc[0]
            records.append({"group": g, "term": term,
                             "count": float(hit["count"]),
                             "p_value": float(hit["p_value"])})
    plot_df = pd.DataFrame(records).dropna(subset=["count", "p_value"])
    plot_df = plot_df[plot_df["p_value"] > 0]
    plot_df["neglog10p"] = -np.log10(plot_df["p_value"])
    return plot_df, group_order, label_map, top_terms


def build_plot(data_dir: Path, output_file: Path, ontology: str, top_n: int,
               per_file_top: bool = False, group_subset: list = None, subtitle: str = ""):
    """单本体气泡图（coolwarm 配色，自适应大小）"""
    frames = load_frames(data_dir)
    plot_df, group_order, label_map, top_terms = prepare_plot_df(
        frames, ontology, top_n, per_file_top=per_file_top, group_subset=group_subset)

    n_terms = len(top_terms)
    n_cols  = len(group_order)
    cell_h  = 0.42
    s_max   = np.pi * (cell_h * 72 * 0.78 / 2) ** 2
    scale_f = s_max / max(float(plot_df["count"].max()), 1.0)

    term_p  = plot_df.groupby("term")["p_value"].min()
    y_order = term_p.sort_values(ascending=False).index.tolist()
    y_map   = {t: i for i, t in enumerate(y_order)}
    x_map   = {g: i for i, g in enumerate(group_order)}
    plot_df = plot_df.copy()
    plot_df["x"] = plot_df["group"].map(x_map)
    plot_df["y"] = plot_df["term"].map(y_map)

    vmin = plot_df["neglog10p"].min()
    vmax = plot_df["neglog10p"].max()
    if np.isclose(vmin, vmax):
        vmax = vmin + 1

    fig_h = max(4.0, n_terms * cell_h + 2.5)
    fig_w = max(7.0, n_cols  * 0.50   + 5.5)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    sc = ax.scatter(plot_df["x"], plot_df["y"],
                    s=plot_df["count"] * scale_f,
                    c=plot_df["neglog10p"],
                    cmap=plt.cm.coolwarm, vmin=vmin, vmax=vmax,
                    alpha=0.90, edgecolors="none")
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels([label_map[g] for g in group_order], fontsize=11)
    ax.set_yticks(range(n_terms))
    ax.set_yticklabels(y_order, fontsize=9)
    ax.set_axisbelow(True)
    ax.grid(True, axis="both", color="#e0e0e0", linewidth=0.8)
    ax.set_xlim(-0.55, n_cols - 0.45)
    ax.set_ylim(-0.55, n_terms - 0.45)
    ax.set_ylabel("GO terms", fontsize=12, weight="bold")
    title_str = ontology.replace("_", " ")
    if subtitle:
        title_str += f"  ({subtitle})"
    ax.set_title(title_str, fontsize=13, weight="bold")

    cbar = fig.colorbar(sc, ax=ax, fraction=0.030, pad=0.02, shrink=0.40,
                        anchor=(0.0, 1.0))
    cbar.ax.set_title("P value", fontsize=10, pad=4)
    tick_vals = np.linspace(vmin, vmax, 5)
    cbar.set_ticks(tick_vals)
    cbar.set_ticklabels(format_p_ticks_from_log10(tick_vals), fontsize=8)

    count_arr = np.unique(plot_df["count"].dropna().astype(int))
    cmin, cmax2 = int(count_arr.min()), int(count_arr.max())
    idxs = np.unique(np.round(np.linspace(0, len(count_arr) - 1, 4)).astype(int))
    c_levels = count_arr[idxs]
    def _ms(c):
        if cmax2 == cmin:
            return 8.5
        return 4.0 + 9.0 * (c - cmin) / (cmax2 - cmin)
    ax.legend([Line2D([0], [0], marker="o", ls="none",
                      markerfacecolor="#777777", markeredgecolor="none",
                      markersize=_ms(c), alpha=0.88) for c in c_levels],
              [str(int(c)) for c in c_levels],
              title="Count", title_fontsize=10, fontsize=9,
              loc="upper left", bbox_to_anchor=(1.03, 0.57),
              frameon=False, handletextpad=0.8, labelspacing=0.8)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {output_file.name}")


def build_three_ontology_plot(data_dir: Path, output_file: Path, top_n: int,
                              group_subset: list = None,
                              title: str = "GO enrichment bubble plot"):
    """将 BP/MF/CC 三个本体合并在同一张气泡图中（分段显示）"""
    frames = load_frames(data_dir)
    ontologies = [("biological_process", "BP"),
                  ("molecular_function", "MF"),
                  ("cellular_component", "CC")]
    prepared = []
    for ont, lbl in ontologies:
        try:
            res = prepare_plot_df(frames, ont, top_n,
                                  per_file_top=True, group_subset=group_subset)
            prepared.append((ont, lbl, *res))
        except ValueError:
            continue
    if not prepared:
        raise ValueError("所有 ontology 均无数据")

    global_vmin = min(it[2]["neglog10p"].min() for it in prepared)
    global_vmax = max(it[2]["neglog10p"].max() for it in prepared)
    if np.isclose(global_vmin, global_vmax):
        global_vmax = global_vmin + 1

    group_order = prepared[0][3]
    label_map   = prepared[0][4]
    all_counts  = pd.concat([it[2]["count"] for it in prepared], ignore_index=True)
    cell_h      = 0.42
    s_max       = np.pi * (cell_h * 72 * 0.78 / 2) ** 2
    scale_f     = s_max / max(float(all_counts.max()), 1.0)
    n_cols      = len(group_order)

    section_labels, term_section, all_points, section_positions = [], {}, [], []
    for idx, (_, short_lbl, plot_df, _, _, top_terms) in enumerate(prepared):
        terms = list(dict.fromkeys(top_terms))[::-1]
        first = last = None
        for term in terms:
            section_labels.append(term)
            term_section[term] = short_lbl
            first = first or term
            last  = term
            sub = plot_df[plot_df["term"] == term].copy()
            sub["term_label"] = term
            all_points.append(sub)
        section_positions.append((short_lbl, first, last))
        if idx < len(prepared) - 1:
            section_labels.append(f"__spacer_{idx}")

    combined_df = pd.concat(all_points, ignore_index=True)
    n_rows  = len(section_labels)
    y_map   = {lbl: (n_rows - 1 - i) for i, lbl in enumerate(section_labels)}
    x_map   = {g: i for i, g in enumerate(group_order)}
    combined_df["x"] = combined_df["group"].map(x_map)
    combined_df["y"] = combined_df["term_label"].map(y_map)

    fig_h = max(8.0, n_rows * cell_h + 2.5)
    fig_w = max(7.0, n_cols * 0.50   + 5.5)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    sc = ax.scatter(combined_df["x"], combined_df["y"],
                    s=combined_df["count"] * scale_f,
                    c=combined_df["neglog10p"],
                    cmap=plt.cm.coolwarm, vmin=global_vmin, vmax=global_vmax,
                    alpha=0.90, edgecolors="none")
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels([label_map[g] for g in group_order], fontsize=11)
    ax.set_yticks([y_map[l] for l in section_labels])
    ax.set_yticklabels(
        ["" if l.startswith("__spacer_") else l for l in section_labels], fontsize=9)
    ax.set_axisbelow(True)
    ax.grid(True, axis="both", color="#e0e0e0", linewidth=0.8)
    ax.set_xlim(-0.55, n_cols - 0.45)
    ax.set_ylim(-0.55, n_rows - 0.45)
    ax.set_title(title, fontsize=13, weight="bold")
    ax.text(-0.85, 0.5, "GO terms", transform=ax.transAxes,
            fontsize=12, fontweight="bold", va="center", ha="center",
            rotation=90, clip_on=False)

    for lbl in section_labels:
        if lbl.startswith("__spacer_"):
            ax.axhline(y=y_map[lbl], color="#aaaaaa", linewidth=1.0, linestyle="--")

    for short_lbl, first_lbl, last_lbl in section_positions:
        if first_lbl is None:
            continue
        y_mid = (y_map[first_lbl] + y_map[last_lbl]) / 2
        ax.text(1.05, y_mid, short_lbl,
                transform=ax.get_yaxis_transform(),
                fontsize=13, fontweight="bold",
                va="center", ha="center", rotation=90, clip_on=False)

    cbar = fig.colorbar(sc, ax=ax, fraction=0.030, pad=0.14, shrink=0.40,
                        anchor=(0.0, 1.0))
    cbar.ax.set_title("P value", fontsize=10, pad=4)
    tick_vals = np.linspace(global_vmin, global_vmax, 5)
    cbar.set_ticks(tick_vals)
    cbar.set_ticklabels(format_p_ticks_from_log10(tick_vals), fontsize=8)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  [OK] {output_file.name}")


# ══════════════════════════════════════════════════════════════════════════════
# 命令行入口（继承自 plot_venn_go_style.py，来自批量模式支持）
# ══════════════════════════════════════════════════════════════════════════════
def _cli():
    parser = argparse.ArgumentParser(
        description="GO 富集气泡图工具（单本体 / 三本体合并）\n"
                    "不传参数时自动生成全套 NC 风格 Fig1-Fig6。")
    parser.add_argument("--data-dir",      default=".",
                        help="富集结果目录（默认当前目录）")
    parser.add_argument("--output",        default="venn_go_combined.png",
                        help="输出图片路径")
    parser.add_argument("--ontology",      default="cellular_component",
                        choices=["biological_process", "molecular_function",
                                 "cellular_component"])
    parser.add_argument("--top-n",         type=int, default=12)
    parser.add_argument("--combine-three", action="store_true",
                        help="将 BP/MF/CC 合并在同一张图")
    parser.add_argument("--per-file-top",  action="store_true")
    parser.add_argument("--batch-six",     action="store_true",
                        help="一键生成单物种×3本体 + 双物种×3本体共6张图")
    args = parser.parse_args()
    data_dir = Path(args.data_dir)
    output   = Path(args.output) if Path(args.output).is_absolute() \
               else data_dir / args.output

    if args.batch_six:
        short = {"biological_process": "bp",
                 "molecular_function": "mf",
                 "cellular_component": "cc"}
        subsets = {
            "single":   (["Gallus", "Anas", "Columba"], "single species"),
            "pairwise": (["A&C", "G&C", "G&A"],         "pairwise shared"),
        }
        for ont in short:
            for tag, (grps, sub_title) in subsets.items():
                build_plot(data_dir, data_dir / f"Fig_venn_go_{short[ont]}_{tag}.png",
                           ont, args.top_n, per_file_top=True,
                           group_subset=grps, subtitle=sub_title)
        build_three_ontology_plot(
            data_dir, data_dir / "Fig_venn_go_single_combined.png", args.top_n,
            group_subset=["Gallus", "Anas", "Columba"],
            title="GO enrichment – single species (BP / MF / CC)")
    elif args.combine_three:
        build_three_ontology_plot(data_dir, output, args.top_n)
    else:
        build_plot(data_dir, output, args.ontology, args.top_n,
                   per_file_top=args.per_file_top)


# ══════════════════════════════════════════════════════════════════════════════
# 默认执行：自动生成全套 NC 风格 Fig1-Fig6
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # 有命令行参数 → 进入 CLI 模式
        _cli()
    else:
        # 无参数 → 自动生成全套 NC 风格图表
        frames = load_all(DATA_DIR)
        print(f"\u8f93\u51fa\u76ee\u5f55: {OUT_DIR}\n")

        print("[1/6] \u6c34\u5e73\u6761\u5f62\u56fe\u9762\u677f \u2192 Fig1_barplot_panel.png")
        plot_hbar_panel(frames, OUT_DIR / "Fig1_barplot_panel.png", top_n=8)

        print("[2/6] \u5355\u7269\u79cd\u6c14\u6ce1\u56fe   \u2192 Fig2_bubble_single.png")
        plot_bubble_panel(frames, ["Gallus", "Anas", "Columba"],
                          OUT_DIR / "Fig2_bubble_single.png",
                          top_n_per_group=6,
                          title="GO enrichment \u2013 single species")

        print("[3/6] \u4e24\u7269\u79cd\u5171\u6709\u6c14\u6ce1\u56fe \u2192 Fig3_bubble_pairwise.png")
        plot_bubble_panel(frames, ["A&C", "G&C", "G&A"],
                          OUT_DIR / "Fig3_bubble_pairwise.png",
                          top_n_per_group=12,
                          title="GO enrichment \u2013 pairwise shared")

        print("[4/6] \u97e6\u6069\u56fe         \u2192 Fig4_venn.png")
        plot_venn_panel(frames, OUT_DIR / "Fig4_venn.png")

        print("[5/6] GO term \u6570\u91cf\u6c47\u603b \u2192 Fig5_summary_bar.png")
        plot_summary_bar(frames, OUT_DIR / "Fig5_summary_bar.png")

        print("[6/6] \u70ed\u56fe\u603b\u89c8       \u2192 Fig6_heatmap.png")
        plot_heatmap_overview(frames, OUT_DIR / "Fig6_heatmap.png", top_n=20)

        print(f"\n[OK] All done!6 \u5f20\u56fe\u4fdd\u5b58\u5728: {OUT_DIR}")
