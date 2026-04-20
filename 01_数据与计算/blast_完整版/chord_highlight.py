"""
Circos-style chord diagram — 突出显示 OVAL / OC116 / OC17 / TRFE
- GlyGallus 蛋白为 query（上方弧段）
- GlyAnas / GlyColumba 各占一段
- 四个关键蛋白用独立颜色标注，其弦不透明度更高并加箭头标签
"""

import numpy as np
import colorsys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path
from matplotlib.patches import PathPatch, FancyArrowPatch
from collections import defaultdict, OrderedDict
import os

# ── 路径 ────────────────────────────────────────────────────────────────────
BASE = r"D:\system_folder\Desktop\Work On\01_数据与计算\blast_完整版"
TSV  = os.path.join(BASE, "blastp_gallus_coords.tsv")
OUT  = os.path.join(BASE, "chord_highlight.png")

# ── 目标蛋白（高亮） ─────────────────────────────────────────────────────────
HIGHLIGHT = {
    "P01012":     {"label": "OVAL",  "color": "#FF6B35"},   # 亮橙红
    "A0A8V0XA58": {"label": "OC116", "color": "#00D4AA"},   # 青绿
    "Q9PRS8":     {"label": "OC17",  "color": "#FFE600"},   # 高亮黄
    "A0A8V1A6Y9": {"label": "TRFE",  "color": "#C77DFF"},   # 紫
}

# ── 颜色方案（按用户指定） ────────────────────────────────────────────────────
BG           = "white"
REF_COLOR    = "#B54664"   # Gallus 普通弧段
SP_COLORS    = {
    "GlyAnas":    "#7895C1",
    "GlyColumba": "#F0C284",
}
# 高亮：各物种颜色的提饱和加亮版，用于高亮蛋白弧段和弦
HIGHLIGHT_ARC_COLOR  = "#FF2D74"   # Gallus #B54664 → 大幅提饱和
HIGHLIGHT_SP_COLORS  = {
    "GlyAnas":    "#2E6FE8",   # Anas #7895C1 → 深蓝亮版
    "GlyColumba": "#F59000",   # Columba #F0C284 → 深橙亮版
}
RIBBON_ALPHA_DIM  = 0.15   # 普通弦透明度
RIBBON_ALPHA_HIGH = 0.82   # 高亮弦透明度
LABEL_COLOR  = "#333333"

# ── BLASTp 筛选阈值（用于背景蛋白）──────────────────────────────────────────
# 严格条件：只保留跨物种高度保守的背景蛋白
# HIGHLIGHT 中的蛋白无论比对值如何，始终保留（目标蛋白）
EVALUE_MAX   = 1e-50   # E-value 严格阈值
IDENTITY_MIN = 40.0    # 序列一致性下限（%）
QCOV_MIN     = 80.0    # Query coverage 下限（%）

# ── 读取数据（全量，筛选由阈值决定） ─────────────────────────────────────────
with open(TSV, encoding="utf-8") as f:
    header = f.readline().rstrip().split("\t")
    all_rows = [dict(zip(header, ln.rstrip().split("\t"))) for ln in f]

def passes(r):
    """严格 BLAST 筛选：高 identity、低 e-value、高 query coverage"""
    try:
        qcov = (int(r["q_end"]) - int(r["q_start"]) + 1) / int(r["query_len"]) * 100
        return (float(r["evalue"]) <= EVALUE_MAX and
                float(r["pct_identity"]) >= IDENTITY_MIN and
                qcov >= QCOV_MIN)
    except (ValueError, ZeroDivisionError):
        return False

# 保留：通过严格筛选 OR 属于 HIGHLIGHT 目标蛋白
rows = [r for r in all_rows if passes(r) or r["query_acc"] in HIGHLIGHT]

# 每对 (query_acc, species) 的最佳 hit（score 最高）
best = defaultdict(dict)
for r in rows:
    key = r["query_acc"]
    db  = r["subject_db"]
    if db not in best[key] or float(r["score"]) > float(best[key][db]["score"]):
        best[key][db] = r

SPECIES = ["GlyAnas", "GlyColumba"]

# 仅保留在两个物种均有命中的蛋白
qualified = {qacc for qacc, hits in best.items() if all(sp in hits for sp in SPECIES)}
rows = [r for r in rows if r["query_acc"] in qualified]
best = {qacc: hits for qacc, hits in best.items() if qacc in qualified}

print(f"筛选后保留 {len(qualified)} 个蛋白（一般蛋白: E≤{EVALUE_MAX}, id≥{IDENTITY_MIN}%, qcov≥{QCOV_MIN}%；目标蛋白始终保留）")
for qacc in sorted(qualified):
    label = HIGHLIGHT.get(qacc, {}).get("label", "")
    flag = " ★" if qacc in HIGHLIGHT else ""
    print(f"  {qacc:15s} {label:6s}{flag}")

# ── 收集蛋白列表（仅四个高亮蛋白） ────────────────────────────────────────────
ref_list = sorted(
    {(r["query_acc"], r["query_name"], int(r["query_len"])) for r in rows},
    key=lambda x: -x[2]
)

sp_prots = {sp: OrderedDict() for sp in SPECIES}
for qacc, _, _ in ref_list:
    for sp in SPECIES:
        if sp not in best[qacc]:
            continue
        h   = best[qacc][sp]
        sid = h["subject_acc"]
        if sid not in sp_prots[sp]:
            sp_prots[sp][sid] = {"name": h["subject_name"],
                                 "len":  int(h["subject_len"])}

# ── 弧段角度分配 ─────────────────────────────────────────────────────────────
GAP_MAIN  = np.radians(10)
GAP_SM    = np.radians(0.6)

ref_tot  = sum(l for _,_,l in ref_list)
sp_tots  = {sp: sum(v["len"] for v in sp_prots[sp].values()) for sp in SPECIES}
grand    = ref_tot + sum(sp_tots.values())

usable   = 2*np.pi - 4*GAP_MAIN
ref_arc  = usable * ref_tot / grand
sp_arcs  = {sp: usable * sp_tots[sp] / grand for sp in SPECIES}

cur = np.pi/2
ref_start = cur
cur += ref_arc

sp_starts = {}
for sp in SPECIES:
    cur += GAP_MAIN
    sp_starts[sp] = cur
    cur += sp_arcs[sp]

# ── 各蛋白弧段位置 ────────────────────────────────────────────────────────────
ref_arc_pos = {}
cur = ref_start
for qacc, _, qlen in ref_list:
    span = (qlen / ref_tot) * ref_arc
    ref_arc_pos[qacc] = (cur + GAP_SM/2, cur + span - GAP_SM/2)
    cur += span

sp_arc_pos = {}
for sp in SPECIES:
    cur = sp_starts[sp]
    sp_len = sp_tots[sp]
    for sid, info in sp_prots[sp].items():
        span = (info["len"] / sp_len) * sp_arcs[sp]
        sp_arc_pos[(sp, sid)] = (cur + GAP_SM/2, cur + span - GAP_SM/2)
        cur += span

# ── 绘图辅助 ──────────────────────────────────────────────────────────────────
R_OUT = 1.00
R_IN  = 0.93
R_RIB = 0.925

def arc_patch(ax, a0, a1, r_out, r_in, color, lw=0.4, zorder=3, n=200,
              edgecolor="white"):
    t  = np.linspace(a0, a1, n)
    ox, oy = r_out*np.cos(t), r_out*np.sin(t)
    tb = t[::-1]
    ix, iy = r_in*np.cos(tb), r_in*np.sin(tb)
    xs = np.concatenate([ox, ix, [ox[0]]])
    ys = np.concatenate([oy, iy, [oy[0]]])
    verts = list(zip(xs, ys))
    codes = [Path.MOVETO] + [Path.LINETO]*(len(verts)-2) + [Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(verts, codes),
                           facecolor=color, edgecolor=edgecolor,
                           linewidth=lw, zorder=zorder))

def bezier_ribbon(ax, a1s, a1e, a2s, a2e, r=R_RIB, color="purple",
                  alpha=RIBBON_ALPHA_DIM, zorder=1, n=60):
    C = np.array([0., 0.])
    def arc(a, b, nn=n):
        return [(r*np.cos(t), r*np.sin(t)) for t in np.linspace(a, b, nn)]
    p1 = (r*np.cos(a1s), r*np.sin(a1s))
    p2 = (r*np.cos(a1e), r*np.sin(a1e))
    p3 = (r*np.cos(a2s), r*np.sin(a2s))
    p4 = (r*np.cos(a2e), r*np.sin(a2e))
    verts = [p1]
    codes = [Path.MOVETO]
    verts += [tuple(C), tuple(C), p3]; codes += [Path.CURVE4]*3
    for pt in arc(a2s, a2e)[1:]: verts.append(pt); codes.append(Path.LINETO)
    verts += [tuple(C), tuple(C), p2]; codes += [Path.CURVE4]*3
    for pt in arc(a1e, a1s)[1:]: verts.append(pt); codes.append(Path.LINETO)
    verts.append(p1); codes.append(Path.CLOSEPOLY)
    ax.add_patch(PathPatch(Path(verts, codes),
                           facecolor=color, edgecolor="none",
                           alpha=alpha, zorder=zorder))

def rotated_label(ax, angle, text, r_lab, fontsize=6.5, color=LABEL_COLOR,
                  fontweight="normal"):
    deg = np.degrees(angle) % 360
    lx, ly = r_lab * np.cos(angle), r_lab * np.sin(angle)
    if np.cos(angle) >= 0:
        rot = deg - 90
        ha  = "left"
    else:
        rot = deg + 90
        ha  = "right"
    ax.text(lx, ly, text, fontsize=fontsize, color=color,
            ha=ha, va="center", rotation=rot,
            rotation_mode="anchor", zorder=6, fontweight=fontweight)

def adjust_lightness(hex_color, factor=1.12):
    r, g, b = [int(hex_color[i:i+2], 16)/255 for i in (1, 3, 5)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = min(1.0, l * factor)
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
    return "#{:02X}{:02X}{:02X}".format(int(r2*255), int(g2*255), int(b2*255))

# ── 作图 ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(18, 18), facecolor=BG)
ax.set_aspect("equal")
ax.axis("off")
ax.set_facecolor(BG)
ax.set_xlim(-1.9, 1.9)
ax.set_ylim(-1.9, 1.9)

# ── (1) 普通弦（暗淡，先绘） ──────────────────────────────────────────────────
for qacc, _, qlen in ref_list:
    if qacc in HIGHLIGHT:
        continue   # 高亮蛋白的弦后绘
    q_s, q_e = ref_arc_pos[qacc]
    q_span   = q_e - q_s
    for sp in SPECIES:
        if sp not in best[qacc]:
            continue
        h   = best[qacc][sp]
        sid = h["subject_acc"]
        if (sp, sid) not in sp_arc_pos:
            continue
        qs_frac = (int(h["q_start"])-1) / qlen
        qe_frac = int(h["q_end"])       / qlen
        r_qs = q_s + qs_frac * q_span
        r_qe = q_s + qe_frac * q_span
        if r_qe - r_qs < 1e-5:
            r_qe = r_qs + q_span * 0.05
        s_a_s, s_a_e = sp_arc_pos[(sp, sid)]
        s_span  = s_a_e - s_a_s
        slen    = int(h["subject_len"])
        ss_frac = (int(h["s_start"])-1) / slen
        se_frac = int(h["s_end"])       / slen
        r_ss = s_a_s + ss_frac * s_span
        r_se = s_a_s + se_frac * s_span
        if r_se - r_ss < 1e-5:
            r_se = r_ss + s_span * 0.05
        bezier_ribbon(ax, r_qs, r_qe, r_ss, r_se,
                      color=SP_COLORS[sp], alpha=RIBBON_ALPHA_DIM, zorder=1)

# ── (2) 高亮蛋白的弦（高不透明度，前景） ────────────────────────────────────
for qacc, info in HIGHLIGHT.items():
    if qacc not in ref_arc_pos:
        continue
    q_s, q_e = ref_arc_pos[qacc]
    q_span = q_e - q_s
    qlen = next(l for a,_,l in ref_list if a == qacc)
    for sp in SPECIES:
        if sp not in best[qacc]:
            continue
        h   = best[qacc][sp]
        sid = h["subject_acc"]
        if (sp, sid) not in sp_arc_pos:
            continue
        qs_frac = (int(h["q_start"])-1) / qlen
        qe_frac = int(h["q_end"])       / qlen
        r_qs = q_s + qs_frac * q_span
        r_qe = q_s + qe_frac * q_span
        if r_qe - r_qs < 1e-5:
            r_qe = r_qs + q_span * 0.05
        s_a_s, s_a_e = sp_arc_pos[(sp, sid)]
        s_span = s_a_e - s_a_s
        slen   = int(h["subject_len"])
        ss_frac = (int(h["s_start"])-1) / slen
        se_frac = int(h["s_end"])       / slen
        r_ss = s_a_s + ss_frac * s_span
        r_se = s_a_s + se_frac * s_span
        if r_se - r_ss < 1e-5:
            r_se = r_ss + s_span * 0.05
        bezier_ribbon(ax, r_qs, r_qe, r_ss, r_se,
                      color=HIGHLIGHT[qacc]["color"], alpha=RIBBON_ALPHA_HIGH, zorder=4)

# ── (3) Reference 蛋白弧段 ─────────────────────────────────────────────────
for i, (qacc, qname, qlen) in enumerate(ref_list):
    a_s, a_e = ref_arc_pos[qacc]
    if qacc in HIGHLIGHT:
        c = HIGHLIGHT[qacc]["color"]
        ec = "white"
        lw = 1.5
        zord = 5
    else:
        c = REF_COLOR if i % 2 == 0 else adjust_lightness(REF_COLOR, 1.15)
        ec = "white"
        lw = 0.3
        zord = 3
    arc_patch(ax, a_s, a_e, R_OUT, R_IN, c, lw=lw, zorder=zord, edgecolor=ec)
    # 刻度
    for pos in range(0, qlen+1, 200):
        t   = a_s + (pos / qlen) * (a_e - a_s)
        h_  = 0.025 if pos % 1000 == 0 else 0.012
        ax.plot([R_OUT*np.cos(t), (R_OUT+h_)*np.cos(t)],
                [R_OUT*np.sin(t), (R_OUT+h_)*np.sin(t)],
                color="#AAAAAA", lw=0.6, zorder=5)

# 构建高亮 hit 映射：(sp, sid) → 高亮颜色
highlight_hits = {}
for qacc, hinfo in HIGHLIGHT.items():
    for sp in SPECIES:
        if sp not in best[qacc]:
            continue
        sid = best[qacc][sp]["subject_acc"]
        highlight_hits[(sp, sid)] = hinfo["color"]

# ── (3) 物种 hit 弧段 ───────────────────────────────────────────────────────
for sp in SPECIES:
    base_c  = SP_COLORS[sp]
    light_c = adjust_lightness(base_c, 1.20)
    for i, (sid, info) in enumerate(sp_prots[sp].items()):
        a_s, a_e = sp_arc_pos[(sp, sid)]
        key = (sp, sid)
        if key in highlight_hits:
            c    = highlight_hits[key]
            lw_  = 1.5
            zord = 5
        else:
            c    = base_c if i % 2 == 0 else light_c
            lw_  = 0.4
            zord = 3
        arc_patch(ax, a_s, a_e, R_OUT, R_IN, c, lw=lw_, zorder=zord)
        slen = info["len"]
        for pos in range(0, slen+1, 300):
            t  = a_s + (pos / slen) * (a_e - a_s)
            h_ = 0.018 if pos % 900 == 0 else 0.009
            ax.plot([R_OUT*np.cos(t), (R_OUT+h_)*np.cos(t)],
                    [R_OUT*np.sin(t), (R_OUT+h_)*np.sin(t)],
                    color="#AAAAAA", lw=0.5, zorder=5)

# ── (5) 高亮蛋白标签（带箭头批注） ──────────────────────────────────────────
for qacc, hinfo in HIGHLIGHT.items():
    if qacc not in ref_arc_pos:
        continue
    a_s, a_e = ref_arc_pos[qacc]
    mid = (a_s + a_e) / 2
    px = (R_OUT + 0.01) * np.cos(mid)
    py = (R_OUT + 0.01) * np.sin(mid)
    r_lbl = R_OUT + 0.32
    lx = r_lbl * np.cos(mid)
    ly = r_lbl * np.sin(mid)
    deg = np.degrees(mid) % 360
    if 45 < deg < 135:
        ha, va = "center", "bottom"
    elif 225 < deg < 315:
        ha, va = "center", "top"
    elif deg <= 45 or deg >= 315:
        ha, va = "left", "center"
    else:
        ha, va = "right", "center"

    c = hinfo["color"]
    ax.annotate(
        hinfo["label"],
        xy=(px, py),
        xytext=(lx, ly),
        fontsize=13,
        fontweight="bold",
        color=c,
        ha=ha, va=va,
        zorder=10,
        arrowprops=dict(
            arrowstyle="-|>",
            color=c,
            lw=1.5,
            connectionstyle="arc3,rad=0.0",
        ),
        bbox=dict(
            boxstyle="round,pad=0.25",
            facecolor="white",
            edgecolor=c,
            linewidth=1.8,
            alpha=0.95,
        ),
    )

# ── (6) 物种组大标签 ─────────────────────────────────────────────────────────
SP_NAMES = {"GlyAnas":    "Anas zonorhyncha\n(Duck)",
            "GlyColumba": "Columba livia\n(Pigeon)"}
for sp in SPECIES:
    mid   = sp_starts[sp] + sp_arcs[sp] / 2
    r_lbl = R_OUT + 0.26
    lx, ly = r_lbl * np.cos(mid), r_lbl * np.sin(mid)
    deg = np.degrees(mid) % 360
    rot = deg - 90
    if rot > 90:
        rot -= 180
    elif rot < -90:
        rot += 180
    ax.text(lx, ly, SP_NAMES[sp], fontsize=11, fontweight="bold",
            color=SP_COLORS[sp], ha="center", va="center",
            rotation=rot, rotation_mode="anchor", zorder=6)

# GlyGallus 大标签
mid_ref = ref_start + ref_arc / 2
ax.text((R_OUT+0.22)*np.cos(mid_ref), (R_OUT+0.22)*np.sin(mid_ref),
        "Gallus gallus\n(Chicken)", fontsize=12, fontweight="bold",
        color="#888888", ha="center", va="center", zorder=6)

# ── (6) 图例 ──────────────────────────────────────────────────────────────────────────────────
legend_handles = [
    mpatches.Patch(color=REF_COLOR,               label="Gallus gallus"),
    mpatches.Patch(color=SP_COLORS["GlyAnas"],    label="Anas zonorhyncha"),
    mpatches.Patch(color=SP_COLORS["GlyColumba"], label="Columba livia"),
]
for qacc, hinfo in HIGHLIGHT.items():
    legend_handles.append(
        mpatches.Patch(color=hinfo["color"], label=hinfo["label"])
    )
ax.legend(handles=legend_handles, loc="lower center",
          bbox_to_anchor=(0.5, -0.02), ncol=3, frameon=True,
          fontsize=10, labelcolor=LABEL_COLOR,
          edgecolor="#CCCCCC", facecolor="white")

plt.tight_layout(pad=0.3)
plt.savefig(OUT, dpi=180, bbox_inches="tight", facecolor=BG)
plt.close()
print(f"Saved → {OUT}")
