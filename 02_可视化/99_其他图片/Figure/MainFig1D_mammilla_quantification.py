"""
乳突层形态结构可视化 (合并自 plot_microstructure.py + plot_mammilla_density_significance.py)
============================================================
统计方法：三组比较采用 Tukey's HSD
输出：
    Fig_mammilla_microstructure_panels.png  — 三指标 (密度/体积/比) 箱线图面板（含Tukey字母）
    Fig_mammilla_density_significance.png   — 乳突密度显著性统计箱线图（含Tukey字母）
"""

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats

import os
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _save import save_fig

# ─── 全局绘图风格 ──────────────────────────────────────────────────────────
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams['font.sans-serif'] = ['Times New Roman', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="ticks", font="Times New Roman")

# ─── 数据路径 ──────────────────────────────────────────────────────────────
FILE_PATH = r'D:\system_folder\Desktop\Work On\01_数据与计算\乳突层形态结构\specie.xlsx'
OUT_DIR   = r'D:\system_folder\Desktop\Work On\02_可视化\Figure\png'
os.makedirs(OUT_DIR, exist_ok=True)

# ─── Standard species colors ──────────────────────────────────────────────
STANDARD_SPECIES_COLORS = {
    'Gallus': '#C46B83',
    'Anas': '#93AACD',
    'Columba': '#F3CE9D',
}
COLORS = {
    'Chicken': STANDARD_SPECIES_COLORS['Gallus'],
    'Duck': STANDARD_SPECIES_COLORS['Anas'],
    'Pigeon': STANDARD_SPECIES_COLORS['Columba'],
}
ORDER  = ['Chicken', 'Duck', 'Pigeon']
SPECIES_TICK_LABELS = ['Gallus', 'Anas', 'Columba']


# ══════════════════════════════════════════════════════════════════════════════
# Tukey's HSD (3组)
# ══════════════════════════════════════════════════════════════════════════════
def tukey_hsd(groups: list, names: list, alpha: float = 0.05) -> dict:
    """
    Tukey's HSD（单因素方差分析后多重比较）。

    参数
    ----
    groups : list of 1-D numpy arrays
    names  : list of str，各组名称
    alpha  : 显著水平（默认 0.05）

    返回
    ----
    dict 包含 ANOVA 结果、两两显著性矩阵、CLD 字母等
    """
    k     = len(groups)
    ns    = [len(g) for g in groups]
    means = np.array([g.mean() for g in groups])

    f_stat, p_anova = stats.f_oneway(*groups)

    # 按均值升序排列
    order    = np.argsort(means)
    s_means  = means[order]
    s_names  = [names[i]  for i in order]
    s_groups = [groups[i] for i in order]
    s_stds   = np.array([groups[i].std(ddof=1) for i in order])
    s_ns     = [ns[i]     for i in order]

    SS_e = sum(float(np.sum((g - g.mean()) ** 2)) for g in groups)
    df_e = sum(ns) - k
    MSE  = SS_e / df_e

    # 显著性矩阵（排序后编号）
    sig   = np.zeros((k, k), dtype=bool)
    diffs = np.zeros((k, k), dtype=float)
    q_crit = stats.studentized_range.ppf(1.0 - alpha, k=k, df=df_e)
    for i in range(k):
        for j in range(i + 1, k):
            diff = s_means[j] - s_means[i]
            se = np.sqrt(MSE / 2.0 * (1.0 / s_ns[i] + 1.0 / s_ns[j]))
            threshold = q_crit * se
            sig[i, j] = sig[j, i] = bool(diff > threshold)
            diffs[i, j] = diff
            diffs[j, i] = -diff

    # CLD 字母标注（3 组）
    letters = {}
    if k == 3:
        s01 = bool(sig[0, 1])
        s02 = bool(sig[0, 2])
        s12 = bool(sig[1, 2])
        table = {
            (False, False, False): ("a",  "a",  "a"),
            (False, False, True ): ("ab", "a",  "b"),
            (False, True,  False): ("a",  "ab", "b"),
            (False, True,  True ): ("a",  "a",  "b"),
            (True,  False, False): ("a",  "b",  "ab"),
            (True,  False, True ): ("a",  "b",  "a"),
            (True,  True,  False): ("a",  "b",  "b"),
            (True,  True,  True ): ("a",  "b",  "c"),
        }
        ltrs = table[(s01, s02, s12)]
        letters = {s_names[i]: ltrs[i] for i in range(3)}

    return dict(
        f_stat=f_stat, p_anova=p_anova,
        s_names=s_names, s_means=s_means, s_stds=s_stds,
        s_groups=s_groups, s_ns=s_ns,
        sig=sig, diffs=diffs, letters=letters,
    )


def print_tukey(label: str, res: dict):
    print(f"\n{'='*60}")
    print(f"  Tukey HSD — {label}")
    print(f"{'='*60}")
    print(f"  ANOVA: F = {res['f_stat']:.4f},  p = {res['p_anova']:.4e}")
    print(f"\n  {'Species':<12}  {'n':>3}  {'Mean':>10}  {'SD':>9}  {'Letter':>6}")
    print(f"  {'-'*48}")
    for i, nm in enumerate(res['s_names']):
        ltr = res['letters'].get(nm, '?')
        print(f"  {nm:<12}  {res['s_ns'][i]:>3}  {res['s_means'][i]:>10.4f}"
              f"  {res['s_stds'][i]:>9.4f}  {ltr:>6}")
    k = len(res['s_names'])
    print(f"\n  两两比较:")
    for i in range(k):
        for j in range(i + 1, k):
            d    = res['diffs'][i, j]
            sig  = res['sig'][i, j]
            mark = "sig **" if sig else " ns"
            print(f"    {res['s_names'][i]} vs {res['s_names'][j]}: "
                  f"diff={d:+.4f}  [{mark}]")

# ══════════════════════════════════════════════════════════════════════════════
# 共用数据加载函数
# ══════════════════════════════════════════════════════════════════════════════
def load_data():
    """加载全部三项指标的 DataFrame，限 iloc[0:9] 保证与密度列对齐"""
    df = pd.read_excel(FILE_PATH, header=0)
    rows = []
    for sp, d_col, v_col, r_col in [
        ('Chicken', 9,  11, 12),
        ('Duck',    18, 20, 21),
        ('Pigeon',  28, 30, 31),
    ]:
        slice_ = df.iloc[0:9]
        for _, row in slice_.iterrows():
            try:
                d = float(row.iloc[d_col])
                v = float(row.iloc[v_col])
                r = float(row.iloc[r_col])
            except (ValueError, TypeError):
                continue
            if pd.notna(d) and pd.notna(v) and pd.notna(r):
                rows.append({
                    'Species': sp,
                    'Mammilla Density (per mm²)': d,
                    'Column Unit Volume (10⁻³ mm³)': v,
                    'Unit Volume Ratio': r,
                })
    return pd.DataFrame(rows)


def load_metric_arrays():
    """返回各物种三项指标 numpy 数组（限 iloc[0:9] 避免下方混入其他量纲数据）"""
    df = pd.read_excel(FILE_PATH, header=0)
    result = {}
    for sp, d_col, v_col, r_col in [
        ('Chicken', 9,  11, 12),
        ('Duck',    18, 20, 21),
        ('Pigeon',  28, 30, 31),
    ]:
        result[sp] = {
            'density': df.iloc[0:9, d_col].dropna().astype(float).values,
            'volume':  df.iloc[0:9, v_col].dropna().astype(float).values,
            'ratio':   df.iloc[0:9, r_col].dropna().astype(float).values,
        }
    return result


# ══════════════════════════════════════════════════════════════════════════════
# Fig 1 — 三指标箱线图面板 (Density / Volume / Ratio)，含 Tukey 字母
# ══════════════════════════════════════════════════════════════════════════════
def plot_microstructure_panels(df_plot, metric_arrays: dict):
    """
    metric_arrays: dict  {species: {density/volume/ratio: np.ndarray}}
    """
    # Column Unit Volume panel removed; only Density and Unit Volume Ratio
    METRIC_KEYS = ['density', 'ratio']
    DF_COLS = [
        'Mammilla Density (per mm²)',
        'Unit Volume Ratio',
    ]
    titles = ['Mammilla Density', 'Unit Volume Ratio']

    fig, axes = plt.subplots(1, 2, figsize=(10, 6))

    for i, (mk, col) in enumerate(zip(METRIC_KEYS, DF_COLS)):
        ax = axes[i]

        # Tukey HSD
        grp_data  = [metric_arrays[sp][mk] for sp in ORDER]
        res = tukey_hsd(grp_data, ORDER)
        print_tukey(f"{titles[i]}", res)

        sns.boxplot(x='Species', y=col, hue='Species', order=ORDER, data=df_plot, ax=ax,
                palette=COLORS, width=0.5, showfliers=False,
                saturation=1, legend=False,
                boxprops=dict(alpha=1.0, linewidth=1.5),
                whiskerprops=dict(color='#444444', linewidth=1.5),
                capprops=dict(color='#444444', linewidth=1.5),
                medianprops=dict(color='#333333', linewidth=2.0))
        sns.stripplot(x='Species', y=col, hue='Species', order=ORDER, data=df_plot, ax=ax,
                  palette=COLORS, alpha=0.95, jitter=True, size=5,
                  edgecolor='#222222', linewidth=0.45, legend=False)

        # 标注 Tukey 字母
        y_range = df_plot[col].max() - df_plot[col].min()
        y_letter = df_plot[col].max() + y_range * 0.06
        for xi, sp in enumerate(ORDER):
            ltr = res['letters'].get(sp, '')
            ax.text(xi, y_letter, ltr, ha='center', va='bottom',
                    fontsize=20, fontweight='bold', color='#333333')

        ax.set_title(
            f"{titles[i]}\n"
            f"p = {res['p_anova']:.2e}",
            fontsize=20, fontweight='bold')
        ax.set_xlabel('')
        ax.set_ylabel(col, fontsize=20)
        ax.set_xticks(range(len(ORDER)))
        ax.set_xticklabels(SPECIES_TICK_LABELS)
        for tick in ax.get_xticklabels():
            tick.set_fontfamily('Times New Roman')
            tick.set_fontstyle('italic')
        ax.tick_params(axis='both', which='major', labelsize=20)
        ax.set_ylim(top=y_letter + y_range * 0.12)
        sns.despine(ax=ax)

    plt.tight_layout()
    save_fig(plt.gcf(), 'Fig1D')
    plt.close()


# ══════════════════════════════════════════════════════════════════════════════
# Fig 2 — 乳突密度显著性统计箱线图（Tukey HSD）
# ══════════════════════════════════════════════════════════════════════════════
def plot_mammilla_density_significance(chicken_data, duck_data, pigeon_data):
    # --- Tukey HSD ---
    groups = [chicken_data, duck_data, pigeon_data]
    names  = ['Chicken', 'Duck', 'Pigeon']
    res = tukey_hsd(groups, names)
    print_tukey("Mammilla Density (per mm²)", res)

    df_plot = pd.DataFrame(
        [{'Species': 'Chicken', 'Density': x} for x in chicken_data] +
        [{'Species': 'Duck',    'Density': x} for x in duck_data]    +
        [{'Species': 'Pigeon',  'Density': x} for x in pigeon_data]
    )

    # --- 绘图 ---
    fig, ax = plt.subplots(figsize=(6, 5.5))
    sns.boxplot(x='Species', y='Density', data=df_plot, hue='Species', order=ORDER, ax=ax,
                palette=COLORS, width=0.5, showfliers=False,
                saturation=1, legend=False,
                boxprops=dict(alpha=1.0, linewidth=1.5),
                whiskerprops=dict(color='#444444', linewidth=1.5),
                capprops=dict(color='#444444', linewidth=1.5),
                medianprops=dict(color='#333333', linewidth=2.0))
    sns.stripplot(x='Species', y='Density', data=df_plot, hue='Species', order=ORDER, ax=ax,
                  palette=COLORS, alpha=0.95, jitter=True, size=6,
                  edgecolor='#222222', linewidth=0.45, legend=False)
    ax.set_ylabel('Mammilla Density (per mm²)', fontsize=20, fontweight='bold')
    ax.set_xlabel('')
    ax.tick_params(axis='both', which='major', labelsize=20)

    # 标注显著性连线（有差异的组对）+ Tukey 字母
    y_range  = df_plot['Density'].max() - df_plot['Density'].min()
    y_base   = df_plot['Density'].max()
    h        = y_range * 0.08
    bracket_top = y_base

    # 显著对用连线标注
    sig_pairs = [(i, j) for i in range(3) for j in range(i+1, 3)
                 if res['sig'][
                     res['s_names'].index(ORDER[i]),
                     res['s_names'].index(ORDER[j])]]
    for (xi, xj) in sig_pairs:
        by = bracket_top + h * 0.5
        ax.plot([xi, xi, xj, xj],
                [by - h * 0.1, by, by, by - h * 0.1],
                lw=1.5, color='black')
        ax.text((xi + xj) / 2, by + h * 0.05, '**',
                ha='center', va='bottom', fontsize=20, color='black')
        bracket_top = by + h * 0.4

    # Tukey 字母
    y_letter = bracket_top + h * 0.8
    for xi, sp in enumerate(ORDER):
        ltr = res['letters'].get(sp, '')
        ax.text(xi, y_letter, ltr, ha='center', va='bottom',
                fontsize=20, fontweight='bold', color='#333333')

    ax.set_ylim(top=y_letter + y_range * 0.15)
    ax.set_title(
        f"Mammilla Density\n"
        f"Tukey ANOVA: F={res['f_stat']:.2f}, p={res['p_anova']:.2e}",
        fontsize=20, fontweight='bold')

    sns.despine()
    plt.tight_layout()
    pass  # density significance plot — supplementary, not main figure
    plt.close()


# ══════════════════════════════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    df_all     = load_data()
    m_arrays   = load_metric_arrays()
    chicken_arr = m_arrays['Chicken']['density']
    duck_arr    = m_arrays['Duck']['density']
    pigeon_arr  = m_arrays['Pigeon']['density']

    print("=== Fig 1: 三指标形态结构面板 (Tukey HSD) ===")
    plot_microstructure_panels(df_all, m_arrays)

    # Fig 2 (mammilla_density_significance) disabled — removed from output
    # print("\n=== Fig 2: 乳突密度显著性 (Tukey HSD) ===")
    # plot_mammilla_density_significance(chicken_arr, duck_arr, pigeon_arr)

    print("\n全部图表已生成完毕。")
