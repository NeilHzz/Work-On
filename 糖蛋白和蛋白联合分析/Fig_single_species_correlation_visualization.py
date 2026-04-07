"""
单物种糖蛋白-蛋白质 Spearman 相关性散点图
===========================================
合并自 single_species_correlation.py + single_species_correlation_auto.py
(以 auto 版本为基础，整合旧版本中的 Fig_ 输出规范)

输出:
  20260225/Figure/Fig_correlation_Gallus.png
  20260225/Figure/Fig_correlation_Anas.png
  20260225/Figure/Fig_correlation_Columba.png
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from matplotlib.colors import LinearSegmentedColormap
import os

# ─── 路径配置 ─────────────────────────────────────────────────────────────
DATA_DIR = r"e:\Data\Desktop\Work On\Raw_Data\MS_DATA"
OUT_DIR  = r"e:\Data\Desktop\Work On\20260225\Figure"
os.makedirs(OUT_DIR, exist_ok=True)

GLYCAN_FNAME = {
    'Gallus': 'Glycan_MS_Gallus_New.xlsx',
    'Anas':   'Glycan_MS_Anas.xlsx',
    'Columba':'Glycan_MS_Columba.xlsx',
}
PROTEIN_FNAME = {
    'Gallus': 'Protein_MS_Gallus_New.xlsx',
    'Anas':   'Protein_MS_Anas.xlsx',
    'Columba':'Protein_MS_Columba.xlsx',
}
GLYCAN_SHEET_SITE = {
    'Gallus': 'Site_quant Normalized',
    'Anas':   'Site_quant',
    'Columba':'Site_quant',
}
GLYCAN_SHEET_HEADER = {
    'Gallus': 1,
    'Anas':   0,
    'Columba':0,
}

# ─── 全局绘图风格 (Nature Publishing Group) ───────────────────────────────
import matplotlib as mpl
mpl.rcParams['font.family']           = 'sans-serif'
mpl.rcParams['font.sans-serif']       = ['Arial', 'Helvetica', 'DejaVu Sans']
mpl.rcParams['axes.spines.top']       = False
mpl.rcParams['axes.spines.right']     = False
mpl.rcParams['axes.linewidth']        = 1.5
mpl.rcParams['xtick.major.width']     = 1.5
mpl.rcParams['ytick.major.width']     = 1.5
mpl.rcParams['xtick.labelsize']       = 12
mpl.rcParams['ytick.labelsize']       = 12


def analyze_single_species(species_name: str, data_dir: str):
    """
    读取指定物种的蛋白质与糖基化位点质谱数据，
    计算 Log2 强度并绘制 Spearman 相关散点图。

    Parameters
    ----------
    species_name : str
        物种名称，例如 'Gallus', 'Anas', 'Columba'
    data_dir : str
        数据目录路径，包含 Protein_MS_<species>.xlsx 和 Glycan_MS_<species>.xlsx

    Returns
    -------
    df_merged : pd.DataFrame | None
    """
    print(f"\n{'='*40}")
    print(f"开始分析物种: {species_name}")
    print(f"{'='*40}")

    prot_file = os.path.join(data_dir, PROTEIN_FNAME.get(species_name, f'Protein_MS_{species_name}.xlsx'))
    glyc_file = os.path.join(data_dir, GLYCAN_FNAME.get(species_name, f'Glycan_MS_{species_name}.xlsx'))

    try:
        df_prot = pd.read_excel(prot_file, sheet_name="Protein_quant")
        # Site_quant sheet 含有明确位点定量，优先使用；回退到默认 sheet
        site_sheet = GLYCAN_SHEET_SITE.get(species_name, 'Site_quant')
        site_header = GLYCAN_SHEET_HEADER.get(species_name, 0)
        try:
            df_glyc = pd.read_excel(glyc_file, sheet_name=site_sheet, header=site_header)
        except Exception:
            df_glyc = pd.read_excel(glyc_file)
    except Exception as e:
        print(f"读取 {species_name} 数据失败: {e}")
        return None

    # ── 提取强度列 & 计算均值 ────────────────────────────────────────────
    prot_int_cols = [c for c in df_prot.columns if 'Intensity' in c]
    glyc_int_cols = [c for c in df_glyc.columns if 'Intensity' in c]

    df_prot['Protein_Mean_Intensity'] = df_prot[prot_int_cols].mean(axis=1)
    df_glyc['Glycan_Mean_Intensity']  = df_glyc[glyc_int_cols].mean(axis=1)

    df_prot = df_prot[df_prot['Protein_Mean_Intensity'] > 0]
    df_glyc = df_glyc[df_glyc['Glycan_Mean_Intensity']  > 0]

    # ── 合并 (Protein accession) ─────────────────────────────────────────
    df_merged = pd.merge(
        df_glyc[['Protein accession', 'Position', 'N-glycan types',
                  'Glycan_Mean_Intensity']],
        df_prot[['Protein accession', 'Protein_Mean_Intensity', 'Gene name']],
        on='Protein accession',
        how='inner'
    )

    if df_merged.empty:
        print(f"警告: {species_name} 蛋白质与糖肽数据无交集！")
        return None

    # ── Log2 转换 & Spearman 相关 ────────────────────────────────────────
    df_merged['Log2_Protein_Intensity'] = np.log2(df_merged['Protein_Mean_Intensity'])
    df_merged['Log2_Glycan_Intensity']  = np.log2(df_merged['Glycan_Mean_Intensity'])

    correlation, p_value = spearmanr(
        df_merged['Log2_Protein_Intensity'],
        df_merged['Log2_Glycan_Intensity']
    )
    sig = ("***" if p_value < 0.001 else
           "**"  if p_value < 0.01  else
           "*"   if p_value < 0.05  else "ns")
    print(f"匹配位点数: {len(df_merged)}")
    print(f"Spearman rho: {correlation:.4f}  p={p_value:.4e} ({sig})")

    # ── 散点图 ───────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(14, 10))

    sizes  = (df_merged['Protein_Mean_Intensity'] /
              df_merged['Protein_Mean_Intensity'].max()) * 500 + 100
    colors = df_merged['N-glycan types'].clip(upper=21)

    # 白 → 红 → 黑 色图
    custom_cols = (['white'] +
                   [plt.cm.Reds(i / 20) for i in range(1, 21)] +
                   ['black'])
    custom_cmap = LinearSegmentedColormap.from_list(
        'white_red_black', custom_cols, N=22)

    sc = ax.scatter(
        df_merged['Log2_Protein_Intensity'],
        df_merged['Log2_Glycan_Intensity'],
        s=sizes, c=colors, cmap=custom_cmap,
        vmin=0, vmax=21,
        alpha=0.7, edgecolors='black', linewidth=1.5
    )

    # y=x 参考线
    lo = min(df_merged['Log2_Protein_Intensity'].min(),
             df_merged['Log2_Glycan_Intensity'].min())
    hi = max(df_merged['Log2_Protein_Intensity'].max(),
             df_merged['Log2_Glycan_Intensity'].max())
    ax.plot([lo, hi], [lo, hi], 'k--', alpha=0.5, label='y=x (Perfect Correlation)')

    # 标注丰度最高5个点
    top5 = df_merged.nlargest(5, 'Log2_Glycan_Intensity')
    for _, row in top5.iterrows():
        lbl = (f"{row['Gene name']}\n{row['Position']}N"
               if pd.notna(row['Gene name'])
               else f"{row['Protein accession']}\n{row['Position']}N")
        ax.annotate(lbl,
                    (row['Log2_Protein_Intensity'], row['Log2_Glycan_Intensity']),
                    xytext=(5, 5), textcoords='offset points', fontsize=9,
                    bbox=dict(boxstyle='round,pad=0.3', fc='white',
                              ec='gray', alpha=0.8))

    plt.colorbar(sc, ax=ax, label='N-glycan types')
    ax.set_xlabel('Log2(Protein Intensity)',  fontsize=14)
    ax.set_ylabel('Log2(Glycan Intensity)',   fontsize=14)
    ax.set_title(f'{species_name}  Spearman rho = {correlation:.4f},'
                 f' p = {p_value:.2e} ({sig})', fontsize=16)
    ax.grid(True, alpha=0.3)
    ax.legend()

    out = os.path.join(OUT_DIR, f'Fig_correlation_{species_name}.png')
    fig.savefig(out, dpi=300, bbox_inches='tight')
    print(f"散点图已保存: {out}")
    plt.close(fig)

    df_merged.to_excel(
        os.path.join(OUT_DIR, f'Merged_Data_{species_name}.xlsx'), index=False)
    return df_merged


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    for sp in ['Gallus', 'Anas', 'Columba']:
        analyze_single_species(sp, DATA_DIR)
