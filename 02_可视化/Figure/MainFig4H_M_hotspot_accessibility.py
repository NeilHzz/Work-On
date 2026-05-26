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
matplotlib.rcParams["font.family"] = "Times New Roman"
matplotlib.rcParams["font.sans-serif"] = ["Times New Roman", "DejaVu Sans"]
matplotlib.rcParams["mathtext.fontset"] = "stix"
from matplotlib.gridspec import GridSpec
from scipy import stats
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _save import save_fig


TITLE_FS = 24
AXIS_LABEL_FS = 24
TICK_FS = 24
LEGEND_FS = 24
STAT_FS = 24
VALUE_FS = 24


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
SPECIES_COLOR = {'Gallus': '#B54664', 'Anas': '#7895C1', 'Columba': '#F0C284'}


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
        body.set_alpha(0.55)
        body.set_edgecolor('none')

    for i, sp in enumerate(SPECIES_ORDER):
        vals = groups_dict[sp]
        jit  = rng.uniform(-0.12, 0.12, len(vals))
        ax.scatter(i + jit, vals, s=14, color=SPECIES_COLOR[sp],
                   alpha=0.65, edgecolors='none', zorder=3)
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

    n_labels = [f'\n(n={len(groups_dict[sp])})' for sp in SPECIES_ORDER]
    ax.set_xticks(positions)
    ax.set_xticklabels([sp + n for sp, n in zip(SPECIES_ORDER, n_labels)],
                       fontsize=TICK_FS)
    ax.set_ylabel(ylabel, fontsize=AXIS_LABEL_FS)
    ax.set_title(f"{title}\n{format_p_value(res['p_anova'])}",
                 fontsize=TITLE_FS, pad=6)
    ax.set_ylim(y_min - y_range * ypad_bot, letter_y + y_range * 0.20)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


# ── 堆叠柱状图 ────────────────────────────────────────────────────────────────
def draw_stacked_bar(ax, df):
    means, stds, shielded_means = {}, {}, {}
    for sp in SPECIES_ORDER:
        g = df[df.species == sp]
        means[sp]         = g['net_accessible'].mean()
        stds[sp]          = g['net_accessible'].std() / np.sqrt(len(g)) * 1.96
        shielded_means[sp] = g['n_shielded_cands'].mean()

    xs = np.arange(len(SPECIES_ORDER))
    bar_w = 0.52

    for i, sp in enumerate(SPECIES_ORDER):
        col  = SPECIES_COLOR[sp]
        net  = means[sp]
        sh   = shielded_means[sp]
        err  = stds[sp]

        # Net accessible bar (solid)
        ax.bar(xs[i], net, bar_w, color=col, alpha=0.80,
               label='Net Accessible' if i == 0 else '')

        # Shielded bar on top (hatched)
        ax.bar(xs[i], sh, bar_w, bottom=net, color=col, alpha=0.28,
               hatch='///', edgecolor=col, linewidth=0.6,
             label='Glycan-Shielded' if i == 0 else '')

        # Error bar on net
        ax.errorbar(xs[i], net, yerr=err, fmt='none',
                    color='#333', elinewidth=1.4, capsize=5, zorder=5)

        # Text labels
        ax.text(xs[i], net / 2, f'{net:.1f}', ha='center', va='center',
            fontsize=VALUE_FS, color='white')
        ax.text(xs[i], net + sh / 2, f'{sh:.1f}', ha='center', va='center',
            fontsize=VALUE_FS, color='#555')

    # Duncan's MRT CLD letters on net_accessible
    y_top = max(means[sp] + shielded_means[sp] for sp in SPECIES_ORDER)
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
    ax.set_ylabel('Hotspot Count (mean ± 95% CI)', fontsize=AXIS_LABEL_FS)
    ax.set_title(
        f'Ca$^{{2+}}$ Hotspot Accessibility'
        f'\n{format_p_value(res_bar["p_anova"])}',
        fontsize=TITLE_FS, pad=8)
    ax.set_ylim(0, letter_y + y_top * 0.22)
    ax.set_xlim(-0.6, len(SPECIES_ORDER) - 0.4)

    legend_handles = [
        mpatches.Patch(facecolor='#aaa', label='Net Accessible'),
        mpatches.Patch(facecolor='#ddd', hatch='///', edgecolor='#888',
                       label='Glycan-Shielded'),
    ]
    ax.legend(handles=legend_handles, fontsize=LEGEND_FS, loc='upper right',
              framealpha=0.8, edgecolor='none')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


# ── Panel F: 热点残基 SASA 堆叠柱图（iface_full_sasa vs. iface_shielding）─────
def draw_sasa_bar(ax, df):
    means, stds, shielded_means = {}, {}, {}
    for sp in SPECIES_ORDER:
        g = df[df.species == sp]
        means[sp]          = g['iface_full_sasa'].mean()
        stds[sp]           = g['iface_full_sasa'].std() / np.sqrt(len(g)) * 1.96
        shielded_means[sp] = g['iface_shielding'].mean()

    xs    = np.arange(len(SPECIES_ORDER))
    bar_w = 0.52

    for i, sp in enumerate(SPECIES_ORDER):
        col  = SPECIES_COLOR[sp]
        net  = means[sp]
        sh   = shielded_means[sp]
        err  = stds[sp]

        ax.bar(xs[i], net, bar_w, color=col, alpha=0.80,
            label='Net Accessible' if i == 0 else '')
        ax.bar(xs[i], sh, bar_w, bottom=net, color=col, alpha=0.28,
            hatch='///', edgecolor=col, linewidth=0.6,
            label='Glycan-Shielded' if i == 0 else '')
        ax.errorbar(xs[i], net, yerr=err, fmt='none',
                    color='#333', elinewidth=1.4, capsize=5, zorder=5)
        ax.text(xs[i], net / 2, f'{net:.1f}',
            ha='center', va='center', fontsize=VALUE_FS, color='white')
        # shielded 段太窄时将标注移到柱顶上方避免遗挮
        min_inside = (net + sh) * 0.09
        if sh >= min_inside:
            ax.text(xs[i], net + sh / 2, f'{sh:.1f}',
                    ha='center', va='center', fontsize=VALUE_FS, color='#555')
        else:
            ax.text(xs[i], net + sh + (net + sh) * 0.015, f'{sh:.1f}',
                    ha='center', va='bottom', fontsize=VALUE_FS, color='#555')

    y_top = max(means[sp] + shielded_means[sp] for sp in SPECIES_ORDER)
    # Duncan's MRT CLD letters on iface_full_sasa
    res_sasa = duncan_mrt(
        [df[df.species == sp]['iface_full_sasa'].values for sp in SPECIES_ORDER],
        SPECIES_ORDER)
    letter_y = y_top + (y_top * 0.08)
    for xi, sp in enumerate(SPECIES_ORDER):
        ltr = res_sasa['letters'].get(sp, '')
        ax.text(xi, letter_y, ltr, ha='center', va='bottom',
                fontsize=STAT_FS, fontweight='bold', color='#333')

    ax.set_xticks(xs)
    ax.set_xticklabels(SPECIES_ORDER, fontsize=TICK_FS)
    ax.set_ylabel(r'Hotspot Residue SASA (Å²)', fontsize=AXIS_LABEL_FS)
    ax.set_title(
        r'Ca$^{2+}$ Hotspot Residue SASA'
        f'\n{format_p_value(res_sasa["p_anova"])}',
        fontsize=TITLE_FS, pad=8)
    ax.set_ylim(0, letter_y + y_top * 0.22)
    ax.set_xlim(-0.6, len(SPECIES_ORDER) - 0.4)
    legend_handles = [
        mpatches.Patch(facecolor='#aaa', label='Net Accessible'),
        mpatches.Patch(facecolor='#ddd', hatch='///', edgecolor='#888',
                       label='Glycan-Shielded'),
    ]
    ax.legend(handles=legend_handles, fontsize=LEGEND_FS, loc='upper right',
              framealpha=0.8, edgecolor='none')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


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
         'Hotspot Fraction\n(hotspots / candidates)', 'Hotspot Fraction'),
        ('D', {sp: g[sp]['net_accessible'].dropna().values for sp in SPECIES_ORDER},
         r'Net Accessible Ca$^{2+}$ Hotspots', r'Net Accessible Ca$^{2+}$ Hotspots'),
    ]

    # Panels A-D: individual violin plots
    for lbl, gd, ylabel, title in panels_violin:
        fig, ax = plt.subplots(figsize=(5.9, 5.5))
        fig.patch.set_facecolor('white')
        draw_violin_panel(ax, gd, ylabel, title, lbl)
        fig.tight_layout()
        save_panel(fig, f'Fig5{chr(ord("I") + ord(lbl) - ord("A"))}')
        plt.close(fig)

    # Panel E: stacked bar
    fig, ax = plt.subplots(figsize=(5.9, 5.5))
    fig.patch.set_facecolor('white')
    draw_stacked_bar(ax, df)
    fig.tight_layout()
    save_panel(fig, 'Fig5M')
    plt.close(fig)

    # Panel F: SASA bar
    fig, ax = plt.subplots(figsize=(5.9, 5.5))
    fig.patch.set_facecolor('white')
    draw_sasa_bar(ax, df)
    fig.tight_layout()
    save_panel(fig, 'Fig5N')
    plt.close(fig)


if __name__ == '__main__':
    main()
