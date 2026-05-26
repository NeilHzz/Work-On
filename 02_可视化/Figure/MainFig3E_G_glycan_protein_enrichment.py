"""
2D Glycan-Protein Enrichment Analysis  — three pairwise comparisons
=====================================================================
Produces three figures:
  Fig_2d_enrichment_Gallus_vs_Columba.png   (precocial vs altricial)
  Fig_2d_enrichment_Gallus_vs_Anas.png      (two precocial birds)
  Fig_2d_enrichment_Anas_vs_Columba.png     (precocial vs altricial)

Background mapping (all three pairs via BLASTP):
  Gallus vs Columba : Result_CvsG  (Columba→Gallus outfmt6)
  Gallus vs Anas    : Result_AvsG  (Anas→Gallus outfmt6)
  Anas   vs Columba : Bridge via Gallus (AvsG ∩ CvsG)

Target proteins (OVAL/OC116/TRFE) are identified automatically from blast
results by their Gallus accession — no manual pair specification.
Filtering: E-value ≤ 1e-5, identity ≥ 40% (standard inter-species ortholog
cutoff; Rost 1999).
"""

import os, re
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _save import save_fig
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from matplotlib.collections import PatchCollection
from collections import defaultdict
from adjustText import adjust_text

# ─── 绘图风格 ──────────────────────────────────────────────────────────────
mpl.rcParams['font.family'] = 'Times New Roman'
mpl.rcParams['font.sans-serif']      = ['Times New Roman', 'DejaVu Sans']
mpl.rcParams['mathtext.fontset']     = 'stix'
mpl.rcParams['axes.spines.top']      = False
mpl.rcParams['axes.spines.right']    = False
mpl.rcParams['axes.linewidth']       = 1.5
mpl.rcParams['xtick.major.width']    = 1.5
mpl.rcParams['ytick.major.width']    = 1.5
mpl.rcParams['xtick.labelsize']      = 12
mpl.rcParams['ytick.labelsize']      = 12

# ─── 路径 ─────────────────────────────────────────────────────────────────
BASE           = r"D:\system_folder\Desktop\Work On"
DATA_DIR       = os.path.join(BASE, "01_数据与计算", "Raw_Data", "MS_DATA")
AVG_FILE = os.path.join(BASE, "01_数据与计算", "Raw_Data", "原始fasta", "Result_AvsG")  # Anas→Gallus outfmt6
CVG_FILE = os.path.join(BASE, "01_数据与计算", "Raw_Data", "原始fasta", "Result_CvsG")  # Columba→Gallus outfmt6
OUT_DIR  = r"D:\system_folder\Desktop\Work On\02_可视化\Figure\png"
os.makedirs(OUT_DIR, exist_ok=True)
NOLEG = os.environ.get('NOLEG', '0') == '1'
_PAIR_PANEL = {
    ('Gallus', 'Columba'): 'Fig4H',
    ('Gallus', 'Anas'):    'Fig4I',
    ('Anas',   'Columba'): 'Fig4J',
}

# ─── 物种配置 ─────────────────────────────────────────────────────────────
PREF = {'Gallus': 'G', 'Anas': 'A', 'Columba': 'C'}

# ─── 目标蛋白（仅 Gallus accession）——comp 侧 accession 由 Blast 自动确定 ───
GALLUS_TARGETS = {
    'P01012':     'OVAL',
    'A0A8V0XA58': 'OC116',
    'A0A8V1A6Y9': 'TRFE',
}

TARGET_COLORS = {
    'OVAL':  '#C62828',
    'OC116': '#66A96B',
    'TRFE':  '#5A5A5A',
}
BACKGROUND_PROTEIN_COLOR = '#C7C7C7'
LABEL_GRAY = '#4A4A4A'

# ─── Blastp 过滤参数 ──────────────────────────────────────────────────────
EVALUE_CUTOFF = 1e-5
AVG_ID_CUTOFF = 0.40   # 跨鸟类同源蛋白标准阈值（Rost 1999）
MAX_ID_CUTOFF = 0.40   # HSP 数不一致时使用最高 identity

# ══════════════════════════════════════════════════════════════════════════
# 数据加载工具
# ══════════════════════════════════════════════════════════════════════════

def get_int_cols(df, sp):
    cols = [c for c in df.columns if f'Intensity {PREF[sp]}' in c]
    return cols if cols else [c for c in df.columns if 'Intensity' in c]


def load_protein_by_acc(sp):
    """返回 {accession: mean_intensity}，过滤 Number Comparable>=2（若列存在）"""
    df = pd.read_excel(os.path.join(DATA_DIR, f"Protein_MS_{sp}.xlsx"),
                       sheet_name='Protein_quant')
    if 'Number Comparable' in df.columns:
        df = df[df['Number Comparable'] >= 2].copy()
    ic = get_int_cols(df, sp)
    df['prot_mean'] = df[ic].replace(0, np.nan).mean(axis=1)
    df = df[df['prot_mean'] > 0]
    return df.set_index('Protein accession')['prot_mean']


def load_glycan_by_acc(sp):
    """返回 {accession: summed mean site intensity}"""
    df = pd.read_excel(os.path.join(DATA_DIR, f"Glycan_MS_{sp}.xlsx"),
                       sheet_name='Site_quant')
    ic = get_int_cols(df, sp)
    df['glyc_mean'] = df[ic].replace(0, np.nan).mean(axis=1)
    df = df[df['glyc_mean'] > 0]
    return df.groupby('Protein accession')['glyc_mean'].sum()


def derive_label(gene, desc):
    """
    从基因名或蛋白描述中派生简短标签。
    优先基因名；若缺失（'--' 或空），从描述文字中提取缩写。
    """
    gene = str(gene).strip()
    if gene and gene not in ('--', '-', 'nan') and len(gene) <= 14:
        return gene

    core = str(desc).split(' OS=')[0].strip()
    if not core or core == 'nan':
        return ''

    # Very short names: use directly
    if len(core) <= 9 and ' ' not in core:
        return core

    # Words to skip when building abbreviation
    SKIP = {
        'and', 'or', 'of', 'the', 'a', 'an', 'in', 'to', 'for',
        'domain', 'containing', 'like', 'related', 'binding', 'protein',
        'chain', 'family', 'member', 'type', 'subunit', 'associated',
        'dependent', 'specific', 'mediated', 'factor', 'activating',
    }
    PREFIX = {'Alpha': 'A', 'Beta': 'B', 'Gamma': 'G', 'Delta': 'D'}

    parts = []
    for w in core.split():
        w2 = w.strip('(),[]/-')
        if not w2:
            continue
        wl = w2.lower()
        if wl in SKIP:
            continue
        mapped = PREFIX.get(w2)
        if mapped:
            parts.append(mapped)
        else:
            parts.append(w2[:4] if len(w2) > 4 else w2)
        if len(''.join(parts)) >= 7:
            break

    result = ''.join(parts)
    return result[:10] if result else core[:8]


def load_gene_names(sp):
    """返回 {accession: label}，优先基因名，缺失时从蛋白描述派生缩写"""
    df = pd.read_excel(os.path.join(DATA_DIR, f"Protein_MS_{sp}.xlsx"),
                       sheet_name='Protein_quant')
    labels = {}
    for _, row in df.iterrows():
        acc  = row['Protein accession']
        gene = str(row.get('Gene name', '')).strip()
        desc = str(row.get('Protein description', '')).strip()
        labels[acc] = derive_label(gene, desc)
    return labels


# ══════════════════════════════════════════════════════════════════════════
# 背景蛋白映射构建
# ══════════════════════════════════════════════════════════════════════════

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


def build_blastp_background(blastp_file, prot_ref, prot_comp, glyc_ref, glyc_comp,
                             target_accs):
    """
    Blastp 表格文件(列格式：QueryID=comp, SubjectDefID=ref) → {comp_acc: ref_acc}
    仅保留通过过滤且四项数据均完整、且非目标蛋白的对。
    """
    raw = pd.read_csv(blastp_file, sep='\t')
    raw['comp_acc'] = raw['QueryID'].apply(extract_acc)
    raw['ref_acc']  = raw['SubjectDefID'].apply(extract_acc)

    recs = []
    for (ca, ra), grp in raw.groupby(['comp_acc', 'ref_acc']):
        q_hsp = count_nonoverlap(grp['QueryStart'],   grp['QueryEnd'])
        s_hsp = count_nonoverlap(grp['SubjectStart'],  grp['SubjectEnd'])
        mean_e = grp['E-value'].mean()
        max_id = grp['Identity'].max()  / 100.0
        avg_id = grp['Identity'].mean() / 100.0
        recs.append({'comp_acc': ca, 'ref_acc': ra,
                     'mean_evalue': mean_e, 'max_identity': max_id,
                     'avg_identity': avg_id, 'q_hsp': q_hsp, 's_hsp': s_hsp,
                     'max_bitscore': grp['BitScore'].max()})

    agg = pd.DataFrame(recs)

    def passes(row):
        if row['mean_evalue'] > EVALUE_CUTOFF: return False
        if row['q_hsp'] != row['s_hsp']:       return row['max_identity'] >= MAX_ID_CUTOFF
        return row['avg_identity'] >= AVG_ID_CUTOFF

    agg['pass'] = agg.apply(passes, axis=1)
    best = (agg[agg['pass']]
            .sort_values('max_bitscore', ascending=False)
            .drop_duplicates('comp_acc').reset_index(drop=True))

    bg = {}
    for _, row in best.iterrows():
        ca, ra = row['comp_acc'], row['ref_acc']
        if ca in target_accs or ra in target_accs: continue
        if (ra not in prot_ref or ca not in prot_comp or
            ra not in glyc_ref or ca not in glyc_comp): continue
        bg[ca] = ra
    return bg


def build_ortho_background(sp_ref, sp_comp, prot_ref, prot_comp, glyc_ref, glyc_comp,
                            target_accs):
    """
    Orthogroups 文件 → {comp_acc: ref_acc}
    从每个含两种物种成员的 orthogroup 中选取各有一个完整数据的代表蛋白。
    """
    bg = {}
    used_ref = set()
    with open(ORTHO_FILE, encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            sp_members = defaultdict(list)
            for token in re.split(r'\s+', line):
                if '|' in token:
                    sp, acc = token.split('|', 1)
                    sp_members[sp].append(acc)

            ref_cands  = [a for a in sp_members.get(sp_ref,  [])
                          if a not in target_accs and a in prot_ref and a in glyc_ref]
            comp_cands = [a for a in sp_members.get(sp_comp, [])
                          if a not in target_accs and a in prot_comp and a in glyc_comp]

            if not ref_cands or not comp_cands: continue

            ra = max(ref_cands,  key=lambda a: float(prot_ref[a]))
            ca = max(comp_cands, key=lambda a: float(prot_comp[a]))

            if ra in used_ref: continue
            bg[ca] = ra
            used_ref.add(ra)
    return bg


def _parse_tabular6(path):
    """
    解析标准 blastp outfmt 6 文件（无 header，列：
    qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore [...]
    返回 DataFrame，comp_acc = query, ref_acc = subject
    """
    cols = ['qseqid', 'sseqid', 'pident', 'length', 'mismatch', 'gapopen',
            'qstart', 'qend', 'sstart', 'send', 'evalue', 'bitscore']
    df = pd.read_csv(path, sep='\t', header=None, names=cols,
                     usecols=range(12))  # 忽略多余列
    df['comp_acc'] = df['qseqid'].apply(extract_acc)
    df['ref_acc']  = df['sseqid'].apply(extract_acc)
    df['Identity'] = df['pident']
    df['E-value']  = df['evalue']
    df['BitScore'] = df['bitscore']
    df['QueryStart']   = df['qstart']
    df['QueryEnd']     = df['qend']
    df['SubjectStart'] = df['sstart']
    df['SubjectEnd']   = df['send']
    return df


def _agg_tabular(df):
    """将 tabular6 DataFrame 聚合为 per-pair 统计，应用相同筛选后返回 best hit。"""
    recs = []
    for (ca, ra), grp in df.groupby(['comp_acc', 'ref_acc']):
        q_hsp = count_nonoverlap(grp['QueryStart'],   grp['QueryEnd'])
        s_hsp = count_nonoverlap(grp['SubjectStart'],  grp['SubjectEnd'])
        mean_e = grp['E-value'].mean()
        max_id = grp['Identity'].max() / 100.0
        avg_id = grp['Identity'].mean() / 100.0
        recs.append({'comp_acc': ca, 'ref_acc': ra,
                     'mean_evalue': mean_e, 'max_identity': max_id,
                     'avg_identity': avg_id, 'q_hsp': q_hsp, 's_hsp': s_hsp,
                     'max_bitscore': grp['BitScore'].max()})
    agg = pd.DataFrame(recs)

    def passes(row):
        if row['mean_evalue'] > EVALUE_CUTOFF: return False
        if row['q_hsp'] != row['s_hsp']:       return row['max_identity'] >= MAX_ID_CUTOFF
        return row['avg_identity'] >= AVG_ID_CUTOFF

    agg['pass'] = agg.apply(passes, axis=1)
    return (agg[agg['pass']]
            .sort_values('max_bitscore', ascending=False)
            .drop_duplicates('comp_acc')
            .reset_index(drop=True))


def build_blastp_tabular_background(tabular_file, prot_ref, prot_comp,
                                     glyc_ref, glyc_comp):
    """
    解析 outfmt6 tabular blastp（comp→Gallus）→ {comp_acc: ref_acc}
    包含所有造过过滤的对（含目标蛋白）。
    """
    df   = _parse_tabular6(tabular_file)
    best = _agg_tabular(df)
    bg   = {}
    for _, row in best.iterrows():
        ca, ra = row['comp_acc'], row['ref_acc']
        if (ra not in prot_ref or ca not in prot_comp or
                ra not in glyc_ref or ca not in glyc_comp): continue
        bg[ca] = ra    # comp(Anas/Columba) → ref(Gallus)
    return bg


def build_blast_bridge_tabular(avg_file, cvg_file,
                                prot_anas, prot_colum,
                                glyc_anas, glyc_colum):
    """
    AvsC 桥接：
    avg_file: Anas→Gallus outfmt6
    cvg_file: Columba→Gallus outfmt6
    通过共同 Gallus 直系同源建立 Anas↔Columba 对。
    返回 ({colum_acc: anas_acc}, gallus_to_anas).
    """
    avg_df   = _parse_tabular6(avg_file)
    cvg_df   = _parse_tabular6(cvg_file)
    avg_best = _agg_tabular(avg_df)
    cvg_best = _agg_tabular(cvg_df)

    # Gallus → best Anas hit
    gallus_to_anas = {}
    for _, row in avg_best.iterrows():
        ga_acc = row['ref_acc']   # Gallus
        aa     = row['comp_acc']  # Anas
        if aa not in prot_anas or aa not in glyc_anas: continue
        if ga_acc not in gallus_to_anas:
            gallus_to_anas[ga_acc] = aa

    bg = {}
    used_anas = set()
    for _, row in cvg_best.iterrows():
        ga_acc = row['ref_acc']    # Gallus
        ca     = row['comp_acc']   # Columba
        if ca not in prot_colum or ca not in glyc_colum: continue
        aa = gallus_to_anas.get(ga_acc)
        if aa is None or aa in used_anas: continue
        bg[ca] = aa    # Columba → Anas
        used_anas.add(aa)
    return bg, gallus_to_anas


def load_blast_xlsx(path):
    """
    读取 TBtools 格式 Blast 结果 xlsx，返回标准化 DataFrame。
    Query = comp 物种，Subject = Gallus (ref)。
    """
    df = pd.read_excel(path)
    df = df.dropna(how='all').reset_index(drop=True)

    # 提取 comp accession（query）
    if 'Unnamed: 1' in df.columns and df['Unnamed: 1'].notna().sum() > 0:
        df['comp_acc'] = df['Unnamed: 1'].astype(str).str.strip()
    else:
        df['comp_acc'] = df['Query_def'].apply(extract_acc)

    # 提取 ref accession（subject = Gallus）
    if 'Unnamed: 5' in df.columns and df['Unnamed: 5'].notna().sum() > 0:
        df['ref_acc'] = df['Unnamed: 5'].astype(str).str.strip()
    else:
        df['ref_acc'] = df['Subject_def'].apply(extract_acc)

    df = df.rename(columns={
        'Subject_Mean_evalue':           'mean_evalue',
        'Max_Identity':                  'max_identity',
        'Query_NonOverlapped_Hsp_Num':   'q_hsp',
        'Subject_NonOverlapped_Hsp_Num': 's_hsp',
        'Max_BitScore':                  'max_bitscore',
    })
    if '平均Identity' in df.columns:
        df['avg_identity'] = df['平均Identity']
    else:
        df['avg_identity'] = df['max_identity']

    keep = ['comp_acc', 'ref_acc', 'mean_evalue', 'max_identity',
            'avg_identity', 'q_hsp', 's_hsp', 'max_bitscore']
    return df[keep].dropna(subset=['comp_acc', 'ref_acc'])


def _blast_filter(df):
    """应用统一的 evalue / identity 过滤，返回每个 comp_acc 的最佳 hit。"""
    def passes(row):
        if float(row['mean_evalue']) > EVALUE_CUTOFF:  return False
        if int(row['q_hsp']) != int(row['s_hsp']):     return float(row['max_identity']) >= MAX_ID_CUTOFF
        return float(row['avg_identity']) >= AVG_ID_CUTOFF
    df = df.copy()
    df['pass'] = df.apply(passes, axis=1)
    return (df[df['pass']]
            .sort_values('max_bitscore', ascending=False)
            .drop_duplicates('comp_acc')
            .reset_index(drop=True))


def build_blast_xlsx_background(result_xlsx, prot_ref, prot_comp,
                                 glyc_ref, glyc_comp, target_accs):
    """
    读取 TBtools xlsx Blast 结果 (comp→Gallus) → {comp_acc: ref_acc}
    用于 GvsA（GA_RESULT.xlsx: Anas→Gallus）。
    """
    df   = load_blast_xlsx(result_xlsx)
    best = _blast_filter(df)
    bg   = {}
    for _, row in best.iterrows():
        ca, ra = row['comp_acc'], row['ref_acc']
        if ca in target_accs or ra in target_accs: continue
        if (ra not in prot_ref or ca not in prot_comp or
                ra not in glyc_ref or ca not in glyc_comp): continue
        bg[ca] = ra
    return bg


def build_blast_bridge_background(ga_xlsx, gc_xlsx,
                                   prot_anas, prot_colum,
                                   glyc_anas, glyc_colum, target_accs):
    """
    AvsC 桥接：Anas→Gallus (GA_RESULT) ＋ Columba→Gallus (GC_RESULT)
    通过共同的 Gallus 直系同源蛋白建立 Anas↔Columba 对应关系。
    返回 {colum_acc: anas_acc}。
    """
    ga_df = load_blast_xlsx(ga_xlsx)  # comp=Anas,   ref=Gallus
    gc_df = load_blast_xlsx(gc_xlsx)  # comp=Columba, ref=Gallus

    ga_best = _blast_filter(ga_df)
    gc_best = _blast_filter(gc_df)

    # 建立 Gallus → Anas 映射（每个 Gallus 蛋白取最佳 Anas hit）
    gallus_to_anas = {}
    for _, row in ga_best.iterrows():
        ga_acc = row['ref_acc']   # Gallus
        aa     = row['comp_acc']  # Anas
        if aa in target_accs or ga_acc in target_accs: continue
        if aa not in prot_anas or aa not in glyc_anas:  continue
        if ga_acc not in gallus_to_anas:
            gallus_to_anas[ga_acc] = aa

    # 遍历 Columba→Gallus，通过 Gallus 桥接到 Anas
    bg = {}
    used_anas = set()
    for _, row in gc_best.iterrows():
        ga_acc = row['ref_acc']    # Gallus
        ca     = row['comp_acc']   # Columba
        if ca in target_accs: continue
        if ca not in prot_colum or ca not in glyc_colum: continue
        aa = gallus_to_anas.get(ga_acc)
        if aa is None or aa in used_anas: continue
        bg[ca] = aa    # Columba → Anas
        used_anas.add(aa)
    return bg


# ══════════════════════════════════════════════════════════════════════════
# 绘图函数
# ══════════════════════════════════════════════════════════════════════════

def plot_2d_enrichment(sp_ref, sp_comp):
    print(f"\n{'='*60}")
    print(f"  {sp_ref} vs {sp_comp}")
    print(f"{'='*60}")

    prot_ref  = load_protein_by_acc(sp_ref)
    prot_comp = load_protein_by_acc(sp_comp)
    glyc_ref  = load_glycan_by_acc(sp_ref)
    glyc_comp = load_glycan_by_acc(sp_comp)
    acc2gene  = load_gene_names(sp_ref)

    # ── 背景蛋白映射（所有通过 Blast 过滤的对，含目标蛋白）──────────────
    gallus_to_anas = {}   # 仅 AvsC 时使用
    if (sp_ref, sp_comp) == ('Gallus', 'Columba'):
        print(f"  Building background from Blastp (CvsG): {CVG_FILE}")
        bg_map = build_blastp_tabular_background(CVG_FILE,
                                                  prot_ref, prot_comp,
                                                  glyc_ref, glyc_comp)
    elif (sp_ref, sp_comp) == ('Gallus', 'Anas'):
        print(f"  Building background from Blastp (AvsG): {AVG_FILE}")
        bg_map = build_blastp_tabular_background(AVG_FILE,
                                                  prot_ref, prot_comp,
                                                  glyc_ref, glyc_comp)
    else:  # Anas vs Columba
        print(f"  Building background via Blast bridge (AvsG + CvsG through Gallus)")
        bg_map, gallus_to_anas = build_blast_bridge_tabular(AVG_FILE, CVG_FILE,
                                                             prot_ref, prot_comp,
                                                             glyc_ref, glyc_comp)

    # ── 目标 Anas accession（AvsC 时 ref=Anas，需从 Gallus→Anas 映射推算）──
    anas_targets = {}  # {anas_acc: target_name}，仅 AvsC 时填充
    if gallus_to_anas:
        for g_acc, tname in GALLUS_TARGETS.items():
            a_acc = gallus_to_anas.get(g_acc)
            if a_acc:
                anas_targets[a_acc] = tname

    print(f"  Background pairs (data-complete): {len(bg_map)}")

    # ── 计算 log2FC ───────────────────────────────────────────────────────
    records = []
    labeled_targets = set()   # 每个 target 只标记最佳命中（最高 bitscore）
    for comp_a, ref_a in bg_map.items():
        prot_fc = np.log2(prot_ref[ref_a])  - np.log2(prot_comp[comp_a])
        glyc_fc = np.log2(glyc_ref[ref_a])  - np.log2(glyc_comp[comp_a])
        # 判断是否为目标蛋白
        if gallus_to_anas:
            # AvsC: ref=Anas
            tname = anas_targets.get(ref_a)
        else:
            # GvsC / GvsA: ref=Gallus
            tname = GALLUS_TARGETS.get(ref_a)
        # 若同名 target 已在图上则降级为背景（保留最高 bitscore 的那个）
        if tname:
            if tname in labeled_targets:
                tname = None
            else:
                labeled_targets.add(tname)
                print(f"  {tname}: prot_FC={prot_fc:.2f}  glyc_FC={glyc_fc:.2f}")
        records.append({'Gene': ref_a, 'ref_acc': ref_a, 'comp_acc': comp_a,
                        'prot_log2FC': prot_fc, 'glyc_log2FC': glyc_fc,
                        'target': tname})

    df = pd.DataFrame(records)
    n_targets = df['target'].notna().sum()
    print(f"  Total: {len(df)} points  ({len(df) - n_targets} bg + {n_targets} targets)")

    if df.empty:
        print("  No data — skipping plot.")
        return

    # ── 坐标范围 ──────────────────────────────────────────────────────────
    vals = pd.concat([df['prot_log2FC'], df['glyc_log2FC']])
    pad  = (vals.max() - vals.min()) * 0.22
    vmin, vmax = vals.min() - pad, vals.max() + pad

    # ── 画布 ──────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(7.5, 7.0))
    ax  = fig.add_axes([0.13, 0.11, 0.82, 0.80])

    # 参考线
    ax.plot([vmin, vmax], [vmin, vmax], '--', color='#666666', lw=1.6, zorder=3, alpha=0.7)
    ax.axhline(0, color='#BBBBBB', lw=0.9, linestyle=':', zorder=2)
    ax.axvline(0, color='#BBBBBB', lw=0.9, linestyle=':', zorder=2)

    # 背景蛋白 — 只绘点，不标注
    bg_df = df[df['target'].isna()].copy()

    texts = []
    for _, row in bg_df.iterrows():
        ax.scatter(row['prot_log2FC'], row['glyc_log2FC'],
                   c=BACKGROUND_PROTEIN_COLOR, s=55, zorder=4, linewidths=0,
                   edgecolors='none', alpha=0.85)

    # 目标蛋白
    TARGET_ANNOT = {
        'OVAL':  {'dx': -55, 'dy': -15, 'ha': 'right', 'no_arrow': False},
        'OC116': {'dx': -90, 'dy': -18, 'ha': 'right', 'no_arrow': False},
        'TRFE':  {'dx': -90, 'dy': -46, 'ha': 'right', 'no_arrow': False},
    }
    # Pair-specific label position overrides
    if (sp_ref, sp_comp) == ('Gallus', 'Columba'):
        TARGET_ANNOT['TRFE']  = {'dx': -12, 'dy':   0, 'ha': 'right', 'no_arrow': True}
        TARGET_ANNOT['OVAL']  = {'dx': -12, 'dy': -18, 'ha': 'right', 'no_arrow': True}
        TARGET_ANNOT['OC116'] = {'dx':  12, 'dy':   0, 'ha': 'left',  'no_arrow': True}
    if (sp_ref, sp_comp) == ('Gallus', 'Anas'):
        TARGET_ANNOT['TRFE']  = {'dx': -12, 'dy':   0, 'ha': 'right', 'no_arrow': True}
        TARGET_ANNOT['OVAL']  = {'dx':  12, 'dy':   0, 'ha': 'left',  'no_arrow': True}
        TARGET_ANNOT['OC116'] = {'dx':  12, 'dy':   0, 'ha': 'left',  'no_arrow': True}
    if (sp_ref, sp_comp) == ('Anas', 'Columba'):
        TARGET_ANNOT['OC116'] = {'dx': -12, 'dy':   0, 'ha': 'right', 'no_arrow': True}
        TARGET_ANNOT['OVAL']  = {'dx': -12, 'dy':   0, 'ha': 'right', 'no_arrow': True}
        TARGET_ANNOT['TRFE']  = {'dx':  30, 'dy':   0, 'ha': 'left',  'no_arrow': True}
    for pname, color in TARGET_COLORS.items():
        sub = df[df['target'] == pname]
        if sub.empty: continue
        row = sub.iloc[0]
        if pname == 'OVAL':
            ax.text(row['prot_log2FC'], row['glyc_log2FC'], '⭐',
                    color=color, ha='center', va='center', fontsize=17,
                    zorder=7, fontfamily='Segoe UI Emoji')
        else:
            ax.scatter(row['prot_log2FC'], row['glyc_log2FC'],
                       c=color, s=170, zorder=6, linewidths=0, edgecolors='none', alpha=0.92)
        cfg = TARGET_ANNOT.get(pname, {'dx': 40, 'dy': 20})
        annot_kw = dict(
            xy=(row['prot_log2FC'], row['glyc_log2FC']),
            xytext=(cfg['dx'], cfg['dy']), textcoords='offset points',
            fontsize=8.5, color=color if pname == 'OVAL' else LABEL_GRAY,
            ha=cfg.get('ha', 'right'), va='center',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='white',
                      edgecolor=color if pname == 'OVAL' else LABEL_GRAY,
                      linewidth=1.0, alpha=0.92),
        )
        if not cfg.get('no_arrow', False):
            annot_kw['arrowprops'] = dict(arrowstyle='->', color=color, lw=1.2,
                                          shrinkA=0, shrinkB=5,
                                          connectionstyle='arc3,rad=0.08')
        ax.annotate(f"$\\bf{{{pname}}}$", **annot_kw)

    # Auto-adjust background labels to avoid overlap
    if texts:
        adjust_text(texts, ax=ax,
                    expand=(1.2, 1.4),
                    arrowprops=dict(arrowstyle='-', color='#AAAAAA', lw=0.5))

    # 象限文字
    ax.text(vmax - 0.3, vmin + 0.4, f'Glycan suppressed\nin {sp_ref}',
            fontsize=7.5, color='#C0392B', ha='right', va='bottom',
            style='italic', alpha=0.75)
    ax.text(vmin + 0.3, vmax - 0.4, f'Glycan enriched\nin {sp_ref}',
            fontsize=7.5, color='#1565C0', ha='left', va='top',
            style='italic', alpha=0.75)

    # 坐标轴
    ax.set_xlabel(f'Protein  $\\log_2$FC  ({sp_ref} / {sp_comp})',
                  fontsize=12, fontweight='bold', labelpad=6)
    ax.set_ylabel(f'Glycan  $\\log_2$FC  ({sp_ref} / {sp_comp})',
                  fontsize=12, fontweight='bold', labelpad=6)
    ax.set_xlim(vmin, vmax)
    ax.set_ylim(vmin, vmax)
    ax.set_aspect('equal')
    ax.tick_params(labelsize=10)
    ax.spines['left'].set_linewidth(1.4)
    ax.spines['bottom'].set_linewidth(1.4)

    # 标题
    fig.text(0.42, 0.96,
             f'2D Glycan–Protein Enrichment  ({sp_ref} vs {sp_comp})',
             ha='center', va='top', fontsize=13, fontweight='bold', color='#222222')

    _panel = _PAIR_PANEL.get((sp_ref, sp_comp), f'Fig4_{sp_ref}_{sp_comp}')
    save_fig(plt.gcf(), _panel)
    plt.close()


# ══════════════════════════════════════════════════════════════════════════
# 主程序：生成三张图
# ══════════════════════════════════════════════════════════════════════════
def make_legend():
    """生成 Fig4H-J 独立图例，风格与 Fig4A-C 一致"""
    import matplotlib.lines as mlines
    import matplotlib.patches as mpatches

    fig, ax = plt.subplots(figsize=(2.8, 2.2))
    ax.set_visible(False)

    # 构造与 Fig4A-C 相同风格的 legend handles
    handle_bg = plt.scatter([], [], color=BACKGROUND_PROTEIN_COLOR, s=80, edgecolor='none',
                            linewidth=0.5, label='Other Proteins')
    handles = [handle_bg]
    handles.append(mpl.lines.Line2D([], [], marker='$⭐$', linestyle='None',
                                    color=TARGET_COLORS['OVAL'], markersize=16,
                                    label='OVAL'))
    for pname in ['OC116', 'TRFE']:
        handles.append(plt.scatter([], [], color=TARGET_COLORS[pname], s=170,
                                   edgecolor='none', linewidth=0, label=pname))

    leg = fig.legend(
        handles=handles,
        loc='center',
        frameon=True,
        fontsize=12,
        edgecolor='#CCCCCC',
        title='Highlighted Proteins',
        title_fontsize=13,
    )
    leg.get_frame().set_linewidth(1.0)

    plt.tight_layout(pad=0.3)
    save_fig(fig, 'Fig4H-J_Legend')
    plt.close()


if __name__ == '__main__':
    for sp_ref, sp_comp in [('Gallus', 'Columba'),
                             ('Gallus', 'Anas'),
                             ('Anas',   'Columba')]:
        plot_2d_enrichment(sp_ref, sp_comp)

    make_legend()
    print("\nAll done.")
