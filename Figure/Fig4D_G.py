"""
糖型分析可视化（合并自 extract_all_glycans.py + extract_oval_glycans.py）
==========================================================================
输出:
  20260225/Figure/Fig_glycan_profiling_OVAL.png      — OVAL 三物种堆叠柱图
  20260225/Figure/Fig_glycan_profiling_OC116.png
  20260225/Figure/Fig_glycan_profiling_TRFE.png
  20260225/Figure/Fig_glycan_profiling_OC17.png
  20260225/Figure/Fig_glycan_profiling_OVAL_vs_Columba.png  — Gallus vs Columba 直接对比
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _save import save_fig
import re

# ─── 绘图风格 ──────────────────────────────────────────────────────────────
mpl.rcParams['font.family'] = 'Times New Roman'
mpl.rcParams['font.sans-serif']       = ['Times New Roman', 'DejaVu Sans']
mpl.rcParams['axes.spines.top']       = False
mpl.rcParams['axes.spines.right']     = False
mpl.rcParams['axes.linewidth']        = 1.5
mpl.rcParams['xtick.major.width']     = 1.5
mpl.rcParams['ytick.major.width']     = 1.5
mpl.rcParams['xtick.labelsize']       = 12
mpl.rcParams['ytick.labelsize']       = 12

# ─── 路径配置 ─────────────────────────────────────────────────────────────
DATA_DIR = r"D:\system_folder\Desktop\Work On\Raw_Data\MS_DATA"
OUT_DIR  = r"D:\system_folder\Desktop\Work On\Figure\png"
os.makedirs(OUT_DIR, exist_ok=True)
NOLEG = True
_PROT_PANEL = {"OVAL": "Fig4D", "OC116": "Fig4E", "TRFE": "Fig4F", "OC17": "Fig4G"}

# ─── 目标蛋白映射表（Blastp 严格筛选结果） ───────────────────────────────
TARGET_MAPPING = {
    'Gallus': {
        'OVAL':  ['P01012'],
        'OC116': ['A0A8V0XA58'],
        'TRFE':  ['A0A8V1A6Y9'],
        'OC17':  ['V5NUE7']
    },
    'Anas': {
        'OVAL':  ['A0A8B9QNT8'],
        'OC116': ['A0A8B9ZY54'],
        'TRFE':  ['A0A493TBB4'],
        'OC17':  []
    },
    'Columba': {
        'OVAL':  ['A0A2I0MWA2'],
        'OC116': ['A0A2I0MGY6'],
        'TRFE':  ['A0A2I0LUS7'],
        'OC17':  []
    }
}

# ─── 配色（NPG） ──────────────────────────────────────────────────────────
COLOR_MAP = {
    'High-Mannose':               '#4DBBD5',
    'Neutral (Complex/Hybrid)':   '#00A087',
    'Fucosylated (Complex/Hybrid)': '#F39B7F',
    'Sialylated (Complex/Hybrid)':  '#E64B35',
    'Paucimannose/Truncated':    '#8491B4',
    'Other':                      '#CCCCCC',
}
ORDERED_CLASSES = [
    'High-Mannose', 'Paucimannose/Truncated',
    'Neutral (Complex/Hybrid)', 'Fucosylated (Complex/Hybrid)',
    'Sialylated (Complex/Hybrid)', 'Other',
]


# ══════════════════════════════════════════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════════════════════════════════════════
def parse_glycan_composition(mod_str: str) -> dict:
    """解析 Oxford 格式糖链组成字符串 → {sugar: count}"""
    if pd.isna(mod_str):
        return {}
    return {sugar: int(n)
            for sugar, n in re.findall(r'([A-Za-z]+)\((\d+)\)', str(mod_str))}


def classify_glycan(comp: dict) -> str:
    """按单糖组成对糖链进行五类分类"""
    if not comp:
        return 'Other'
    hexnac = comp.get('HexNAc', 0)
    hex_   = comp.get('Hex',    0)
    fuc    = comp.get('Fuc',    0)
    neuac  = comp.get('NeuAc',  0) + comp.get('NeuGc', 0)

    if hexnac == 2 and hex_ >= 5 and fuc == 0 and neuac == 0:
        return 'High-Mannose'
    elif neuac > 0:
        return 'Sialylated (Complex/Hybrid)'
    elif fuc > 0 and neuac == 0:
        return 'Fucosylated (Complex/Hybrid)'
    elif hexnac >= 3 and fuc == 0 and neuac == 0:
        return 'Neutral (Complex/Hybrid)'
    elif hexnac == 2 and hex_ < 5 and fuc == 0 and neuac == 0:
        return 'Paucimannose/Truncated'
    return 'Other'


def get_protein_abundance(protein: str, species: str) -> 'pd.Series | None':
    """返回某蛋白在某物种中各糖类的相对丰度 (%)"""
    accessions = TARGET_MAPPING[species].get(protein, [])
    if not accessions:
        return None
    fpath = os.path.join(DATA_DIR, f"Glycan_MS_{species}.xlsx")
    try:
        df = pd.read_excel(fpath, sheet_name="IGP_quant")
    except Exception:
        return None

    df_t = df[df['Protein accession'].isin(accessions)].copy()
    if df_t.empty:
        return None

    int_cols = [c for c in df.columns if 'Intensity' in c]
    df_t['Mean_Intensity'] = df_t[int_cols].mean(axis=1)
    df_t = df_t[df_t['Mean_Intensity'] > 0]
    if df_t.empty:
        return None

    mod_col = 'Observed Modification'
    if mod_col not in df_t.columns:
        return None

    df_t['Composition'] = df_t[mod_col].apply(parse_glycan_composition)
    df_t['Glycan_Class'] = df_t['Composition'].apply(classify_glycan)

    cls_int   = df_t.groupby('Glycan_Class')['Mean_Intensity'].sum()
    total     = cls_int.sum()
    return (cls_int / total) * 100 if total > 0 else None


# ══════════════════════════════════════════════════════════════════════════════
# Fig A — 多物种堆叠柱状图（每个目标蛋白 × 3 物种）
# ══════════════════════════════════════════════════════════════════════════════
def plot_protein_glycan_profiling(protein: str, species_list: list):
    protein_data = {}
    for sp in species_list:
        data = get_protein_abundance(protein, sp)
        if data is not None:
            protein_data[sp] = data

    if not protein_data:
        print(f"  未找到 {protein} 数据，跳过")
        return

    df_plot = pd.DataFrame(protein_data).fillna(0)
    plot_classes = [c for c in ORDERED_CLASSES if c in df_plot.index]
    df_plot = df_plot.loc[plot_classes]

    print(f"\n--- {protein} 糖型相对丰度 (%) ---")
    print(df_plot.round(2))

    fig, ax = plt.subplots(figsize=(8, 6))
    bottom = np.zeros(len(df_plot.columns))
    for cls in df_plot.index:
        vals = df_plot.loc[cls].values
        ax.bar(df_plot.columns, vals, bottom=bottom, label=cls,
               color=COLOR_MAP.get(cls, '#333333'), edgecolor='white', width=0.5)
        bottom += vals

    ax.set_ylabel('Relative Abundance (%)', fontsize=14, fontweight='bold')
    ax.set_title(f'{protein} Glycosylation Profiling',
                 fontsize=16, fontweight='bold', pad=20)
    if not NOLEG:
        ax.legend(title='Glycan Classification', bbox_to_anchor=(1.05, 1),
                  loc='upper left', frameon=False, fontsize=11, title_fontsize=12)
    plt.tight_layout()
    save_fig(plt.gcf(), _PROT_PANEL[protein], dpi=300)
    plt.close()
    print(f"  已保存: {_PROT_PANEL[protein]}")


# ══════════════════════════════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    proteins     = ['OVAL', 'OC116', 'TRFE', 'OC17']
    species_list = ['Gallus', 'Anas', 'Columba']
    SP_LABEL     = {'Gallus': 'G', 'Anas': 'A', 'Columba': 'C'}

    # ── 收集所有数据 ──────────────────────────────────────────────────
    all_data = {}   # key = (protein, species), value = Series
    for protein in proteins:
        for sp in species_list:
            data = get_protein_abundance(protein, sp)
            if data is not None:
                all_data[(protein, sp)] = data

    # ── 构建 DataFrame：列 = 每根柱子 ────────────────────────────────
    col_order = []       # (protein, species) tuples in display order
    for prot in proteins:
        for sp in species_list:
            if (prot, sp) in all_data:
                col_order.append((prot, sp))

    df_all = pd.DataFrame({k: all_data[k] for k in col_order}).fillna(0)
    plot_classes = [c for c in ORDERED_CLASSES if c in df_all.index]
    df_all = df_all.loc[plot_classes]

    print("=== 合并糖型相对丰度 (%) ===")
    print(df_all.round(2))

    # ── 计算 x 位置（蛋白组之间留间距）────────────────────────────────
    bar_w   = 0.55
    gap     = 0.35        # 组间额外间距
    x_pos   = []
    x       = 0.0
    prev_prot = None
    for (prot, sp) in col_order:
        if prev_prot is not None and prot != prev_prot:
            x += gap
        x_pos.append(x)
        x += bar_w + 0.08   # 柱间微距
        prev_prot = prot
    x_pos = np.array(x_pos)

    # ── 绘图 ─────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(12, 6))

    # 蛋白组底色（连续无间隔，更饱和）
    _PROT_BG = {'OVAL': '#CADCF8', 'OC116': '#FFE0B2', 'TRFE': '#C8E6C9', 'OC17': '#F8BBD0'}
    # 计算每组边界，相邻组共享中点
    _grp_bounds = []
    for prot in proteins:
        idxs = [i for i, (p, _) in enumerate(col_order) if p == prot]
        if not idxs:
            continue
        _grp_bounds.append((prot, idxs[0], idxs[-1]))

    for gi, (prot, i0, i1) in enumerate(_grp_bounds):
        # 左边界：与前一组共享中点，或留小边距
        if gi == 0:
            x_left = x_pos[i0] - bar_w/2 - 0.12
        else:
            prev_i1 = _grp_bounds[gi-1][2]
            x_left = (x_pos[prev_i1] + x_pos[i0]) / 2
        # 右边界：与下一组共享中点，或留小边距
        if gi == len(_grp_bounds) - 1:
            x_right = x_pos[i1] + bar_w/2 + 0.12
        else:
            next_i0 = _grp_bounds[gi+1][1]
            x_right = (x_pos[i1] + x_pos[next_i0]) / 2
        ax.axvspan(x_left, x_right, ymin=0, ymax=110/112,
                   color=_PROT_BG.get(prot, '#F5F5F5'),
                   alpha=0.45, zorder=0, lw=0)

    bottom = np.zeros(len(col_order))
    for cls in plot_classes:
        vals = df_all.loc[cls].values
        ax.bar(x_pos, vals, bottom=bottom, width=bar_w,
               color=COLOR_MAP.get(cls, '#333333'), edgecolor='white', label=cls)
        bottom += vals

    # x 轴：G/A/C
    ax.set_xticks(x_pos)
    ax.set_xticklabels([SP_LABEL[sp] for (_, sp) in col_order], fontsize=11)

    # 蛋白名标在柱子上方
    for prot in proteins:
        idxs = [i for i, (p, _) in enumerate(col_order) if p == prot]
        if not idxs:
            continue
        cx = (x_pos[idxs[0]] + x_pos[idxs[-1]]) / 2
        ax.text(cx, 103, prot, ha='center', va='bottom',
                fontsize=13, fontweight='bold', clip_on=False)

    ax.set_ylabel('Relative Abundance (%)', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 112)
    ax.set_title('Glycosylation Profiling', fontsize=16, fontweight='bold', pad=15)

    # 图例
    handles = [mpl.patches.Patch(facecolor=COLOR_MAP[c], edgecolor='white', label=c)
               for c in plot_classes]
    ax.legend(handles=handles, title='Glycan Classification',
              bbox_to_anchor=(1.02, 1), loc='upper left', frameon=False,
              fontsize=10, title_fontsize=11)

    plt.tight_layout()
    save_fig(fig, 'Fig4D_G', dpi=300)
    plt.close()
    print("  已保存: Fig4D_G (合并图)")

    print("\n全部糖型分析完成！")
