"""
τ_normal 均值曲线对比图（单轴，以τ曲线为主）
三物种 Gallus / Columba / Anas — 逐点均值 ± 1σ 阴影带
"""

import os
import re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.interpolate import PchipInterpolator
from scipy import stats

# ─────────────────────────────────────────
# 配置
# ─────────────────────────────────────────
CHICKEN_DIR = r"D:\system_folder\Desktop\LS-DYNA\chicken_results"
PIGEON_DIR  = r"D:\system_folder\Desktop\LS-DYNA\pigeon_results"
DUCK_DIR    = r"D:\system_folder\Desktop\LS-DYNA\duck_results"
OUTPUT_PNG  = r"D:\system_folder\Desktop\LS-DYNA\tau_comparison.png"
T_MAX       = 23.0   # μs

D_SHELL    = 2.0     # mm
T_CHICKEN  = 0.29
T_PIGEON   = 0.19
T_DUCK     = 0.3462

def tau(F_N, T_mm):
    return 1000.0 * F_N / (np.pi * D_SHELL * T_mm)

CASES = [
    "pos_p1_p1", "pos_p1_n1", "pos_n1_p1", "pos_n1_n1",
    "pos_p0_p1", "pos_p0_n1", "pos_p1_p0", "pos_n1_p0", "pos_p0_p0"
]

COLOR_C = "#B54664"   # Gallus
COLOR_P = "#F0C284"   # Columba
COLOR_D = "#7895C1"   # Anas

# ─────────────────────────────────────────
# 解析 rcforc
# ─────────────────────────────────────────
RE_MASTER = re.compile(
    r'master\s+\d+\s+time\s+([\d.E+\-]+)\s+x\s+[\d.E+\-]+\s+y\s+([\d.E+\-]+)'
)

def parse_rcforc(filepath, sign=1.0):
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

def load_matrix(results_dir, sign=1.0):
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

mean_c, std_c = mat_c.mean(axis=0), mat_c.std(axis=0)
mean_p, std_p = mat_p.mean(axis=0), mat_p.std(axis=0)
have_duck = mat_d is not None
if have_duck:
    mean_d, std_d = mat_d.mean(axis=0), mat_d.std(axis=0)

# ─────────────────────────────────────────
# 每工况 τ_max → Duncan MRT
# ─────────────────────────────────────────
def per_case_taumax(mat, T_mm):
    return np.array([tau(row.max(), T_mm) for row in mat])

tau_max_c = per_case_taumax(mat_c, T_CHICKEN)
tau_max_p = per_case_taumax(mat_p, T_PIGEON)
tau_max_d = per_case_taumax(mat_d, T_DUCK) if have_duck else np.array([])

def duncan_letters(groups, names, alpha=0.05):
    """返回 {name: letter} 的 CLD 字典（仅支持 3 组）"""
    k  = len(groups)
    ns = [len(g) for g in groups]
    means = np.array([g.mean() for g in groups])
    SS_e  = sum(float(np.sum((g - g.mean())**2)) for g in groups)
    df_e  = sum(ns) - k
    MSE   = SS_e / df_e
    n_harm = k / sum(1.0 / n for n in ns)
    SE    = np.sqrt(MSE / n_harm)
    order = np.argsort(means)
    s_names = [names[i] for i in order]
    s_groups = [groups[i] for i in order]
    crit = []
    for p in range(2, k + 1):
        q = stats.studentized_range.ppf(1.0 - alpha, k=p, df=df_e)
        crit.append(q * SE)
    s_means = means[order]
    sig = np.zeros((k, k), dtype=bool)
    for i in range(k):
        for j in range(i + 1, k):
            p = j - i + 1
            sig[i, j] = sig[j, i] = (s_means[j] - s_means[i]) > crit[p - 2]
    s01, s02, s12 = bool(sig[0,1]), bool(sig[0,2]), bool(sig[1,2])
    table = {
        (False,False,False): ("a","a","a"),
        (False,False,True ): ("ab","a","b"),
        (False,True, False): ("a","ab","b"),
        (False,True, True ): ("a","a","b"),
        (True, False,False): ("a","b","ab"),
        (True, False,True ): ("a","b","a"),
        (True, True, False): ("a","b","b"),
        (True, True, True ): ("a","b","c"),
    }
    ltrs = table[(s01, s02, s12)]
    return {s_names[i]: ltrs[i] for i in range(k)}

SPECIES_NAMES = ["Gallus", "Columba", "Anas"]
groups_tau = [tau_max_c, tau_max_p, tau_max_d]
cld_letters = duncan_letters(groups_tau, SPECIES_NAMES)
print("Duncan CLD (τ_max):", cld_letters)

# τ 换算
tau_c   = tau(mean_c, T_CHICKEN)
tau_lo_c = np.clip(tau(mean_c - std_c, T_CHICKEN), 0, None)
tau_hi_c = tau(mean_c + std_c, T_CHICKEN)

tau_p   = tau(mean_p, T_PIGEON)
tau_lo_p = np.clip(tau(mean_p - std_p, T_PIGEON), 0, None)
tau_hi_p = tau(mean_p + std_p, T_PIGEON)

if have_duck:
    tau_d   = tau(mean_d, T_DUCK)
    tau_lo_d = np.clip(tau(mean_d - std_d, T_DUCK), 0, None)
    tau_hi_d = tau(mean_d + std_d, T_DUCK)

# ─────────────────────────────────────────
# 平滑（三次样条）
# ─────────────────────────────────────────
def smooth(t, y):
    t_s = np.linspace(t[0], t[-1], len(t) * 10)
    return t_s, PchipInterpolator(t, y)(t_s)

ts_c,  tms_c   = smooth(t_ref_c, tau_c)
_,     tlo_c   = smooth(t_ref_c, tau_lo_c)
_,     thi_c   = smooth(t_ref_c, tau_hi_c)

ts_p,  tms_p   = smooth(t_ref_p, tau_p)
_,     tlo_p   = smooth(t_ref_p, tau_lo_p)
_,     thi_p   = smooth(t_ref_p, tau_hi_p)

if have_duck:
    ts_d,  tms_d = smooth(t_ref_d, tau_d)
    _,     tlo_d = smooth(t_ref_d, tau_lo_d)
    _,     thi_d = smooth(t_ref_d, tau_hi_d)

# ─────────────────────────────────────────
# 绘图
# ─────────────────────────────────────────
matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "axes.linewidth": 1.2,
})

fig, ax = plt.subplots(figsize=(11, 6))

# 阴影带
ax.fill_between(ts_c, tlo_c, thi_c, color=COLOR_C, alpha=0.18, linewidth=0)
ax.fill_between(ts_p, tlo_p, thi_p, color=COLOR_P, alpha=0.18, linewidth=0)
if have_duck:
    ax.fill_between(ts_d, tlo_d, thi_d, color=COLOR_D, alpha=0.18, linewidth=0)

# 均值曲线（实线，加粗）
ax.plot(ts_c, tms_c, color=COLOR_C, linewidth=2.5, linestyle="-",
        label=f"Gallus   (n={mat_c.shape[0]},  τ mean±1σ)")
ax.plot(ts_p, tms_p, color=COLOR_P, linewidth=2.5, linestyle="-",
        label=f"Columba  (n={mat_p.shape[0]},  τ mean±1σ)")
if have_duck:
    ax.plot(ts_d, tms_d, color=COLOR_D, linewidth=2.5, linestyle="-",
            label=f"Anas     (n={mat_d.shape[0]},  τ mean±1σ)")

# 峰值标注（每物种独立指定文本坐标，避免重叠）
def annotate_peak(ts, tms, tsd, color, letter, txt_xy):
    """tsd: 平滑后的 τ 标准差曲线"""
    imax = np.argmax(tms)
    peak_xy = (ts[imax], tms[imax])
    ax.annotate(f"{tms[imax]:.1f}±{tsd[imax]:.1f}",
                xy=peak_xy,
                xytext=txt_xy,
                fontsize=10.5, color=color, fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=color, lw=1.1))
    # CLD 字母标注（数值文本正上方）
    ax.text(txt_xy[0], txt_xy[1] + 28, letter,
            ha="center", va="bottom",
            fontsize=15, fontweight="bold", color=color)

# τ 标准差平滑曲线
_, tsd_c = smooth(t_ref_c, tau(std_c, T_CHICKEN))
_, tsd_p = smooth(t_ref_p, tau(std_p, T_PIGEON))
if have_duck:
    _, tsd_d = smooth(t_ref_d, tau(std_d, T_DUCK))

# 根据各曲线峰值位置手动错开
annotate_peak(ts_c, tms_c, tsd_c, COLOR_C, cld_letters["Gallus"],  txt_xy=(15.5, 590))
annotate_peak(ts_p, tms_p, tsd_p, COLOR_P, cld_letters["Columba"], txt_xy=(11.5, 120))
if have_duck:
    annotate_peak(ts_d, tms_d, tsd_d, COLOR_D, cld_letters["Anas"], txt_xy=( 8.0,  80))

# 轴装饰
ax.set_xlabel("Time (μs)", fontsize=13)
ax.set_ylabel("τ (MPa)", fontsize=13)
ax.set_title(
    "Contact Shear Stress τ vs Time — Gallus / Columba / Anas Egg\n"
    "(Mean ± 1σ across 9 offset positions, grid = 0.5 mm)",
    fontsize=12.5, fontweight="bold"
)
ax.axhline(0, color="black", linewidth=0.9, zorder=0)
ax.set_xlim(0, 19)
ax.set_ylim(-20, None)
ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.6)
ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))

ax.legend(loc="upper left", fontsize=10.5, framealpha=0.88,
          edgecolor="#cccccc", borderpad=0.8, handlelength=2.2)

plt.tight_layout()
plt.savefig(OUTPUT_PNG, dpi=180, bbox_inches="tight")
print(f"Plot saved: {OUTPUT_PNG}")
plt.close('all')
