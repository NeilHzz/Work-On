"""
Circos-style chord diagram  —  匹配 circle_plot.png 风格
- 白色背景，圆弧色块，弦连接比对区域，弧外旋转标签，刻度线
- GlyGallus 作为 query（上方大弧段）
- GlyAnas / GlyColumba 各占一段
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from collections import defaultdict, OrderedDict
import os

# ── 路径 ────────────────────────────────────────────────────────────────────
BASE = r"d:\system_folder\Desktop\Work on Desk\blast"
TSV  = os.path.join(BASE, "blastp_gallus_coords.tsv")
OUT  = os.path.join(BASE, "chord_circos_gallus.png")

# ── 颜色方案（贴近参考图） ───────────────────────────────────────────────────
BG          = "white"
REF_COLOR   = "#B54664"          # GlyGallus query
SP_COLORS   = {
    "GlyAnas":    "#7895C1",
    "GlyColumba": "#F0C284",
}
RIBBON_ALPHA = 0.35
LABEL_COLOR  = "#333333"

# ── 读取数据 ─────────────────────────────────────────────────────────────────
with open(TSV, encoding="utf-8") as f:
    header = f.readline().rstrip().split("\t")
    rows   = [dict(zip(header, ln.rstrip().split("\t"))) for ln in f]

# 每对 (query, species) 的最佳 hit（score 最高）
best = defaultdict(dict)
for r in rows:
    key = r["query_acc"]
    db  = r["subject_db"]
    if db not in best[key] or float(r["score"]) > float(best[key][db]["score"]):
        best[key][db] = r

SPECIES = ["GlyAnas", "GlyColumba"]

# ── 收集蛋白列表 ──────────────────────────────────────────────────────────────
# GlyGallus query（按长度降序排列）
ref_list = sorted(
    {(r["query_acc"], r["query_name"], int(r["query_len"])) for r in rows},
    key=lambda x: -x[2]
)

# 每个物种的最优 hit 蛋白（去重，按出现先后保留）
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
GAP_MAIN  = np.radians(10)   # 大组之间的间隔
GAP_SM    = np.radians(0.6)  # 蛋白之间的小间隔

ref_tot  = sum(l for _,_,l in ref_list)
sp_tots  = {sp: sum(v["len"] for v in sp_prots[sp].values()) for sp in SPECIES}
grand    = ref_tot + sum(sp_tots.values())

usable   = 2*np.pi - 4*GAP_MAIN
ref_arc  = usable * ref_tot / grand
sp_arcs  = {sp: usable * sp_tots[sp] / grand for sp in SPECIES}

# 起始角（从顶部 π/2 开始，顺时针即增大角度）
cur = np.pi/2
ref_start = cur
cur += ref_arc

sp_starts = {}
for sp in SPECIES:
    cur += GAP_MAIN
    sp_starts[sp] = cur
    cur += sp_arcs[sp]

# ── 各蛋白弧段位置 ────────────────────────────────────────────────────────────
ref_arc_pos = {}   # acc → (start, end)
cur = ref_start
for qacc, _, qlen in ref_list:
    span = (qlen / ref_tot) * ref_arc
    ref_arc_pos[qacc] = (cur + GAP_SM/2, cur + span - GAP_SM/2)
    cur += span

sp_arc_pos = {}    # (sp, sid) → (start, end)
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
R_RIB = 0.925    # 弦的附着半径

def arc_patch(ax, a0, a1, r_out, r_in, color, lw=0.4, zorder=3, n=200):
    t  = np.linspace(a0, a1, n)
    ox, oy = r_out*np.cos(t), r_out*np.sin(t)
    tb = t[::-1]
    ix, iy = r_in*np.cos(tb),  r_in*np.sin(tb)
    xs = np.concatenate([ox, ix, [ox[0]]])
    ys = np.concatenate([oy, iy, [oy[0]]])
    verts = list(zip(xs, ys))
    codes = [Path.MOVETO] + [Path.LINETO]*(len(verts)-2) + [Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(verts, codes),
                           facecolor=color, edgecolor="white",
                           linewidth=lw, zorder=zorder))

def bezier_ribbon(ax, a1s, a1e, a2s, a2e, r=R_RIB, color="purple",
                  alpha=RIBBON_ALPHA, n=60):
    """填充贝塞尔弦：弧段1 ↔ 弧段2"""
    C = np.array([0., 0.])
    def arc(a, b, nn=n): return [(r*np.cos(t), r*np.sin(t)) for t in np.linspace(a, b, nn)]
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
                           alpha=alpha, zorder=1))

def rotated_label(ax, angle, text, r_lab, fontsize=6.5, color=LABEL_COLOR,
                  fontweight="normal"):
    """沿弧方向放置旋转标签"""
    deg = np.degrees(angle) % 360
    lx, ly = r_lab * np.cos(angle), r_lab * np.sin(angle)
    # 用 cos 值判断左右半圆，避免270°边界问题
    if np.cos(angle) >= 0:
        rot = deg - 90
        ha  = "left"
    else:
        rot = deg + 90
        ha  = "right"
    ax.text(lx, ly, text, fontsize=fontsize, color=color,
            ha=ha, va="center", rotation=rot,
            rotation_mode="anchor", zorder=6, fontweight=fontweight)

# ── 作图 ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(18, 18), facecolor=BG)
ax.set_aspect("equal")
ax.axis("off")
ax.set_facecolor(BG)
ax.set_xlim(-1.75, 1.75)
ax.set_ylim(-1.75, 1.75)

# ── (1) 弦（先画，在弧段下方） ────────────────────────────────────────────────
for qacc, _, qlen in ref_list:
    q_s, q_e = ref_arc_pos[qacc]
    q_span   = q_e - q_s
    for sp in SPECIES:
        if sp not in best[qacc]:
            continue
        h   = best[qacc][sp]
        sid = h["subject_acc"]
        if (sp, sid) not in sp_arc_pos:
            continue
        # Query 端：按比对区域缩放到弧段内
        qs_frac = (int(h["q_start"])-1) / qlen
        qe_frac = int(h["q_end"])       / qlen
        r_qs = q_s + qs_frac * q_span
        r_qe = q_s + qe_frac * q_span
        if r_qe - r_qs < 1e-5:
            r_qe = r_qs + q_span * 0.05
        # Subject 端：按比对区域缩放
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
                      color=SP_COLORS[sp], alpha=RIBBON_ALPHA)

# ── (2) Reference 蛋白弧段 ─────────────────────────────────────────────────
# 颜色在紫色范围内交替，使相邻蛋白可区分
ref_colors = ["#B54664", "#C96680"]
for i, (qacc, qname, qlen) in enumerate(ref_list):
    a_s, a_e = ref_arc_pos[qacc]
    arc_patch(ax, a_s, a_e, R_OUT, R_IN, ref_colors[i % 2])
    # 刻度（每 200 aa 一个小刻度，每 1000 aa 长刻度）
    for pos in range(0, qlen+1, 200):
        t   = a_s + (pos / qlen) * (a_e - a_s)
        h_  = 0.025 if pos % 1000 == 0 else 0.012
        ax.plot([R_OUT*np.cos(t), (R_OUT+h_)*np.cos(t)],
                [R_OUT*np.sin(t), (R_OUT+h_)*np.sin(t)],
                color="#888888", lw=0.7, zorder=5)
    # 标签
    mid = (a_s + a_e) / 2
    if (a_e - a_s) > np.radians(1.5):   # 弧段够宽才加标签
        rotated_label(ax, mid, qacc, R_OUT + 0.04, fontsize=5.5, color="#5A3080")

# ── (3) 物种 hit 弧段 ───────────────────────────────────────────────────────
sp_alt = {sp: [c, _brighter(c, 0.12)] for sp, c in SP_COLORS.items()
          for _brighter in [lambda c, f: c]}   # 占位，下面重算

def adjust_lightness(hex_color, factor=1.12):
    import colorsys
    r, g, b = [int(hex_color[i:i+2], 16)/255 for i in (1, 3, 5)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = min(1.0, l * factor)
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
    return "#{:02X}{:02X}{:02X}".format(int(r2*255), int(g2*255), int(b2*255))

for sp in SPECIES:
    base_c  = SP_COLORS[sp]
    light_c = adjust_lightness(base_c, 1.20)
    for i, (sid, info) in enumerate(sp_prots[sp].items()):
        a_s, a_e = sp_arc_pos[(sp, sid)]
        c = base_c if i % 2 == 0 else light_c
        arc_patch(ax, a_s, a_e, R_OUT, R_IN, c)
        # 刻度
        slen = info["len"]
        for pos in range(0, slen+1, 300):
            t  = a_s + (pos / slen) * (a_e - a_s)
            h_ = 0.018 if pos % 900 == 0 else 0.009
            ax.plot([R_OUT*np.cos(t), (R_OUT+h_)*np.cos(t)],
                    [R_OUT*np.sin(t), (R_OUT+h_)*np.sin(t)],
                    color="#AAAAAA", lw=0.5, zorder=5)
        # 标签
        mid = (a_s + a_e) / 2
        if (a_e - a_s) > np.radians(1.2):
            rotated_label(ax, mid, sid, R_OUT + 0.04,
                          fontsize=5.5, color=SP_COLORS[sp])

# ── (4) 物种组大标签 ─────────────────────────────────────────────────────────
SP_NAMES = {"GlyAnas":    "Anas platyrhynchos",
            "GlyColumba": "Columba livia"}
for sp in SPECIES:
    mid   = sp_starts[sp] + sp_arcs[sp] / 2
    r_lbl = R_OUT + 0.22
    lx, ly = r_lbl * np.cos(mid), r_lbl * np.sin(mid)
    # 始终保持可读：旋转角限制在 -90°~90° 之间
    deg = np.degrees(mid) % 360
    rot = deg - 90
    if rot > 90:    # 左半圆：翻转避免倒置
        rot -= 180
    elif rot < -90:
        rot += 180
    ax.text(lx, ly, SP_NAMES[sp], fontsize=11, fontweight="bold",
            color=SP_COLORS[sp], ha="center", va="center",
            rotation=rot, rotation_mode="anchor", zorder=6)

# GlyGallus (Query) 大标签
mid_ref = ref_start + ref_arc / 2
ax.text((R_OUT+0.19)*np.cos(mid_ref), (R_OUT+0.19)*np.sin(mid_ref),
        "Gallus gallus\n(Query)", fontsize=12, fontweight="bold",
        color=REF_COLOR, ha="center", va="center", zorder=6)

# ── (5) 图例 ────────────────────────────────────────────────────────────────
handles = [mpatches.Patch(color=REF_COLOR,                  label="Gallus gallus (Query)"),
           mpatches.Patch(color=SP_COLORS["GlyAnas"],    label="GlyAnas hits"),
           mpatches.Patch(color=SP_COLORS["GlyColumba"], label="GlyColumba hits")]
ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.03),
          ncol=4, frameon=False, fontsize=10, labelcolor=LABEL_COLOR)

plt.tight_layout(pad=0.3)
plt.savefig(OUT, dpi=180, bbox_inches="tight", facecolor=BG)
plt.close()
print(f"Saved → {OUT}")
