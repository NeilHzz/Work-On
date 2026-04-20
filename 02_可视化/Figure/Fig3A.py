"""
三物种糖蛋白 OrthoFinder 聚类 + 糖型分类网络可视化
======================================================
布局说明
  - 中心同心圆：三物种共同表达蛋白（GAC），共 7 圈，等间距 0.42
  - 内圈扇形：单物种蛋白，弧行排列
  - 外圈扇形：双物种蛋白，弧行排列
  - 最外圈：7 种糖型节点，均匀分布在 R_GLYCAN=9.6 圆上
节点颜色
  - GAC：自定义渐变 #D6E2E2→#73A5A2→#4C7780，cluster_size 越大越深
  - 单物种：菱形，物种代表色
  - 双物种：圆形，物种混合色
  - 糖型：coolwarm，连接蛋白数越多越红
"""

# ── 依赖库（仅保留实际使用的部分） ──────────────────────────────
import os, re, math, warnings
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _save import save_fig
from collections import defaultdict

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
from matplotlib.patches import Wedge

warnings.filterwarnings("ignore")
matplotlib.rcParams['font.family'] = 'Times New Roman'
matplotlib.rcParams['font.sans-serif'] = ['Times New Roman', 'DejaVu Sans']
matplotlib.rcParams['mathtext.fontset'] = 'stix'

# ── 工作目录 ────────────────────────────────────────────────────
BASE = r"D:\system_folder\Desktop\Work On"

# ══════════════════════════════════════════════════════════════════
# STEP 1  读取 OrthoFinder 聚类结果
#   每行为一个 orthogroup，token 格式 "物种|蛋白accession"
# ══════════════════════════════════════════════════════════════════
def parse_orthogroups(path):
    """将 Orthogroups.txt 解析为 list[set[str]]，每个元素是一行 token 集合"""
    groups = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                groups.append(set(re.split(r"\s+", line)))
    return groups

# ══════════════════════════════════════════════════════════════════
# STEP 2  从各物种糖蛋白 FASTA 中提取 accession 集合
#   FASTA header 格式：>sp|ACCESSION|... 或 >ACCESSION ...
# ══════════════════════════════════════════════════════════════════
def load_gly_ids(fasta_path):
    """返回 FASTA 文件中所有蛋白 accession 的集合"""
    ids = set()
    with open(fasta_path, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.startswith(">"):
                acc = line.split("|")[1].strip() if "|" in line else line[1:].split()[0].strip()
                ids.add(acc)
    return ids

# 三物种糖蛋白 accession 集合（用于判断某蛋白是否为糖蛋白）
gly_ids = {
    "Gallus":  load_gly_ids(os.path.join(BASE, "01_数据与计算", "Raw_Data", "原始fasta", "GlyGallus.fasta")),
    "Anas":    load_gly_ids(os.path.join(BASE, "01_数据与计算", "Raw_Data", "原始fasta", "GlyAnas.fasta")),
    "Columba": load_gly_ids(os.path.join(BASE, "01_数据与计算", "Raw_Data", "原始fasta", "GlyColumba.fasta")),
}
print(f"糖蛋白  Gallus={len(gly_ids['Gallus'])}  Anas={len(gly_ids['Anas'])}  Columba={len(gly_ids['Columba'])}")

# ══════════════════════════════════════════════════════════════════
# STEP 3  构建蛋白属性字典
#   protein_info[acc] = {species, cluster_size, cluster_type, sp_set}
#   cluster_type: "three"/"two"/"one"（聚类中物种数）或 "singleton"（未聚类）
#   cluster_size: 聚类内所有蛋白数量（反映保守程度）
# ══════════════════════════════════════════════════════════════════
ortho_path = os.path.join(BASE, "01_数据与计算", "同源糖型蛋白圆环大图", "Orthogroups.txt.gz.txt")
groups = parse_orthogroups(ortho_path)

protein_info  = {}   # acc → 属性字典
clustered_ids = set()

for grp in groups:
    # 按物种拆分 token
    sp_members = defaultdict(set)
    for token in grp:
        if "|" in token:
            sp, acc = token.split("|", 1)
            sp_members[sp].add(acc)
    sp_present = set(sp_members.keys())
    # 仅保留在糖蛋白列表中的成员
    gly_in_grp = {sp: sp_members[sp] & gly_ids[sp] for sp in sp_present}
    if sum(len(v) for v in gly_in_grp.values()) == 0:
        continue  # 该 orthogroup 中无糖蛋白，跳过
    ct           = {3: "three", 2: "two"}.get(len(sp_present), "one")
    cluster_size = sum(len(v) for v in sp_members.values())
    for sp, accs in gly_in_grp.items():
        for acc in accs:
            protein_info[acc] = {
                "species":      sp,
                "cluster_size": cluster_size,
                "cluster_type": ct,
                "sp_set":       frozenset(sp_present),
            }
            clustered_ids.add(acc)

# 未参与聚类的糖蛋白作为 singleton 处理
for sp, ids_set in gly_ids.items():
    for acc in ids_set:
        if acc not in clustered_ids:
            protein_info[acc] = {
                "species":      sp,
                "cluster_size": 1,
                "cluster_type": "singleton",
                "sp_set":       frozenset([sp]),
            }

print("蛋白分类:", {ct: sum(1 for v in protein_info.values() if v["cluster_type"] == ct)
                  for ct in ["three", "two", "one", "singleton"]})

# ══════════════════════════════════════════════════════════════════
# STEP 4  从质谱数据读取糖链信息
#   glycan_type_chains[gt]  : 每种糖型包含的糖链字符串集合（用于计数）
#   glycan_type_intensity[gt]: 各糖型 IGP 强度累计（备用，当前未参与绘图）
#   prot_to_gtypes[acc]     : 蛋白 accession → 出现的糖型集合
# ══════════════════════════════════════════════════════════════════
GLYCAN_TYPES_ORDER = [
    "High Mannose", "Pauci-mannose", "Hybrid",
    "Complex-Plain", "Complex-Fucosylated", "Complex-Sialylated", "Other",
]

def classify_glycan(g):
    """根据组成式将糖链归类到 7 种糖型之一"""
    comp = {}
    for k in ("HexNAc", "Hex", "Fuc", "NeuAc"):
        m = re.search(rf"{k}\((\d+)\)", g)
        comp[k] = int(m.group(1)) if m else 0
    h, m, f, s = comp["HexNAc"], comp["Hex"], comp["Fuc"], comp["NeuAc"]
    if h == 2 and m >= 5 and f == 0 and s == 0: return "High Mannose"
    if h <= 2 and m <= 4:                        return "Pauci-mannose"
    if h == 3 and m >= 5:                        return "Hybrid"
    if h >= 3 and s >= 1:                        return "Complex-Sialylated"
    if h >= 3 and f >= 1 and s == 0:             return "Complex-Fucosylated"
    if h >= 3 and f == 0 and s == 0:             return "Complex-Plain"
    return "Other"

# 各物种 IGP 强度列名
IGP_INT = {
    "Gallus":  ["Intensity G1", "Intensity G2", "Intensity G3"],
    "Anas":    ["Intensity A1", "Intensity A2", "Intensity A3"],
    "Columba": ["Intensity C1", "Intensity C2", "Intensity C3"],
}

glycan_type_intensity = defaultdict(float)   # 各糖型强度累计（备用）
glycan_type_chains    = defaultdict(set)     # 各糖型糖链字符串集合
prot_to_gtypes        = defaultdict(set)     # 蛋白 → 糖型集合
acc_species           = {}                  # 蛋白 accession → 物种名

MS_FILES = {
    "Gallus":  os.path.join(BASE, "01_数据与计算", "Raw_Data", "MS_DATA", "Glycan_MS_Gallus.xlsx"),
    "Anas":    os.path.join(BASE, "01_数据与计算", "Raw_Data", "MS_DATA", "Glycan_MS_Anas.xlsx"),
    "Columba": os.path.join(BASE, "01_数据与计算", "Raw_Data", "MS_DATA", "Glycan_MS_Columba.xlsx"),
}
for sp, fpath in MS_FILES.items():
    # IGP_quant 表：逐行读取蛋白-糖链对，累计强度
    df_igp   = pd.read_excel(fpath, sheet_name="IGP_quant")
    int_cols = [c for c in IGP_INT[sp] if c in df_igp.columns]
    for _, row in df_igp.iterrows():
        acc  = str(row["Protein accession"]).strip()
        gstr = str(row.get("Observed Modification", "")).strip()
        if not gstr or gstr == "nan":
            continue
        gt = classify_glycan(gstr)
        glycan_type_chains[gt].add(gstr)
        vals = pd.to_numeric(pd.Series([row[c] for c in int_cols]), errors="coerce")
        glycan_type_intensity[gt] += float(vals.mean()) if vals.notna().any() else 0.0
        prot_to_gtypes[acc].add(gt)
        acc_species[acc] = sp
    # Site_quant 表：仅记录蛋白-糖型关系（N-glycan modifications 列）
    df_site = pd.read_excel(fpath, sheet_name="Site_quant")
    if "N-glycan modifications" in df_site.columns:
        for _, row in df_site.iterrows():
            acc  = str(row["Protein accession"]).strip()
            mods = str(row.get("N-glycan modifications", ""))
            if mods in ("nan", ""):
                continue
            for entry in re.split(r";\s*", mods):
                entry = entry.strip()
                if entry:
                    gt = classify_glycan(entry)
                    glycan_type_chains[gt].add(entry)
                    prot_to_gtypes[acc].add(gt)

print("糖型链数:", {gt: len(glycan_type_chains[gt]) for gt in GLYCAN_TYPES_ORDER})

# 每种糖型连接的蛋白数（用于节点颜色和大小）
gt_prot_count = {
    gt: sum(1 for acc in prot_to_gtypes if gt in prot_to_gtypes[acc])
    for gt in GLYCAN_TYPES_ORDER
}

# 各糖型各物种蛋白数（用于外圈饼环）
_SP_RING_ORDER = ["Gallus", "Anas", "Columba"]
_SP_RING_COLOR = {"Gallus": "#B54664", "Anas": "#7895C1", "Columba": "#F0C284"}
gt_sp_prot_count = {
    gt: {sp: sum(1 for acc in prot_to_gtypes
                 if gt in prot_to_gtypes[acc] and acc_species.get(acc) == sp)
         for sp in _SP_RING_ORDER}
    for gt in GLYCAN_TYPES_ORDER
}

# 各物种在所有糖型上的蛋白数总和（每个物种跨所有糖型之和 = 360° 基准）
_sp_grand_total = {
    sp: sum(gt_sp_prot_count[gt][sp] for gt in GLYCAN_TYPES_ORDER)
    for sp in _SP_RING_ORDER
}

# ══════════════════════════════════════════════════════════════════
# STEP 5  筛选参与可视化的蛋白节点
#   条件：有糖链数据（在 prot_to_gtypes 中）且有聚类信息（在 protein_info 中）
# ══════════════════════════════════════════════════════════════════
prot_nodes = [acc for acc in prot_to_gtypes if acc in protein_info]
print(f"蛋白节点总数: {len(prot_nodes)}")

# ══════════════════════════════════════════════════════════════════
# STEP 6  布局参数
# ══════════════════════════════════════════════════════════════════
SPECIES_LIST = ["Gallus", "Anas", "Columba"]
_GAC = frozenset(["Gallus", "Anas", "Columba"])   # 三物种共同表达标识

# 三物种共同表达蛋白，按 cluster_size 降序（大 cluster 优先放内圈）
gac_prots = [
    acc for acc in prot_nodes
    if frozenset(s for s in protein_info[acc]["sp_set"] if s in SPECIES_LIST) == _GAC
]
gac_prots.sort(key=lambda a: (-protein_info[a]["cluster_size"], -len(prot_to_gtypes.get(a, []))))
print(f"三物种共同蛋白 (GAC): {len(gac_prots)} 个")

# 同心圆：7 圈，圆心为第 0 圈，半径等间距 0.42
RING_SPACING = 0.42   # 相邻节点最小间距（数据坐标单位）
RING_RADII   = [0, 0.42, 0.84, 1.26, 1.68, 2.10, 2.52]

def ring_cap(r):
    """按弧长计算该圈最多能放几个节点"""
    if r == 0:
        return 1
    return max(4, int(2 * math.pi * r / RING_SPACING))

caps = [ring_cap(r) for r in RING_RADII]
# 若总容量不足，自动扩充最外圈
if sum(caps) < len(gac_prots):
    caps[-1] += len(gac_prots) - sum(caps)
print(f"各圈容量: {caps}  共 {sum(caps)} 槽, GAC 蛋白 {len(gac_prots)} 个")

R_GLYCAN       = 9.6    # 糖型节点圆的半径
R_SECTOR_IN    = max(RING_RADII) + 0.55   # 单物种扇形内边界（紧接 GAC 外圈）
R_SECTOR_OUT_1 = 5.80   # 单物种扇形外边界
R_SECTOR_IN_2  = 6.40   # 双物种扇形内边界
R_SECTOR_OUT_2 = 10.00  # 双物种扇形外边界

# ══════════════════════════════════════════════════════════════════
# STEP 7  颜色方案
# ══════════════════════════════════════════════════════════════════
# GAC 蛋白：自定义渐变（cluster_size 越大颜色越深：#D6E2E2 → #73A5A2 → #4C7780）
from matplotlib.colors import LinearSegmentedColormap as _LSC
CMAP_GAC = _LSC.from_list("gac_custom", ["#D6E2E2", "#5B9198", "#1B4D59"])
sz_vals  = [protein_info[a]["cluster_size"] for a in gac_prots]
sz_min, sz_max = min(sz_vals), max(sz_vals)

# 糖型节点：自定义渐变（糖链数目越多越深：#E8F3FB → #317BB2，差异更大）
CMAP_GLYCAN = _LSC.from_list("glycan_custom", ["#9DC4DE", "#1A5C8E"])
_max_gpc    = max(gt_prot_count.values(), default=1)
_max_chain_cnt = max([len(glycan_type_chains[gt]) for gt in GLYCAN_TYPES_ORDER], default=1)

def glycan_node_color(gt):
    """根据该糖型修饰的蛋白数目，从浅到深取色（#9DC4DE → #1A5C8E）"""
    prot_cnt = gt_prot_count.get(gt, 0)
    v = prot_cnt / _max_gpc
    return CMAP_GLYCAN(v)  # 全范围映射，差异最大

# 固定节点大小 = Complex-Plain 对应半径
_FIXED_GLYCAN_R = 0.40 + (gt_prot_count.get("Complex-Plain", 0) / _max_gpc) * 0.90

def glycan_draw_radius(gt):
    """所有糖型节点大小统一（Complex-Plain 对应半径）"""
    return _FIXED_GLYCAN_R

# 各物种/组合的边框色（用于节点描边和背景色块）
SP_COLOR = {
    frozenset(["Gallus"]):            "#B54664",
    frozenset(["Anas"]):              "#7895C1",
    frozenset(["Columba"]):           "#F0C284",
    frozenset(["Gallus", "Anas"]):    "#682487",
    frozenset(["Anas", "Columba"]):   "#84BA42",
    frozenset(["Gallus", "Columba"]): "#D4563E",
}
# 各扇形背景填充色（物种代表色的淡化版）
SP_FACECOLOR = {
    frozenset(["Gallus"]):            "#B54664",
    frozenset(["Anas"]):              "#7895C1",
    frozenset(["Columba"]):           "#F0C284",
    frozenset(["Gallus", "Anas"]):    "#682487",
    frozenset(["Anas", "Columba"]):   "#84BA42",
    frozenset(["Gallus", "Columba"]): "#D4563E",
}

# ══════════════════════════════════════════════════════════════════
# STEP 8  蛋白节点坐标分配
# ══════════════════════════════════════════════════════════════════
pos_prot        = {}   # nid → (x, y)
ring_assignment = []   # (acc, ring_index, angle)，仅 GAC 蛋白
sector_prots    = {}   # frozenset(sp_set) → [(acc, r, angle)]

def clock_to_math(deg):
    """顺时针角度（0°=顶）→ 数学极坐标弧度（0=右，逆时针）"""
    return math.pi / 2 - math.radians(deg)

# ── 8A  GAC 同心圆 ────────────────────────────────────────────
# cluster_size 最大的蛋白居圆心，其余按降序依次向外排列
prot_idx = 0
for ring_i, (r, cap) in enumerate(zip(RING_RADII, caps)):
    batch = gac_prots[prot_idx: prot_idx + cap]
    prot_idx += cap
    n = len(batch)
    if n == 0:
        continue
    for j, acc in enumerate(batch):
        if r == 0:
            px, py, angle = 0.0, 0.0, 0.0
        else:
            angle  = -math.pi / 2 + 2 * math.pi * j / n   # 从顶部起顺时针
            px, py = r * math.cos(angle), r * math.sin(angle)
        nid = f"P|{acc}"
        pos_prot[nid] = (px, py)
        ring_assignment.append((acc, ring_i, angle if r > 0 else 0.0))

# ── 8B/8C  扇形弧行排列（单物种 & 双物种）────────────────────
ARC_SPACING = 0.36   # 同弧行相邻节点最小间距
ROW_SPACING = 0.44   # 相邻弧行径向间距

def fill_sector(sp_set, clk_start, clk_end, r_in, r_out):
    """
    将 sp_set 对应的蛋白按弧行填入 [r_in, r_out] x [clk_start, clk_end] 扇形。
    - 每行按弧长估算容量；若总量超出，追加到最外弧行之后的溢出行。
    - 结果写入 pos_prot 和 sector_prots。
    """
    sp_accs = [
        acc for acc in prot_nodes
        if frozenset(s for s in protein_info[acc]["sp_set"] if s in SPECIES_LIST) == sp_set
    ]
    sp_accs.sort(key=lambda a: (-protein_info[a]["cluster_size"], -len(prot_to_gtypes.get(a, []))))
    n_sp = len(sp_accs)
    print(f"  {'+'.join(sorted(sp_set))}: {n_sp} 个  [{clk_start} ~{clk_end} ]")

    a_start = clock_to_math(clk_start)
    a_end   = clock_to_math(clk_end)

    # 按径向从内到外预算每弧行容量
    arc_rows = []
    r = r_in
    while r <= r_out + 1e-6:
        arc_len = r * abs(a_start - a_end)
        arc_rows.append((r, max(1, int(arc_len / ARC_SPACING))))
        r += ROW_SPACING

    idx = 0
    row_assignments = []
    for r_row, cap_row in arc_rows:
        if idx >= n_sp:
            break
        batch = sp_accs[idx: idx + cap_row]
        idx  += cap_row
        n_b   = len(batch)
        for j, acc in enumerate(batch):
            frac  = j / max(n_b - 1, 1)
            angle = a_start + (a_end - a_start) * frac
            nid   = f"P|{acc}"
            pos_prot[nid] = (r_row * math.cos(angle), r_row * math.sin(angle))
            row_assignments.append((acc, r_row, angle))

    # 溢出：超出最外弧行的蛋白额外增加一行
    if idx < n_sp:
        r_extra   = (arc_rows[-1][0] + ROW_SPACING) if arc_rows else r_in
        remaining = sp_accs[idx:]
        n_rem     = len(remaining)
        for j, acc in enumerate(remaining):
            frac  = j / max(n_rem - 1, 1)
            angle = a_start + (a_end - a_start) * frac
            nid   = f"P|{acc}"
            pos_prot[nid] = (r_extra * math.cos(angle), r_extra * math.sin(angle))
            row_assignments.append((acc, r_extra, angle))

    sector_prots[frozenset(sp_set)] = row_assignments

# 单物种（内圈扇形，120° 三等分，各留 10° 间隔）
SECTOR_DEFS = [
    (frozenset(["Gallus"]),   20,  100, None),   # 鸡：顶部偏右
    (frozenset(["Anas"]),    110,  235, None),   # 鸭：左侧
    (frozenset(["Columba"]), 245,  370, None),   # 鸽：右侧（370=360+10 跨零度）
]
for sp_set, clk_start, clk_end, _ in SECTOR_DEFS:
    fill_sector(sp_set, clk_start, clk_end, R_SECTOR_IN, R_SECTOR_OUT_1)

# 双物种（外圈扇形，与单物种扇形径向错开）
SECTOR_DEFS_DUAL = [
    (frozenset(["Gallus", "Columba"]), 335, 415, None),   # 鸡鸽：跨顶（415=360+55）
    (frozenset(["Gallus", "Anas"]),     65, 145, None),   # 鸡鸭：右上
    (frozenset(["Anas", "Columba"]),   155, 325, None),   # 鸭鸽：左侧大扇形
]
for sp_set, clk_start, clk_end, _ in SECTOR_DEFS_DUAL:
    fill_sector(sp_set, clk_start, clk_end, R_SECTOR_IN_2, R_SECTOR_OUT_2)

print(f"坐标分配完成: {len(pos_prot)} 个蛋白节点")

# ══════════════════════════════════════════════════════════════════
# STEP 9  糖型节点坐标
#   按与 GAC 蛋白连接数降序，顺时针从顶部均匀排列在 R_GLYCAN 圆上
# ══════════════════════════════════════════════════════════════════
gac_accs_set = {a for a, _, _ in ring_assignment}

# 统计每种糖型与 GAC 蛋白的连接数（决定排列顺序）
gt_gac_count = {
    gt: sum(1 for a in gac_accs_set if gt in prot_to_gtypes.get(a, []))
    for gt in GLYCAN_TYPES_ORDER
}

# 仅保留有实际糖链数据的糖型，按 GAC 连接数降序排列
active_gtypes = [gt for gt in GLYCAN_TYPES_ORDER if len(glycan_type_chains[gt]) > 0]
active_gtypes.sort(key=lambda gt: -gt_gac_count[gt])

glyan_pos        = {}   # gt → (x, y)
glycan_node_list = []
for i, gt in enumerate(active_gtypes):
    # 顺时针从正上方开始，math_angle = pi/2 - 2pi*i/n
    angle = math.pi / 2 - 2 * math.pi * i / len(active_gtypes)
    glyan_pos[gt]    = (R_GLYCAN * math.cos(angle), R_GLYCAN * math.sin(angle))
    glycan_node_list.append(gt)

# ══════════════════════════════════════════════════════════════════
# STEP 10  绘图
# ══════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(24, 24))

# 统计蛋白的连接度（连接的糖型数量），用于动态设定节点大小
prot_degrees = [len(prot_to_gtypes.get(a, [])) for a in prot_nodes]
deg_min = min(prot_degrees) if prot_degrees else 1
deg_max = max(prot_degrees) if prot_degrees else 1

def get_prot_node_size(acc):
    """根据蛋白连接的糖链（糖型）数量确定节点大小（范围 50~250）"""
    d = len(prot_to_gtypes.get(acc, []))
    if deg_max <= deg_min:
        return 100
    return 50 + 200 * (d - deg_min) / (deg_max - deg_min)

ax.set_aspect("equal")
ax.axis("off")
fig.patch.set_facecolor("white")

# ── 10A  扇形背景色块 ─────────────────────────────────────────
# 背景角度比蛋白坐标角度各扩展 5°，使色块完整覆盖节点
# r_outer 固定上限 7.8，避免色块遮挡糖型节点（糖型节点内缘约 8.3）
def draw_sector_bg(ax, defs_list, r_in, r_out):
    """在 ax 上绘制各扇形的半透明背景 Wedge"""
    for sp_set, clk_start, clk_end, _ in defs_list:
        fc      = SP_FACECOLOR[sp_set]
        theta1  = 90 - clk_end    # matplotlib Wedge 逆时针角度（从 x 轴正方向算）
        theta2  = 90 - clk_start
        r_outer = min(r_out + 0.25, 7.8)
        width   = r_outer - (r_in - 0.2)
        wedge   = Wedge((0, 0), r_outer, theta1, theta2,
                        width=width, facecolor=fc, edgecolor="none",
                        alpha=0.25, zorder=0)
        ax.add_patch(wedge)

# 背景角度略宽于坐标角度，确保边缘节点不超出色块
SECTOR_DEFS_BG = [
    (frozenset(["Gallus"]),   15,  105, None),
    (frozenset(["Anas"]),    105,  240, None),
    (frozenset(["Columba"]), 240,  375, None),
]
SECTOR_DEFS_DUAL_BG = [
    (frozenset(["Gallus", "Columba"]), 330, 420, None),
    (frozenset(["Gallus", "Anas"]),     60, 150, None),
    (frozenset(["Anas", "Columba"]),   150, 330, None),
]
draw_sector_bg(ax, SECTOR_DEFS_BG,      R_SECTOR_IN,   R_SECTOR_OUT_1)
draw_sector_bg(ax, SECTOR_DEFS_DUAL_BG, R_SECTOR_IN_2, R_SECTOR_OUT_2)

# ── 10B  蛋白 → 糖型连线 ─────────────────────────────────────
# 所有连线统一灰色，低透明度，避免视觉拥挤
# GAC 蛋白连线
for acc, _, _ in ring_assignment:
    if acc not in prot_to_gtypes:
        continue
    nid = f"P|{acc}"
    if nid not in pos_prot:
        continue
    px, py = pos_prot[nid]
    for gt in prot_to_gtypes[acc]:
        if gt not in glyan_pos:
            continue
        gx, gy = glyan_pos[gt]
        ax.plot([px, gx], [py, gy], color="#999999", alpha=0.05, linewidth=1.5, zorder=1)

# 扇形蛋白（单物种 + 双物种）连线
for acc in (a for rows in sector_prots.values() for a, _, _ in rows):
    if acc not in prot_to_gtypes:
        continue
    nid = f"P|{acc}"
    if nid not in pos_prot:
        continue
    px, py = pos_prot[nid]
    for gt in prot_to_gtypes[acc]:
        if gt not in glyan_pos:
            continue
        gx, gy = glyan_pos[gt]
        ax.plot([px, gx], [py, gy], color="#999999", alpha=0.05, linewidth=1.5, zorder=1)

# ── 10C  GAC 蛋白节点 ─────────────────────────────────────────
# RdYlBu_r 配色，cluster_size 大小决定颜色；细黑描边
for acc, _, _ in ring_assignment:
    nid = f"P|{acc}"
    px, py = pos_prot[nid]
    sz = protein_info[acc]["cluster_size"]
    v  = (sz - sz_min) / (sz_max - sz_min + 1e-9)
    c  = CMAP_GAC(v)
    ns = get_prot_node_size(acc)
    ax.scatter(px, py, s=ns, c=[c],
               edgecolors="#444444", linewidths=0.5, zorder=4)

# 圆心节点单独绘制（cluster_size 最大，位于 (0,0)）
center_acc = gac_prots[0]
center_v   = (protein_info[center_acc]["cluster_size"] - sz_min) / (sz_max - sz_min + 1e-9)
ns_cen     = get_prot_node_size(center_acc)
ax.scatter(0, 0, s=ns_cen, c=[CMAP_GAC(center_v)],
           edgecolors="#444444", linewidths=0.5, zorder=5)

# ── 10D  扇形蛋白节点（单物种 & 双物种）─────────────────────
# 单物种：菱形（"D"），双物种：圆形（"o"）
# 节点填充色在物种颜色基础上按 cluster_size 深浅变化
for sp_set_key, rows in sector_prots.items():
    ec     = SP_COLOR[sp_set_key]
    all_sz = [protein_info[acc]["cluster_size"] for acc, _, _ in rows]
    sz_lo  = min(all_sz) if all_sz else 1
    sz_hi  = max(all_sz) if all_sz else 1
    marker = "o" if len(sp_set_key) == 2 else "D"
    for acc, r_row, angle in rows:
        nid = f"P|{acc}"
        if nid not in pos_prot:
            continue
        px, py = pos_prot[nid]
        sz = protein_info[acc]["cluster_size"]
        v  = (sz - sz_lo) / (sz_hi - sz_lo + 1e-9)
        ns = get_prot_node_size(acc)
        # cluster_size 越大，填充色越深（向物种色趋近）
        fc = tuple(1.0 - v * (1.0 - c) * 0.8 for c in mcolors.to_rgb(ec))
        ax.scatter(px, py, s=ns, c=[fc], edgecolors="#444444", linewidths=0.5,
                   marker=marker, zorder=4)

# ── 10E  糖型节点 ─────────────────────────────────────────────
# 每个糖型节点由三层构成：
#   1. 浅灰阴影圆（右下偏移 0.06，营造立体感）
#   2. 主色圆（coolwarm 配色，深色边框）
#   3. 内部短名称标签（白色粗体，深色光晕）
# 节点外部绘制完整名称 + chains/proteins 统计注释框
SHORT_NAME = {
    "High Mannose":        "H.Man",
    "Pauci-mannose":       "Pauci",
    "Hybrid":              "Hybrid",
    "Complex-Plain":       "Cx-Pl",
    "Complex-Fucosylated": "Cx-Fuc",
    "Complex-Sialylated":  "Cx-Sia",
    "Other":               "Other",
}
for gt in glycan_node_list:
    gx, gy  = glyan_pos[gt]
    color   = glycan_node_color(gt)
    fc_rgb  = mcolors.to_rgb(color[:3] if len(color) >= 3 else color)
    ec_col  = mcolors.to_hex(tuple(max(0.0, c * 0.60) for c in fc_rgb))   # 主色加深 40% 作边框
    gr      = glycan_draw_radius(gt)
    # 阴影圆
    ax.add_patch(plt.Circle((gx + 0.06, gy - 0.06), gr,
                             color="#bbbbbb", alpha=0.25, zorder=5))
    # 主体圆
    ax.add_patch(plt.Circle((gx, gy), gr,
                             color=color, ec=ec_col, linewidth=2.0, zorder=6))
    # 三物种同心圆环：每物种独占一圈，填色弧角 = 该糖型蛋白数/该物种全部糖型蛋白总数×360°
    # 七个节点同一物种的填色弧加起来 = 360°（一个完整圆）
    # 起始角：节点圆心与图中心连线方向，再逆时针旋转 45°
    _node_angle  = math.degrees(math.atan2(gy, gx))  # 节点与图中心连线方向
    _gap   = 0.10   # 节点到第一个圆环内径的间距
    _w     = 0.18   # 每个圆环宽度
    _sep   = 0.10   # 圆环间间距
    for ring_i, sp in enumerate(_SP_RING_ORDER):
        r_inner = gr + _gap + ring_i * (_w + _sep)
        r_outer = r_inner + _w
        cnt     = gt_sp_prot_count[gt].get(sp, 0)
        total   = _sp_grand_total.get(sp, 1)
        sweep   = 360.0 * cnt / total
        # 填色弧段（从顶部 90° 顺时针）
        if sweep > 0:
            ax.add_patch(Wedge((gx, gy), r_outer,
                               _node_angle - sweep / 2, _node_angle + sweep / 2,
                               width=_w,
                               facecolor=_SP_RING_COLOR[sp],
                               edgecolor="white", linewidth=0.5,
                               alpha=0.92, zorder=7))

    # 内部短名称标签（第一行缩写，第二行 chains 数）
    inner_label = f"{SHORT_NAME.get(gt, gt)}\n{len(glycan_type_chains[gt])}"
    ax.text(gx, gy, inner_label, fontsize=15, fontweight="bold",
            color="white", ha="center", va="center", zorder=7,
            linespacing=1.3,
            path_effects=[pe.withStroke(linewidth=1.2, foreground=ec_col)])
    # 外部注释框（偏移 0.8 个单位，超出节点边缘；左右按角度自动对齐）
    angle_rad = math.atan2(gy, gx)
    lx = (R_GLYCAN + gr + 1.8) * math.cos(angle_rad)
    ly = (R_GLYCAN + gr + 1.8) * math.sin(angle_rad)
    annot = f"{gt}\nproteins={gt_prot_count.get(gt, 0)}"
    ha    = "left" if math.cos(angle_rad) >= 0 else "right"
    ax.text(lx, ly, annot, fontsize=15, color="#111111",
            ha=ha, va="center", linespacing=1.35, zorder=8,
            bbox=dict(boxstyle="round,pad=0.25", fc="white",
                      ec=ec_col, lw=1.2, alpha=0.88))

# ══════════════════════════════════════════════════════════════════
# STEP 11  输出
# ══════════════════════════════════════════════════════════════════
margin = R_GLYCAN + 6.5   # 图像边距 = 糖型圆半径 + 注释文字空间
ax.set_xlim(-margin, margin)
ax.set_ylim(-margin, margin)
plt.tight_layout()
# Vector formats skipped for Fig3A — 567-node network is too complex
from _save import PNG_DIR
import os as _os
plt.gcf().savefig(_os.path.join(PNG_DIR, "Fig3A.png"), dpi=200, bbox_inches='tight', facecolor='white')
print("  Saved: Fig3A [PNG]")
# Generate PDF from PNG using Pillow
from PIL import Image as _PILImage
_png_path = _os.path.join(PNG_DIR, "Fig3A.png")
from _save import PDF_DIR
_pdf_path = _os.path.join(PDF_DIR, "Fig3A.pdf")
_im = _PILImage.open(_png_path).convert('RGB')
_im.save(_pdf_path, 'PDF', resolution=200)
print("  Saved: Fig3A [PDF from raster]")
plt.close('all')