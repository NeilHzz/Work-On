"""
Fig_hotspot_ensemble_1_visualization.py
=========================================
Ca2+ 热点分布与构象轨迹（三面板）

面板布局（1行 × 3列）：
  Panel A: 每结构 Total Ca2+ 热点数分布（小提琴 + 散点）
  Panel B: 每结构 Glycan-Shielded 热点数分布（小提琴 + 散点）
  Panel C: 50 构象轨迹折线图 —— 各结构 n_hotspots 随模型编号变化

输入文件（csv/）：
  hotspot_per_conformation.csv

输出：
  Fig_hotspot_ensemble_1.png
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
    order  = np.argsort(means)
    s_means = means[order]
    s_names = [names[i] for i in order]
    crit = [stats.studentized_range.ppf(1.0 - alpha, k=p, df=df_e) * SE
            for p in range(2, k + 1)]
    sig = np.zeros((k, k), dtype=bool)
    for i in range(k):
        for j in range(i + 1, k):
            p_span = j - i + 1
            sig[i, j] = sig[j, i] = (s_means[j] - s_means[i] > crit[p_span - 2])
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
OUT_PNG = os.path.join(FOLDER, "Fig_hotspot_ensemble_1.png")
DPI     = 300

SPECIES_ORDER = ['Gallus', 'Anas', 'Columba']
SPECIES_COLOR = {'Gallus': '#B54664', 'Anas': '#7895C1', 'Columba': '#F0C284'}
STRUCTURE_ALPHA = {'Gallus': 0.55, 'Anas': 0.35, 'Columba': 0.22}


# ── 工具函数 ──────────────────────────────────────────────────────────────────
def sig_label(p):
    if p < 0.001: return '***'
    if p < 0.01:  return '**'
    if p < 0.05:  return '*'
    return 'ns'


def add_significance_brackets(ax, x1, x2, y, h, label, fs=8):
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], lw=0.9, c='#333')
    ax.text((x1 + x2) / 2, y + h * 1.1, label,
            ha='center', va='bottom', fontsize=fs, color='#333')


def mannwhitney_pairs(groups: list, alpha: float = 0.05) -> list:
    pairs = []
    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
            _, p = stats.mannwhitneyu(groups[i], groups[j], alternative='two-sided')
            if p < alpha:
                pairs.append((i, j, p))
    return sorted(pairs, key=lambda item: (item[1] - item[0], item[0], item[1]))


# ── Panel A / B: 小提琴 + 散点 ────────────────────────────────────────────────
def draw_violin_panel(ax, groups_dict, ylabel, title, panel_label):
    positions  = list(range(len(SPECIES_ORDER)))
    all_vals   = np.concatenate(list(groups_dict.values()))
    y_min, y_max = np.nanmin(all_vals), np.nanmax(all_vals)
    y_range    = y_max - y_min
    rng = np.random.default_rng(42)

    data_lists = [groups_dict[sp] for sp in SPECIES_ORDER]
    vp = ax.violinplot(data_lists, positions=positions,
                       showmedians=False, showextrema=False, widths=0.7)
    for i, body in enumerate(vp['bodies']):
        sp = SPECIES_ORDER[i]
        body.set_facecolor(SPECIES_COLOR[sp])
        body.set_alpha(0.55)
        body.set_edgecolor('none')

    for i, sp in enumerate(SPECIES_ORDER):
        vals = groups_dict[sp]
        jit  = rng.uniform(-0.12, 0.12, len(vals))
        ax.scatter(i + jit, vals, s=14, color=SPECIES_COLOR[sp],
                   alpha=0.65, edgecolors='none', zorder=3)
        med = np.median(vals)
        ax.hlines(med, i - 0.22, i + 0.22, color='#222', lw=1.6, zorder=4)

    grp_data = [groups_dict[sp] for sp in SPECIES_ORDER]
    sig_pairs = mannwhitney_pairs(grp_data)
    bracket_top = y_max
    if sig_pairs:
        base_y = y_max + y_range * 0.05
        step = max(y_range * 0.08, 0.4)
        for level, (i, j, p) in enumerate(sig_pairs):
            y = base_y + level * step
            add_significance_brackets(ax, i, j, y, step * 0.35, sig_label(p), fs=10)
            bracket_top = y + step * 1.2

    n_labels = [f'\n(n={len(groups_dict[sp])})' for sp in SPECIES_ORDER]
    ax.set_xticks(positions)
    ax.set_xticklabels([sp + n for sp, n in zip(SPECIES_ORDER, n_labels)], fontsize=8.5)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_title(f"{title}\nPairwise Mann–Whitney U", fontsize=9, pad=6)
    ax.set_ylim(y_min - y_range * 0.03, bracket_top + y_range * 0.20)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.text(-0.12, 1.04, panel_label, transform=ax.transAxes,
            fontsize=13, fontweight='bold', va='top')


# ── Panel C: 构象轨迹折线图 ───────────────────────────────────────────────────
def draw_trajectory(ax, df):
    """
    每条结构（short_name）画一条折线，model 1-50 为 x 轴，n_hotspots 为 y 轴。
    同物种线条颜色相同，Gallus 最粗，Anas 中等，Columba 最细。
    物种均值用加粗实线叠加。
    """
    lw_map    = {'Gallus': 1.4, 'Anas': 0.9, 'Columba': 0.55}
    alpha_map = {'Gallus': 0.65, 'Anas': 0.40, 'Columba': 0.25}

    for short in df['short_name'].unique():
        sub = df[df['short_name'] == short].sort_values('model')
        sp  = sub['species'].iloc[0]
        ax.plot(sub['model'], sub['n_hotspots'],
                color=SPECIES_COLOR[sp],
                lw=lw_map[sp], alpha=alpha_map[sp], zorder=2)

    # 物种均值线
    for sp in SPECIES_ORDER:
        sub = df[df['species'] == sp].groupby('model')['n_hotspots'].mean()
        ax.plot(sub.index, sub.values,
                color=SPECIES_COLOR[sp], lw=2.4, alpha=0.95, zorder=4,
                label=f'{sp} mean')

    # 图例
    legend_handles = [
        mpatches.Patch(facecolor=SPECIES_COLOR[sp], label=sp)
        for sp in SPECIES_ORDER
    ]
    ax.legend(handles=legend_handles, fontsize=8.5, loc='upper right',
              framealpha=0.7, edgecolor='none')

    ax.set_xlabel('Conformation model index', fontsize=9)
    ax.set_ylabel(r'Total Ca$^{2+}$ Hotspot Count', fontsize=9)
    ax.set_title('Hotspot Count Trajectory Across 50 Conformations', fontsize=10, pad=6)
    ax.set_xlim(1, 50)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.text(-0.07, 1.04, 'C', transform=ax.transAxes,
            fontsize=13, fontweight='bold', va='top')


# ══════════════════════════════════════════════════════════════════════════════
# 主函数
# ══════════════════════════════════════════════════════════════════════════════
def save_panel(fig, name):
    """Save as PNG (300 dpi) and PDF to FOLDER."""
    for ext in ('png', 'pdf'):
        out = os.path.join(FOLDER, f'{name}.{ext}')
        fig.savefig(out, dpi=DPI, bbox_inches='tight', facecolor='white')
        print(f"已保存: {out}")


def main():
    df = pd.read_csv(os.path.join(CSV_DIR, 'hotspot_per_conformation.csv'))
    g  = {sp: df[df.species == sp] for sp in SPECIES_ORDER}

    # ── Panel A: Total Ca2+ hotspots ──────────────────────────────────────
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    fig.patch.set_facecolor('white')
    draw_violin_panel(
        ax,
        {sp: g[sp]['n_hotspots'].dropna().values for sp in SPECIES_ORDER},
        r'Total Ca$^{2+}$ Hotspot Count',
        r'Total Ca$^{2+}$ Hotspots' + '\n(Exposed SASA > 1 Å²)',
        'A'
    )
    fig.tight_layout()
    save_panel(fig, 'Fig_hotspot_ensemble_1_A')
    plt.close(fig)

    # ── Panel B: Glycan-Shielded hotspots ────────────────────────────────
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    fig.patch.set_facecolor('white')
    draw_violin_panel(
        ax,
        {sp: g[sp]['n_shielded_cands'].dropna().values for sp in SPECIES_ORDER},
        'Glycan-Shielded Hotspot Count',
        'Glycan-Shielded Hotspots\n(ΔSASA > 5 Å²)',
        'B'
    )
    fig.tight_layout()
    save_panel(fig, 'Fig_hotspot_ensemble_1_B')
    plt.close(fig)

    # ── Panel C: Trajectory ───────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    fig.patch.set_facecolor('white')
    draw_trajectory(ax, df)
    fig.tight_layout()
    save_panel(fig, 'Fig_hotspot_ensemble_1_C')
    plt.close(fig)


if __name__ == '__main__':
    main()
