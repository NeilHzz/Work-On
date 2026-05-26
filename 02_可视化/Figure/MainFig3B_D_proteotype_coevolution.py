import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from adjustText import adjust_text
import os
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _save import save_fig
import matplotlib as mpl

# ==========================================
# 设置全局绘图风格 (参考 Science Advances 等高水平期刊)
# ==========================================
mpl.rcParams['font.family'] = 'Times New Roman'
mpl.rcParams['font.sans-serif'] = ['Times New Roman', 'DejaVu Sans']
mpl.rcParams['mathtext.fontset'] = 'stix'
mpl.rcParams['axes.spines.top'] = False    # 隐藏顶部边框
mpl.rcParams['axes.spines.right'] = False  # 隐藏右侧边框
mpl.rcParams['axes.linewidth'] = 1.5       # 加粗坐标轴
mpl.rcParams['xtick.major.width'] = 1.5    # 加粗刻度线
mpl.rcParams['ytick.major.width'] = 1.5
mpl.rcParams['xtick.labelsize'] = 22
mpl.rcParams['ytick.labelsize'] = 22

data_dir = r"D:\system_folder\Desktop\Work On\01_数据与计算\Raw_Data\MS_DATA"
out_dir = r"D:\system_folder\Desktop\Work On\02_可视化\Figure\png"
_SP_PANEL = {"Gallus": "Fig4A", "Anas": "Fig4B", "Columba": "Fig4C"}

# ==========================================
# 目标蛋白映射表 (基于 Blastp 严格筛选结果)
# ==========================================
target_mapping = {
    'Gallus': {
        'OVAL': ['P01012'],
        'OC116': ['A0A8V0XA58'], 
        'TRFE': ['A0A8V1A6Y9'], 
        'OC17': ['V5NUE7']
    },
    'Anas': {
        'OVAL': ['A0A8B9QNT8'],
        'OC116': ['A0A8B9ZY54'], 
        'TRFE': ['A0A493TBB4'], 
        'OC17': [] # Anas 中未通过严格筛选
    },
    'Columba': {
        'OVAL': ['A0A2I0MWA2'],
        'OC116': ['A0A2I0MGY6'], 
        'TRFE': ['A0A2I0LUS7'], 
        'OC17': [] # Columba 中未通过严格筛选
    }
}

SPECIES_COLORS = {'Gallus': '#B54664', 'Anas': '#7895C1', 'Columba': '#F0C284'}
MUTED_SPECIES_COLORS = {'Gallus': '#E3B7C1', 'Anas': '#CDD8EA', 'Columba': '#F0DDAE'}
BACKGROUND_PROTEIN_COLOR = '#C7C7C7'
OVAL_COLOR = '#C62828'
OC116_COLOR = '#66A96B'
TRFE_COLOR = '#5A5A5A'
LABEL_GRAY = '#4A4A4A'


def target_color(species, target_name):
    if target_name == 'OVAL':
        return OVAL_COLOR
    if target_name == 'OC116':
        return OC116_COLOR
    if target_name == 'TRFE':
        return TRFE_COLOR
    return MUTED_SPECIES_COLORS[species]

species_list = ["Gallus", "Anas", "Columba"]

# 标签左侧放置配置 (避免遮挡右侧数据点)
LEFT_PROTS = {
    'Anas':    {'OVAL', 'TRFE'},
    'Columba': {'OVAL', 'TRFE'},
}
# 单点蛋白间 y 坐标接近时的 dy override (单位: offset points)
DY_OVERRIDE = {
    ('Anas', 'TRFE'):  14,
    ('Anas', 'OVAL'): -14,
}
# 逐点 dy 微调: (species, protein, position) -> dy 叠加值
POINT_DY_ADJUST = {
    ('Columba', 'OC116', '185'): 14,
}

for species in species_list:
    print(f"正在处理 {species} ...")
    prot_file = os.path.join(data_dir, f"Protein_MS_{species}.xlsx")
    glyc_file = os.path.join(data_dir, f"Glycan_MS_{species}.xlsx")
    
    try:
        df_prot = pd.read_excel(prot_file, sheet_name="Protein_quant")
        df_glyc = pd.read_excel(glyc_file, sheet_name="Site_quant")
    except Exception as e:
        print(f"读取 {species} 数据失败: {e}")
        continue
        
    # ==========================================
    # 严格数据质控: Number Comparable >= 2
    # ==========================================
    if 'Number Comparable' in df_prot.columns:
        df_prot = df_prot[df_prot['Number Comparable'] >= 2]
    if 'Number Comparable' in df_glyc.columns:
        df_glyc = df_glyc[df_glyc['Number Comparable'] >= 1]
        
    prot_int_cols = [col for col in df_prot.columns if 'Intensity' in col]
    glyc_int_cols = [col for col in df_glyc.columns if 'Intensity' in col]
    
    df_prot['Protein_Mean_Intensity'] = df_prot[prot_int_cols].mean(axis=1)
    df_glyc['Glycan_Mean_Intensity'] = df_glyc[glyc_int_cols].mean(axis=1)
    
    df_prot = df_prot[df_prot['Protein_Mean_Intensity'] > 0]
    df_glyc = df_glyc[df_glyc['Glycan_Mean_Intensity'] > 0]
    
    df_merged = pd.merge(
        df_glyc[['Protein accession', 'Position', 'N-glycan types', 'Glycan_Mean_Intensity']],
        df_prot[['Protein accession', 'Protein_Mean_Intensity', 'Gene name']],
        on='Protein accession',
        how='inner'
    )
    
    if df_merged.empty:
        continue
        
    df_merged['Log2_Protein_Intensity'] = np.log2(df_merged['Protein_Mean_Intensity'])
    df_merged['Log2_Glycan_Intensity'] = np.log2(df_merged['Glycan_Mean_Intensity'])
    
    correlation, p_value = spearmanr(df_merged['Log2_Protein_Intensity'], df_merged['Log2_Glycan_Intensity'])
    
    # 标记目标蛋白
    df_merged['Target'] = 'Other'
    for target_name, accessions in target_mapping[species].items():
        df_merged.loc[df_merged['Protein accession'].isin(accessions), 'Target'] = target_name
        
    # ==========================================
    # 开始绘图
    # ==========================================
    plt.figure(figsize=(8.5, 7.5))
    
    # 1. 绘制背景点 (灰色，半透明)
    mask_other = df_merged['Target'] == 'Other'
    plt.scatter(
        df_merged.loc[mask_other, 'Log2_Protein_Intensity'],
        df_merged.loc[mask_other, 'Log2_Glycan_Intensity'],
        color=BACKGROUND_PROTEIN_COLOR, alpha=0.65, s=80, edgecolor='white', linewidth=0.5, label='Other Proteins', zorder=2
    )
    
    # 2. 绘制目标蛋白点 (高亮颜色，大尺寸)
    for target_name in ['OVAL', 'OC116', 'TRFE', 'OC17']:
        mask_target = df_merged['Target'] == target_name
        if mask_target.sum() > 0:
            highlight_color = target_color(species, target_name)
            if target_name == 'OVAL':
                ax = plt.gca()
                for _, oval_row in df_merged[mask_target].iterrows():
                    ax.text(
                        oval_row['Log2_Protein_Intensity'],
                        oval_row['Log2_Glycan_Intensity'],
                        '⭐', color=highlight_color, ha='center', va='center',
                        fontsize=24, zorder=7, fontfamily='Segoe UI Emoji'
                    )
            else:
                plt.scatter(
                    df_merged.loc[mask_target, 'Log2_Protein_Intensity'],
                    df_merged.loc[mask_target, 'Log2_Glycan_Intensity'],
                    color=highlight_color, alpha=0.85, s=180,
                    marker='o', edgecolor='none', linewidth=0,
                    label=target_name, zorder=5
                )
            
            rows = df_merged[mask_target].sort_values('Log2_Glycan_Intensity').reset_index(drop=True)
            n = len(rows)
            go_left = target_name in LEFT_PROTS.get(species, set())
            dx = -12 if go_left else 12
            ha = 'right' if go_left else 'left'
            for idx, row in rows.iterrows():
                # 多点时按 y 排序均匀分布: 最低点往下, 最高点往上
                if n > 1:
                    dy = (idx - (n - 1) / 2) * 22
                elif (species, target_name) in DY_OVERRIDE:
                    dy = DY_OVERRIDE[(species, target_name)]
                else:
                    dy = 0
                # 逐点微调
                dy += POINT_DY_ADJUST.get((species, target_name, str(row['Position'])), 0)
                plt.annotate(
                    f"{target_name}\n({row['Position']}N)",
                    xy=(row['Log2_Protein_Intensity'], row['Log2_Glycan_Intensity']),
                    xytext=(dx, dy), textcoords='offset points',
                    fontsize=18, fontweight='bold', color=OVAL_COLOR if target_name == 'OVAL' else LABEL_GRAY,
                    va='center', ha=ha,
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=highlight_color if target_name == 'OVAL' else LABEL_GRAY,
                              linewidth=0.8, alpha=0.90),
                    zorder=6
                )
                
    # 3. 添加 y=x 参考线
    min_val = min(df_merged['Log2_Protein_Intensity'].min(), df_merged['Log2_Glycan_Intensity'].min()) - 1
    max_val = max(df_merged['Log2_Protein_Intensity'].max(), df_merged['Log2_Glycan_Intensity'].max()) + 1
    plt.plot([min_val, max_val], [min_val, max_val], color='#888888', linestyle='--', linewidth=1.5, zorder=1)
    
    # 4. 格式化坐标轴和标题
    plt.xlabel('Log$_2$(Protein Intensity)', fontsize=24, fontweight='bold')
    plt.ylabel('Log$_2$(Glycan Intensity)', fontsize=24, fontweight='bold')
    plt.title(f'{species} Proteotype Coevolution', fontsize=26, fontweight='bold', pad=22)
    
    # 5. 添加统计学信息框
    sig = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*" if p_value < 0.05 else "ns"
    stats_text = f"Spearman $\\rho$ = {correlation:.2f}\n$P$ = {p_value:.2e} ({sig})"
    plt.text(0.05, 0.95, stats_text, transform=plt.gca().transAxes, fontsize=20, fontweight='bold',
             verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='#F8F9FA', alpha=0.9, edgecolor='#CCCCCC'))
             
    plt.tight_layout()
    
    # 保存图片
    save_fig(plt.gcf(), _SP_PANEL[species])
    plt.close()

print("所有高亮图绘制完成！")
