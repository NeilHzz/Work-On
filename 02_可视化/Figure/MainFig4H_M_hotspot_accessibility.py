"""
Fig_hotspot_ensemble_2_visualization.py
=========================================
Ca2+ 热点可及性与糖链屏蔽分析（六面板）

面板布局（3行）：
  Row 1: A — 界面屏蔽 (Å²)         B — 热点残基平均 SASA
  Row 2: C — 热点比例               D — 净可及热点数
  Row 3: E — 热点数堆叠柱（净+屏蔽）  F — 热点残基SASA堆叠（净+屏蔽）

输入文件（csv/）：
  hotspot_per_conformation.csv

输出：
  Fig_hotspot_ensemble_2.png
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
matplotlib.rcParams["font.family"] = "Times New Roman"
matplotlib.rcParams["font.sans-serif"] = ["Times New Roman", "DejaVu Sans"]
matplotlib.rcParams["mathtext.fontset"] = "stix"
from matplotlib.gridspec import GridSpec
from scipy import stats
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _save import save_fig


TITLE_FS = 20
AXIS_LABEL_FS = 20
TICK_FS = 20
LEGEND_FS = 18
STAT_FS = 20
VALUE_FS = 18
PANEL_FIGSIZE = (5.9, 5.5)
TITLE_PAD = 6
TITLE_LINESPACING = 1.0
YLABEL_X = -0.09
YLABEL_PAD = 0
XTICK_PAD = 6
PANEL_ADJUST = dict(left=0.20, right=0.98, bottom=0.21, top=0.83)


def format_p_value(p_value: float) -> str:
    if p_value <= 0 or not np.isfinite(p_value):
        return 'p < 1e-300'
    return f'p = {p_value:.2e}'


# ═════ Duncan's Multiple Range Test ════════════════════════════════════════
def duncan_mrt(groups: list, names: list, alpha: float = 0.05) -> dict:
    k = len(groups)
    ns = [len(g) for g in groups]
    means = np.array([g.mean() for g in groups])
    f_stat, p_anova = stats.f_oneway(*groups)
    SS_e   = sum(float(np.sum((g - g.mean()) ** 2)) for g in groups)
    df_e   = sum(ns) - k
    MSE    = SS_e / df_e
    n_harm = k / sum(1.0 / n for n in ns)
    SE     = np.sqrt(MSE / n_harm)
    order  = np.argsort(means)[::-1]
    s_means = means[order]
    s_names = [names[i] for i in order]
    crit = [stats.studentized_range.ppf(1.0 - alpha, k=p, df=df_e) * SE
            for p in range(2, k + 1)]
    sig = np.zeros((k, k), dtype=bool)
    for i in range(k):
        for j in range(i + 1, k):
            p_span = j - i + 1
            sig[i, j] = sig[j, i] = (s_means[i] - s_means[j] > crit[p_span - 2])
    if k == 3:
        s01, s02, s12 = bool(sig[0,1]), bool(sig[0,2]), bool(sig[1,2])
        table = {
            (False,False,False): ('a','a','a'),
            (False,False,True ): ('ab','a','b'),
            (False,True, False): ('a','ab','b'),
            (False,True, True ): ('a','a','b'),
            (True, False,False): ('a','b','ab'),
            (True, False,True ): ('a','b','a'),
            (True, True, False): ('a','b','b'),
            (True, True, True ): ('a','b','c'),
        }
        ltrs = table[(s01, s02, s12)]
        letters = {s_names[i]: ltrs[i] for i in range(3)}
    else:
        letters = {}
    return dict(f_stat=f_stat, p_anova=p_anova, letters=letters)


FOLDER  = r"D:\system_folder\Desktop\Work On\01_数据与计算\ReGlyco_Ensemble"
CSV_DIR = os.path.join(FOLDER, "csv")
OUT_PNG = os.path.join(r"D:\system_folder\Desktop\Work On\02_可视化\Figure\png", "Fig5I_N.png")
DPI     = 300

SPECIES_ORDER = ['Gallus', 'Anas', 'Columba']
SPECIES_COLOR = {'Gallus': '#C46B83', 'Anas': '#93AACD', 'Columba': '#F3CE9D'}


# ── 统计标注 ──────────────────────────────────────────────────────────────────
def sig_label(p):
    if p < 0.001: return '***'
    if p < 0.01:  return '**'
    if p < 0.05:  return '*'
    return 'ns'


def add_significance_brackets(ax, x1, x2, y, h, label, fs=STAT_FS):
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], lw=0.9, c='#333')
    ax.text((x1 + x2) / 2, y + h * 1.05, label,
            ha='center', va='bottom', fontsize=fs, color='#333')


def style_panel_axes(ax, ylabel: str, title: str,
                     ylabel_x: float | None = None,
                     ylabel_fs: int | None = None) -> None:
    ax.set_ylabel(ylabel, fontsize=ylabel_fs or AXIS_LABEL_FS, labelpad=YLABEL_PAD)
    ax.yaxis.set_label_coords(ylabel_x if ylabel_x is not None else YLABEL_X, 0.5)
    ax.set_title(title, fontsize=TITLE_FS, pad=TITLE_PAD,
                 linespacing=TITLE_LINESPACING)
    ax.tick_params(axis='x', pad=XTICK_PAD)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


# ── 小提琴 + 散点（单面板）────────────────────────────────────────────────────
def draw_violin_panel(ax, groups_dict, ylabel, title, panel_label,
                      ypad_top=0.12, ypad_bot=0.02):
    positions   = list(range(len(SPECIES_ORDER)))
    all_vals    = np.concatenate(list(groups_dict.values()))
    y_min, y_max = np.nanmin(all_vals), np.nanmax(all_vals)
    y_range      = y_max - y_min
    rng = np.random.default_rng(42)

    data_lists = [groups_dict[sp] for sp in SPECIES_ORDER]
    vp = ax.violinplot(data_lists, positions=positions,
                       showmedians=False, showextrema=False, widths=0.7)
    for i, body in enumerate(vp['bodies']):
        sp  = SPECIES_ORDER[i]
        body.set_facecolor(SPECIES_COLOR[sp])
        body.set_alpha(1.0)
        body.set_edgecolor('none')

    for i, sp in enumerate(SPECIES_ORDER):
        vals = groups_dict[sp]
        jit  = rng.uniform(-0.12, 0.12, len(vals))
        ax.scatter(i + jit, vals, s=14, color=SPECIES_COLOR[sp],
                   alpha=1.0, edgecolors='none', zorder=3)
        med = np.median(vals)
        ax.hlines(med, i - 0.22, i + 0.22,
                  color='#222', lw=1.6, zorder=4)

    # Duncan's MRT CLD 字母标注
    grp_data = [groups_dict[sp] for sp in SPECIES_ORDER]
    res = duncan_mrt(grp_data, SPECIES_ORDER)
    letter_y = y_max + y_range * 0.05
    for xi, sp in enumerate(SPECIES_ORDER):
        ltr = res['letters'].get(sp, '')
        ax.text(xi, letter_y, ltr, ha='center', va='bottom',
            fontsize=STAT_FS, fontweight='bold', color='#333')

    ax.set_xticks(positions)
    ax.set_xticklabels(SPECIES_ORDER, fontsize=TICK_FS)
    style_panel_axes(ax, ylabel, f"{title}\n{format_p_value(res['p_anova'])}")
    ax.set_ylim(y_min - y_range * ypad_bot, letter_y + y_range * 0.20)


def draw_box_jitter_panel(ax, groups_dict, ylabel, title):
    positions = list(range(len(SPECIES_ORDER)))
    data_lists = [groups_dict[species] for species in SPECIES_ORDER]
    all_vals = np.concatenate(data_lists)
    y_min, y_max = np.nanmin(all_vals), np.nanmax(all_vals)
    y_range = max(y_max - y_min, 1e-9)

    res = duncan_mrt(data_lists, SPECIES_ORDER)
    box = ax.boxplot(
        data_lists,
        positions=positions,
        widths=0.48,
        patch_artist=True,
        showfliers=False,
        medianprops=dict(color='#222222', linewidth=1.7),
        whiskerprops=dict(color='#555555', linewidth=1.2),
        capprops=dict(color='#555555', linewidth=1.2),
    )
    for patch, species in zip(box['boxes'], SPECIES_ORDER):
        patch.set_facecolor(SPECIES_COLOR[species])
        patch.set_alpha(0.45)
        patch.set_edgecolor(SPECIES_COLOR[species])
        patch.set_linewidth(1.3)

    rng = np.random.default_rng(42)
    for index, species in enumerate(SPECIES_ORDER):
        vals = groups_dict[species]
        shown = vals
        if len(vals) > 140:
            shown = rng.choice(vals, size=140, replace=False)
        jitter = rng.uniform(-0.10, 0.10, len(shown))
        ax.scatter(index + jitter, shown, s=12,
                   color=SPECIES_COLOR[species], alpha=0.72,
                   edgecolors='none', zorder=3)

    letter_y = y_max + y_range * 0.05
    for index, species in enumerate(SPECIES_ORDER):
        label = res['letters'].get(species, '')
        ax.text(index, letter_y, label, ha='center', va='bottom',
                fontsize=STAT_FS, fontweight='bold', color='#333')

    ax.set_xticks(positions)
    ax.set_xticklabels(SPECIES_ORDER, fontsize=TICK_FS)
    style_panel_axes(ax, ylabel, f"{title}\n{format_p_value(res['p_anova'])}")
    ax.set_ylim(y_min - y_range * 0.04, letter_y + y_range * 0.18)


def draw_dot_ci_panel(ax, groups_dict, ylabel, title):
    positions = np.arange(len(SPECIES_ORDER))
    data_lists = [groups_dict[species] for species in SPECIES_ORDER]
    all_vals = np.concatenate(data_lists)
    y_min, y_max = np.nanmin(all_vals), np.nanmax(all_vals)
    y_range = max(y_max - y_min, 1e-9)
    means = np.array([np.mean(values) for values in data_lists])
    ci95 = np.array([
        1.96 * np.std(values, ddof=1) / np.sqrt(len(values)) if len(values) > 1 else 0.0
        for values in data_lists
    ])

    res = duncan_mrt(data_lists, SPECIES_ORDER)
    for index, species in enumerate(SPECIES_ORDER):
        ax.errorbar(index, means[index], yerr=ci95[index], fmt='o',
                    markersize=10, markerfacecolor=SPECIES_COLOR[species],
                    markeredgecolor='#222222', markeredgewidth=0.9,
                    ecolor='#333333', elinewidth=1.5, capsize=6, zorder=4)

    letter_y = max(means + ci95) + y_range * 0.08
    for index, species in enumerate(SPECIES_ORDER):
        label = res['letters'].get(species, '')
        ax.text(index, letter_y, label, ha='center', va='bottom',
                fontsize=STAT_FS, fontweight='bold', color='#333')

    ax.set_xticks(positions)
    ax.set_xticklabels(SPECIES_ORDER, fontsize=TICK_FS)
    style_panel_axes(ax, ylabel, f"{title}\n{format_p_value(res['p_anova'])}")
    ax.set_xlim(-0.45, len(SPECIES_ORDER) - 0.55)
    ax.set_ylim(y_min - y_range * 0.08, letter_y + y_range * 0.20)


def draw_half_violin_box_panel(ax, groups_dict, ylabel, title):
    positions = np.arange(len(SPECIES_ORDER))
    data_lists = [groups_dict[species] for species in SPECIES_ORDER]
    all_vals = np.concatenate(data_lists)
    y_min, y_max = np.nanmin(all_vals), np.nanmax(all_vals)
    y_range = max(y_max - y_min, 1e-9)

    res = duncan_mrt(data_lists, SPECIES_ORDER)
    vp = ax.violinplot(data_lists, positions=positions,
                       showmedians=False, showextrema=False, widths=0.72)
    for index, body in enumerate(vp['bodies']):
        vertices = body.get_paths()[0].vertices
        vertices[:, 0] = np.minimum(vertices[:, 0], positions[index])
        species = SPECIES_ORDER[index]
        body.set_facecolor(SPECIES_COLOR[species])
        body.set_alpha(0.82)
        body.set_edgecolor('none')

    box = ax.boxplot(
        data_lists,
        positions=positions + 0.12,
        widths=0.22,
        patch_artist=True,
        showfliers=False,
        medianprops=dict(color='#222222', linewidth=1.5),
        whiskerprops=dict(color='#555555', linewidth=1.1),
        capprops=dict(color='#555555', linewidth=1.1),
    )
    for patch, species in zip(box['boxes'], SPECIES_ORDER):
        patch.set_facecolor('white')
        patch.set_alpha(0.90)
        patch.set_edgecolor(SPECIES_COLOR[species])
        patch.set_linewidth(1.3)

    letter_y = y_max + y_range * 0.05
    for index, species in enumerate(SPECIES_ORDER):
        label = res['letters'].get(species, '')
        ax.text(index, letter_y, label, ha='center', va='bottom',
                fontsize=STAT_FS, fontweight='bold', color='#333')

    ax.set_xticks(positions)
    ax.set_xticklabels(SPECIES_ORDER, fontsize=TICK_FS)
    style_panel_axes(ax, ylabel, f"{title}\n{format_p_value(res['p_anova'])}")
    ax.set_xlim(-0.55, len(SPECIES_ORDER) - 0.45)
    ax.set_ylim(y_min - y_range * 0.04, letter_y + y_range * 0.18)


def draw_slim_bar_jitter_panel(ax, groups_dict, ylabel, title):
    positions = np.arange(len(SPECIES_ORDER))
    data_lists = [groups_dict[species] for species in SPECIES_ORDER]
    all_vals = np.concatenate(data_lists)
    y_min, y_max = np.nanmin(all_vals), np.nanmax(all_vals)
    y_range = max(y_max - y_min, 1e-9)
    means = np.array([np.mean(values) for values in data_lists])
    ci95 = np.array([
        1.96 * np.std(values, ddof=1) / np.sqrt(len(values)) if len(values) > 1 else 0.0
        for values in data_lists
    ])

    res = duncan_mrt(data_lists, SPECIES_ORDER)
    bar_width = 0.28
    for index, species in enumerate(SPECIES_ORDER):
        color = SPECIES_COLOR[species]
        ax.bar(index, means[index], width=bar_width, color=color,
               alpha=0.50, edgecolor=color, linewidth=1.2, zorder=2)
        ax.errorbar(index, means[index], yerr=ci95[index], fmt='none',
                    color='#333333', elinewidth=1.3, capsize=5, zorder=4)

    rng = np.random.default_rng(42)
    for index, species in enumerate(SPECIES_ORDER):
        values = groups_dict[species]
        shown = values if len(values) <= 140 else rng.choice(values, size=140, replace=False)
        jitter = rng.uniform(-0.10, 0.10, len(shown))
        ax.scatter(index + jitter, shown, s=12,
                   color=SPECIES_COLOR[species], alpha=0.70,
                   edgecolors='none', zorder=3)

    letter_y = max(y_max, np.nanmax(means + ci95)) + y_range * 0.06
    for index, species in enumerate(SPECIES_ORDER):
        label = res['letters'].get(species, '')
        ax.text(index, letter_y, label, ha='center', va='bottom',
                fontsize=STAT_FS, fontweight='bold', color='#333')

    ax.set_xticks(positions)
    ax.set_xticklabels(SPECIES_ORDER, fontsize=TICK_FS)
    style_panel_axes(ax, ylabel, f"{title}\n{format_p_value(res['p_anova'])}")
    ax.set_xlim(-0.55, len(SPECIES_ORDER) - 0.45)
    ax.set_ylim(min(0, y_min - y_range * 0.05), letter_y + y_range * 0.20)


def draw_fraction_bar_jitter_panel(ax, groups_dict, ylabel, title):
    draw_slim_bar_jitter_panel(ax, groups_dict, ylabel, title)
    ax.set_ylim(0, 1)


def draw_line_panel(ax, groups_dict, ylabel, title):
    positions = np.arange(len(SPECIES_ORDER))
    data_lists = [groups_dict[species] for species in SPECIES_ORDER]
    all_vals = np.concatenate(data_lists)
    y_min, y_max = np.nanmin(all_vals), np.nanmax(all_vals)
    y_range = max(y_max - y_min, 1e-9)
    means = np.array([np.mean(values) for values in data_lists])
    stds = np.array([
        np.std(values, ddof=1) if len(values) > 1 else 0.0
        for values in data_lists
    ])

    res = duncan_mrt(data_lists, SPECIES_ORDER)
    ax.plot(positions, means, color='#444444', linewidth=1.8, zorder=2)
    for index, species in enumerate(SPECIES_ORDER):
        ax.errorbar(index, means[index], yerr=stds[index], fmt='o',
                    markersize=9, markerfacecolor=SPECIES_COLOR[species],
                    markeredgecolor='#222222', markeredgewidth=0.9,
                    ecolor='#333333', elinewidth=1.3, capsize=5, zorder=4)

    letter_y = max(means + stds) + y_range * 0.08
    for index, species in enumerate(SPECIES_ORDER):
        label = res['letters'].get(species, '')
        ax.text(index, letter_y, label, ha='center', va='bottom',
                fontsize=STAT_FS, fontweight='bold', color='#333')

    ax.set_xticks(positions)
    ax.set_xticklabels(SPECIES_ORDER, fontsize=TICK_FS)
    style_panel_axes(ax, ylabel, f"{title}\n{format_p_value(res['p_anova'])}")
    ax.set_xlim(-0.45, len(SPECIES_ORDER) - 0.55)
    ax.set_ylim(y_min - y_range * 0.08, letter_y + y_range * 0.20)


# ── 堆叠柱状图 ────────────────────────────────────────────────────────────────
def draw_hotspot_lollipop(ax, df, show_legend=True):
    net_means, net_ci95, total_means, shielded_means = {}, {}, {}, {}
    net_values = {}
    for sp in SPECIES_ORDER:
        g = df[df.species == sp]
        net_values[sp]     = g['net_accessible'].dropna().values
        net_means[sp]      = g['net_accessible'].mean()
        net_ci95[sp]       = g['net_accessible'].std() / np.sqrt(len(g)) * 1.96
        total_means[sp]    = g['n_hotspots'].mean()
        shielded_means[sp] = g['n_shielded_cands'].mean()

    xs = np.arange(len(SPECIES_ORDER))
    rng = np.random.default_rng(42)
    half_positions = xs - 0.10
    vp = ax.violinplot([net_values[sp] for sp in SPECIES_ORDER], positions=half_positions,
                       showmedians=False, showextrema=False, widths=0.42)
    for body, sp, center in zip(vp['bodies'], SPECIES_ORDER, half_positions):
        vertices = body.get_paths()[0].vertices
        vertices[:, 0] = np.minimum(vertices[:, 0], center)
        body.set_facecolor(SPECIES_COLOR[sp])
        body.set_alpha(0.52)
        body.set_edgecolor('none')

    for i, sp in enumerate(SPECIES_ORDER):
        color = SPECIES_COLOR[sp]
        net = net_means[sp]
        total = total_means[sp]
        loss = shielded_means[sp]
        shown = net_values[sp]
        if len(shown) > 160:
            shown = rng.choice(shown, size=160, replace=False)
        jitter = rng.uniform(-0.28, -0.12, len(shown))
        ax.scatter(xs[i] + jitter, shown, s=10, color=color,
               alpha=0.26, edgecolors='none', zorder=2)
        ax.vlines(xs[i], net, total, color=color, linewidth=8, alpha=0.32, zorder=1)
        ax.scatter(xs[i], total, s=120, facecolor='white', edgecolor=color,
                   linewidth=2.0, zorder=4)
        ax.errorbar(xs[i], net, yerr=net_ci95[sp], fmt='o', markersize=10,
                    markerfacecolor=color, markeredgecolor='#222222',
                    markeredgewidth=0.9, ecolor='#333333', elinewidth=1.4,
                    capsize=5, zorder=5)
        ax.text(xs[i] + 0.06, total, f'{total:.1f}', ha='left', va='center',
                fontsize=VALUE_FS - 2, color='#555')
        ax.text(xs[i] + 0.06, (net + total) / 2, f'-{loss:.1f}', ha='left',
                va='center', fontsize=VALUE_FS - 3, color='#555')

    # Duncan's MRT CLD letters on net_accessible
    y_top = max(total_means[sp] for sp in SPECIES_ORDER)
    y_min = min(np.nanmin(net_values[sp]) for sp in SPECIES_ORDER)
    y_span = max(y_top - y_min, 1e-9)
    res_bar = duncan_mrt(
        [df[df.species == sp]['net_accessible'].values for sp in SPECIES_ORDER],
        SPECIES_ORDER)
    letter_y = y_top + (y_top * 0.08)
    for xi, sp in enumerate(SPECIES_ORDER):
        ltr = res_bar['letters'].get(sp, '')
        ax.text(xi, letter_y, ltr, ha='center', va='bottom',
                fontsize=STAT_FS, fontweight='bold', color='#333')

    ax.set_xticks(xs)
    ax.set_xticklabels(SPECIES_ORDER, fontsize=TICK_FS)
    style_panel_axes(
        ax,
        'Hotspot Count',
        f'Ca$^{{2+}}$ Hotspot Accessibility\n{format_p_value(res_bar["p_anova"])}',
    )
    ax.set_ylim(max(0, y_min - y_span * 0.28), letter_y + y_span * 0.30)
    ax.set_xlim(-0.6, len(SPECIES_ORDER) - 0.4)

    if show_legend:
        legend_handles = [
            Line2D([0], [0], marker='o', color='none', markerfacecolor='#777',
                   markeredgecolor='#222', markersize=8, label='Net Accessible'),
            Line2D([0], [0], marker='o', color='none', markerfacecolor='white',
                   markeredgecolor='#777', markersize=8, label='Total Candidate'),
        ]
        ax.legend(handles=legend_handles, fontsize=LEGEND_FS - 2,
                  loc='upper left', bbox_to_anchor=(0.52, 0.98),
                  framealpha=0.78, edgecolor='none',
                  borderpad=0.25, labelspacing=0.3,
                  handlelength=1.6, handletextpad=0.5)


# ── Panel F: 热点残基 SASA 堆叠柱图（iface_full_sasa vs. iface_shielding）─────
def draw_sasa_dumbbell(ax, df, show_legend=True):
    full_means, residual_means, residual_ci95, shielded_means = {}, {}, {}, {}
    residual_values = {}
    for sp in SPECIES_ORDER:
        g = df[df.species == sp]
        residual = g['iface_full_sasa'] - g['iface_shielding']
        residual_values[sp] = residual.dropna().values
        full_means[sp]     = g['iface_full_sasa'].mean()
        residual_means[sp] = residual.mean()
        residual_ci95[sp]  = residual.std() / np.sqrt(len(residual)) * 1.96
        shielded_means[sp] = g['iface_shielding'].mean()

    xs    = np.arange(len(SPECIES_ORDER))
    y_top = max(full_means[sp] for sp in SPECIES_ORDER)
    rng = np.random.default_rng(42)
    half_positions = xs - 0.10
    vp = ax.violinplot([residual_values[sp] for sp in SPECIES_ORDER], positions=half_positions,
                       showmedians=False, showextrema=False, widths=0.42)
    for body, sp, center in zip(vp['bodies'], SPECIES_ORDER, half_positions):
        vertices = body.get_paths()[0].vertices
        vertices[:, 0] = np.minimum(vertices[:, 0], center)
        body.set_facecolor(SPECIES_COLOR[sp])
        body.set_alpha(0.52)
        body.set_edgecolor('none')

    for i, sp in enumerate(SPECIES_ORDER):
        color = SPECIES_COLOR[sp]
        full = full_means[sp]
        residual = residual_means[sp]
        shielded = shielded_means[sp]
        shown = residual_values[sp]
        if len(shown) > 160:
            shown = rng.choice(shown, size=160, replace=False)
        jitter = rng.uniform(-0.28, -0.12, len(shown))
        ax.scatter(xs[i] + jitter, shown, s=10, color=color,
               alpha=0.26, edgecolors='none', zorder=2)
        ax.vlines(xs[i], residual, full, color=color, linewidth=8,
                  alpha=0.32, zorder=1)
        ax.scatter(xs[i], full, s=120, facecolor='white', edgecolor=color,
                   linewidth=2.0, zorder=4)
        ax.errorbar(xs[i], residual, yerr=residual_ci95[sp], fmt='o', markersize=10,
                    markerfacecolor=color, markeredgecolor='#222222',
                    markeredgewidth=0.9, ecolor='#333333', elinewidth=1.4,
                    capsize=5, zorder=5)
        ax.text(xs[i] + 0.07, full, f'{full:.1f}', ha='left', va='center',
                fontsize=VALUE_FS - 2, color='#555')
        loss_label_y = residual - max(0.7, y_top * 0.018)
        ax.text(xs[i] + 0.07, loss_label_y, f'-{shielded:.1f}',
            ha='left', va='center', fontsize=VALUE_FS - 3, color='#555')

    # Duncan's MRT CLD letters on residual hotspot SASA
    res_sasa = duncan_mrt(
        [(df[df.species == sp]['iface_full_sasa'] -
          df[df.species == sp]['iface_shielding']).values for sp in SPECIES_ORDER],
        SPECIES_ORDER)
    letter_y = y_top + (y_top * 0.08)
    for xi, sp in enumerate(SPECIES_ORDER):
        ltr = res_sasa['letters'].get(sp, '')
        ax.text(xi, letter_y, ltr, ha='center', va='bottom',
                fontsize=STAT_FS, fontweight='bold', color='#333')

    ax.set_xticks(xs)
    ax.set_xticklabels(SPECIES_ORDER, fontsize=TICK_FS)
    style_panel_axes(
        ax,
        r'Hotspot Residue SASA (Å²)',
        r'Ca$^{2+}$ Hotspot Residue SASA' + f'\n{format_p_value(res_sasa["p_anova"])}',
    )
    y_min = min(np.nanmin(residual_values[sp]) for sp in SPECIES_ORDER)
    y_span = max(y_top - y_min, 1e-9)
    ax.set_ylim(max(0, y_min - y_span * 0.28), letter_y + y_span * 0.30)
    ax.set_xlim(-0.6, len(SPECIES_ORDER) - 0.4)
    if show_legend:
        legend_handles = [
             Line2D([0], [0], marker='o', color='none', markerfacecolor='#777',
                 markeredgecolor='#222', markersize=8, label='Residual'),
             Line2D([0], [0], marker='o', color='none', markerfacecolor='white',
                 markeredgecolor='#777', markersize=8, label='Full'),
        ]
        ax.legend(handles=legend_handles, fontsize=LEGEND_FS - 2,
                  loc='upper left', bbox_to_anchor=(0.52, 0.98),
                  framealpha=0.78, edgecolor='none',
                  borderpad=0.25, labelspacing=0.3,
                  handlelength=1.6, handletextpad=0.5)


# ══════════════════════════════════════════════════════════════════════════════
# 主函数
# ══════════════════════════════════════════════════════════════════════════════
def save_panel(fig, name):
    """Save as PNG/PDF/SVG."""
    save_fig(fig, name, dpi=DPI)


def main():
    df = pd.read_csv(os.path.join(CSV_DIR, 'hotspot_per_conformation.csv'))
    df['net_accessible'] = df['n_hotspots'] - df['n_shielded_cands']
    g = {sp: df[df.species == sp] for sp in SPECIES_ORDER}

    panels_violin = [
        ('A', {sp: g[sp]['iface_shielding'].dropna().values for sp in SPECIES_ORDER},
         r'Interface Shielding by Glycan (Å$^2$)', 'Interface Shielding'),
        ('B', {sp: g[sp]['hotspot_sasa_mean'].dropna().values for sp in SPECIES_ORDER},
         r'Hotspot Residue Mean SASA (Å$^{-2}$)', 'Hotspot Residue SASA'),
        ('C', {sp: g[sp]['hotspot_frac'].dropna().values for sp in SPECIES_ORDER},
            'Hotspot Fraction', 'Hotspot Fraction'),
        ('D', {sp: g[sp]['net_accessible'].dropna().values for sp in SPECIES_ORDER},
         r'Net Accessible Ca$^{2+}$ Hotspots', r'Net Accessible Ca$^{2+}$ Hotspots'),
    ]

    panel_drawers = {
        'A': draw_violin_panel,
        'B': draw_line_panel,
        'C': draw_fraction_bar_jitter_panel,
        'D': draw_line_panel,
    }

    # Panels A-D: semantic plot styles, with unchanged panel size and filenames
    for lbl, gd, ylabel, title in panels_violin:
        fig, ax = plt.subplots(figsize=PANEL_FIGSIZE)
        fig.patch.set_facecolor('white')
        drawer = panel_drawers[lbl]
        if drawer is draw_violin_panel:
            drawer(ax, gd, ylabel, title, lbl)
        else:
            drawer(ax, gd, ylabel, title)
        fig.subplots_adjust(**PANEL_ADJUST)
        save_panel(fig, f'Fig5{chr(ord("I") + ord(lbl) - ord("A"))}')
        plt.close(fig)

    # Panel E: total-to-net lollipop
    fig, ax = plt.subplots(figsize=PANEL_FIGSIZE)
    fig.patch.set_facecolor('white')
    draw_hotspot_lollipop(ax, df, show_legend=False)
    fig.subplots_adjust(**PANEL_ADJUST)
    save_panel(fig, 'Fig5M')
    plt.close(fig)

    # Panel F: full-to-residual SASA dumbbell
    fig, ax = plt.subplots(figsize=PANEL_FIGSIZE)
    fig.patch.set_facecolor('white')
    draw_sasa_dumbbell(ax, df, show_legend=False)
    fig.subplots_adjust(**PANEL_ADJUST)
    save_panel(fig, 'Fig5N')
    plt.close(fig)


if __name__ == '__main__':
    main()
