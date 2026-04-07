"""
2D Glycan-Protein Enrichment Analysis  (Gallus vs Columba pairwise)
======================================================================
Adapted from Ba et al., 2022, Science Advances, Fig. 3A.

Strategy:
  - X轴: Log2(Gallus_protein / Columba_protein)   蛋白层面的物种差异
  - Y轴: Log2(Gallus_glycan  / Columba_glycan)    糖基化层面的物种差异
  - y=x 对角线: 蛋白与糖基化等比例变化
  - 高于对角线: 糖基化差异 > 蛋白差异 → 鸡/鸽间"超比例糖基化重塑"
  - 低于对角线: 蛋白差异 > 糖基化差异 → 糖基化相对保守

匹配策略:
  - 背景蛋白：解析 Blastp 比对结果 (Result 文件)，按阈值过滤后取每个
    Columba 蛋白的最佳 Gallus hit（Accession 对应）。
    过滤标准: E-value≤1e-5; 若 Q_Hsp=S_Hsp 则平均Identity≥0.8,
              若 Q_Hsp≠S_Hsp 则 MaxIdentity≥0.5
  - 目标蛋白：严格手动指定 Blastp accession 对
     （OVAL/OC116/TRFE 平均Identity<0.8 但生物学上是真正同源蛋白）
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import os
import re

# ─── 绘图风格 ──────────────────────────────────────────────────────────────
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
mpl.rcParams['axes.spines.top'] = False
mpl.rcParams['axes.spines.right'] = False
mpl.rcParams['axes.linewidth'] = 1.5
mpl.rcParams['xtick.major.width'] = 1.5
mpl.rcParams['ytick.major.width'] = 1.5
mpl.rcParams['xtick.labelsize'] = 12
mpl.rcParams['ytick.labelsize'] = 12

# ─── 路径 ─────────────────────────────────────────────────────────────────
DATA_DIR    = r"e:\Data\Desktop\Work On\Raw_Data\MS_DATA"
BLASTP_FILE = r"e:\Data\Desktop\Work On\Raw_Data\原始fasta\Result"
OUT_DIR     = r"e:\Data\Desktop\Work On\20260225\Figure"
os.makedirs(OUT_DIR, exist_ok=True)

SP_REF  = 'Gallus'    # 早成鸟参考 (分子)
SP_COMP = 'Columba'   # 晚成鸟对比 (分母)
PREF    = {'Gallus': 'J', 'Anas': 'A', 'Columba': 'C'}

# Gallus 新版文件名及 sheet 名
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

# ─── 目标蛋白（手动指定 accession 对，不依赖 Blastp 阈值） ──────────────
# { protein_name: (accession_in_Gallus, accession_in_Columba) }
TARGET_PAIRS = {
    'OVAL':  ('P01012',     'A0A2I0MWA2'),
    'OC116': ('A0A8V0XA58', 'A0A2I0MGY6'),
    'TRFE':  ('A0A8V1A6Y9', 'A0A2I0LUS7'),
    # OC17: only in Gallus, skip cross-species FC
}
TARGET_COLORS = {
    'OVAL':  '#E64B35',
    'OC116': '#4DBBD5',
    'TRFE':  '#00A087',
}
# 目标蛋白的所有 accession（用于从背景中去重）
TARGET_ACCS = {acc for pair in TARGET_PAIRS.values() for acc in pair}

# ─── Blastp 过滤参数 ──────────────────────────────────────────────────────
EVALUE_CUTOFF   = 1e-5
AVG_ID_CUTOFF   = 0.80   # Q_Hsp == S_Hsp 时用平均 Identity
MAX_ID_CUTOFF   = 0.50   # Q_Hsp != S_Hsp 时用最高 Identity

# ─── 工具函数 ─────────────────────────────────────────────────────────────
def get_int_cols(df, sp):
    cols = [c for c in df.columns if f'Intensity {PREF[sp]}' in c]
    return cols if cols else [c for c in df.columns if 'Intensity' in c]


def load_protein_by_acc(sp):
    """Protein accession → mean protein intensity (NC>=2)"""
    df = pd.read_excel(os.path.join(DATA_DIR, PROTEIN_FNAME[sp]),
                       sheet_name='Protein_quant')
    if 'Number Comparable' in df.columns:
        df = df[df['Number Comparable'] >= 2].copy()
    ic = get_int_cols(df, sp)
    df['prot_mean'] = df[ic].replace(0, np.nan).mean(axis=1)
    df = df[df['prot_mean'] > 0]
    return df.set_index('Protein accession')['prot_mean']


def load_glycan_by_acc(sp):
    """Protein accession → summed glycan intensity (NC>=1, 多位点求和)"""
    df = pd.read_excel(os.path.join(DATA_DIR, GLYCAN_FNAME[sp]),
                       sheet_name=GLYCAN_SHEET_SITE[sp],
                       header=GLYCAN_SHEET_HEADER[sp])
    ic = get_int_cols(df, sp)
    df['glyc_mean'] = df[ic].replace(0, np.nan).mean(axis=1)
    df = df[df['glyc_mean'] > 0]
    return df.groupby('Protein accession')['glyc_mean'].sum()


def extract_acc(s):
    """从 tr|ACC|ID_XXX 或 sp|ACC|NAME 格式中提取 accession"""
    m = re.search(r'\|([A-Z0-9]+)\|', str(s))
    return m.group(1) if m else str(s)


def count_nonoverlap(starts, ends):
    """贪心区间合并，计算非重叠 HSP 数"""
    intervals = sorted(zip(starts, ends))
    merged, cur_end = 0, -1
    for s, e in intervals:
        if s > cur_end:
            merged += 1
            cur_end = e
        else:
            cur_end = max(cur_end, e)
    return merged


def build_blastp_mapping(blastp_file):
    """
    解析 Blastp tabular 结果，按过滤标准生成
    { columba_acc → gallus_acc } 最佳映射字典。
    """
    raw = pd.read_csv(blastp_file, sep='\t')
    raw['col_acc'] = raw['QueryID'].apply(extract_acc)
    raw['gal_acc'] = raw['SubjectDefID'].apply(extract_acc)

    records = []
    for (col_a, gal_a), grp in raw.groupby(['col_acc', 'gal_acc']):
        q_hsp = count_nonoverlap(grp['QueryStart'],  grp['QueryEnd'])
        s_hsp = count_nonoverlap(grp['SubjectStart'], grp['SubjectEnd'])
        mean_e = grp['E-value'].mean()
        max_id = grp['Identity'].max()  / 100.0
        avg_id = grp['Identity'].mean() / 100.0
        records.append({'col_acc': col_a, 'gal_acc': gal_a,
                        'mean_evalue': mean_e, 'max_identity': max_id,
                        'avg_identity': avg_id, 'q_hsp': q_hsp, 's_hsp': s_hsp,
                        'max_bitscore': grp['BitScore'].max()})

    agg = pd.DataFrame(records)

    def passes(row):
        if row['mean_evalue'] > EVALUE_CUTOFF:
            return False
        if row['q_hsp'] != row['s_hsp']:
            return row['max_identity'] >= MAX_ID_CUTOFF
        return row['avg_identity'] >= AVG_ID_CUTOFF

    agg['pass'] = agg.apply(passes, axis=1)
    best = (agg[agg['pass']]
            .sort_values('max_bitscore', ascending=False)
            .drop_duplicates('col_acc')
            .reset_index(drop=True))
    return dict(zip(best['col_acc'], best['gal_acc']))


# ─── 加载数据 ─────────────────────────────────────────────────────────────
print("Loading data ...")
prot_ref_acc  = load_protein_by_acc(SP_REF)
prot_comp_acc = load_protein_by_acc(SP_COMP)
glyc_ref_acc  = load_glycan_by_acc(SP_REF)
glyc_comp_acc = load_glycan_by_acc(SP_COMP)

# ─── Blastp 映射：Columba accession → Gallus accession ───────────────────
print(f"Parsing Blastp results: {BLASTP_FILE}")
blastp_map = build_blastp_mapping(BLASTP_FILE)
print(f"  Blastp mapping entries (passing filter): {len(blastp_map)}")

# ─── 背景蛋白：从 Blastp 映射中取同时具备蛋白+糖基化数据且非靶蛋白的对 ──
records = []
for col_a, gal_a in blastp_map.items():
    # 排除目标蛋白（靶蛋白的 accession 用手动配对处理）
    if col_a in TARGET_ACCS or gal_a in TARGET_ACCS:
        continue
    # 四项数据齐全才入图
    if (gal_a not in prot_ref_acc  or col_a not in prot_comp_acc or
        gal_a not in glyc_ref_acc  or col_a not in glyc_comp_acc):
        continue
    prot_fc = np.log2(prot_ref_acc[gal_a])  - np.log2(prot_comp_acc[col_a])
    glyc_fc = np.log2(glyc_ref_acc[gal_a])  - np.log2(glyc_comp_acc[col_a])
    records.append({'Gene': gal_a, 'col_acc': col_a, 'gal_acc': gal_a,
                    'prot_log2FC': prot_fc, 'glyc_log2FC': glyc_fc, 'target': None})

print(f"  Background proteins (Blastp, data-complete): {len(records)}")

# ─── 目标蛋白：手动指定 accession 对 ────────────────────────────────────
target_records = []
for pname, (acc_ref, acc_comp) in TARGET_PAIRS.items():
    missing = []
    if acc_ref  not in prot_ref_acc:  missing.append(f"{SP_REF}_prot")
    if acc_comp not in prot_comp_acc: missing.append(f"{SP_COMP}_prot")
    if acc_ref  not in glyc_ref_acc:  missing.append(f"{SP_REF}_glycan")
    if acc_comp not in glyc_comp_acc: missing.append(f"{SP_COMP}_glycan")
    if missing:
        print(f"  SKIP {pname}: not detected in {missing}")
        continue
    prot_fc = np.log2(prot_ref_acc[acc_ref])  - np.log2(prot_comp_acc[acc_comp])
    glyc_fc = np.log2(glyc_ref_acc[acc_ref])  - np.log2(glyc_comp_acc[acc_comp])
    target_records.append({'Gene': pname, 'col_acc': acc_comp, 'gal_acc': acc_ref,
                            'prot_log2FC': prot_fc, 'glyc_log2FC': glyc_fc, 'target': pname})

print(f"  Target proteins (manual accession pairs): {len(target_records)}")

df_enrich = pd.DataFrame(records + target_records)
print(f"\nFinal: {len(df_enrich)} total proteins "
      f"({len(records)} background + {len(target_records)} targets)\n")

print("Target protein FC values:")
print(df_enrich[df_enrich['target'].notna()]
      [['Gene', 'prot_log2FC', 'glyc_log2FC']].to_string(index=False))

# ─── 绘图参数 ─────────────────────────────────────────────────────────────
vals = pd.concat([df_enrich['prot_log2FC'], df_enrich['glyc_log2FC']])
pad  = (vals.max() - vals.min()) * 0.20
vmin, vmax = vals.min() - pad, vals.max() + pad

# 背景蛋白的基因名标注（从 Gallus MS 表获取）
pg_full = pd.read_excel(os.path.join(DATA_DIR, PROTEIN_FNAME['Gallus']),
                        sheet_name='Protein_quant')
acc2gene = dict(zip(pg_full['Protein accession'], pg_full['Gene name'].fillna('')))

# 为背景蛋白补充可读名称
bg_df = df_enrich[df_enrich['target'].isna()].copy()
bg_df['label'] = bg_df['gal_acc'].map(acc2gene).fillna(bg_df['gal_acc'])

# ─── 画布：主图 + 右侧图例面板 ────────────────────────────────────────────
fig = plt.figure(figsize=(9.5, 7.0))
ax  = fig.add_axes([0.10, 0.11, 0.60, 0.80])   # 主图区域

# ── 四象限着色 ────────────────────────────────────────────────────────────
# 对角线以下 & X>0: Glycan相对蛋白在Gallus中更低 → 鸡糖基化相对抑制（暖色）
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection

def fill_below_diag(ax, xmin, xmax, ymin, ymax, color, alpha):
    """填充在对角线以下(glyc_FC < prot_FC)的区域"""
    verts = [(xmin, ymin), (xmax, ymin), (xmax, xmax), (xmin, xmin)]
    poly = Polygon(verts, closed=True)
    pc = PatchCollection([poly], facecolor=color, alpha=alpha, zorder=0,
                         edgecolor='none', transform=ax.transData, clip_on=True)
    ax.add_collection(pc)

def fill_above_diag(ax, xmin, xmax, ymin, ymax, color, alpha):
    """填充在对角线以上(glyc_FC > prot_FC)的区域"""
    verts = [(xmin, xmin), (xmax, xmax), (xmax, ymax), (xmin, ymax)]
    poly = Polygon(verts, closed=True)
    pc = PatchCollection([poly], facecolor=color, alpha=alpha, zorder=0,
                         edgecolor='none', transform=ax.transData, clip_on=True)
    ax.add_collection(pc)

fill_below_diag(ax, vmin, vmax, vmin, vmax, '#FDE8E4', 0.65)  # 暖色：鸡糖基化偏低
fill_above_diag(ax, vmin, vmax, vmin, vmax, '#E4F0FB', 0.65)  # 冷色：鸽糖基化偏高

# ── 参考线 ────────────────────────────────────────────────────────────────
ax.plot([vmin, vmax], [vmin, vmax], '--', color='#666666',
        linewidth=1.6, zorder=3, alpha=0.7)
ax.axhline(0, color='#BBBBBB', linewidth=0.9, linestyle=':', zorder=2)
ax.axvline(0, color='#BBBBBB', linewidth=0.9, linestyle=':', zorder=2)

# ── 对角线标注 ────────────────────────────────────────────────────────────
# y=x 对角线文字已移除

# ── 背景蛋白（带基因名标注） ──────────────────────────────────────────────
# 标签位置微调字典 {label: (dx_points, dy_points)}
LABEL_OFFSETS = {
    'LAMC1':  (  6,   6),
    'SCUBE1': (  6,   8),
    'VTG2':   (-52, -16),
    'ST14':   (  6, -16),
    'CPE':    (  6,   6),
    'TSKU':   (-52,  -6),
    'SORT1':  (-52,   6),
}

for _, row in bg_df.iterrows():
    ax.scatter(row['prot_log2FC'], row['glyc_log2FC'],
               c='#888888', s=55, zorder=4, linewidths=0.6,
               edgecolors='white', alpha=0.9)
    lbl = row['label']
    dx, dy = LABEL_OFFSETS.get(lbl, (7, 5))
    ax.annotate(lbl,
                xy=(row['prot_log2FC'], row['glyc_log2FC']),
                xytext=(dx, dy), textcoords='offset points',
                fontsize=8.5, color='#444444',
                arrowprops=dict(arrowstyle='-', color='#AAAAAA',
                                lw=0.6, shrinkA=0, shrinkB=3) if abs(dx)>15 or abs(dy)>10 else None)

# ── 目标蛋白（彩色高亮 + 注释框） ────────────────────────────────────────
# 详细偏移：避免重叠
TARGET_ANNOT = {
    'OVAL':  {'dx': -58, 'dy': -28, 'boxcolor': '#FDDEDE'},
    'OC116': {'dx': -90, 'dy': -18, 'boxcolor': '#D8F0F7'},
    'TRFE':  {'dx': -90, 'dy': -32, 'boxcolor': '#D3F0EB'},
}

for pname, color in TARGET_COLORS.items():
    sub = df_enrich[df_enrich['target'] == pname]
    if sub.empty:
        continue
    row = sub.iloc[0]
    ax.scatter(row['prot_log2FC'], row['glyc_log2FC'],
               c=color, s=200, zorder=6, linewidths=1.2,
               edgecolors='white')

    cfg = TARGET_ANNOT.get(pname, {'dx': 40, 'dy': 20, 'boxcolor': '#EEEEEE'})
    label_text = f"$\\bf{{{pname}}}$"
    ax.annotate(
        label_text,
        xy=(row['prot_log2FC'], row['glyc_log2FC']),
        xytext=(cfg['dx'], cfg['dy']), textcoords='offset points',
        fontsize=8.5, color=color,
        bbox=dict(boxstyle='round,pad=0.35', facecolor=cfg['boxcolor'],
                  edgecolor=color, linewidth=1.0, alpha=0.92),
        arrowprops=dict(arrowstyle='->', color=color, lw=1.2,
                        shrinkA=0, shrinkB=5,
                        connectionstyle='arc3,rad=0.08'))

# ── 象限区域文字 ─────────────────────────────────────────────────────────
ax.text(vmax - 0.3, vmin + 0.4,
        f'Glycan suppressed\nin {SP_REF}',
        fontsize=7.5, color='#C0392B', ha='right', va='bottom',
        style='italic', alpha=0.75)
ax.text(vmin + 0.3, vmax - 0.4,
        f'Glycan enriched\nin {SP_REF}',
        fontsize=7.5, color='#1565C0', ha='left', va='top',
        style='italic', alpha=0.75)

# ── 坐标轴 ────────────────────────────────────────────────────────────────
ax.set_xlabel(f'Protein  $\\log_2$FC  ({SP_REF} / {SP_COMP})',
              fontsize=12, fontweight='bold', labelpad=6)
ax.set_ylabel(f'Glycan  $\\log_2$FC  ({SP_REF} / {SP_COMP})',
              fontsize=12, fontweight='bold', labelpad=6)
ax.set_xlim(vmin, vmax)
ax.set_ylim(vmin, vmax)
ax.set_aspect('equal')
ax.tick_params(labelsize=10)
for spine in ['top', 'right']:
    ax.spines[spine].set_visible(False)
ax.spines['left'].set_linewidth(1.4)
ax.spines['bottom'].set_linewidth(1.4)

# ─── 右侧独立图例面板 ─────────────────────────────────────────────────────
ax_leg = fig.add_axes([0.73, 0.20, 0.24, 0.55])
ax_leg.set_xlim(0, 1); ax_leg.set_ylim(0, 1)
ax_leg.axis('off')

legend_items = [
    ('circle',  '#888888', 7,   'Background'),
]
for pname, color in TARGET_COLORS.items():
    legend_items.append(('circle', color, 10, pname))
legend_items += [
    ('dash',   '#666666', 0, 'y = x  (equal change)'),
    ('shade',  '#FDE8E4', 0, f'Glycan suppressed\nin {SP_REF}'),
    ('shade',  '#E4F0FB', 0, f'Glycan enriched\nin {SP_REF}'),
]

y_step = 0.075
y_pos  = 0.94

for mtype, color, sz, lbl in legend_items:
    y_pos -= y_step
    if mtype == 'circle':
        ax_leg.scatter([0.13], [y_pos], c=color, s=sz**1.8,
                       zorder=5, edgecolors='white', linewidths=0.5,
                       transform=ax_leg.transData, clip_on=False)
    elif mtype == 'dash':
        ax_leg.plot([0.04, 0.22], [y_pos, y_pos], '--',
                    color=color, lw=1.4)
    elif mtype == 'shade':
        rect = plt.Rectangle((0.04, y_pos - 0.018), 0.18, 0.036,
                              facecolor=color, edgecolor='#AAAAAA',
                              linewidth=0.5, transform=ax_leg.transData)
        ax_leg.add_patch(rect)
    ax_leg.text(0.28, y_pos, lbl, fontsize=8, va='center', color='#333333')

# ─── 标题 ─────────────────────────────────────────────────────────────────
fig.text(0.42, 0.96,
         f'2D Glycan–Protein Enrichment  ({SP_REF} vs {SP_COMP})',
         ha='center', va='top', fontsize=13, fontweight='bold', color='#222222')

out_path = os.path.join(OUT_DIR, f'Fig_2d_enrichment_{SP_REF}_vs_{SP_COMP}.png')
plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f"\nFigure saved → {out_path}")
