"""
鸽蛋 rcforc 3×3 组图
每个子图只显示一个偏移工况的接触力曲线
颜色与 pigeon_rcforc_yforce.png 一致
"""

import os
import re
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.signal import find_peaks
from scipy.interpolate import PchipInterpolator

# ─────────────────────────────────────────
# 配置
# ─────────────────────────────────────────
RESULTS_DIR = r"D:\system_folder\Desktop\LS-DYNA\pigeon_results"
OUTPUT_PNG  = r"D:\system_folder\Desktop\LS-DYNA\pigeon_rcforc_3x3.png"

# τ 换算参数（鸽蛋）
D_SHELL  = 2.0        # mm
T_P_UM   = 198.767    # μm

def f_to_tau(f_n):
    """F(N) → τ(MPa) = 1000·F / (π·D·T)"""
    return 1000.0 * f_n / (np.pi * D_SHELL * T_P_UM)

# 3×3 排列顺序（行优先，dX 为列，dZ 为行，与物理空间对应）
#   列：dX = -0.5, 0.0, +0.5
#   行：dZ = +0.5, 0.0, -0.5
GRID = [
    ("pos_n1_p1", "dX=−0.5, dZ=+0.5 mm"),
    ("pos_p0_p1", "dX= 0.0, dZ=+0.5 mm"),
    ("pos_p1_p1", "dX=+0.5, dZ=+0.5 mm"),
    ("pos_n1_p0", "dX=−0.5, dZ= 0.0 mm"),
    ("pos_p0_p0", "dX= 0.0, dZ= 0.0 mm"),
    ("pos_p1_p0", "dX=+0.5, dZ= 0.0 mm"),
    ("pos_n1_n1", "dX=−0.5, dZ=−0.5 mm"),
    ("pos_p0_n1", "dX= 0.0, dZ=−0.5 mm"),
    ("pos_p1_n1", "dX=+0.5, dZ=−0.5 mm"),
]

# 与 pigeon_rcforc_yforce.png 中各工况颜色一致
CASE_COLORS = {
    "pos_p1_p1": "#d62728",
    "pos_p1_n1": "#1f77b4",
    "pos_n1_p1": "#2ca02c",
    "pos_n1_n1": "#ff7f0e",
    "pos_p0_p1": "#9467bd",
    "pos_p0_n1": "#8c564b",
    "pos_p1_p0": "#e377c2",
    "pos_n1_p0": "#333333",
    "pos_p0_p0": "#bcbd22",
}

# ─────────────────────────────────────────
# 解析 rcforc
# ─────────────────────────────────────────
RE_MASTER = re.compile(
    r'master\s+\d+\s+time\s+([\d.E+\-]+)\s+x\s+[\d.E+\-]+\s+y\s+([\d.E+\-]+)'
)

def parse_rcforc(filepath):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read().replace("\n", " ")
    times, yvals = [], []
    for m in RE_MASTER.finditer(raw):
        t = float(m.group(1)) * 1e6   # s → μs
        if t > 23.0:
            continue
        times.append(t)
        yvals.append(-1.0 * float(m.group(2)))   # 取正值
    return np.array(times), np.array(yvals)

# ─────────────────────────────────────────
# 全局字体设置
# ─────────────────────────────────────────
matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   10,
    "axes.linewidth": 1.1,
})

# ─────────────────────────────────────────
# 绘图
# ─────────────────────────────────────────
fig, axes = plt.subplots(3, 3, figsize=(14, 11), sharex=True, sharey=True)
fig.suptitle(
    "Contact Y-Force vs Time — Columba Egg Parametric Study\n"
    "(Target plate offset, grid = 0.5 mm)",
    fontsize=13, fontweight="bold", y=0.995
)

for idx, (case_key, label) in enumerate(GRID):
    row, col = divmod(idx, 3)
    ax = axes[row][col]

    color = CASE_COLORS.get(case_key, "#1f77b4")

    fpath = os.path.join(RESULTS_DIR, case_key, "rcforc")
    if not os.path.exists(fpath):
        ax.text(0.5, 0.5, "No data", transform=ax.transAxes,
                ha="center", va="center", color="gray")
        ax.set_title(label, fontsize=9)
        continue

    t, y = parse_rcforc(fpath)

    # PCHIP 平滑
    t_sm = np.linspace(t[0], t[-1], len(t) * 10)
    y_sm = PchipInterpolator(t, y)(t_sm)
    tau_sm = f_to_tau(y_sm)

    # 力曲线：虚线 + 半透明
    ax.plot(t_sm, y_sm, color=color, linewidth=1.8, linestyle="--", alpha=0.6)
    ax.axhline(0, color="black", linewidth=0.8, zorder=0)

    # τ 曲线：实线，右轴
    ax2 = ax.twinx()
    ax2.plot(t_sm, tau_sm, color=color, linewidth=1.8, linestyle="-")
    ax2.set_ylim(0, 0.60)
    ax2.tick_params(axis="y", labelsize=7.5)
    ax2.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    if col == 2:
        ax2.set_ylabel("τ_normal (MPa)", fontsize=9, labelpad=4)
    else:
        ax2.tick_params(axis="y", labelright=False)

    # 第一峰（≤6 μs）
    mask6 = t_sm <= 6.0
    if mask6.any():
        y6 = y_sm[mask6];  t6 = t_sm[mask6]
        pks, _ = find_peaks(y6, height=0.01, distance=5)
        if len(pks):
            i1 = pks[np.argmax(y6[pks])]
            t1, v1 = float(t6[i1]), float(y6[i1])
            tau1 = float(f_to_tau(v1))
            # F 标注：右下方（曲线下方）
            ax.plot(t1, v1, marker="*", markersize=10, color=color,
                    markeredgewidth=0.5, markeredgecolor="white", zorder=5)
            ax.annotate(f"{v1:.2f} N", xy=(t1, v1),
                        xytext=(t1 + 0.4, v1 - 0.07),
                        fontsize=7.5, color=color, fontweight="bold",
                        arrowprops=dict(arrowstyle="->", color=color, lw=0.7))
            # τ 标注：曲线上方
            ax2.plot(t1, tau1, marker="*", markersize=10, color=color,
                     markeredgewidth=0.5, markeredgecolor="white", zorder=5)
            ax2.annotate(f"{tau1:.3f} MPa", xy=(t1, tau1),
                         xytext=(t1 + 0.4, tau1 + 0.06),
                         fontsize=7.5, color=color, fontweight="bold",
                         arrowprops=dict(arrowstyle="->", color=color, lw=0.7))

    # 全局峰值
    imax = np.argmax(y_sm)
    tp, vp = float(t_sm[imax]), float(y_sm[imax])
    taup = float(f_to_tau(vp))
    # F 标注：峰值右下方（曲线下方）
    ax.plot(tp, vp, marker="*", markersize=10, color=color,
            markeredgewidth=0.5, markeredgecolor="white", zorder=5)
    ax.annotate(f"{vp:.2f} N", xy=(tp, vp),
                xytext=(tp + 0.5, vp - 0.09),
                fontsize=7.5, color=color, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=color, lw=0.7))
    # τ 标注：峰值上方
    ax2.plot(tp, taup, marker="*", markersize=10, color=color,
             markeredgewidth=0.5, markeredgecolor="white", zorder=5)
    ax2.annotate(f"{taup:.3f} MPa", xy=(tp, taup),
                 xytext=(tp + 0.5, taup + 0.06),
                 fontsize=7.5, color=color, fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color=color, lw=0.7))

    # 子图标题
    ax.set_title(label, fontsize=9.5, pad=4)

    # 坐标轴刻度
    ax.set_xlim(0, 22)
    ax.set_ylim(0, 0.85)
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.55)

# 共用轴标签（仅最左列 / 最下行显示）
for row in range(3):
    axes[row][0].set_ylabel("Y-Force (N)", fontsize=11)
for col in range(3):
    axes[2][col].set_xlabel("Time (μs)", fontsize=11)

plt.tight_layout(rect=[0, 0, 1, 0.97])
plt.savefig(OUTPUT_PNG, dpi=180, bbox_inches="tight")
print(f"Plot saved: {OUTPUT_PNG}")
