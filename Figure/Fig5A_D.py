"""
Fig_ensemble_visualization.py
==============================
Re-Glyco Ensemble Ca2+ 结合能力综合可视化

面板布局（2行 × 3列，上方 strip 图跨全宽）：
  Panel A (top, full-width): Strip chart —— 18 糖基化 + 3 apo 结构
  Panel B (bottom-left)    : Ca2+ 热点残基数（ASP/GLU，APBS < -5 kT/e）
  Panel C (bottom-middle)  : Ca2+-可及羧基 SASA（probe = 裸离子 1.00 A）
  Panel D (bottom-right)   : 表面 APBS 中位值分布（strip chart + 物种均值）

数据来源：
  - {short_name}_APBS_glycanAware.csv  （每蛋白 APBS 结果）
  - {short_name}_ensemble_sasa.csv     （ensemble SASA 均值）
  - summary_ensemble.csv               （汇总指标）
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection
from matplotlib.colors import TwoSlopeNorm
from matplotlib.lines import Line2D
import matplotlib.ticker as ticker
matplotlib.rcParams["font.family"] = "Times New Roman"
matplotlib.rcParams["font.sans-serif"] = ["Times New Roman", "DejaVu Sans"]
matplotlib.rcParams["mathtext.fontset"] = "stix"
from scipy import stats
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _save import save_fig

# ─── 配置 ─────────────────────────────────────────────────────────────────
FOLDER  = r"D:\system_folder\Desktop\Work On\ReGlyco_Ensemble"
CSV_DIR = os.path.join(FOLDER, "csv")
OUT_DIR = r"D:\system_folder\Desktop\Work On\Figure\png"
DPI     = 300
VCLIP   = 20.0    # strip chart ± kT/e 截断

SPECIES_COLOR = {
    'Anas':    '#7895C1',
    'Columba': '#F0C284',
    'Gallus':  '#B54664',
}

# 绘图顺序：G1 + A1-A3 + C1-C14（糖基化），再 3 个 apo
GLYC_ORDER = ['G1', 'A1', 'A2', 'A3',
              'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7',
              'C8', 'C9', 'C10', 'C11', 'C12', 'C13', 'C14']
APO_ORDER  = ['G1_apo', 'A1_apo', 'C1_apo']

# 各物种 N-糖基化修饰位点（残基序号）
GLYCAN_SITE = {'Gallus': 293, 'Anas': 97, 'Columba': 97}


# ─── 统计注释辅助函数 ──────────────────────────────────────────────────────
def _pstar(p):
    if p < 0.001: return '***'
    if p < 0.01:  return '**'
    if p < 0.05:  return '*'
    return 'ns'


def _stat_bracket(ax, x1, x2, y0, tick_h, label):
    """在 x1~x2 之间 y=y0 处绘制带显著性标注的括号线。"""
    ax.plot([x1, x1, x2, x2], [y0, y0 + tick_h, y0 + tick_h, y0],
            color='#333', lw=0.9, clip_on=False)
    ax.text((x1 + x2) / 2, y0 + tick_h * 1.3, label,
            ha='center', va='bottom', fontsize=9,
            color='#222', fontweight='bold', clip_on=False)


def species_of(name):
    n = name.split('_')[0]
    if n.startswith('A'):
        return 'Anas'
    if n.startswith('C'):
        return 'Columba'
    return 'Gallus'


# ─── 数据加载 ─────────────────────────────────────────────────────────────
def load_data():
    csv_map = {}
    for name in GLYC_ORDER:
        f = os.path.join(CSV_DIR, f"{name}_APBS_glycanAware.csv")
        if os.path.exists(f):
            csv_map[name] = pd.read_csv(f)
    for name in APO_ORDER:
        base = name.replace('_apo', '')
        f = os.path.join(CSV_DIR, f"{base}_apo_APBS.csv")
        if os.path.exists(f):
            csv_map[name] = pd.read_csv(f)

    summary_f = os.path.join(FOLDER, "summary_ensemble.csv")
    summary = pd.read_csv(summary_f, encoding='utf-8-sig') if os.path.exists(summary_f) else None
    return csv_map, summary


# ─── Panel A: Strip chart ─────────────────────────────────────────────────
def draw_strip(ax, csv_map):
    # G1 紧跟 G1_apo，再 A1/A1_apo/A2/A3，再 C1/C1_apo/C2-C14
    INTERLEAVED_ORDER = [
        'G1_apo', 'G1',
        'A1_apo', 'A1', 'A2', 'A3',
        'C1_apo', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7',
        'C8', 'C9', 'C10', 'C11', 'C12', 'C13', 'C14',
    ]
    all_names = [n for n in INTERLEAVED_ORDER if n in csv_map]
    n_rows = len(all_names)

    cmap = plt.cm.RdBu
    norm = TwoSlopeNorm(vmin=-VCLIP, vcenter=0, vmax=VCLIP)

    max_res = max(
        int(csv_map[n][csv_map[n]['Type'] == 'Protein']['ResSeq'].max())
        for n in all_names
    )

    patches, colors = [], []
    rect_h = 0.78

    for row_i, name in enumerate(all_names):
        df   = csv_map[name]
        surf = df[(df['SurfaceLabel'] == 'Surface') & (df['Type'] == 'Protein')]
        y_c  = n_rows - row_i - 1 + 0.5

        for _, r in surf.iterrows():
            x   = float(r['ResSeq']) - 0.5
            pot = float(r['APBS_kT_e'])
            rect = mpatches.FancyBboxPatch(
                (x, y_c - rect_h / 2), 1.0, rect_h,
                boxstyle='square,pad=0', linewidth=0
            )
            patches.append(rect)
            colors.append(np.clip(pot, -VCLIP, VCLIP))

    pc = PatchCollection(patches, cmap=cmap, norm=norm, linewidths=0)
    pc.set_array(np.array(colors))
    ax.add_collection(pc)

    # y 轴标签
    for row_i, name in enumerate(all_names):
        sp    = species_of(name)
        color = SPECIES_COLOR[sp]
        label = name.replace('_apo', '') + (' (Deglyco)' if '_apo' in name else '')
        y_c   = n_rows - row_i - 1 + 0.5
        ax.text(-2, y_c, label, ha='right', va='center',
                fontsize=7.5, fontweight='bold', color=color,
                style=('italic' if '_apo' in name else 'normal'))

    ax.tick_params(axis='y', length=0)
    ax.set_yticks([])
    ax.set_ylim(0, n_rows)
    ax.set_xlim(1, max_res + 1)
    ax.set_xlabel('Residue position', fontsize=10)

    # 物种间分隔线（G/A/C 物种组之间）
    prev_sp = None
    for i, n in enumerate(all_names):
        sp = species_of(n)
        if sp != prev_sp and prev_sp is not None:
            y_line = n_rows - i
            ax.axhline(y_line, color='#555', lw=1.4, ls='--', alpha=0.7)
        prev_sp = sp

    # 物种图例
    sp_legend = [
        mpatches.Patch(facecolor=SPECIES_COLOR[sp], label=sp, alpha=0.85)
        for sp in ['Gallus', 'Anas', 'Columba']
    ]
    ax.legend(handles=sp_legend, loc='upper left',
              fontsize=8, framealpha=0.7, edgecolor='none',
              title='Species', title_fontsize=8)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # ── 糖基化修饰位点标记 ──────────────────────────────────────────
    sp_y_ranges = {}
    for row_i, name in enumerate(all_names):
        sp = species_of(name)
        y_bot = n_rows - row_i - 1
        if sp not in sp_y_ranges:
            sp_y_ranges[sp] = [y_bot, y_bot + 1]
        else:
            sp_y_ranges[sp][0] = min(sp_y_ranges[sp][0], y_bot)
            sp_y_ranges[sp][1] = max(sp_y_ranges[sp][1], y_bot + 1)

    labeled_sites = set()
    for sp, (y0, y1) in sp_y_ranges.items():
        site = GLYCAN_SITE.get(sp)
        if site is None:
            continue
        # 白色衬底线增强对比
        ax.vlines(site, y0, y1, colors='white', linewidths=2.5, zorder=5)
        # 黑色虚线标记位点
        ax.vlines(site, y0, y1, colors='#222222', linewidths=1.2,
                  linestyles='--', zorder=6)
        if site not in labeled_sites:
            if site == 293:
                # N293: 顶部（图表上方）
                ax.text(site, y1 + 0.12, f'N{site}', fontsize=6.5, ha='center',
                        va='bottom', color='#222222', fontweight='bold',
                        clip_on=False)
            else:
                # N97: 箭头尖端指向 strip 底部边缘，文字偏移到轴下方
                ax.annotate(f'N{site}', xy=(site, 0.1), xycoords='data',
                            xytext=(-18, -20), textcoords='offset points',
                            fontsize=6.5, ha='center', va='top',
                            color='#222222', fontweight='bold',
                            clip_on=False,
                            arrowprops=dict(arrowstyle='->', color='#222222',
                                            lw=0.8, mutation_scale=7))
            labeled_sites.add(site)

    # colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = ax.get_figure().colorbar(
        sm, ax=ax, orientation='vertical',
        fraction=0.015, pad=0.03, shrink=0.85
    )
    cbar.set_label('APBS potential (kT/e)', fontsize=8)
    cbar.ax.tick_params(labelsize=7)

    return norm, cmap


# ─── Panel B: Ca2+ 热点数 ─────────────────────────────────────────────────
def draw_hotspot(ax, summary):
    """
    每个物种内所有结构以散点展示，叠加物种均值条形图。
    """
    if summary is None:
        ax.text(0.5, 0.5, 'No summary data', ha='center', va='center',
                transform=ax.transAxes, fontsize=10, color='gray')
        return

    species_order = ['Gallus', 'Anas', 'Columba']
    x_map = {sp: i for i, sp in enumerate(species_order)}

    glyc = summary[~summary['IsApo']]
    apo  = summary[ summary['IsApo']]

    rng = np.random.default_rng(42)
    stat_b_queue = []

    for sp in species_order:
        xi = x_map[sp]
        g_vals = glyc[glyc['Species'] == sp]['N_hotspot'].values
        a_vals = apo [apo ['Species'] == sp]['N_hotspot'].values
        col    = SPECIES_COLOR[sp]

        # 条形 (均值)
        if len(g_vals):
            ax.bar(xi - 0.2, g_vals.mean(), 0.35, color=col, alpha=0.80, zorder=2)
            # 误差棒（≥2个样本）
            if len(g_vals) > 1:
                ax.errorbar(xi - 0.2, g_vals.mean(), yerr=g_vals.std(),
                            fmt='none', color='#333', elinewidth=1.2, capsize=4, zorder=3)
        if len(a_vals):
            ax.bar(xi + 0.2, a_vals.mean(), 0.35, color=col,
                   alpha=0.40, hatch='///', edgecolor='gray', linewidth=0.6, zorder=2)

        # 散点
        if len(g_vals):
            jit = rng.uniform(-0.08, 0.08, len(g_vals))
            ax.scatter(xi - 0.2 + jit, g_vals, s=28, color=col,
                       edgecolors='white', linewidths=0.5, zorder=4, alpha=0.9)
        if len(a_vals):
            jit = rng.uniform(-0.08, 0.08, len(a_vals))
            ax.scatter(xi + 0.2 + jit, a_vals, s=28, color=col,
                       edgecolors='white', linewidths=0.5, zorder=4, alpha=0.55)

        # 收集统计数据，稍后统一绘制
        if len(g_vals) and len(a_vals):
            gm   = g_vals.mean()
            am   = a_vals[0]
            gstd = g_vals.std() if len(g_vals) > 1 else 0
            delta = gm - am
            sign  = '+' if delta >= 0 else '-'
            if len(g_vals) >= 2:
                _, p  = stats.ttest_1samp(g_vals, am)
                lbl   = _pstar(p)
                data_top = max(g_vals.max() + gstd, am)
                stat_b_queue.append((xi, data_top, lbl, delta, sign))

    # 统一高度绘制括号
    if stat_b_queue:
        tick_h   = 0.8
        y0_global = max(d[1] for d in stat_b_queue) + 1.5
        for xi, _, lbl, delta, sign in stat_b_queue:
            _stat_bracket(ax, xi - 0.2, xi + 0.2, y0_global, tick_h, lbl)
            ax.text(xi, y0_global + tick_h * 2.5, f'\u0394{sign}{abs(delta):.1f}',
                    ha='center', va='bottom', fontsize=7.5, color='#555')
        ymax_stat = y0_global + tick_h * 5
    else:
        ymax_stat = 0

    all_vals = pd.concat([glyc['N_hotspot'], apo['N_hotspot']]).values
    ymax = max(all_vals.max() + 2, ymax_stat + 1)
    ax.set_xticks(range(len(species_order)))
    ax.set_xticklabels(species_order, fontsize=9)
    ax.set_ylabel('Ca2+ binding hotspots (n)', fontsize=9)
    ax.set_title('Ca2+ Hotspot Residues\n(Asp/Glu, APBS < -5 kT/e, surface)',
                 fontsize=9, pad=8)
    ax.set_ylim(0, max(ymax, 5))

    # 图例
    legend_els = [
        mpatches.Patch(facecolor='#888', alpha=0.80, label='Glycosylated'),
        mpatches.Patch(facecolor='#888', alpha=0.40, hatch='///',
                       edgecolor='gray', label='Deglyco (no glycan)'),
    ]
    ax.legend(handles=legend_els, fontsize=7.5, framealpha=0.6)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))


# ─── Panel C: Asp+Glu 表面 SASA（从 APBS CSV 逐结构计算）────────────────
def draw_ca2_sasa(ax, csv_map):
    """从每个结构的 APBS CSV 中计算 ASP+GLU 表面残基 SASA_A2 之和，
    正确反映糖链存在/缺失对羧基可及性的影响。"""
    CARBOXYL = ['ASP', 'GLU']
    species_order = ['Gallus', 'Anas', 'Columba']
    x_map = {sp: i for i, sp in enumerate(species_order)}
    rng = np.random.default_rng(42)

    # 逐结构计算
    glyc_sasa = {sp: [] for sp in species_order}
    apo_sasa  = {sp: [] for sp in species_order}
    for name in GLYC_ORDER:
        if name not in csv_map:
            continue
        df  = csv_map[name]
        sel = df[(df['Type'] == 'Protein') & (df['ResName'].isin(CARBOXYL))
                 & (df['SurfaceLabel'] == 'Surface')]
        glyc_sasa[species_of(name)].append(sel['SASA_A2'].sum())
    for name in APO_ORDER:
        if name not in csv_map:
            continue
        df  = csv_map[name]
        sel = df[(df['Type'] == 'Protein') & (df['ResName'].isin(CARBOXYL))
                 & (df['SurfaceLabel'] == 'Surface')]
        apo_sasa[species_of(name)].append(sel['SASA_A2'].sum())

    max_y = 0
    stat_c_queue = []   # (xi, data_top, label, delta, sign)

    for sp in species_order:
        xi     = x_map[sp]
        g_vals = np.array(glyc_sasa[sp])
        a_vals = np.array(apo_sasa[sp])
        col    = SPECIES_COLOR[sp]

        if len(g_vals):
            gm   = g_vals.mean()
            gstd = g_vals.std() if len(g_vals) > 1 else 0
            ax.bar(xi - 0.2, gm, 0.35, color=col, alpha=0.80, zorder=2)
            if len(g_vals) > 1:
                ax.errorbar(xi - 0.2, gm, yerr=gstd,
                            fmt='none', color='#333', elinewidth=1.2, capsize=4, zorder=3)
            jit = rng.uniform(-0.08, 0.08, len(g_vals))
            ax.scatter(xi - 0.2 + jit, g_vals, s=28, color=col,
                       edgecolors='white', linewidths=0.5, zorder=4, alpha=0.9)
            max_y = max(max_y, gm + gstd + 30)

        if len(a_vals):
            ax.bar(xi + 0.2, a_vals.mean(), 0.35, color=col,
                   alpha=0.40, hatch='///', edgecolor='gray', linewidth=0.6, zorder=2)
            jit = rng.uniform(-0.08, 0.08, len(a_vals))
            ax.scatter(xi + 0.2 + jit, a_vals, s=28, color=col,
                       edgecolors='white', linewidths=0.5, zorder=4, alpha=0.55)
            max_y = max(max_y, a_vals.max() + 30)

        # 统计检验 + Δ
        if len(g_vals) and len(a_vals):
            am    = a_vals[0]
            gm    = g_vals.mean()
            gstd  = g_vals.std() if len(g_vals) > 1 else 0
            delta = gm - am
            sign  = '+' if delta >= 0 else '-'
            if len(g_vals) >= 2:
                _, p = stats.ttest_1samp(g_vals, am)
                lbl  = _pstar(p)
                data_top = max(g_vals.max() + gstd, a_vals.max())
                stat_c_queue.append((xi, data_top, lbl, delta, sign))

    # 统一高度绘제括号
    if stat_c_queue:
        tick_h    = 120          # Panel C y-range ~2700, font ~75 units; need gap > 80 units
        y0_global = max(d[1] for d in stat_c_queue) + 50
        for xi, _, lbl, delta, sign in stat_c_queue:
            _stat_bracket(ax, xi - 0.2, xi + 0.2, y0_global, tick_h, lbl)
            ax.text(xi, y0_global + tick_h * 3.0, f'\u0394{sign}{abs(delta):.0f} \u00c5\u00b2',
                    ha='center', va='bottom', fontsize=7.5, color='#555')
        max_y = max(max_y, y0_global + tick_h * 4.5 + 50)

    ax.set_xticks(range(len(species_order)))
    ax.set_xticklabels(species_order, fontsize=9)
    ax.set_ylabel('Asp+Glu surface SASA (Å²)', fontsize=9)
    ax.set_title('Carboxylate Surface Accessibility\n'
                 '(glycanAware APBS, water probe, per structure)',
                 fontsize=9, pad=8)
    ax.set_ylim(1000, max(max_y + 10, 3700))

    legend_els = [
        mpatches.Patch(facecolor='#888', alpha=0.80, label='Glycosylated'),
        mpatches.Patch(facecolor='#888', alpha=0.40, hatch='///',
                       edgecolor='gray', label='Deglyco (no glycan)'),
    ]
    ax.legend(handles=legend_els, fontsize=7.5, framealpha=0.6)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


# ─── Panel D: APBS 中位值 strip ───────────────────────────────────────────
def draw_apbs_strip(ax, summary, csv_map):
    """Panel D: 小提琴图展示表面 APBS 所有残基电位分布，
    糖基化并列，叠加 apo 单点 + 统计括号。
    """
    species_order = ['Gallus', 'Anas', 'Columba']
    x_map = {sp: i for i, sp in enumerate(species_order)}

    # 收集小提琴数据（每结构所有表面残基 APBS 值）
    datasets_glyc = {sp: [] for sp in species_order}
    datasets_apo  = {sp: [] for sp in species_order}
    for name in GLYC_ORDER:
        if name not in csv_map:
            continue
        df   = csv_map[name]
        surf = df[(df['SurfaceLabel'] == 'Surface') & (df['Type'] == 'Protein')]
        datasets_glyc[species_of(name)].extend(surf['APBS_kT_e'].dropna().tolist())
    for name in APO_ORDER:
        if name not in csv_map:
            continue
        df   = csv_map[name]
        surf = df[(df['SurfaceLabel'] == 'Surface') & (df['Type'] == 'Protein')]
        datasets_apo[species_of(name)].extend(surf['APBS_kT_e'].dropna().tolist())

    all_vals = []
    for sp in species_order:
        xi  = x_map[sp]
        col = SPECIES_COLOR[sp]
        gd  = np.array(datasets_glyc[sp])
        ad  = np.array(datasets_apo[sp])
        gd  = gd[(gd >= -35) & (gd <= 80)]
        ad  = ad[(ad >= -35) & (ad <= 80)] if len(ad) else ad
        all_vals.extend(gd.tolist())
        if len(ad): all_vals.extend(ad.tolist())

        # 小提琴：糖基化（实心）
        if len(gd) > 1:
            vp = ax.violinplot([gd], positions=[xi - 0.15],
                               showmedians=True, showextrema=False, widths=0.55)
            for body in vp['bodies']:
                body.set_facecolor(col)
                body.set_alpha(0.60)
                body.set_edgecolor('none')
            vp['cmedians'].set_color('white')
            vp['cmedians'].set_linewidth(1.5)

        # 小提琴：apo（半透明虚线轮廓）
        if len(ad) > 1:
            vp2 = ax.violinplot([ad], positions=[xi + 0.15],
                                showmedians=True, showextrema=False, widths=0.55)
            for body in vp2['bodies']:
                body.set_facecolor(col)
                body.set_alpha(0.28)
                body.set_edgecolor(col)
                body.set_linewidth(1)
            vp2['cmedians'].set_color(col)
            vp2['cmedians'].set_linewidth(1.5)
            vp2['cmedians'].set_alpha(0.7)
        elif len(ad) == 1:
            ax.scatter([xi + 0.15], ad, s=60, color=col, marker='D',
                       edgecolors=col, linewidths=1, alpha=0.65, zorder=5)

    ax.axhline(0, color='#666', lw=0.8, ls=':', alpha=0.5)
    ax.axhline(-5, color='#e53935', lw=0.9, ls='--', alpha=0.6)

    # 统计标注（one-sample t-test: glyco 分布 vs apo 单值）
    if summary is not None:
        glyc_d = summary[~summary['IsApo']]
        apo_d  = summary[ summary['IsApo']]
        stat_queue_d = []
        for sp in species_order:
            xi    = x_map[sp]
            g_med = glyc_d[glyc_d['Species'] == sp]['APBS_median'].values
            a_med = apo_d [apo_d ['Species'] == sp]['APBS_median'].values
            if len(g_med) >= 2 and len(a_med) == 1:
                _, p  = stats.ttest_1samp(g_med, a_med[0])
                lbl   = _pstar(p)
                delta = g_med.mean() - a_med[0]
                sign  = '+' if delta >= 0 else '-'
                stat_queue_d.append((xi, lbl, delta, sign))
        if stat_queue_d and all_vals:
            rng_span = max(all_vals) - min(all_vals)
            tick_h   = rng_span * 0.04
            y0_base  = max(all_vals) + rng_span * 0.06
            for xi, lbl, delta, sign in stat_queue_d:
                _stat_bracket(ax, xi - 0.15, xi + 0.15, y0_base, tick_h, lbl)
                ax.text(xi, y0_base + tick_h * 2.8, f'\u0394{sign}{abs(delta):.2f}',
                        ha='center', va='bottom', fontsize=7.5, color='#555')

    ax.set_xticks(range(len(species_order)))
    ax.set_xticklabels(species_order, fontsize=9)
    ax.set_ylabel('Surface APBS potential (kT/e)', fontsize=9)
    ax.set_title('Surface Potential Distribution\n(Glycosylated vs Deglyco)',
                 fontsize=9, pad=8)
    if all_vals:
        ax.set_ylim(min(all_vals) - 1, max(all_vals) * 1.3 + 1)

    legend_els = [
        mpatches.Patch(facecolor='#888', alpha=0.60, label='Glycosylated'),
        mpatches.Patch(facecolor='#888', alpha=0.28,
                       edgecolor='#888', linewidth=1, label='Deglyco (no glycan)'),
        Line2D([0], [0], color='#e53935', lw=1.2, ls='--', alpha=0.8,
               label='-5 kT/e'),
    ]
    ax.legend(handles=legend_els, fontsize=7.5, framealpha=0.6, loc='upper right')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


# ══════════════════════════════════════════════════════════
# 主函数
# ══════════════════════════════════════════════════════════
def save_panel(fig, name):
    """Save as PNG/PDF/SVG."""
    save_fig(fig, name, dpi=DPI)


def main():
    print("载入数据...")
    csv_map, summary = load_data()

    present_glyc = [n for n in GLYC_ORDER if n in csv_map]
    present_apo  = [n for n in APO_ORDER  if n in csv_map]
    print(f"  糖基化蛋白: {present_glyc}")
    print(f"  去糖基化:   {present_apo}")
    if summary is None:
        print("  ⚠  未找到 summary_ensemble.csv，Panel B/C/D 受限")

    n_rows_strip = len(present_glyc) + len(present_apo)
    ROW_H  = 0.44

    # ── Panel A: Strip chart (full-width heatmap) ─────────────────────────
    fig_h_strip = ROW_H * n_rows_strip + 1.0
    fig_a = plt.figure(figsize=(18, fig_h_strip))
    fig_a.patch.set_facecolor('white')
    ax_strip = fig_a.add_axes([0.08, 0.35 / fig_h_strip,
                                0.86, (ROW_H * n_rows_strip + 0.45) / fig_h_strip])
    draw_strip(ax_strip, csv_map)
    fig_a.text(0.01, 1.0 - 0.05 / fig_h_strip, 'A',
               fontsize=16, fontweight='bold', va='top')
    save_panel(fig_a, 'Fig5A')
    plt.close(fig_a)

    # ── Panel B: Ca2+ hotspot residues ────────────────────────────────────
    fig_b, ax_b = plt.subplots(figsize=(6, 5.5))
    fig_b.patch.set_facecolor('white')
    draw_hotspot(ax_b, summary)
    fig_b.text(0.01, 0.98, 'B', transform=fig_b.transFigure,
               fontsize=16, fontweight='bold', va='top')
    fig_b.tight_layout()
    save_panel(fig_b, 'Fig5B')
    plt.close(fig_b)

    # ── Panel C: Ca2+ SASA ────────────────────────────────────────────────
    fig_c, ax_c = plt.subplots(figsize=(6, 5.5))
    fig_c.patch.set_facecolor('white')
    draw_ca2_sasa(ax_c, csv_map)
    fig_c.text(0.01, 0.98, 'C', transform=fig_c.transFigure,
               fontsize=16, fontweight='bold', va='top')
    fig_c.tight_layout()
    save_panel(fig_c, 'Fig5C')
    plt.close(fig_c)

    # ── Panel D: APBS strip ───────────────────────────────────────────────
    fig_d, ax_d = plt.subplots(figsize=(6, 5.5))
    fig_d.patch.set_facecolor('white')
    draw_apbs_strip(ax_d, summary, csv_map)
    fig_d.text(0.01, 0.98, 'D', transform=fig_d.transFigure,
               fontsize=16, fontweight='bold', va='top')
    fig_d.tight_layout()
    save_panel(fig_d, 'Fig5D')
    plt.close(fig_d)


if __name__ == '__main__':
    main()
