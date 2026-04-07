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
DATA_DIR = r"e:\Data\Desktop\Work On\Raw_Data\MS_DATA"
OUT_DIR  = r"e:\Data\Desktop\Work On\糖蛋白和蛋白联合分析\Figure"
os.makedirs(OUT_DIR, exist_ok=True)
NOLEG = os.environ.get('NOLEG', '0') == '1'

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
    _suffix = '_noleg' if NOLEG else ''
    out = os.path.join(OUT_DIR, f'Fig_glycan_profiling_{protein}{_suffix}.png')
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  已保存: {out}")


# ══════════════════════════════════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    proteins     = ['OVAL', 'OC116', 'TRFE', 'OC17']
    species_list = ['Gallus', 'Anas', 'Columba']

    print("=== 各蛋白糖型分析（三物种） ===")
    for protein in proteins:
        print(f"\n{'='*40}")
        print(f"正在处理 {protein} ...")
        plot_protein_glycan_profiling(protein, species_list)

    print("\n全部糖型分析完成！")
