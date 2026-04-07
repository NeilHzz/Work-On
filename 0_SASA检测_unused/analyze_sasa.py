import pandas as pd
import numpy as np
from scipy import stats
import seaborn as sns
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体
plt.rcParams['axes.unicode_minus'] = False     # 解决负号显示问题

# 读取数据
df = pd.read_excel('sasa_results.xlsx')

# 添加分组信息
df['Group'] = df['PDB文件'].apply(lambda x: 'G' if 'G' in x else ('A' if 'A' in x else 'C'))

# 要分析的列
columns_to_analyze = [
    'Total SASA (r=1.0)', 'Protein SASA (r=1.0)', 'Glycan SASA (r=1.0)',
    'Total SASA (r=3.5)', 'Protein SASA (r=3.5)', 'Glycan SASA (r=3.5)'
]

# 计算描述性统计
desc_stats = df.groupby('Group')[columns_to_analyze].agg(['mean', 'std', 'count'])
desc_stats.to_excel('sasa_descriptive_stats.xlsx')

# 创建结果DataFrame
results = pd.DataFrame()

for col in columns_to_analyze:
    # 获取A和C组的数据
    group_a = df[df['Group'] == 'A'][col]
    group_c = df[df['Group'] == 'C'][col]
    
    # 执行t检验
    t_stat, p_value = stats.ttest_ind(group_a, group_c)
    
    # 获取G组的值作为参考
    g_value = df[df['Group'] == 'G'][col].values[0]
    
    # 计算与G组的差异百分比
    a_diff_percent = ((group_a.mean() - g_value) / g_value) * 100
    c_diff_percent = ((group_c.mean() - g_value) / g_value) * 100
    
    results = pd.concat([results, pd.DataFrame({
        '指标': [col],
        'A vs C p值': [p_value],
        '显著性': ['是' if p_value < 0.05 else '否'],
        'G组参考值': [g_value],
        'A组与G组差异(%)': [a_diff_percent],
        'C组与G组差异(%)': [c_diff_percent],
        'A组均值': [group_a.mean()],
        'C组均值': [group_c.mean()],
        'A组标准差': [group_a.std()],
        'C组标准差': [group_c.std()]
    })])

# 保存结果
results.to_excel('sasa_statistical_analysis.xlsx', index=False)