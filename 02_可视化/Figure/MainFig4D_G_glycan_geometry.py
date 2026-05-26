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
matplotlib.rcParams["font.family"] = "Times New Roman"
matplotlib.rcParams["font.sans-serif"] = ["Times New Roman", "DejaVu Sans"]
matplotlib.rcParams["mathtext.fontset"] = "stix"
from matplotlib.lines import Line2D
from pathlib import Path
import sys; sys.path.insert(0, str(Path(__file__).parent))
from _save import save_fig
from scipy import stats


TITLE_FS = 9.5
AXIS_LABEL_FS = 9.5
TICK_FS = 9
STAT_FS = 10


def format_p_value(p_value: float) -> str:
    if p_value <= 0 or not np.isfinite(p_value):
        return 'p < 1e-300'
    return f'p = {p_value:.2e}'


# ══════════════════════════════════════════════════════════════════════
# Duncan's Multiple Range Test (3 groups)
# ══════════════════════════════════════════════════════════════════════
def duncan_mrt(groups: list, names: list, alpha: float = 0.05) -> dict:
    """Duncan's MRT for 3 groups. Returns CLD letters dict {name: letter}."""
    k     = len(groups)
    ns    = [len(g) for g in groups]
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
    return dict(f_stat=f_stat, p_anova=p_anova, letters=letters,
                s_names=s_names, s_means=s_means, sig=sig)

CSV_DIR = Path(r'D:\system_folder\Desktop\Work On\01_数据与计算\ReGlyco_Ensemble\csv')
OUT_DIR = Path(r'D:\system_folder\Desktop\Work On\02_可视化\Figure\png')

SPECIES_ORDER  = ['Gallus', 'Anas', 'Columba']
SPECIES_COLORS = {'Gallus': '#B54664', 'Anas': '#7895C1', 'Columba': '#F0C284'}
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

def significance_label(p: float) -> str:
    if p < 0.001: return '***'
    if p < 0.01:  return '**'
    if p < 0.05:  return '*'
    return 'ns'


def violin_one(ax, metric, ylabel, subtitle=''):
    data = [detail.loc[detail.species==sp, metric].dropna().values
            for sp in SPECIES_ORDER]
    colors = [SPECIES_COLORS[sp] for sp in SPECIES_ORDER]

    # Duncan's MRT
    res = duncan_mrt(data, SPECIES_ORDER)

    parts = ax.violinplot(data, positions=range(len(SPECIES_ORDER)),
                          showmedians=True, showextrema=False, widths=0.6)
    for pc, c in zip(parts['bodies'], colors):
        pc.set_facecolor(c)
        pc.set_alpha(0.75)
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
                   color=SPECIES_COLORS[sp], alpha=0.5, linewidths=0, zorder=3)

    ax.set_xticks(range(len(SPECIES_ORDER)))
    ax.set_xticklabels([f'{sp}\n(n={len(d)})' for sp, d in zip(SPECIES_ORDER, data)],
                       fontsize=TICK_FS)
    ax.set_ylabel(ylabel, fontsize=AXIS_LABEL_FS)

    # Duncan CLD 字母标注
    ymax = max(d.max() for d in data if len(d))
    span = ymax - min(d.min() for d in data if len(d))
    letter_y = ymax + span * 0.05
    for xi, sp in enumerate(SPECIES_ORDER):
        ltr = res['letters'].get(sp, '')
        ax.text(xi, letter_y, ltr, ha='center', va='bottom',
            fontsize=STAT_FS, fontweight='bold', color='#333')
    ax.set_ylim(top=letter_y + span * 0.15)
    p_text = format_p_value(res['p_anova'])
    title_str = (f"{subtitle}\n{p_text}"
                if subtitle else
                p_text)
    ax.set_title(title_str, fontsize=TITLE_FS, color='black', pad=4)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


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

for mk, ml, lbl in zip(metric_keys, metric_labels, panel_labels):
    fig, ax = plt.subplots(figsize=(5, 5))
    fig.patch.set_facecolor('white')
    violin_one(ax, mk, ml, subtitle=SUBTITLES.get(mk, ''))
    fig.tight_layout()
    save_panel(fig, f'Fig5{chr(ord("E") + ord(lbl) - ord("A"))}')
    plt.close(fig)
