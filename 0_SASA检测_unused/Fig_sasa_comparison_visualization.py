import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 读取数据
file_path = 'sasa_statistical_analysis.xlsx'
df = pd.read_excel(file_path, sheet_name='Sheet1')

print("数据概览：")
print(df)
print()

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 准备数据
r_values = ['r=1.0', 'r=3.5']
categories = ['Total SASA', 'Protein SASA', 'Glycan SASA']
colors = ['#3498db', '#e74c3c', '#2ecc71']  # 蓝色、红色、绿色

# 创建图表
fig, axes = plt.subplots(1, 2, figsize=(16, 7))

for idx, r_val in enumerate(r_values):
    ax = axes[idx]
    
    # 筛选当前 r 值的数据
    df_r = df[df['指标'].str.contains(r_val)]
    
    # 提取数据
    labels = []
    g_values = []
    a_values = []
    c_values = []
    a_std = []
    c_std = []
    p_values = []
    significance = []
    
    for cat in categories:
        row = df_r[df_r['指标'].str.contains(cat.split()[0])]
        if not row.empty:
            labels.append(cat.split()[0])
            g_values.append(row['G组参考值'].values[0])
            a_values.append(row['A组均值'].values[0])
            c_values.append(row['C组均值'].values[0])
            a_std.append(row['A组标准差'].values[0])
            c_std.append(row['C组标准差'].values[0])
            p_values.append(row['A vs C p值'].values[0])
            significance.append(row['显著性'].values[0])
    
    # 设置柱状图位置
    x = np.arange(len(labels))
    width = 0.25
    
    # 绘制柱状图（按 G、A、C 顺序）
    bars1 = ax.bar(x - width, g_values, width, label='G组 (Gallus)', 
                   alpha=0.8, edgecolor='black', linewidth=1.5)
    bars2 = ax.bar(x, a_values, width, label='A组 (Anas)', 
                   yerr=a_std, capsize=5, alpha=0.8, edgecolor='black', linewidth=1.5)
    bars3 = ax.bar(x + width, c_values, width, label='C组 (Columba)', 
                   yerr=c_std, capsize=5, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    # 为不同类型设置颜色
    for i, (bar1, bar2, bar3) in enumerate(zip(bars1, bars2, bars3)):
        bar1.set_facecolor(colors[i])
        bar1.set_alpha(0.4)
        bar2.set_facecolor(colors[i])
        bar2.set_alpha(0.9)
        bar3.set_facecolor(colors[i])
        bar3.set_alpha(0.6)
    
    # 添加显著性标记
    y_max = max(max(g_values), max(a_values), max(c_values))
    y_min = min(min(g_values), min(a_values), min(c_values))
    y_data_range = y_max - y_min
    
    for i, (sig, p_val) in enumerate(zip(significance, p_values)):
        if sig == '是':
            # 计算标记位置（在 A 组和 C 组之间）
            y_pos = max(a_values[i] + a_std[i], c_values[i] + c_std[i]) + y_data_range * 0.03
            
            # 绘制显著性线和星号
            ax.plot([i, i + width], [y_pos, y_pos], 'k-', linewidth=1.5)
            ax.plot([i, i], [y_pos - y_data_range*0.01, y_pos], 'k-', linewidth=1.5)
            ax.plot([i + width, i + width], [y_pos - y_data_range*0.01, y_pos], 'k-', linewidth=1.5)
            
            # 添加显著性标记
            if p_val < 0.001:
                sig_marker = '***'
            elif p_val < 0.01:
                sig_marker = '**'
            elif p_val < 0.05:
                sig_marker = '*'
            else:
                sig_marker = 'ns'
            
            ax.text(i + width/2, y_pos + y_data_range*0.005, sig_marker, 
                   ha='center', va='bottom', fontsize=14, fontweight='bold')
            
            # 添加 p 值
            ax.text(i + width/2, y_pos + y_data_range*0.05, f'p={p_val:.4f}', 
                   ha='center', va='bottom', fontsize=9, style='italic')
    
    # 设置标签和标题
    ax.set_xlabel('SASA 类型', fontsize=13, fontweight='bold')
    ax.set_ylabel('SASA 值', fontsize=13, fontweight='bold')
    ax.set_title(f'SASA 比较分析 ({r_val})', fontsize=15, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    
    # 只在第一个子图显示图例
    if idx == 0:
        ax.legend(fontsize=11, loc='upper right', framealpha=0.95)
    
    ax.grid(True, alpha=0.3, axis='y')
    
    # 截断 y 轴以凸显差异（设置合适的 y 轴下限）
    all_values = g_values + a_values + c_values
    y_min_data = min(all_values)
    y_max_data = max([a_values[i] + a_std[i] if i < len(a_std) else a_values[i] 
                      for i in range(len(a_values))] + 
                     [c_values[i] + c_std[i] if i < len(c_std) else c_values[i] 
                      for i in range(len(c_values))])
    
    # 检查是否有显著性标记，如果有则需要更多空间
    has_significance = any(significance)
    
    # 设置 y 轴范围：从最小值的 95% 开始，根据是否有显著性标记调整上限
    y_range = y_max_data - y_min_data
    if has_significance:
        ax.set_ylim(y_min_data - y_range * 0.05, y_max_data + y_range * 0.20)
    else:
        ax.set_ylim(y_min_data - y_range * 0.05, y_max_data + y_range * 0.10)

plt.tight_layout()
plt.savefig('Fig_sasa_comparison_r_value.png', dpi=300, bbox_inches='tight')
print("柱状图已保存为: Fig_sasa_comparison_r_value.png")

# 创建第二个图：按类型分组的图表
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# 为每个物种定义颜色
species_colors = {
    'A': '#7895C1',  # Anas
    'C': '#F0C284',  # Columba
    'G': '#B54664'   # Gallus
}

for idx, cat in enumerate(categories):
    ax = axes[idx]
    
    # 提取该类型在两个 r 值下的数据
    cat_key = cat.split()[0]
    data_rows = df[df['指标'].str.contains(cat_key)]
    
    r_labels = []
    g_vals = []
    a_vals = []
    c_vals = []
    a_errs = []
    c_errs = []
    sigs = []
    p_vals = []
    
    for r_val in r_values:
        row = data_rows[data_rows['指标'].str.contains(r_val)]
        if not row.empty:
            r_labels.append(r_val)
            g_vals.append(row['G组参考值'].values[0])
            a_vals.append(row['A组均值'].values[0])
            c_vals.append(row['C组均值'].values[0])
            a_errs.append(row['A组标准差'].values[0])
            c_errs.append(row['C组标准差'].values[0])
            sigs.append(row['显著性'].values[0])
            p_vals.append(row['A vs C p值'].values[0])
    
    # 绘制柱状图（按 G、A、C 顺序）
    x = np.arange(len(r_labels))
    width = 0.25
    
    bars1 = ax.bar(x - width, g_vals, width, label='G组 (Gallus)', 
                   color=species_colors['G'], alpha=0.8, 
                   edgecolor='black', linewidth=1.5)
    bars2 = ax.bar(x, a_vals, width, label='A组 (Anas)', 
                   yerr=a_errs, capsize=5, color=species_colors['A'], alpha=0.8, 
                   edgecolor='black', linewidth=1.5)
    bars3 = ax.bar(x + width, c_vals, width, label='C组 (Columba)', 
                   yerr=c_errs, capsize=5, color=species_colors['C'], alpha=0.8, 
                   edgecolor='black', linewidth=1.5)
    
    # 添加显著性标记
    for i, (sig, p_val) in enumerate(zip(sigs, p_vals)):
        if sig == '是':
            # 找到 A 组和 C 组柱子的最高点（包含误差棒）
            y_a = a_vals[i] + a_errs[i]
            y_c = c_vals[i] + c_errs[i]
            y_base = max(y_a, y_c)
            
            # 计算数据范围用于相对位置
            all_vals = g_vals + a_vals + c_vals
            y_data_range = max(all_vals) - min(all_vals)
            
            # 显著性线的位置（紧贴最高柱子上方）
            y_line = y_base + y_data_range * 0.02
            
            # 绘制显著性线和星号
            ax.plot([i, i + width], [y_line, y_line], 'k-', linewidth=1.5)
            ax.plot([i, i], [y_base, y_line], 'k-', linewidth=1.5)
            ax.plot([i + width, i + width], [y_c if y_c > y_a else y_a, y_line], 'k-', linewidth=1.5)
            
            # 添加显著性标记
            if p_val < 0.001:
                sig_marker = '***'
            elif p_val < 0.01:
                sig_marker = '**'
            elif p_val < 0.05:
                sig_marker = '*'
            else:
                sig_marker = 'ns'
            
            ax.text(i + width/2, y_line + y_data_range*0.005, sig_marker, 
                   ha='center', va='bottom', fontsize=14, fontweight='bold')
            ax.text(i + width/2, y_line + y_data_range*0.06, f'p={p_val:.4f}', 
                   ha='center', va='bottom', fontsize=9, style='italic')
    
    # 设置标签和标题
    ax.set_xlabel('探针半径', fontsize=13, fontweight='bold')
    ax.set_ylabel('SASA 值', fontsize=13, fontweight='bold')
    ax.set_title(f'{cat}', fontsize=15, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(r_labels, fontsize=11)
    
    # 只在第一个子图显示图例
    if idx == 0:
        ax.legend(fontsize=10, loc='upper right', framealpha=0.95)
    
    ax.grid(True, alpha=0.3, axis='y')
    
    # 截断 y 轴以凸显差异
    all_values = g_vals + a_vals + c_vals
    y_min_data = min(all_values)
    y_max_data = max([a_vals[i] + a_errs[i] for i in range(len(a_vals))] + 
                     [c_vals[i] + c_errs[i] for i in range(len(c_vals))])
    
    # 检查是否有显著性标记，如果有则需要更多空间
    has_sig = any(sigs)
    
    # 设置 y 轴范围：从最小值的 95% 开始，根据是否有显著性标记调整上限
    y_range = y_max_data - y_min_data
    if has_sig:
        ax.set_ylim(y_min_data - y_range * 0.05, y_max_data + y_range * 0.20)
    else:
        ax.set_ylim(y_min_data - y_range * 0.05, y_max_data + y_range * 0.10)

plt.tight_layout()
plt.savefig('Fig_sasa_comparison_by_type.png', dpi=300, bbox_inches='tight')
print("分类柱状图已保存为: Fig_sasa_comparison_by_type.png")

print("\n绘图完成！")
