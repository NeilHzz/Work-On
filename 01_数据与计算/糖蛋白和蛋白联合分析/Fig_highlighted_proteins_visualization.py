import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from adjustText import adjust_text
import os
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
mpl.rcParams['xtick.labelsize'] = 12
mpl.rcParams['ytick.labelsize'] = 12

data_dir = r"D:\system_folder\Desktop\Work On\01_数据与计算\Raw_Data\MS_DATA"
out_dir = r"D:\system_folder\Desktop\Work On\01_数据与计算\糖蛋白和蛋白联合分析\Figure"
NOLEG = os.environ.get('NOLEG', '0') == '1'

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

# 使用 NPG (Nature Publishing Group) 经典配色方案
colors = {
    'OVAL': '#E64B35',   # 红色
    'OC116': '#4DBBD5',  # 亮蓝色
    'TRFE': '#00A087',   # 蓝绿色
    'OC17': '#3C5488'    # 深蓝色
}

species_list = ["Gallus", "Anas", "Columba"]

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
        color='#DFDFDF', alpha=0.6, s=80, edgecolor='white', linewidth=0.5, label='Other Proteins', zorder=2
    )
    
    # 2. 绘制目标蛋白点 (高亮颜色，大尺寸)
    texts = []
    for target_name in ['OVAL', 'OC116', 'TRFE', 'OC17']:
        mask_target = df_merged['Target'] == target_name
        if mask_target.sum() > 0:
            plt.scatter(
                df_merged.loc[mask_target, 'Log2_Protein_Intensity'],
                df_merged.loc[mask_target, 'Log2_Glycan_Intensity'],
                color=colors[target_name], alpha=0.9, s=200, edgecolor='black', linewidth=1.5, label=target_name, zorder=5
            )
            
            # 收集文本标签，用 adjust_text 自动避免重叠
            for _, row in df_merged[mask_target].iterrows():
                t = plt.text(
                    row['Log2_Protein_Intensity'],
                    row['Log2_Glycan_Intensity'],
                    f"{target_name}\n({row['Position']}N)",
                    fontsize=10, fontweight='bold', color=colors[target_name],
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=colors[target_name],
                              linewidth=0.8, alpha=0.90),
                    zorder=6
                )
                texts.append(t)

    # 自动调整标签位置，避免重叠
    if texts:
        adjust_text(texts,
                    ax=plt.gca(),
                    expand=(1.5, 2.0),
                    arrowprops=dict(arrowstyle='->', color='#888888', lw=0.8,
                                    shrinkA=4, shrinkB=4))
                
    # 3. 添加 y=x 参考线
    min_val = min(df_merged['Log2_Protein_Intensity'].min(), df_merged['Log2_Glycan_Intensity'].min()) - 1
    max_val = max(df_merged['Log2_Protein_Intensity'].max(), df_merged['Log2_Glycan_Intensity'].max()) + 1
    plt.plot([min_val, max_val], [min_val, max_val], color='#888888', linestyle='--', linewidth=1.5, zorder=1)
    
    # 4. 格式化坐标轴和标题
    plt.xlabel('Log$_2$(Protein Intensity)', fontsize=16, fontweight='bold')
    plt.ylabel('Log$_2$(Glycan Intensity)', fontsize=16, fontweight='bold')
    plt.title(f'{species} Proteotype Coevolution', fontsize=18, fontweight='bold', pad=20)
    
    # 5. 添加统计学信息框
    sig = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*" if p_value < 0.05 else "ns"
    stats_text = f"Spearman $\\rho$ = {correlation:.2f}\n$P$ = {p_value:.2e} ({sig})"
    plt.text(0.05, 0.95, stats_text, transform=plt.gca().transAxes, fontsize=13, fontweight='bold',
             verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='#F8F9FA', alpha=0.9, edgecolor='#CCCCCC'))
             
    # 6. 图例设置
    if not NOLEG:
        plt.legend(loc='lower right', frameon=True, fontsize=12, edgecolor='#CCCCCC', title="Highlighted Proteins", title_fontsize=13)
    plt.tight_layout()
    
    # 保存图片
    _suffix = '_noleg' if NOLEG else ''
    out_path = os.path.join(out_dir, f"Fig_highlighted_correlation_{species}{_suffix}.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"已保存: {out_path}")

print("所有高亮图绘制完成！")
