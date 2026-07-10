"""
Fig_glycan_ensemble_stats_visualization.py
===========================================
可视化糖链构象多样性分析结果
  Panel A: 各物种糖链 Rg 小提琴图（展示 50 构象分布）
  Panel B: 端到端距离分布（violin + strip）
  Panel C: 糖链质心到蛋白距离（violin）
  Panel D: 糖链最近接触距离（violin）
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
matplotlib.rcParams["font.family"] = "Minion Pro"
matplotlib.rcParams["font.sans-serif"] = ["Minion Pro", "DejaVu Sans"]
matplotlib.rcParams["mathtext.fontset"] = "stix"
from matplotlib.lines import Line2D
from pathlib import Path
import sys; sys.path.insert(0, str(Path(__file__).parent))
from _save import save_fig
from scipy import stats


TITLE_FS = 20
AXIS_LABEL_FS = 20
TICK_FS = 20
STAT_FS = 20
PANEL_FIGSIZE = (5.9, 5.5)
TITLE_PAD = 6
TITLE_LINESPACING = 1.0
YLABEL_X = -0.09
YLABEL_PAD = 0
XTICK_PAD = 6
PANEL_ADJUST = dict(left=0.20, right=0.98, bottom=0.21, top=0.83)


CSV_DIR = Path(r'D:\system_folder\Desktop\Work On\01_数据与计算\ReGlyco_Ensemble\csv')
OUT_DIR = Path(r'D:\system_folder\Desktop\Work On\02_可视化\Figure\png')

SPECIES_ORDER  = ['Gallus', 'Anas', 'Columba']
SPECIES_COLORS = {'Gallus': '#C46B83', 'Anas': '#93AACD', 'Columba': '#F3CE9D'}
METRICS = {
    'glycan_rg':             'Glycan Rg (Å)',
    'glycan_end2end':        'End-to-End Distance (Å)',
    'glycan_dist':           'Glycan–Protein Distance (Å)',
    'glycan_min_dist_to_ca': 'Min. Distance to Cα (Å)',
}

# ─── 加载数据 ────────────────────────────────────────────────────────────

detail  = pd.read_csv(CSV_DIR / 'glycan_conformation_detail.csv')
summary = pd.read_csv(CSV_DIR / 'glycan_species_summary.csv')

# ─── 辅助函数 ────────────────────────────────────────────────────────────

def pairwise_mann_whitney_letters(data, alpha: float = 0.05):
    cleaned = []
    for values in data:
        arr = np.asarray(values, dtype=float)
        cleaned.append(arr[np.isfinite(arr)])

    means = np.array([
        np.mean(values) if len(values) else -np.inf
        for values in cleaned
    ])
    order = np.argsort(means)[::-1]
    sig = np.zeros((len(cleaned), len(cleaned)), dtype=bool)
    for i in range(len(cleaned)):
        for j in range(i + 1, len(cleaned)):
            left_vals = cleaned[order[i]]
            right_vals = cleaned[order[j]]
            if len(left_vals) == 0 or len(right_vals) == 0:
                continue
            _, p_value = stats.mannwhitneyu(left_vals, right_vals, alternative='two-sided')
            sig[i, j] = sig[j, i] = (p_value < alpha)

    letters_by_rank = {
        (False, False, False): ('a', 'a', 'a'),
        (False, False, True): ('ab', 'a', 'b'),
        (False, True, False): ('a', 'ab', 'b'),
        (False, True, True): ('a', 'a', 'b'),
        (True, False, False): ('a', 'b', 'ab'),
        (True, False, True): ('a', 'b', 'a'),
        (True, True, False): ('a', 'b', 'b'),
        (True, True, True): ('a', 'b', 'c'),
    }[(bool(sig[0, 1]), bool(sig[0, 2]), bool(sig[1, 2]))]

    letters = [''] * len(cleaned)
    for ranked_index, original_index in enumerate(order):
        letters[original_index] = letters_by_rank[ranked_index]
    return letters


def add_group_letters(ax, data, y_max, span):
    span = max(span, 1e-9)
    letters = pairwise_mann_whitney_letters(data)
    top_y = y_max
    for index, (values, letter) in enumerate(zip(data, letters)):
        arr = np.asarray(values, dtype=float)
        arr = arr[np.isfinite(arr)]
        if len(arr) == 0:
            continue
        y = arr.max() + span * 0.04
        ax.text(index, y, letter, ha='center', va='bottom',
                fontsize=STAT_FS, color='#333')
        top_y = max(top_y, y + span * 0.08)
    return top_y


def style_panel_axes(ax, ylabel: str, title: str) -> None:
    ax.set_ylabel(ylabel, fontsize=AXIS_LABEL_FS, labelpad=YLABEL_PAD)
    ax.yaxis.set_label_coords(YLABEL_X, 0.5)
    ax.set_title(title, fontsize=TITLE_FS, color='black', pad=TITLE_PAD,
                 linespacing=TITLE_LINESPACING)
    ax.tick_params(axis='x', pad=XTICK_PAD)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


def violin_one(ax, metric, ylabel, subtitle=''):
    data = [detail.loc[detail.species==sp, metric].dropna().values
            for sp in SPECIES_ORDER]
    colors = [SPECIES_COLORS[sp] for sp in SPECIES_ORDER]

    parts = ax.violinplot(data, positions=range(len(SPECIES_ORDER)),
                          showmedians=True, showextrema=False, widths=0.6)
    for pc, c in zip(parts['bodies'], colors):
        pc.set_facecolor(c)
        pc.set_alpha(1.0)
        pc.set_edgecolor('white')
        pc.set_linewidth(0.5)
    parts['cmedians'].set_color('black')
    parts['cmedians'].set_linewidth(1.5)

    # 抖动点 (每组最多 100 个)
    rng = np.random.default_rng(42)
    for i, (sp, d) in enumerate(zip(SPECIES_ORDER, data)):
        idx = rng.choice(len(d), size=min(100, len(d)), replace=False)
        jitter = rng.uniform(-0.08, 0.08, size=len(idx))
        ax.scatter(i + jitter, d[idx], s=8,
                   color=SPECIES_COLORS[sp], alpha=1.0, linewidths=0, zorder=3)

    ax.set_xticks(range(len(SPECIES_ORDER)))
    ax.set_xticklabels(SPECIES_ORDER, fontsize=TICK_FS)

    ymax = max(d.max() for d in data if len(d))
    ymin = min(d.min() for d in data if len(d))
    span = ymax - ymin
    stat_top = add_group_letters(ax, data, ymax, span)
    ax.set_ylim(top=stat_top + span * 0.12)
    style_panel_axes(ax, ylabel, subtitle)


def box_jitter_one(ax, metric, ylabel, subtitle=''):
    data = [detail.loc[detail.species == species, metric].dropna().values
            for species in SPECIES_ORDER]
    colors = [SPECIES_COLORS[species] for species in SPECIES_ORDER]
    box = ax.boxplot(
        data,
        positions=range(len(SPECIES_ORDER)),
        widths=0.48,
        patch_artist=True,
        showfliers=False,
        medianprops=dict(color='#222222', linewidth=1.7),
        whiskerprops=dict(color='#555555', linewidth=1.2),
        capprops=dict(color='#555555', linewidth=1.2),
    )
    for patch, color in zip(box['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.45)
        patch.set_edgecolor(color)
        patch.set_linewidth(1.3)

    rng = np.random.default_rng(42)
    for index, (species, values) in enumerate(zip(SPECIES_ORDER, data)):
        shown = values
        if len(values) > 140:
            shown = rng.choice(values, size=140, replace=False)
        jitter = rng.uniform(-0.10, 0.10, size=len(shown))
        ax.scatter(index + jitter, shown, s=10,
                   color=SPECIES_COLORS[species], alpha=0.72,
                   linewidths=0, zorder=3)

    ax.set_xticks(range(len(SPECIES_ORDER)))
    ax.set_xticklabels(SPECIES_ORDER, fontsize=TICK_FS)

    ymax = max(values.max() for values in data if len(values))
    ymin = min(values.min() for values in data if len(values))
    span = ymax - ymin
    stat_top = add_group_letters(ax, data, ymax, span)
    ax.set_ylim(ymin - span * 0.04, stat_top + span * 0.12)
    style_panel_axes(ax, ylabel, subtitle)


def raincloud_one(ax, metric, ylabel, subtitle=''):
    data = [detail.loc[detail.species == species, metric].dropna().values
            for species in SPECIES_ORDER]
    colors = [SPECIES_COLORS[species] for species in SPECIES_ORDER]
    positions = np.arange(len(SPECIES_ORDER))

    parts = ax.violinplot(data, positions=positions,
                          showmedians=False, showextrema=False, widths=0.72)
    for index, (body, color) in enumerate(zip(parts['bodies'], colors)):
        vertices = body.get_paths()[0].vertices
        vertices[:, 0] = np.minimum(vertices[:, 0], positions[index])
        body.set_facecolor(color)
        body.set_alpha(0.72)
        body.set_edgecolor('none')

    box = ax.boxplot(
        data,
        positions=positions + 0.12,
        widths=0.18,
        patch_artist=True,
        showfliers=False,
        medianprops=dict(color='#222222', linewidth=1.4),
        whiskerprops=dict(color='#555555', linewidth=1.0),
        capprops=dict(color='#555555', linewidth=1.0),
    )
    for patch, color in zip(box['boxes'], colors):
        patch.set_facecolor('white')
        patch.set_alpha(0.88)
        patch.set_edgecolor(color)
        patch.set_linewidth(1.2)

    rng = np.random.default_rng(42)
    for index, (species, values) in enumerate(zip(SPECIES_ORDER, data)):
        shown = values if len(values) <= 150 else rng.choice(values, size=150, replace=False)
        jitter = rng.uniform(0.17, 0.34, size=len(shown))
        ax.scatter(index + jitter, shown, s=10,
                   color=SPECIES_COLORS[species], alpha=0.66,
                   linewidths=0, zorder=3)

    ax.set_xticks(positions)
    ax.set_xticklabels(SPECIES_ORDER, fontsize=TICK_FS)

    ymax = max(values.max() for values in data if len(values))
    ymin = min(values.min() for values in data if len(values))
    span = ymax - ymin
    stat_top = add_group_letters(ax, data, ymax, span)
    ax.set_xlim(-0.55, len(SPECIES_ORDER) - 0.45)
    ax.set_ylim(ymin - span * 0.04, stat_top + span * 0.12)
    style_panel_axes(ax, ylabel, subtitle)


def half_violin_box_one(ax, metric, ylabel, subtitle=''):
    data = [detail.loc[detail.species == species, metric].dropna().values
            for species in SPECIES_ORDER]
    colors = [SPECIES_COLORS[species] for species in SPECIES_ORDER]
    positions = np.arange(len(SPECIES_ORDER))

    parts = ax.violinplot(data, positions=positions,
                          showmedians=False, showextrema=False, widths=0.72)
    for index, (body, color) in enumerate(zip(parts['bodies'], colors)):
        vertices = body.get_paths()[0].vertices
        vertices[:, 0] = np.minimum(vertices[:, 0], positions[index])
        body.set_facecolor(color)
        body.set_alpha(0.82)
        body.set_edgecolor('none')

    box = ax.boxplot(
        data,
        positions=positions + 0.12,
        widths=0.22,
        patch_artist=True,
        showfliers=False,
        medianprops=dict(color='#222222', linewidth=1.5),
        whiskerprops=dict(color='#555555', linewidth=1.1),
        capprops=dict(color='#555555', linewidth=1.1),
    )
    for patch, color in zip(box['boxes'], colors):
        patch.set_facecolor('white')
        patch.set_alpha(0.90)
        patch.set_edgecolor(color)
        patch.set_linewidth(1.3)

    ax.set_xticks(positions)
    ax.set_xticklabels(SPECIES_ORDER, fontsize=TICK_FS)

    ymax = max(values.max() for values in data if len(values))
    ymin = min(values.min() for values in data if len(values))
    span = ymax - ymin
    stat_top = add_group_letters(ax, data, ymax, span)
    ax.set_xlim(-0.55, len(SPECIES_ORDER) - 0.45)
    ax.set_ylim(ymin - span * 0.04, stat_top + span * 0.12)
    style_panel_axes(ax, ylabel, subtitle)


# ─── 保存工具函数 ────────────────────────────────────────────────────────

DPI_OUT = 300

def save_panel(fig, name):
    """Save as PNG/PDF/SVG."""
    save_fig(fig, name, dpi=DPI_OUT)


# ─── 逐面板独立输出 ───────────────────────────────────────────────────────

SUBTITLES = {
    'glycan_rg':             'Glycan Radius of Gyration',
    'glycan_end2end':        'Glycan End-to-End Distance',
    'glycan_dist':           'Glycan–Protein Distance',
    'glycan_min_dist_to_ca': 'Glycan–Backbone Proximity',
}

metric_keys   = list(METRICS.keys())
metric_labels = list(METRICS.values())
panel_labels  = list('ABCD')
PANEL_NAMES = {
    'glycan_rg': 'Fig4C_glycan_radius_of_gyration',
    'glycan_min_dist_to_ca': 'Fig4D_glycan_backbone_proximity',
    'glycan_end2end': 'Fig4E_glycan_end_to_end_distance',
    'glycan_dist': 'Fig4F_glycan_protein_distance',
}

for mk, ml, lbl in zip(metric_keys, metric_labels, panel_labels):
    fig, ax = plt.subplots(figsize=PANEL_FIGSIZE)
    fig.patch.set_facecolor('white')
    if mk == 'glycan_rg':
        raincloud_one(ax, mk, ml, subtitle=SUBTITLES.get(mk, ''))
    elif mk in {'glycan_end2end', 'glycan_dist'}:
        box_jitter_one(ax, mk, ml, subtitle=SUBTITLES.get(mk, ''))
    elif mk == 'glycan_min_dist_to_ca':
        raincloud_one(ax, mk, ml, subtitle=SUBTITLES.get(mk, ''))
    else:
        half_violin_box_one(ax, mk, ml, subtitle=SUBTITLES.get(mk, ''))
    fig.subplots_adjust(**PANEL_ADJUST)
    save_panel(fig, PANEL_NAMES[mk])
    plt.close(fig)
