"""
Chicken vs Pigeon vs Duck 均值曲线对比图
逐点均值 ± 1σ 阴影带，三物种放在同一张图
"""

import os
import re
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.interpolate import PchipInterpolator

# ─────────────────────────────────────────
# 配置
# ─────────────────────────────────────────
CHICKEN_DIR = r"D:\system_folder\Desktop\LS-DYNA\chicken_results"
PIGEON_DIR  = r"D:\system_folder\Desktop\LS-DYNA\pigeon_results"
DUCK_DIR    = r"D:\system_folder\Desktop\LS-DYNA\duck_results"
OUTPUT_PNG  = r"D:\system_folder\Desktop\LS-DYNA\mean_comparison.png"
T_MAX       = 23.0   # μs

# 壳厚参数（mm）
D_SHELL    = 2.0
T_CHICKEN  = 0.29
T_PIGEON   = 0.19
T_DUCK     = 0.3462  # 实测值 346.2 μm

def tau(F_N, T_mm):
    return 1000.0 * F_N / (np.pi * D_SHELL * T_mm)

CASES = [
    "pos_p1_p1", "pos_p1_n1", "pos_n1_p1", "pos_n1_n1",
    "pos_p0_p1", "pos_p0_n1", "pos_p1_p0", "pos_n1_p0", "pos_p0_p0"
]

# ─────────────────────────────────────────
# 解析 rcforc
# ─────────────────────────────────────────
RE_MASTER = re.compile(
    r'master\s+\d+\s+time\s+([\d.E+\-]+)\s+x\s+[\d.E+\-]+\s+y\s+([\d.E+\-]+)'
)

def parse_rcforc(filepath, sign=-1.0):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read().replace("\n", " ")
    times, yvals = [], []
    for m in RE_MASTER.finditer(raw):
        t = float(m.group(1)) * 1e6
        if t > T_MAX:
            continue
        times.append(t)
        yvals.append(sign * float(m.group(2)))
    return np.array(times), np.array(yvals)

def load_matrix(results_dir, sign=-1.0):
    """返回 (t_ref, matrix)，matrix shape = (n_cases, n_timepoints)"""
    all_t, all_y = [], []
    for case_key in CASES:
        fpath = os.path.join(results_dir, case_key, "rcforc")
        if os.path.exists(fpath):
            t, y = parse_rcforc(fpath, sign=sign)
            all_t.append(t)
            all_y.append(y)
    if not all_t:
        return None, None
    t_ref = all_t[0]
    matrix = np.vstack([np.interp(t_ref, t, y) for t, y in zip(all_t, all_y)])
    return t_ref, matrix

t_ref_c, mat_c = load_matrix(CHICKEN_DIR, sign=+1.0)
t_ref_p, mat_p = load_matrix(PIGEON_DIR,  sign=-1.0)
t_ref_d, mat_d = load_matrix(DUCK_DIR,    sign=+1.0)

# 逐点均值 / 标准差
mean_c, std_c = mat_c.mean(axis=0), mat_c.std(axis=0)
mean_p, std_p = mat_p.mean(axis=0), mat_p.std(axis=0)
have_duck = mat_d is not None
if have_duck:
    mean_d, std_d = mat_d.mean(axis=0), mat_d.std(axis=0)

# ─────────────────────────────────────────
# 平滑（三次样条）
# ─────────────────────────────────────────
def smooth(t, y):
    t_s = np.linspace(t[0], t[-1], len(t) * 10)
    return t_s, PchipInterpolator(t, y)(t_s)

ts_c,  ms_c  = smooth(t_ref_c, mean_c)
_,     lo_c  = smooth(t_ref_c, mean_c - std_c)
_,     hi_c  = smooth(t_ref_c, mean_c + std_c)

ts_p,  ms_p  = smooth(t_ref_p, mean_p)
_,     lo_p  = smooth(t_ref_p, mean_p - std_p)
_,     hi_p  = smooth(t_ref_p, mean_p + std_p)

# clip 下界不低于 0
lo_c = np.clip(lo_c, 0, None)
lo_p = np.clip(lo_p, 0, None)

if have_duck:
    ts_d,  ms_d  = smooth(t_ref_d, mean_d)
    _,     lo_d  = smooth(t_ref_d, mean_d - std_d)
    _,     hi_d  = smooth(t_ref_d, mean_d + std_d)
    lo_d = np.clip(lo_d, 0, None)

# ─────────────────────────────────────────
# 绘图
# ─────────────────────────────────────────
matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "axes.linewidth": 1.2,
})

COLOR_C = "#B54664"   # Gallus
COLOR_P = "#F0C284"   # Columba
COLOR_D = "#7895C1"   # Anas

fig, ax = plt.subplots(figsize=(13, 6))
ax2 = ax.twinx()   # 右轴:τ (MPa)

# 阴影带 (F轴)
ax.fill_between(ts_c, lo_c, hi_c, color=COLOR_C, alpha=0.15, linewidth=0)
ax.fill_between(ts_p, lo_p, hi_p, color=COLOR_P, alpha=0.15, linewidth=0)
if have_duck:
    ax.fill_between(ts_d, lo_d, hi_d, color=COLOR_D, alpha=0.15, linewidth=0)

# 均值曲线 F(虚线) + τ(实线)
def plot_species(ts, ms, T_mm, color, label_name, n):
    tau_ms = tau(ms, T_mm)
    ax.plot(ts, ms,     color=color, linewidth=2.2, linestyle="--", alpha=0.8,
            label=f"{label_name}  (n={n},  F mean±1σ)")
    ax2.plot(ts, tau_ms, color=color, linewidth=2.2, linestyle="-",
             label=f"{label_name}  τ")

plot_species(ts_c, ms_c, T_CHICKEN, COLOR_C, "Gallus egg",  mat_c.shape[0])
plot_species(ts_p, ms_p, T_PIGEON,  COLOR_P, "Columba egg", mat_p.shape[0])
if have_duck:
    plot_species(ts_d, ms_d, T_DUCK, COLOR_D, "Anas egg",   mat_d.shape[0])
    ax.fill_between(ts_d, tau(lo_d, T_DUCK), tau(hi_d, T_DUCK),  # τ 阴影
                    color=COLOR_D, alpha=0.12, linewidth=0, transform=ax2.transData)
ax.fill_between(ts_c, tau(lo_c, T_CHICKEN), tau(hi_c, T_CHICKEN),
                color=COLOR_C, alpha=0.12, linewidth=0, transform=ax2.transData)
ax.fill_between(ts_p, tau(lo_p, T_PIGEON), tau(hi_p, T_PIGEON),
                color=COLOR_P, alpha=0.12, linewidth=0, transform=ax2.transData)

# 峰值标注 (F)
def annotate_peak(ax_obj, ts, ms, color, dy=0.03):
    imax = np.argmax(ms)
    ax_obj.annotate(f"{ms[imax]:.2f}",
                    xy=(ts[imax], ms[imax]),
                    xytext=(ts[imax] + 0.5, ms[imax] + dy),
                    fontsize=10.5, color=color, fontweight="bold",
                    arrowprops=dict(arrowstyle="-", color=color, lw=1.1))

annotate_peak(ax, ts_c, ms_c, COLOR_C)
annotate_peak(ax, ts_p, ms_p, COLOR_P)
if have_duck:
    annotate_peak(ax, ts_d, ms_d, COLOR_D)

# 峰值标注 (τ)
def annotate_tau_peak(ax_obj, ts, ms, T_mm, color, dy=0.02):
    tau_ms = tau(ms, T_mm)
    imax = np.argmax(tau_ms)
    ax_obj.annotate(f"{tau_ms[imax]:.3f}",
                    xy=(ts[imax], tau_ms[imax]),
                    xytext=(ts[imax] - 2.0, tau_ms[imax] + dy),
                    fontsize=10.5, color=color, fontweight="bold",
                    arrowprops=dict(arrowstyle="-", color=color, lw=1.1))

annotate_tau_peak(ax2, ts_c, ms_c, T_CHICKEN, COLOR_C)
annotate_tau_peak(ax2, ts_p, ms_p, T_PIGEON,  COLOR_P)
if have_duck:
    annotate_tau_peak(ax2, ts_d, ms_d, T_DUCK, COLOR_D)

# 统计框
lines  = [f"{'Species':<12} {'F_max (N)':>12}  {'T (μm)':>8}  {'τ_max (MPa)':>13}"]
lines += ["-" * 52]
for name, ms, std, T_mm in [
    ("Gallus",   mean_c, std_c, T_CHICKEN),
    ("Columba",  mean_p, std_p, T_PIGEON),
] + ([("Anas", mean_d, std_d, T_DUCK)] if have_duck else []):
    imax = np.argmax(ms)
    fv, fs = ms[imax], std[imax]
    tv = tau(fv, T_mm)
    lines.append(f"{name:<12} {fv:>8.3f}±{fs:>5.3f}  {T_mm*1000:>8.1f}  {tv:>13.4f}")
stats_txt = "\n".join(lines)
ax.text(0.99, 0.97, stats_txt,
        transform=ax.transAxes, ha="right", va="top",
        fontsize=9.5, family="monospace",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                  edgecolor="#aaaaaa", alpha=0.92))

# 轴明、标题、布局
ax.set_xlabel("Time (μs)", fontsize=13)
ax.set_ylabel("Y-Force (N)", fontsize=13)
ax2.set_ylabel("τ_normal (MPa)", fontsize=13)
ax.set_title(
    "Contact Y-Force vs Time — Gallus / Columba / Anas Egg\n"
    "(Mean ± 1σ across 9 offset positions, grid = 0.5 mm  |  ―― F(N)   ── τ(MPa))",
    fontsize=12.5, fontweight="bold"
)
ax.axhline(0, color="black", linewidth=0.9, zorder=0)
ax.set_xlim(0, 22)
ax.set_ylim(-0.1, 1.4)
ax2.set_ylim(-0.1 / (np.pi * D_SHELL * T_PIGEON) * 1000,
             1.4   / (np.pi * D_SHELL * T_PIGEON) * 1000)
ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.6)
ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
ax2.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))

# 合并图例（只展示 F 曲线，避免重复）
handles_f, labels_f = ax.get_legend_handles_labels()
ax.legend(handles_f, labels_f,
          loc="upper left", fontsize=10.5, framealpha=0.88,
          edgecolor="#cccccc", borderpad=0.8, handlelength=2.2)

plt.tight_layout()
plt.savefig(OUTPUT_PNG, dpi=180, bbox_inches="tight")
print(f"Plot saved: {OUTPUT_PNG}")
plt.close('all')
