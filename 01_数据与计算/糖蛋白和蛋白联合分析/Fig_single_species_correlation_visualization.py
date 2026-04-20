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
DATA_DIR = r"D:\system_folder\Desktop\Work On\01_数据与计算\Raw_Data\MS_DATA"
OUT_DIR  = r"D:\system_folder\Desktop\Work On\01_数据与计算\糖蛋白和蛋白联合分析\Figure"
os.makedirs(OUT_DIR, exist_ok=True)

# ─── 全局绘图风格 (Nature Publishing Group) ───────────────────────────────
import matplotlib as mpl
mpl.rcParams['font.family'] = 'Times New Roman'
mpl.rcParams['font.sans-serif']       = ['Times New Roman', 'DejaVu Sans']
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

    prot_file = os.path.join(data_dir, f"Protein_MS_{species_name}.xlsx")
    glyc_file = os.path.join(data_dir, f"Glycan_MS_{species_name}.xlsx")

    try:
        df_prot = pd.read_excel(prot_file, sheet_name="Protein_quant")
        # Site_quant sheet 含有明确位点定量，优先使用；回退到默认 sheet
        try:
            df_glyc = pd.read_excel(glyc_file, sheet_name="Site_quant")
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
    df_merged['log2_prot'] = np.log2(df_merged['Protein_Mean_Intensity'])
    df_merged['log2_glyc'] = np.log2(df_merged['Glycan_Mean_Intensity'])
    rho, pval = spearmanr(df_merged['log2_prot'], df_merged['log2_glyc'])
    n = len(df_merged)

    if pval < 0.001:
        sig_str = "***"
    elif pval < 0.01:
        sig_str = "**"
    elif pval < 0.05:
        sig_str = "*"
    else:
        sig_str = "ns"

    print(f"匹配位点数: {n}")
    print(f"Spearman rho: {rho:.4f}  p={pval:.4e} ({sig_str})")

    # ── 绘图 ─────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(4.2, 4.0))
    ax.scatter(df_merged['log2_prot'], df_merged['log2_glyc'],
               s=18, alpha=0.55, color='#3175A6', linewidths=0)
    # 回归线
    z = np.polyfit(df_merged['log2_prot'], df_merged['log2_glyc'], 1)
    p = np.poly1d(z)
    xline = np.linspace(df_merged['log2_prot'].min(), df_merged['log2_prot'].max(), 200)
    ax.plot(xline, p(xline), color='#D62728', linewidth=1.5, linestyle='--')

    ax.set_xlabel("Protein abundance (log$_2$)", fontsize=12)
    ax.set_ylabel("Glycopeptide abundance (log$_2$)", fontsize=12)
    ax.set_title(f"{species_name}", fontsize=13, fontweight='bold')
    ax.text(0.97, 0.05,
            f"ρ = {rho:.3f}\n{sig_str}\nn = {n}",
            transform=ax.transAxes, ha='right', va='bottom',
            fontsize=11, color='#333333')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()

    out_path = os.path.join(OUT_DIR, f"Fig_correlation_{species_name}.png")
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"已保存: {out_path}")
    return df_merged


# ── 主程序 ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    for sp in ["Gallus", "Anas", "Columba"]:
        analyze_single_species(sp, DATA_DIR)
    print("\n全部图表已生成完毕。")
