"""
LS-DYNA rcforc 后处理脚本（鸽鸟版）
从 pigeon_results/ 各工况的 rcforc 文件中提取 master Y 接触力
保存到 Excel，并绘制曲线图
"""

import os
import re
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.signal import find_peaks
from scipy.interpolate import PchipInterpolator

# ─────────────────────────────────────────
# 配置
# ─────────────────────────────────────────
RESULTS_DIR  = r"D:\system_folder\Desktop\LS-DYNA\pigeon_results"
OUTPUT_EXCEL = r"D:\system_folder\Desktop\LS-DYNA\pigeon_rcforc_yforce.xlsx"
OUTPUT_PNG   = r"D:\system_folder\Desktop\LS-DYNA\pigeon_rcforc_yforce.png"

CASES = [
    ("pos_p1_p1", "dX=+0.5, dZ=+0.5 mm"),
    ("pos_p1_n1", "dX=+0.5, dZ=-0.5 mm"),
    ("pos_n1_p1", "dX=-0.5, dZ=+0.5 mm"),
    ("pos_n1_n1", "dX=-0.5, dZ=-0.5 mm"),
    ("pos_p0_p1", "dX= 0.0, dZ=+0.5 mm"),
    ("pos_p0_n1", "dX= 0.0, dZ=-0.5 mm"),
    ("pos_p1_p0", "dX=+0.5, dZ= 0.0 mm"),
    ("pos_n1_p0", "dX=-0.5, dZ= 0.0 mm"),
]

COLORS = ["#d62728", "#1f77b4", "#2ca02c", "#ff7f0e",
          "#9467bd", "#8c564b", "#e377c2", "#333333"]

# ─────────────────────────────────────────
# 解析 rcforc
# ─────────────────────────────────────────
RE_MASTER = re.compile(
    r'master\s+\d+\s+time\s+([\d.E+\-]+)\s+x\s+[\d.E+\-]+\s+y\s+([\d.E+\-]+)'
)

def parse_rcforc(filepath):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    raw = raw.replace("\n", " ")
    times, yvals = [], []
    for m in RE_MASTER.finditer(raw):
        t = float(m.group(1))
        y = -1.0 * float(m.group(2))
        times.append(t * 1e6)   # s → μs
        yvals.append(y)
    return np.array(times), np.array(yvals)


# ─────────────────────────────────────────
# 读取所有工况
# ─────────────────────────────────────────
data = {}
for case_key, _ in CASES:
    fpath = os.path.join(RESULTS_DIR, case_key, "rcforc")
    if not os.path.exists(fpath):
        print(f"[SKIP] {case_key}: rcforc not found")
        continue
    t, y = parse_rcforc(fpath)
    data[case_key] = (t, y)
    print(f"  {case_key}: {len(t)} points, max Y = {y.max():.4f} N")

# ─────────────────────────────────────────
# 保存到 Excel
# ─────────────────────────────────────────
with pd.ExcelWriter(OUTPUT_EXCEL, engine="openpyxl") as writer:
    for case_key, label in CASES:
        if case_key not in data:
            continue
        t, y = data[case_key]
        df = pd.DataFrame({"Time (μs)": t, "Y-Force (N)": y})
        df.to_excel(writer, sheet_name=case_key[:31], index=False)

    # Summary sheet（插值到第一个工况的时间轴）
    ref_key = next((k for k, _ in CASES if k in data), None)
    if ref_key:
        t_ref, _ = data[ref_key]
        summary = pd.DataFrame({"Time (μs)": t_ref})
        for case_key, label in CASES:
            if case_key not in data:
                continue
            t, y = data[case_key]
            summary[label] = np.interp(t_ref, t, y, left=0, right=0)
        summary.to_excel(writer, sheet_name="Summary", index=False)

print(f"\nExcel saved: {OUTPUT_EXCEL}")

# ─────────────────────────────────────────
# 绘图
# ─────────────────────────────────────────
matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.linewidth": 1.2,
})

fig, ax = plt.subplots(figsize=(14, 7))

peak_firsts = []
peak_maxs   = []

for idx, (case_key, label) in enumerate(CASES):
    if case_key not in data:
        continue
    t, y = data[case_key]
    color = COLORS[idx]
    # 三次 PCHIP 平滑曲线（保形，不过冲）
    t_smooth = np.linspace(t[0], t[-1], len(t) * 10)
    y_smooth = PchipInterpolator(t, y)(t_smooth)
    ax.plot(t_smooth, y_smooth, color=color, linewidth=1.6, label=label)

    # 第一个峰（前 6 μs，取正值峰）
    mask_early = t <= 6.0
    if mask_early.any():
        local_y = y[mask_early]
        local_t = t[mask_early]
        pks, _ = find_peaks(local_y, height=0.01, distance=3)
        i1 = pks[np.argmax(local_y[pks])] if len(pks) > 0 else np.argmax(local_y)
        v1, t1 = local_y[i1], local_t[i1]
        mask_s1 = (t_smooth >= t1 - 1.0) & (t_smooth <= t1 + 1.0)
        vs1_idx = np.argmax(y_smooth[mask_s1])
        t1_s = t_smooth[mask_s1][vs1_idx]
        v1_s  = y_smooth[mask_s1][vs1_idx]
        ax.plot(t1_s, v1_s, marker="*", markersize=13, color=color,
                markeredgewidth=0.5, markeredgecolor="white", zorder=5)
        ax.annotate(f"{v1_s:.2f}", xy=(t1_s, v1_s),
                    xytext=(t1_s + 0.1, v1_s + 0.03),
                    fontsize=9, color=color, fontweight="bold")
        peak_firsts.append(v1_s)

    # 全局峰值 —— 从样条曲线取峰，与视觉一致
    imax_s = np.argmax(y_smooth)
    t_peak, v_peak = t_smooth[imax_s], y_smooth[imax_s]
    ax.plot(t_peak, v_peak, marker="*", markersize=13, color=color,
            markeredgewidth=0.5, markeredgecolor="white", zorder=5)
    ax.annotate(f"{v_peak:.2f}", xy=(t_peak, v_peak),
                xytext=(t_peak + 0.15, v_peak + 0.025),
                fontsize=9, color=color, fontweight="bold")
    peak_maxs.append(v_peak)

# 统计框
if peak_firsts and peak_maxs:
    mu1, s1 = np.mean(peak_firsts), np.std(peak_firsts)
    mum, sm = np.mean(peak_maxs),   np.std(peak_maxs)
    stats_text = (
        f"8-case statistics (N)\n"
        f"1st peak : {mu1:.3f} ± {s1:.3f}\n"
        f"Peak (max): {mum:.3f} ± {sm:.3f}"
    )
    ax.text(0.99, 0.04, stats_text,
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=10, family="monospace",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                      edgecolor="#aaaaaa", alpha=0.9))

ax.set_xlabel("Time (μs)", fontsize=13)
ax.set_ylabel("Y-Force (N)", fontsize=13)
ax.set_title(
    "Contact Y-Force vs Time — Pigeon Egg Parametric Study\n"
    "(Target plate horizontal offset, grid = 0.5 mm)",
    fontsize=13, fontweight="bold"
)
ax.axhline(0, color="black", linewidth=1.0, zorder=0)
ax.set_xlim(0, 22)
ax.set_ylim(-0.2, 1.4)
ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.6)
ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
ax.legend(loc="upper right", fontsize=9.5, framealpha=0.85,
          edgecolor="#cccccc", borderpad=0.8, handlelength=2.0)

plt.tight_layout()
plt.savefig(OUTPUT_PNG, dpi=180, bbox_inches="tight")
print(f"Plot saved: {OUTPUT_PNG}")
plt.show()
