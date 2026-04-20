"""
BLAST Ortholog Mapping – Chord Diagram
Three species: Gallus (#B54664), Anas (#7895C1), Columba (#F0C284)
Data source: Blast_Ortholog_Mapping.xlsx  (GvsC_, GvsA_, AvsC_入图数据)
"""

import math
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
from matplotlib.path import Path
import matplotlib.patheffects as pe
from collections import defaultdict

# ── 0. 配色 ────────────────────────────────────────────────────────────────────
COL = {
    "Gallus":  "#B54664",
    "Anas":    "#7895C1",
    "Columba": "#F0C284",
}
ALPHA_CHORD = 0.45          # 弦半透明度
ALPHA_CHORD_HIGHLIGHT = 0.7 # 目标蛋白弦高亮透明度
ARC_WIDTH   = 0.08          # 外环宽度（radius单位）
RADIUS      = 1.0
GAP_DEG     = 6             # 物种间隔（度）
PROTEIN_GAP_DEG = 0.8       # 蛋白间隔（度）
LABEL_PAD   = 0.13          # 标签离外环距离
FONT_FAMILY = "Times New Roman"

# ── 1. 蛋白名称映射 ──────────────────────────────────────────────────────────────
import json, re

with open(r"D:\system_folder\Desktop\Work on Desk\blast\acc_name_map.json",
          encoding="utf-8") as _f:
    _raw_map = json.load(_f)

# 手动修正：目标蛋白用常用名
_OVERRIDES = {
    # 目标蛋白
    "P01012":     "Ovalbumin",      # OVAL (Gallus)
    "A0A8B9QNT8": "Ovalbumin",      # OVAL (Anas)
    "A0A2I0MWA2": "Ovalbumin",      # OVAL (Columba)
    "A0A8V0XA58": "Ovocleidin-116", # OC116 (Gallus)
    "A0A8B9ZY54": "Ovocleidin-116", # OC116 (Anas)
    "A0A2I0MGY6": "Ovocleidin-116", # OC116 (Columba)
    "A0A8V1A6Y9": "Ovotransferrin", # TRFE (Gallus)
    "A0A493TBB4": "Ovotransferrin", # TRFE (Anas)
    "A0A2I0LUS7": "Ovotransferrin", # TRFE (Columba)
    # Ovalbumin-related
    "A0A8V0Y614": "OVALX",
    "A0A8V0YJ25": "OVALY",
    "A0A1R7T3L5": "OVA-Y",
    "A0A2I0MW20": "OVA-X",
    # 长名截短
    "R0LL03":     "CPE",
    "A0A2I0LJ29": "Clusterin",
    "A0A2I0LWC3": "AGP1",
    "A0A2I0MGH1": "VWF-D",
    "A0A2I0LS76": "SORL1",
    "A0A8B9V707": "HYAL",
    "A0A8B9U4F1": "A2M",
    "A0A8B9UUB6": "VWFD-prot",
    "A0A8B9UC52": "COL5A",
    "A0A8B9VAE3": "LAMB2",
    "A0A8B9VJN1": "DCBLD",
    "A0A8B9V9H7": "Ig-domain prot",
    "A0A8B9ZNM3": "TMPRSS",
    "A0A8B9UXD7": "Serpin-prot",
    "A0A8B9QKV7": "PTPRJ",
    "A0A8B9SZ12": "NTN1",
    "A0A8B9TMM6": "SEMA3B",
    "A0A8B9R8Y2": "PSAP",
    "A0A8B9R6K5": "MFGE8",
    "A0A8B9UQR5": "Mucin-5AC",
    "A0A8B9QRE5": "CPE",
    "A0A493TSH0": "CHRD",
    "A0A493TA36": "CPM",
    "A0A493SY10": "Ovomucoid",
    "A0A493SWC3": "PROS1",
    "A0A3Q2TZZ7": "PTPRF",
    "A0A3Q3ADW5": "EDIL3",
}
_raw_map.update(_OVERRIDES)

def _safe_name(acc):
    """返回不超过20字符的显示名，若无映射则返回acc"""
    n = _raw_map.get(acc, acc)
    # 去除括号内注释，取首段
    n = re.sub(r'\s*\(.*', '', n).strip()
    return n[:20] + ('…' if len(n) > 20 else '')

# 读取数据完毕后，为每个species的蛋白列表去重显示名
def _dedup_names(acc_list):
    """对同一物种内重复的显示名添加数字后缀"""
    seen = {}      # name -> count
    result = {}
    for acc in acc_list:
        name = _safe_name(acc)
        if name not in seen:
            seen[name] = 0
            result[acc] = name
        else:
            seen[name] += 1
            result[acc] = f"{name} {seen[name]+1}"
    # 对出现了后缀的名再把原来第一个也加"1"
    name_counts = {}
    for acc, nm in result.items():
        base = _safe_name(acc)
        name_counts[base] = name_counts.get(base, 0) + 1
    final = {}
    idx = {}
    for acc in acc_list:
        base = _safe_name(acc)
        if name_counts[base] > 1:
            idx[base] = idx.get(base, 0) + 1
            final[acc] = f"{base}-{idx[base]}"
        else:
            final[acc] = base
    return final

# ── 2. 读取数据 ────────────────────────────────────────────────────────────────
XLSX = r"D:\system_folder\Desktop\Work on Desk\blast\Blast_Ortholog_Mapping.xlsx"

gvc = pd.read_excel(XLSX, sheet_name="GvsC_入图数据")
gva = pd.read_excel(XLSX, sheet_name="GvsA_入图数据")
avc = pd.read_excel(XLSX, sheet_name="AvsC_入图数据")

# 统一列名
gvc_links = gvc[["Gallus_acc", "Columba_acc", "max_bitscore", "目标蛋白"]].rename(
    columns={"Gallus_acc": "src", "Columba_acc": "dst", "max_bitscore": "score",
             "目标蛋白": "target"})
gvc_links["src_sp"]  = "Gallus"
gvc_links["dst_sp"]  = "Columba"

gva_links = gva[["Gallus_acc", "Anas_acc", "max_bitscore", "目标蛋白"]].rename(
    columns={"Gallus_acc": "src", "Anas_acc": "dst", "max_bitscore": "score",
             "目标蛋白": "target"})
gva_links["src_sp"]  = "Gallus"
gva_links["dst_sp"]  = "Anas"

avc_links = avc[["anas_acc", "columba_acc", "AvsG_max_bitscore", "target_name"]].rename(
    columns={"anas_acc": "src", "columba_acc": "dst",
             "AvsG_max_bitscore": "score", "target_name": "target"})
avc_links["src_sp"] = "Anas"
avc_links["dst_sp"] = "Columba"

all_links = pd.concat([gvc_links, gva_links, avc_links], ignore_index=True)
all_links["score"] = pd.to_numeric(all_links["score"], errors="coerce").fillna(50)
all_links["is_target"] = all_links["target"].notna()

# ── 2. 各物种蛋白列表（按总bitscore降序）─────────────────────────────────────
# ── 灰色 Gallus 蛋白（原始 HSP 有记录但未通过筛选）───────────────────────────
COL_GREY   = "#aaaaaa"   # 无匹配 Gallus 蛋白颜色
GREY_G_ACCS = {
    'A0A1D5PMF7','A0A1D5PT25','A0A3Q2TZZ7','A0A8V0X4N4','A0A8V0Y248',
    'A0A8V0Y614','A0A8V0YB27','A0A8V0YUU0','A0A8V0YYS9','A0A8V0Z1W6',
    'A0A8V0Z3S9','A0A8V0ZCK4','A0A8V0ZV19','A0A8V1AC48','A0A8V1ADW6',
    'A0A8V1AHD4','P02552','Q98UI9','V5NUE7',
}
GREY_SCORE  = 180   # 灰色蛋白统一小定宽（代表无有效比对）
GREY_GAP_DEG = 0    # 红色区与灰色区无额外间隙，连在一起

def build_protein_list(species: str):
    """每个蛋白的弧宽 = 该蛋白参与的所有比较中最高 bitscore（最佳比对质量）"""
    srcs = all_links[all_links["src_sp"] == species][["src", "score"]].rename(
        columns={"src": "acc"})
    dsts = all_links[all_links["dst_sp"] == species][["dst", "score"]].rename(
        columns={"dst": "acc"})
    combined = pd.concat([srcs, dsts])
    return (combined.groupby("acc")["score"].max()   # 用 max 代替 sum
                    .reset_index()
                    .sort_values("score", ascending=False)
                    .rename(columns={"score": "total"}))

g_prots = build_protein_list("Gallus")

# 添加灰色 Gallus 到 g_prots 末尾
grey_df = pd.DataFrame([
    {"acc": acc, "total": GREY_SCORE} for acc in sorted(GREY_G_ACCS)
    if acc not in set(g_prots["acc"])
])
if not grey_df.empty:
    g_prots = pd.concat([g_prots, grey_df], ignore_index=True)

a_prots = build_protein_list("Anas")
c_prots = build_protein_list("Columba")

TOP_N = 5   # 每物种额外显示 bitscore 最高的前5个非目标蛋白

# 目标蛋白始终显示
# 并额外展示 OC17
G_EXTRA_LABELS = {'V5NUE7'}   # OC17 必展示
def _target_accs(species):
    mask = ((all_links["src_sp"] == species) | (all_links["dst_sp"] == species)) & all_links["is_target"]
    accs = set()
    for col in ["src", "dst"]:
        accs.update(all_links.loc[mask & (all_links[f"{col}_sp"] == species), col].tolist())
    return accs

g_targets = _target_accs("Gallus")
a_targets = _target_accs("Anas")
c_targets = _target_accs("Columba")

def pick_top(df, targets, n=TOP_N, extra=None):
    """先取非目标蛋白中 bitscore 最高的前 n 个，再加上全部目标蛋白和 extra 蛋白"""
    must = targets | (extra or set())
    # 非目标、非灰色蛋白中按 bitscore 取前 n
    rest = df[~df["acc"].isin(must) & ~df["acc"].isin(GREY_G_ACCS)]
    top_regular = set(rest.head(n)["acc"].tolist())
    # 灰色蛋白中只取 extra（如 OC17）
    return top_regular | must

g_top = pick_top(g_prots, g_targets, extra=G_EXTRA_LABELS)
a_top = pick_top(a_prots, a_targets, extra=set())
c_top = pick_top(c_prots, c_targets, extra=set())

# 构建各物种去重显示名 (acc -> display_name)
g_names = _dedup_names(g_prots["acc"].tolist())
a_names = _dedup_names(a_prots["acc"].tolist())
c_names = _dedup_names(c_prots["acc"].tolist())
all_display_names = {**g_names, **a_names, **c_names}

# OC17 覆盖确保名称正确
all_display_names['V5NUE7'] = 'Ovocleidin-17'

# ── 3. 分配弧度 ────────────────────────────────────────────────────────────────
# 每个物种总角度 = 按蛋白数量比例分配（扣除间隔）
TOTAL_DEG    = 360 - 3 * GAP_DEG
n_g, n_a, n_c = len(g_prots), len(a_prots), len(c_prots)
n_total      = n_g + n_a + n_c

# 计算每个物种分配到的总角度（按蛋白数量比）
total_prots_gap = (n_g - 1) * PROTEIN_GAP_DEG + (n_a - 1) * PROTEIN_GAP_DEG + (n_c - 1) * PROTEIN_GAP_DEG
net_deg = TOTAL_DEG - total_prots_gap

deg_per_unit = net_deg / (g_prots["total"].sum() + a_prots["total"].sum() + c_prots["total"].sum())

def assign_angles(df, start_deg, grey_set=None, grey_gap=0):
    """给每个蛋白分配 [start, end] 弧度范围。
    grey_set: 在进入灰色区首个蛋白前插入 grey_gap 度的额外间隙。
    """
    result = {}
    cur = start_deg
    in_grey = False
    for _, row in df.iterrows():
        acc = row["acc"]
        is_grey = (grey_set is not None) and (acc in grey_set)
        if is_grey and not in_grey:
            cur += grey_gap   # 红/灰分界处额外间隙
            in_grey = True
        span = row["total"] * deg_per_unit
        mid  = cur + span / 2
        result[acc] = (
            math.radians(mid),
            math.radians(cur),
            math.radians(cur + span),
        )
        cur += span + PROTEIN_GAP_DEG
    return result, cur

# 物种起始角度（从正上方顺时针）：Gallus 上方偏左，Anas 下方，Columba 右
#  使图像类似参考图（Gallus 在左上，Columba 在右，Anas 在下/左下）
g_start = 90 + GAP_DEG / 2        # Gallus 从 ~96° 开始（逆时针坐标）
g_angles, after_g = assign_angles(g_prots, g_start,
                                  grey_set=GREY_G_ACCS, grey_gap=GREY_GAP_DEG)

a_start = after_g + GAP_DEG
a_angles, after_a = assign_angles(a_prots, a_start)

c_start = after_a + GAP_DEG
c_angles, after_c = assign_angles(c_prots, c_start)

all_angles = {**g_angles, **a_angles, **c_angles}

def acc_species(acc):
    if acc in g_angles: return "Gallus"
    if acc in a_angles: return "Anas"
    if acc in c_angles: return "Columba"
    return None

# ── 4. 绘图 ────────────────────────────────────────────────────────────────────
matplotlib.rcParams["font.family"] = "Times New Roman"
matplotlib.rcParams["font.serif"]  = ["Times New Roman"]

# 双栏宽度 7英寸，给名称留足够边距
fig, ax = plt.subplots(figsize=(8, 8), facecolor="white")
ax.set_aspect("equal")
ax.axis("off")
ax.set_xlim(-2.0, 2.0)
ax.set_ylim(-2.0, 2.0)

# ── 辅助函数 ──────────────────────────────────────────────────────────────────
def polar_xy(r, angle_rad):
    return r * math.cos(angle_rad), r * math.sin(angle_rad)

def draw_arc(ax, r, start_rad, end_rad, color, lw=1.5, zorder=3):
    """画圆弧（用多段折线近似）"""
    angles = np.linspace(start_rad, end_rad, 300)
    xs = r * np.cos(angles)
    ys = r * np.sin(angles)
    ax.plot(xs, ys, color=color, lw=lw, zorder=zorder, solid_capstyle="round")

def draw_filled_arc(ax, r_in, r_out, start_rad, end_rad, color, alpha=1.0, zorder=2):
    """画填充的环形弧（外环色块）"""
    angles = np.linspace(start_rad, end_rad, 300)
    # 外弧顺时针 → 内弧逆时针 → 闭合
    xs_out = r_out * np.cos(angles)
    ys_out = r_out * np.sin(angles)
    xs_in  = r_in  * np.cos(angles[::-1])
    ys_in  = r_in  * np.sin(angles[::-1])
    xs = np.concatenate([xs_out, xs_in])
    ys = np.concatenate([ys_out, ys_in])
    ax.fill(xs, ys, color=color, alpha=alpha, zorder=zorder, linewidth=0)

def bezier_chord(ax, mid1, mid2, w1=0.02, w2=0.02, color="gray",
                 alpha=0.4, zorder=1, is_target=False):
    """
    在 mid1、mid2 两点之间画贝塞尔弦。
    w1/w2 = 弦在各端的半角宽度（弧度）。
    """
    r = RADIUS - ARC_WIDTH - 0.005

    # 四个端点
    s1  = math.radians(math.degrees(mid1) - math.degrees(w1) / 2) if w1 > 0.001 else mid1 - 0.008
    e1  = math.radians(math.degrees(mid1) + math.degrees(w1) / 2) if w1 > 0.001 else mid1 + 0.008
    s2  = math.radians(math.degrees(mid2) - math.degrees(w2) / 2) if w2 > 0.001 else mid2 - 0.008
    e2  = math.radians(math.degrees(mid2) + math.degrees(w2) / 2) if w2 > 0.001 else mid2 + 0.008

    p1a = np.array(polar_xy(r, s1))
    p1b = np.array(polar_xy(r, e1))
    p2a = np.array(polar_xy(r, s2))
    p2b = np.array(polar_xy(r, e2))

    ctrl = np.array([0.0, 0.0])   # 控制点（圆心）

    # 弦路径：p1a → (bezier) → p2a → 弧 → p2b → (bezier) → p1b → 弧 → 闭合
    n = 80

    def cubic_bezier(t, P0, P1, P2, P3):
        return ((1-t)**3 * P0 + 3*(1-t)**2*t * P1
                + 3*(1-t)*t**2 * P2 + t**3 * P3)

    # 调整控制点强度：让弦内凹
    ctrl_strength = 0.3
    c1_out = ctrl_strength * p1a
    c2_out = ctrl_strength * p2a
    c1_in  = ctrl_strength * p1b
    c2_in  = ctrl_strength * p2b

    t_vals = np.linspace(0, 1, n)

    curve1 = np.array([cubic_bezier(t, p1a, c1_out, c2_out, p2a) for t in t_vals])
    arc2   = np.array([polar_xy(r, a) for a in np.linspace(s2, e2, 20)])
    curve2 = np.array([cubic_bezier(t, p2b, c2_in,  c1_in,  p1b) for t in t_vals])
    arc1   = np.array([polar_xy(r, a) for a in np.linspace(e1, s1, 20)])

    verts = np.concatenate([curve1, arc2, curve2, arc1])
    ax.fill(verts[:, 0], verts[:, 1],
            color=color, alpha=alpha if not is_target else ALPHA_CHORD_HIGHLIGHT,
            zorder=zorder, linewidth=0)

# ── 4a. 画弦（先画，在弧下方）─────────────────────────────────────────────────
# 按 score 升序绘制，高分弦在前
sorted_links = all_links.sort_values("score", ascending=True)

for _, row in sorted_links.iterrows():
    src, dst = row["src"], row["dst"]
    if src not in all_angles or dst not in all_angles:
        continue
    src_sp = row["src_sp"]

    mid_src = all_angles[src][0]
    mid_dst = all_angles[dst][0]

    # 弦宽度 ∝ bitscore；限制最小/最大
    max_bs  = all_links["score"].max()
    w_frac  = max(0.003, min(0.06, row["score"] / max_bs * 0.05))
    half_w  = math.radians(w_frac * 60)   # 转为弧度

    chord_color = COL[src_sp]
    bezier_chord(ax, mid_src, mid_dst,
                 w1=half_w, w2=half_w,
                 color=chord_color,
                 alpha=ALPHA_CHORD,
                 zorder=1,
                 is_target=row["is_target"])

# ── 4b. 画外环弧段（蛋白级和物种级）──────────────────────────────────────────
# 先画物种级大弧（颜色块背景 + 细线）
def species_range(angle_dict):
    """返回物种弧段的起止弧度"""
    starts = [v[1] for v in angle_dict.values()]
    ends   = [v[2] for v in angle_dict.values()]
    return min(starts), max(ends)

for sp, ang_dict in [("Gallus", g_angles), ("Anas", a_angles), ("Columba", c_angles)]:
    # 用物种颜色先画常规弧段
    regular_arcs = {acc: v for acc, v in ang_dict.items() if acc not in GREY_G_ACCS}
    grey_arcs    = {acc: v for acc, v in ang_dict.items() if acc in GREY_G_ACCS}

    if regular_arcs:
        s_rad = min(v[1] for v in regular_arcs.values())
        e_rad = max(v[2] for v in regular_arcs.values())
        draw_filled_arc(ax, RADIUS - ARC_WIDTH, RADIUS, s_rad, e_rad, COL[sp], alpha=0.85, zorder=4)
        angles_arr = np.linspace(s_rad, e_rad, 300)
        ax.plot(RADIUS * np.cos(angles_arr), RADIUS * np.sin(angles_arr), color=COL[sp], lw=1.2, zorder=6)
        ax.plot((RADIUS-ARC_WIDTH)*np.cos(angles_arr), (RADIUS-ARC_WIDTH)*np.sin(angles_arr),
                color="white", lw=0.6, zorder=6, alpha=0.6)

    if grey_arcs:
        s_rad = min(v[1] for v in grey_arcs.values())
        e_rad = max(v[2] for v in grey_arcs.values())
        draw_filled_arc(ax, RADIUS - ARC_WIDTH, RADIUS, s_rad, e_rad, COL_GREY, alpha=0.90, zorder=4)
        angles_arr = np.linspace(s_rad, e_rad, 300)
        ax.plot(RADIUS * np.cos(angles_arr), RADIUS * np.sin(angles_arr), color=COL_GREY, lw=1.2, zorder=6)
        ax.plot((RADIUS-ARC_WIDTH)*np.cos(angles_arr), (RADIUS-ARC_WIDTH)*np.sin(angles_arr),
                color="white", lw=0.6, zorder=6, alpha=0.6)

# 蛋白分隔线（细白线）
for ang_dict in [g_angles, a_angles, c_angles]:
    for acc, (mid, start, end) in ang_dict.items():
        for ang in [start, end]:
            x0, y0 = polar_xy(RADIUS - ARC_WIDTH, ang)
            x1, y1 = polar_xy(RADIUS, ang)
            ax.plot([x0, x1], [y0, y1], color="white", lw=0.8, zorder=7, alpha=0.8)

# ── 4c. 画刻度（bitscore 数字标注）─（可选，参考图有刻度值）─────────────────
# 在外圈刻度位置标注 bitscore 区间内某几个代表数字
# 这里简化：只在物种弧的中点位置画物种标签

# ── 4d. 标签（每物种 top10，目标蛋白必显示）────────────────────────────────────
sp_top_map = {"Gallus": g_top, "Anas": a_top, "Columba": c_top}
for sp, ang_dict in [("Gallus", g_angles), ("Anas", a_angles), ("Columba", c_angles)]:
    color   = COL[sp]
    top_set = sp_top_map[sp]
    for acc, (mid, start, end) in ang_dict.items():
        if acc not in top_set:
            continue   # 非 top10 不贴标签
        r_label = RADIUS + LABEL_PAD
        x, y    = polar_xy(r_label, mid)

        angle_deg = math.degrees(mid)
        rot = angle_deg
        if 90 < angle_deg % 360 < 270:
            ha  = "right"
            rot = angle_deg + 180
        else:
            ha  = "left"
            rot = angle_deg

        is_target_prot = ((all_links["src"] == acc) | (all_links["dst"] == acc)) & all_links["is_target"]
        is_target_prot = is_target_prot.any()
        is_oc17 = (acc == 'V5NUE7')

        label_text = all_display_names.get(acc, acc)
        fw = "bold" if is_target_prot else "normal"
        fs = 8.5 if is_target_prot else 7.5

        if is_oc17:
            label_color = COL_GREY
        elif is_target_prot:
            label_color = color   # 物种代表色
        else:
            label_color = "black"

        txt = ax.text(x, y, label_text,
                      ha=ha, va="center",
                      rotation=rot,
                      rotation_mode="anchor",
                      fontsize=fs,
                      fontweight=fw,
                      color=label_color,
                      zorder=10)
        if is_target_prot:
            txt.set_path_effects([
                pe.withStroke(linewidth=2, foreground="white")])

# 物种大字标签已移除，仅用图例表示物种 ─────────────────────────────────────

# ── 4f. 图例 ──────────────────────────────────────────────────────────────────
legend_patches = [
    mpatches.Patch(color=COL["Gallus"],  label=r"$\it{Gallus}$",  alpha=0.9),
    mpatches.Patch(color=COL["Anas"],    label=r"$\it{Anas}$",    alpha=0.9),
    mpatches.Patch(color=COL["Columba"], label=r"$\it{Columba}$", alpha=0.9),
    mpatches.Patch(color=COL_GREY,        label=r"$\it{Gallus}$ (no ortholog)", alpha=0.85),
]
ax.legend(handles=legend_patches,
          loc="lower right",
          frameon=True, framealpha=0.9,
          edgecolor="#bbbbbb",
          fontsize=8,
          title="Species",
          title_fontsize=8,
          prop={"family": "Times New Roman", "size": 8},
          bbox_to_anchor=(0.99, 0.01))

# ── 4g. 标题 ──────────────────────────────────────────────────────────────────
ax.set_title("BLAST Ortholog Mapping – Chord Diagram",
             fontsize=9, fontweight="bold", pad=6, color="#222222",
             fontfamily="Times New Roman")

plt.tight_layout()
out_pdf  = r"D:\system_folder\Desktop\Work on Desk\blast\chord_diagram.pdf"
out_tiff = r"D:\system_folder\Desktop\Work on Desk\blast\chord_diagram.tiff"
out_png  = r"D:\system_folder\Desktop\Work on Desk\blast\chord_diagram.png"
plt.savefig(out_pdf,  dpi=300, bbox_inches="tight", facecolor="white")
plt.savefig(out_tiff, dpi=300, bbox_inches="tight", facecolor="white", format="tiff")
plt.savefig(out_png,  dpi=300, bbox_inches="tight", facecolor="white")
print(f"Saved: {out_pdf}")
print(f"Saved: {out_tiff}")
print(f"Saved: {out_png}")
plt.close()
