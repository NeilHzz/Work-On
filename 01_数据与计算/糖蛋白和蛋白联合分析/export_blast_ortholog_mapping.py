"""
export_blast_ortholog_mapping.py
================================
导出三组物种对的 BLASTP 同源配对结果及筛选参数到 Excel 文件。

输出文件：
  Figure_Data_Tables/Blast_Ortholog_Mapping.xlsx
    - Sheet "GvsC_all"        : Columba→Gallus 所有 HSP 原始记录
    - Sheet "GvsC_aggregated" : 聚合后每对的统计及 pass/fail 状态
    - Sheet "GvsA_all"        : Anas→Gallus 所有 HSP 原始记录
    - Sheet "GvsA_aggregated" : 聚合后每对的统计及 pass/fail 状态
    - Sheet "AvsC_bridge"     : 通过 Gallus 桥接的 Anas↔Columba 对（最终入图数据）
    - Sheet "Filter_Criteria" : 筛选参数说明
    - Sheet "Target_Proteins" : 目标蛋白（OVAL/OC116/TRFE）在各对中的自动识别结果
"""

import os, re
import pandas as pd
import numpy as np
from collections import defaultdict

# ──────────────────────────────────────────────────────────────────────────
# 参数（与主脚本保持一致）
# ──────────────────────────────────────────────────────────────────────────
BASE      = r"D:\system_folder\Desktop\Work On"
AVG_FILE  = os.path.join(BASE, "01_数据与计算", "Raw_Data", "原始fasta", "Result_AvsG")
CVG_FILE  = os.path.join(BASE, "01_数据与计算", "Raw_Data", "原始fasta", "Result_CvsG")
DATA_DIR  = os.path.join(BASE, "01_数据与计算", "Raw_Data", "MS_DATA")
OUT_FILE  = os.path.join(BASE, "Figure_Data_Tables", "Blast_Ortholog_Mapping.xlsx")

EVALUE_CUTOFF = 1e-5
AVG_ID_CUTOFF = 0.40
MAX_ID_CUTOFF = 0.40

GALLUS_TARGETS = {
    'P01012':     'OVAL',
    'A0A8V0XA58': 'OC116',
    'A0A8V1A6Y9': 'TRFE',
}

PREF = {'Gallus': 'G', 'Anas': 'A', 'Columba': 'C'}

# ──────────────────────────────────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────────────────────────────────

def extract_acc(s):
    m = re.search(r'\|([A-Z0-9]+)\|', str(s))
    return m.group(1) if m else str(s)


def count_nonoverlap(starts, ends):
    intervals = sorted(zip(starts, ends))
    merged, cur_end = 0, -1
    for s, e in intervals:
        if s > cur_end:
            merged += 1; cur_end = e
        else:
            cur_end = max(cur_end, e)
    return merged


def parse_tabular6(path):
    cols = ['qseqid', 'sseqid', 'pident', 'length', 'mismatch', 'gapopen',
            'qstart', 'qend', 'sstart', 'send', 'evalue', 'bitscore']
    df = pd.read_csv(path, sep='\t', header=None, names=cols, usecols=range(12))
    df['comp_acc'] = df['qseqid'].apply(extract_acc)
    df['ref_acc']  = df['sseqid'].apply(extract_acc)
    return df


def agg_tabular(df):
    """聚合每个 (comp, ref) 对的 HSP，返回含 pass 列的 DataFrame（包含全部对）。"""
    recs = []
    for (ca, ra), grp in df.groupby(['comp_acc', 'ref_acc']):
        q_hsp  = count_nonoverlap(grp['qstart'], grp['qend'])
        s_hsp  = count_nonoverlap(grp['sstart'], grp['send'])
        mean_e = grp['evalue'].mean()
        max_id = grp['pident'].max() / 100.0
        avg_id = grp['pident'].mean() / 100.0
        recs.append({
            'comp_acc':    ca,
            'ref_acc':     ra,
            'hsp_count':   len(grp),
            'q_hsp_nonoverlap': q_hsp,
            's_hsp_nonoverlap': s_hsp,
            'mean_evalue': mean_e,
            'max_identity': max_id,
            'avg_identity': avg_id,
            'max_bitscore': grp['bitscore'].max(),
        })
    agg = pd.DataFrame(recs)
    if agg.empty:
        return agg

    def passes(row):
        if row['mean_evalue'] > EVALUE_CUTOFF:   return False
        if row['q_hsp_nonoverlap'] != row['s_hsp_nonoverlap']:
            return row['max_identity'] >= MAX_ID_CUTOFF
        return row['avg_identity'] >= AVG_ID_CUTOFF

    agg['pass_filter'] = agg.apply(passes, axis=1)
    agg['filter_reason'] = agg.apply(_reason, axis=1)
    return agg.sort_values('max_bitscore', ascending=False).reset_index(drop=True)


def _reason(row):
    if row['mean_evalue'] > EVALUE_CUTOFF:
        return f"E-value {row['mean_evalue']:.2e} > {EVALUE_CUTOFF:.0e}"
    if row['q_hsp_nonoverlap'] != row['s_hsp_nonoverlap']:
        if row['max_identity'] < MAX_ID_CUTOFF:
            return f"HSP数不一致且 max_id {row['max_identity']:.1%} < {MAX_ID_CUTOFF:.0%}"
        return "PASS (max_id, HSP数不一致)"
    if row['avg_identity'] < AVG_ID_CUTOFF:
        return f"avg_id {row['avg_identity']:.1%} < {AVG_ID_CUTOFF:.0%}"
    return "PASS"


def best_per_comp(agg):
    """每个 comp_acc 保留最高 bitscore 的通过对。"""
    passed = agg[agg['pass_filter']].copy()
    return (passed.sort_values('max_bitscore', ascending=False)
                  .drop_duplicates('comp_acc')
                  .reset_index(drop=True))


def load_accessions(sp):
    """读取 MS 数据，返回 (prot_accs, glyc_accs) 两个 set。"""
    prot_df = pd.read_excel(os.path.join(DATA_DIR, f"Protein_MS_{sp}.xlsx"),
                             sheet_name='Protein_quant')
    if 'Number Comparable' in prot_df.columns:
        prot_df = prot_df[prot_df['Number Comparable'] >= 2]
    ic = [c for c in prot_df.columns if f'Intensity {PREF[sp]}' in c]
    if not ic:
        ic = [c for c in prot_df.columns if 'Intensity' in c]
    prot_df['mean'] = prot_df[ic].replace(0, np.nan).mean(axis=1)
    prot_df = prot_df[prot_df['mean'] > 0]
    prot_accs = set(prot_df['Protein accession'])

    glyc_df = pd.read_excel(os.path.join(DATA_DIR, f"Glycan_MS_{sp}.xlsx"),
                             sheet_name='Site_quant')
    ic2 = [c for c in glyc_df.columns if f'Intensity {PREF[sp]}' in c]
    if not ic2:
        ic2 = [c for c in glyc_df.columns if 'Intensity' in c]
    glyc_df['mean'] = glyc_df[ic2].replace(0, np.nan).mean(axis=1)
    glyc_df = glyc_df[glyc_df['mean'] > 0]
    glyc_accs = set(glyc_df['Protein accession'])

    return prot_accs, glyc_accs


def add_target_label(df, gallus_col):
    """在 DataFrame 中添加 target_name 列，根据 gallus_col 中的 accession 查询。"""
    df = df.copy()
    df['target_name'] = df[gallus_col].map(GALLUS_TARGETS).fillna('')
    return df


def format_pct(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = df[c].apply(lambda x: f"{x:.1%}" if pd.notna(x) and x != '' else x)
    return df


# ──────────────────────────────────────────────────────────────────────────
# 主逻辑
# ──────────────────────────────────────────────────────────────────────────

print("Loading MS accessions...")
prot_G, glyc_G = load_accessions('Gallus')
prot_A, glyc_A = load_accessions('Anas')
prot_C, glyc_C = load_accessions('Columba')

print(f"  Gallus  prot={len(prot_G)}  glyc={len(glyc_G)}")
print(f"  Anas    prot={len(prot_A)}  glyc={len(glyc_A)}")
print(f"  Columba prot={len(prot_C)}  glyc={len(glyc_C)}")

# ── 解析 blast 原始文件 ────────────────────────────────────────────────────
print("\nParsing blast files...")
avg_raw = parse_tabular6(AVG_FILE)   # Anas→Gallus
cvg_raw = parse_tabular6(CVG_FILE)   # Columba→Gallus

avg_agg = agg_tabular(avg_raw)
cvg_agg = agg_tabular(cvg_raw)

avg_best = best_per_comp(avg_agg)   # Gallus ref
cvg_best = best_per_comp(cvg_agg)   # Gallus ref

# ── GvsC ──────────────────────────────────────────────────────────────────
# 过滤数据完整的对（蛋白+糖肽均检测到）
def data_complete_GvsC(row):
    return (row['ref_acc'] in prot_G and row['comp_acc'] in prot_C and
            row['ref_acc'] in glyc_G and row['comp_acc'] in glyc_C)

gvc_best = cvg_best.copy()
gvc_best['data_complete'] = gvc_best.apply(data_complete_GvsC, axis=1)
gvc_final = gvc_best[gvc_best['data_complete']].copy()
gvc_final = add_target_label(gvc_final, 'ref_acc')

# ── GvsA ──────────────────────────────────────────────────────────────────
def data_complete_GvsA(row):
    return (row['ref_acc'] in prot_G and row['comp_acc'] in prot_A and
            row['ref_acc'] in glyc_G and row['comp_acc'] in glyc_A)

gva_best = avg_best.copy()
gva_best['data_complete'] = gva_best.apply(data_complete_GvsA, axis=1)
gva_final = gva_best[gva_best['data_complete']].copy()
# GvsA: 去重目标（同一 Gallus target 只取最高 bitscore 的 Anas 命中）
seen_gallus_targets = set()
final_rows = []
for _, row in gva_final.iterrows():
    tname = GALLUS_TARGETS.get(row['ref_acc'])
    if tname:
        if tname in seen_gallus_targets:
            final_rows.append({**row, 'target_name': '', 'note': 'paralog (降级为背景)'})
            continue
        seen_gallus_targets.add(tname)
    final_rows.append({**row, 'target_name': tname or '', 'note': ''})
gva_final = pd.DataFrame(final_rows)

# ── AvsC bridge ───────────────────────────────────────────────────────────
gallus_to_anas = {}
for _, row in avg_best.iterrows():
    ga = row['ref_acc']
    aa = row['comp_acc']
    if aa not in prot_A or aa not in glyc_A: continue
    if ga not in gallus_to_anas:
        gallus_to_anas[ga] = aa

bridge_rows = []
used_anas = set()
for _, row in cvg_best.iterrows():
    ga = row['ref_acc']
    ca = row['comp_acc']
    if ca not in prot_C or ca not in glyc_C: continue
    aa = gallus_to_anas.get(ga)
    if aa is None or aa in used_anas: continue
    used_anas.add(aa)
    tname = GALLUS_TARGETS.get(ga, '')

    # 找 AvsG 那条对应行的统计数据
    avg_row = avg_best[avg_best['comp_acc'] == aa]
    cvg_row = row

    bridge_rows.append({
        'anas_acc':             aa,
        'columba_acc':          ca,
        'gallus_bridge_acc':    ga,
        'target_name':          tname,
        # AvsG statistics
        'AvsG_avg_identity':    avg_row['avg_identity'].values[0] if len(avg_row) else '',
        'AvsG_max_identity':    avg_row['max_identity'].values[0] if len(avg_row) else '',
        'AvsG_mean_evalue':     avg_row['mean_evalue'].values[0]  if len(avg_row) else '',
        'AvsG_max_bitscore':    avg_row['max_bitscore'].values[0] if len(avg_row) else '',
        # CvsG statistics
        'CvsG_avg_identity':    cvg_row['avg_identity'],
        'CvsG_max_identity':    cvg_row['max_identity'],
        'CvsG_mean_evalue':     cvg_row['mean_evalue'],
        'CvsG_max_bitscore':    cvg_row['max_bitscore'],
    })

avc_df = pd.DataFrame(bridge_rows)

# ── 筛选参数说明 ───────────────────────────────────────────────────────────
criteria_rows = [
    ('参数',                     '值',           '说明'),
    ('E-value 上限',              f'{EVALUE_CUTOFF:.0e}',
     '最大允许期望值（E-value cutoff）'),
    ('avg_identity 下限',         f'{AVG_ID_CUTOFF:.0%}',
     'HSP 数相同时：所有 HSP identity 均值 ≥ 40%（Rost 1999 跨物种同源阈值）'),
    ('max_identity 下限（备用）', f'{MAX_ID_CUTOFF:.0%}',
     'HSP 数不一致时（可能有 alternative splicing）：最高 HSP identity ≥ 40%'),
    ('每 comp_acc 保留规则',      '最高 max_bitscore', '同一 comp 蛋白只保留最佳命中'),
    ('数据完整性过滤',            '蛋白+糖肽均检测',
     '蛋白组（Number Comparable ≥ 2）和糖蛋白组数据均有定量值'),
    ('目标蛋白识别',              '自动（Gallus accession）',
     'bf  OVAL=P01012  OC116=A0A8V0XA58  TRFE=A0A8V1A6Y9'),
    ('AvsC 桥接策略',             'AvsG ∩ CvsG via Gallus',
     '分别对 Gallus 建立最佳命中，以共同 Gallus 蛋白为桥接点'),
    ('输入 blast 文件',           'outfmt 6 (tabular)', 'TBtools blastp 输出，无 header'),
    ('AvsG 文件',                 AVG_FILE,       'Anas 为 query，Gallus 为 subject'),
    ('CvsG 文件',                 CVG_FILE,       'Columba 为 query，Gallus 为 subject'),
]
criteria_df = pd.DataFrame(criteria_rows[1:], columns=criteria_rows[0])

# ── 目标蛋白汇总 ─────────────────────────────────────────────────────────
target_rows = []
for gallus_acc, tname in GALLUS_TARGETS.items():
    # GvsC
    r = gvc_final[gvc_final['ref_acc'] == gallus_acc]
    if not r.empty:
        row = r.iloc[0]
        target_rows.append({
            '比较对':          'Gallus vs Columba',
            '目标蛋白':        tname,
            'Gallus_acc':     gallus_acc,
            'Comp_acc':       row['comp_acc'],
            'avg_identity':   row['avg_identity'],
            'max_bitscore':   row['max_bitscore'],
            'mean_evalue':    row['mean_evalue'],
        })
    else:
        target_rows.append({'比较对': 'Gallus vs Columba', '目标蛋白': tname,
                             'Gallus_acc': gallus_acc, 'Comp_acc': 'NOT FOUND',
                             'avg_identity': '', 'max_bitscore': '', 'mean_evalue': ''})
    # GvsA
    r = gva_final[gva_final['ref_acc'] == gallus_acc]
    r_tgt = r[r['target_name'] == tname] if 'target_name' in r.columns else r
    if not r_tgt.empty:
        row = r_tgt.iloc[0]
        target_rows.append({
            '比较对':          'Gallus vs Anas',
            '目标蛋白':        tname,
            'Gallus_acc':     gallus_acc,
            'Comp_acc':       row['comp_acc'],
            'avg_identity':   row['avg_identity'],
            'max_bitscore':   row['max_bitscore'],
            'mean_evalue':    row['mean_evalue'],
        })
    else:
        target_rows.append({'比较对': 'Gallus vs Anas', '目标蛋白': tname,
                             'Gallus_acc': gallus_acc, 'Comp_acc': 'NOT FOUND',
                             'avg_identity': '', 'max_bitscore': '', 'mean_evalue': ''})
    # AvsC
    r = avc_df[avc_df['target_name'] == tname] if not avc_df.empty else pd.DataFrame()
    if not r.empty:
        row = r.iloc[0]
        target_rows.append({
            '比较对':          'Anas vs Columba',
            '目标蛋白':        tname,
            'Gallus_acc':     row['gallus_bridge_acc'],
            'Comp_acc':       f"Anas={row['anas_acc']} / Columba={row['columba_acc']}",
            'avg_identity':   f"AvsG={row['AvsG_avg_identity']:.1%} / CvsG={row['CvsG_avg_identity']:.1%}",
            'max_bitscore':   f"AvsG={row['AvsG_max_bitscore']} / CvsG={row['CvsG_max_bitscore']}",
            'mean_evalue':    f"AvsG={row['AvsG_mean_evalue']:.2e} / CvsG={row['CvsG_mean_evalue']:.2e}",
        })
    else:
        target_rows.append({'比较对': 'Anas vs Columba', '目标蛋白': tname,
                             'Gallus_acc': gallus_acc, 'Comp_acc': 'NOT FOUND',
                             'avg_identity': '', 'max_bitscore': '', 'mean_evalue': ''})

target_df = pd.DataFrame(target_rows)

# ── 原始文件整理 ──────────────────────────────────────────────────────────
avg_raw_out = avg_raw[['comp_acc', 'ref_acc', 'pident', 'length', 'evalue', 'bitscore',
                        'qstart', 'qend', 'sstart', 'send']].copy()
avg_raw_out.columns = ['Anas_acc (query)', 'Gallus_acc (subject)', 'identity_%',
                        'alignment_length', 'evalue', 'bitscore',
                        'query_start', 'query_end', 'subject_start', 'subject_end']

cvg_raw_out = cvg_raw[['comp_acc', 'ref_acc', 'pident', 'length', 'evalue', 'bitscore',
                        'qstart', 'qend', 'sstart', 'send']].copy()
cvg_raw_out.columns = ['Columba_acc (query)', 'Gallus_acc (subject)', 'identity_%',
                        'alignment_length', 'evalue', 'bitscore',
                        'query_start', 'query_end', 'subject_start', 'subject_end']

# ── 聚合表格整理 ──────────────────────────────────────────────────────────
def format_agg(df, comp_label, ref_label, include_target=None):
    out = df.copy()
    out = out.rename(columns={
        'comp_acc': comp_label,
        'ref_acc':  ref_label,
        'hsp_count': 'HSP数(原始)',
        'q_hsp_nonoverlap': 'HSP数(query非重叠)',
        's_hsp_nonoverlap': 'HSP数(subject非重叠)',
        'mean_evalue': 'mean_E-value',
        'max_identity': 'max_identity',
        'avg_identity': 'avg_identity',
        'max_bitscore': 'max_bitscore',
        'pass_filter':  '通过筛选',
        'filter_reason': '原因/状态',
    })
    if include_target is not None:
        out['目标蛋白'] = out[ref_label].map(GALLUS_TARGETS).fillna('')
    out['max_identity_%'] = (out['max_identity'] * 100).map(lambda x: f"{x:.1f}%" if pd.notna(x) else '')
    out['avg_identity_%'] = (out['avg_identity'] * 100).map(lambda x: f"{x:.1f}%" if pd.notna(x) else '')
    drop_cols = [c for c in ['max_identity', 'avg_identity'] if c in out.columns]
    out = out.drop(columns=drop_cols)
    return out

avg_agg_out = format_agg(avg_agg, 'Anas_acc (query)', 'Gallus_acc (subject)',
                          include_target='ref')
cvg_agg_out = format_agg(cvg_agg, 'Columba_acc (query)', 'Gallus_acc (subject)',
                          include_target='ref')

# AvsC 输出格式化
if not avc_df.empty:
    avc_out = avc_df.copy()
    for c in ['AvsG_avg_identity', 'AvsG_max_identity', 'CvsG_avg_identity', 'CvsG_max_identity']:
        if c in avc_out.columns:
            avc_out[c] = avc_out[c].apply(
                lambda x: f"{x:.1%}" if isinstance(x, float) else x)
    for c in ['AvsG_mean_evalue', 'CvsG_mean_evalue']:
        if c in avc_out.columns:
            avc_out[c] = avc_out[c].apply(
                lambda x: f"{x:.2e}" if isinstance(x, float) else x)
else:
    avc_out = avc_df

gvc_out = gvc_final[['ref_acc', 'comp_acc', 'avg_identity', 'max_identity',
                       'mean_evalue', 'max_bitscore', 'data_complete', 'target_name']].copy()
gvc_out.rename(columns={
    'ref_acc': 'Gallus_acc', 'comp_acc': 'Columba_acc',
    'target_name': '目标蛋白', 'data_complete': '数据完整'
}, inplace=True)
gvc_out['avg_identity_%'] = (gvc_out['avg_identity'] * 100).map(lambda x: f"{x:.1f}%")
gvc_out['max_identity_%'] = (gvc_out['max_identity'] * 100).map(lambda x: f"{x:.1f}%")
gvc_out = gvc_out.drop(columns=['avg_identity', 'max_identity'])

gva_out = gva_final[['ref_acc', 'comp_acc', 'avg_identity', 'max_identity',
                       'mean_evalue', 'max_bitscore', 'data_complete', 'target_name',
                       'note']].copy() if 'note' in gva_final.columns else \
           gva_final[['ref_acc', 'comp_acc', 'avg_identity', 'max_identity',
                        'mean_evalue', 'max_bitscore', 'data_complete', 'target_name']].copy()
gva_out.rename(columns={
    'ref_acc': 'Gallus_acc', 'comp_acc': 'Anas_acc',
    'target_name': '目标蛋白', 'data_complete': '数据完整',
    'note': '备注'
}, inplace=True)
gva_out['avg_identity_%'] = (gva_out['avg_identity'] * 100).map(lambda x: f"{x:.1f}%")
gva_out['max_identity_%'] = (gva_out['max_identity'] * 100).map(lambda x: f"{x:.1f}%")
gva_out = gva_out.drop(columns=['avg_identity', 'max_identity'])

# ── 写出 Excel ────────────────────────────────────────────────────────────
print(f"\nWriting to {OUT_FILE} ...")
with pd.ExcelWriter(OUT_FILE, engine='openpyxl') as writer:
    criteria_df.to_excel(writer, sheet_name='筛选参数',       index=False)
    target_df.to_excel(  writer, sheet_name='目标蛋白识别结果', index=False)
    gvc_out.to_excel(    writer, sheet_name='GvsC_入图数据',   index=False)
    gva_out.to_excel(    writer, sheet_name='GvsA_入图数据',   index=False)
    avc_out.to_excel(    writer, sheet_name='AvsC_入图数据',   index=False)
    cvg_agg_out.to_excel(writer, sheet_name='CvsG_聚合统计',   index=False)
    avg_agg_out.to_excel(writer, sheet_name='AvsG_聚合统计',   index=False)
    cvg_raw_out.to_excel(writer, sheet_name='CvsG_原始HSP',    index=False)
    avg_raw_out.to_excel(writer, sheet_name='AvsG_原始HSP',    index=False)

print("Done!")
print(f"\n  筛选参数:      {len(criteria_df)} 条")
print(f"  目标蛋白识别:  {len(target_df)} 条")
print(f"  GvsC 入图:     {len(gvc_out)} 对")
print(f"  GvsA 入图:     {len(gva_out)} 对")
print(f"  AvsC 入图:     {len(avc_out)} 对")
print(f"  CvsG 聚合统计: {len(cvg_agg_out)} 对")
print(f"  AvsG 聚合统计: {len(avg_agg_out)} 对")
print(f"  CvsG 原始 HSP: {len(cvg_raw_out)} 条")
print(f"  AvsG 原始 HSP: {len(avg_raw_out)} 条")
