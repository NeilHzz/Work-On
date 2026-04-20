"""
Duncan's Multiple Range Test (DMRT)
三物种 Chicken / Pigeon / Duck — F_max 与 τ_max
α = 0.05，n = 9 个偏移工况
"""

import os
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy import stats

# ─────────────────────────────────────────
# 配置
# ─────────────────────────────────────────
CHICKEN_DIR = r"D:\system_folder\Desktop\LS-DYNA\chicken_results"
PIGEON_DIR  = r"D:\system_folder\Desktop\LS-DYNA\pigeon_results"
DUCK_DIR    = r"D:\system_folder\Desktop\LS-DYNA\duck_results"
OUTPUT_PNG  = r"D:\system_folder\Desktop\LS-DYNA\duncan_comparison.png"
OUTPUT_XLSX = r"D:\system_folder\Desktop\LS-DYNA\duncan_comparison.xlsx"

T_MAX    = 23.0   # μs
D_SHELL  = 2.0    # mm
T_C_MM   = 0.29        # Chicken 壳厚 mm
T_P_MM   = 0.19        # Pigeon  壳厚 mm
T_D_MM   = 0.3462      # Duck    壳厚 mm（346.2 μm 实测）

CASES = [
    "pos_p1_p1", "pos_p1_n1", "pos_n1_p1", "pos_n1_n1",
    "pos_p0_p1", "pos_p0_n1", "pos_p1_p0", "pos_n1_p0", "pos_p0_p0",
]

SPECIES = ["Gallus",   "Columba",  "Anas"]
SIGNS   = [+1.0,      -1.0,       +1.0]
T_MMS   = [T_C_MM,    T_P_MM,     T_D_MM]
DIRS    = [CHICKEN_DIR, PIGEON_DIR, DUCK_DIR]
COLORS  = ["#B54664",   "#F0C284",  "#7895C1"]

# ─────────────────────────────────────────
# 数据加载
# ─────────────────────────────────────────
RE_MASTER = re.compile(
    r'master\s+\d+\s+time\s+([\d.E+\-]+)\s+x\s+[\d.E+\-]+\s+y\s+([\d.E+\-]+)'
)

def parse_rcforc(filepath, sign=1.0):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read().replace("\n", " ")
    ts, ys = [], []
    for m in RE_MASTER.finditer(raw):
        t = float(m.group(1)) * 1e6
        if t > T_MAX:
            continue
        ts.append(t)
        ys.append(sign * float(m.group(2)))
    return np.array(ts), np.array(ys)

def load_species(d, sign, T_mm):
    f_vals, tau_vals = [], []
    for case in CASES:
        fp = os.path.join(d, case, "rcforc")
        if not os.path.exists(fp):
            continue
        _, y = parse_rcforc(fp, sign=sign)
        fmax = float(y.max())
        f_vals.append(fmax)
        tau_vals.append(fmax / (np.pi * D_SHELL * T_mm))
    return np.array(f_vals), np.array(tau_vals)

F_DATA, TAU_DATA = [], []
for d, s, t in zip(DIRS, SIGNS, T_MMS):
    fv, tv = load_species(d, s, t)
    F_DATA.append(fv)
    TAU_DATA.append(tv)

for sp, f, t in zip(SPECIES, F_DATA, TAU_DATA):
    print(f"  {sp:<10}  n={len(f)}  F_max: {f.mean():.4f}±{f.std(ddof=1):.4f} N"
          f"   τ_max: {t.mean():.4f}±{t.std(ddof=1):.4f} MPa")

# ─────────────────────────────────────────
# Duncan's Multiple Range Test 实现
# ─────────────────────────────────────────

def _cld3(names, sig):
    """
    3 组的 Compact Letter Display（sorted ascending by mean）。
    sig[i,j]=True 表示组 i 与组 j 存在显著差异。
    """
    s01 = bool(sig[0, 1])
    s02 = bool(sig[0, 2])
    s12 = bool(sig[1, 2])
    # 8 种组合的 CLD（0=最小均值, 2=最大均值）
    #           s01    s02    s12   → letters(0, 1, 2)
    table = {
        (False, False, False): ("a",  "a",  "a"),   # 全不显著
        (False, False, True ): ("ab", "a",  "b"),   # 非传递：0≈1, 0≈2, 1≠2
        (False, True,  False): ("a",  "ab", "b"),   # 非传递：0≈1, 1≈2, 0≠2
        (False, True,  True ): ("a",  "a",  "b"),   # 正常：0=1 < 2
        (True,  False, False): ("a",  "b",  "ab"),  # 非传递：0≠1, 0≈2, 1≈2
        (True,  False, True ): ("a",  "b",  "a"),   # 完全非传递（极罕见）
        (True,  True,  False): ("a",  "b",  "b"),   # 正常：0 < 1=2
        (True,  True,  True ): ("a",  "b",  "c"),   # 全显著
    }
    ltrs = table[(s01, s02, s12)]
    return {names[i]: ltrs[i] for i in range(3)}


def duncan_mrt(groups, names, alpha=0.05):
    """
    Duncan's Multiple Range Test（单因素方差分析后多重比较）。

    参数
    ----
    groups  : list of 1-D numpy arrays，每组观察值
    names   : list of str，各组名称
    alpha   : 显著水平（默认 0.05）

    返回
    ----
    dict 包含 ANOVA 结果、临界极差、显著性矩阵、CLD 字母等
    """
    k  = len(groups)
    ns = [len(g) for g in groups]
    means = np.array([g.mean() for g in groups])

    # ── 单因素 ANOVA ──────────────────────────────────────
    f_stat, p_anova = stats.f_oneway(*groups)

    # ── MSE & df_e ────────────────────────────────────────
    SS_e = sum(float(np.sum((g - g.mean())**2)) for g in groups)
    df_e = sum(ns) - k
    MSE  = SS_e / df_e

    # ── 调和均值 n（等样本量时等于 n）──────────────────────
    n_harm = k / sum(1.0 / n for n in ns)
    SE     = np.sqrt(MSE / n_harm)

    # ── 按均值升序排列 ──────────────────────────────────────
    order    = np.argsort(means)
    s_means  = means[order]
    s_names  = [names[i]        for i in order]
    s_groups = [groups[i]       for i in order]
    s_stds   = np.array([groups[i].std(ddof=1) for i in order])
    s_ns     = [ns[i]           for i in order]

    # ── Duncan 临界极差 R_p（p = 2, ..., k）─────────────────
    # R_p = q_α(p, df_e) × SE_mean
    # 使用 scipy.stats.studentized_range（Tukey 全域分布）
    crit = []
    for p in range(2, k + 1):
        q_p = stats.studentized_range.ppf(1.0 - alpha, k=p, df=df_e)
        crit.append(q_p * SE)

    # ── 显著性矩阵（排序后编号）──────────────────────────────
    sig   = np.zeros((k, k), dtype=bool)
    diffs = np.zeros((k, k))
    for i in range(k):
        for j in range(i + 1, k):
            p  = j - i + 1          # 跨度
            d  = s_means[j] - s_means[i]
            Rp = crit[p - 2]        # crit[0]=R2, crit[1]=R3, ...
            sig[i, j] = sig[j, i] = (d > Rp)
            diffs[i, j] = d
            diffs[j, i] = -d

    # ── CLD 字母标注 ─────────────────────────────────────────
    letters = _cld3(s_names, sig) if k == 3 else {}

    return dict(
        f_stat=f_stat, p_anova=p_anova,
        MSE=MSE, df_e=df_e, SE=SE,
        order=order,
        s_names=s_names, s_means=s_means, s_stds=s_stds,
        s_groups=s_groups, s_ns=s_ns,
        crit=crit, sig=sig, diffs=diffs, letters=letters,
    )


# ─────────────────────────────────────────
# 执行检验
# ─────────────────────────────────────────
res_F   = duncan_mrt(F_DATA,   SPECIES)
res_tau = duncan_mrt(TAU_DATA, SPECIES)


# ─────────────────────────────────────────
# 控制台输出
# ─────────────────────────────────────────
def sig_star(sig_bool):
    return "sig **" if sig_bool else "ns"

def print_dmrt(label, res):
    print(f"\n{'='*62}")
    print(f"  Duncan's MRT — {label}")
    print(f"{'='*62}")
    print(f"  One-way ANOVA:  F = {res['f_stat']:.4f},  p = {res['p_anova']:.4e}")
    print(f"  MSE = {res['MSE']:.6f}  |  df_error = {res['df_e']}  |  SE_mean = {res['SE']:.6f}")
    print(f"\n  临界极差（Critical Ranges）:")
    for idx, Rp in enumerate(res['crit']):
        print(f"    R{idx+2} = {Rp:.6f}")
    print(f"\n  {'Species':<12}  {'n':>3}  {'Mean':>10}  {'SD':>9}  {'Letter':>6}")
    print(f"  {'-'*50}")
    for i, nm in enumerate(res['s_names']):
        ltr = res['letters'].get(nm, '?')
        print(f"  {nm:<12}  {res['s_ns'][i]:>3}  {res['s_means'][i]:>10.4f}  "
              f"{res['s_stds'][i]:>9.4f}  {ltr:>6}")
    k = len(res['s_names'])
    print(f"\n  两两比较（sorted order）:")
    for i in range(k):
        for j in range(i + 1, k):
            p   = j - i + 1
            d   = res['diffs'][i, j]
            Rp  = res['crit'][p - 2]
            sig = res['sig'][i, j]
            sig_lbl = "***" if sig else " ns"
            print(f"    {res['s_names'][i]} vs {res['s_names'][j]:12} "
                  f"diff={d:+.4f}  R{p}={Rp:.4f}  [{sig_lbl}]")

print_dmrt("F_max (N)",    res_F)
print_dmrt("τ_max (MPa)",  res_tau)


# ─────────────────────────────────────────
# Excel 输出
# ─────────────────────────────────────────
def dmrt_to_rows(res, metric_col):
    rows = []
    for i, nm in enumerate(res['s_names']):
        rows.append({
            "Species":       nm,
            "n":             res['s_ns'][i],
            metric_col:      round(float(res['s_means'][i]), 6),
            "SD":            round(float(res['s_stds'][i]), 6),
            "Duncan Letter": res['letters'].get(nm, ''),
        })
    # 追加临界极差
    rows.append({})
    rows.append({"Species": "─ Critical Ranges ─"})
    for idx, Rp in enumerate(res['crit']):
        rows.append({"Species": f"R{idx+2}", metric_col: round(Rp, 6)})
    # ANOVA summary
    rows.append({})
    rows.append({"Species": "ANOVA F",  metric_col: round(res['f_stat'],  6)})
    rows.append({"Species": "ANOVA p",  metric_col: round(res['p_anova'], 9)})
    rows.append({"Species": "MSE",      metric_col: round(res['MSE'],     9)})
    rows.append({"Species": "df_error", metric_col: res['df_e']})
    # Pairwise
    rows.append({})
    rows.append({"Species": "─ Pairwise ─"})
    k = len(res['s_names'])
    for i in range(k):
        for j in range(i + 1, k):
            p    = j - i + 1
            d    = res['diffs'][i, j]
            Rp   = res['crit'][p - 2]
            sig  = res['sig'][i, j]
            rows.append({
                "Species":           f"{res['s_names'][i]} vs {res['s_names'][j]}",
                metric_col:          round(float(d), 6),
                "SD":                round(float(Rp), 6),
                "Duncan Letter":     "sig" if sig else "ns",
            })
    return rows

# Raw data sheet
raw_rows = []
for sp, fv, tv in zip(SPECIES, F_DATA, TAU_DATA):
    for case, fval, tval in zip(CASES[:len(fv)], fv, tv):
        raw_rows.append({"Species": sp, "Case": case,
                         "F_max (N)": round(float(fval), 6),
                         "τ_max (MPa)": round(float(tval), 6)})

with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
    pd.DataFrame(dmrt_to_rows(res_F,   "F_max (N)"  )).to_excel(
        writer, sheet_name="F_max_Duncan",   index=False)
    pd.DataFrame(dmrt_to_rows(res_tau, "τ_max (MPa)")).to_excel(
        writer, sheet_name="tau_max_Duncan",  index=False)
    pd.DataFrame(raw_rows).to_excel(
        writer, sheet_name="Raw_Data",        index=False)

print(f"\nExcel saved: {OUTPUT_XLSX}")


# ─────────────────────────────────────────
# 绘图
# ─────────────────────────────────────────
matplotlib.rcParams.update({
    "font.family":    "DejaVu Sans",
    "font.size":      12,
    "axes.linewidth": 1.3,
})

fig, axes = plt.subplots(1, 2, figsize=(12, 6.5))
fig.suptitle(
    "Duncan's Multiple Range Test — Egg Shell Impact Simulation\n"
    "(n = 9 per species, α = 0.05;  same letter = no significant difference)",
    fontsize=12.5, fontweight="bold"
)

rng = np.random.default_rng(42)

def plot_dmrt(ax, res, data_orig, metric_label, unit):
    """Bar (mean) + SD error bar + jittered scatter + Duncan letter."""
    orig_means = np.array([g.mean() for g in data_orig])
    orig_stds  = np.array([g.std(ddof=1) for g in data_orig])

    x = np.arange(len(SPECIES))

    # ── 柱状图 ────────────────────────────────────────────────
    bars = ax.bar(x, orig_means, width=0.5,
                  color=COLORS, alpha=0.70,
                  edgecolor="k", linewidth=1.0, zorder=2)

    # ── 误差棒 ────────────────────────────────────────────────
    ax.errorbar(x, orig_means, yerr=orig_stds,
                fmt="none", ecolor="k",
                elinewidth=1.8, capsize=7, capthick=1.8, zorder=3)

    # ── 散点（jitter）────────────────────────────────────────
    for xi, sp_data, color in zip(x, data_orig, COLORS):
        jitter = rng.uniform(-0.14, 0.14, size=len(sp_data))
        ax.scatter(xi + jitter, sp_data, s=36,
                   color=color, edgecolors="k",
                   linewidths=0.5, zorder=4, alpha=0.90)

    # ── 显著差异连线标注 ─────────────────────────────────────
    y_top  = orig_means + orig_stds
    y_max  = float(y_top.max())
    # 将排序后的显著对用括号线标出，针对原始 SPECIES 顺序
    def sp_idx(name):
        return SPECIES.index(name)

    k = len(res['s_names'])
    bracket_y = y_max * 1.08
    for i in range(k):
        for j in range(i + 1, k):
            if res['sig'][i, j]:
                xi = sp_idx(res['s_names'][i])
                xj = sp_idx(res['s_names'][j])
                x_lo, x_hi = sorted([xi, xj])
                by = bracket_y
                ax.plot([x_lo, x_lo, x_hi, x_hi],
                        [by - y_max*0.01, by, by, by - y_max*0.01],
                        color="k", linewidth=1.1, zorder=5)
                ax.text((x_lo + x_hi) / 2, by + y_max * 0.01,
                        "***", ha="center", va="bottom",
                        fontsize=13, color="k")
                bracket_y += y_max * 0.09

    # ── 坐标轴装饰 ────────────────────────────────────────────
    ax.set_xticks(x)
    ax.set_xticklabels(SPECIES, fontsize=12.5)
    ax.set_ylabel(f"{metric_label} ({unit})", fontsize=13)
    ax.set_ylim(0, bracket_y * 1.12)
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.5, zorder=0)
    ax.set_title(
        f"{metric_label}\n"
        f"ANOVA:  F = {res['f_stat']:.2f},  p = {res['p_anova']:.2e}",
        fontsize=11.5, pad=8
    )




plot_dmrt(axes[0], res_F,   F_DATA,   "F_max",  "N")
plot_dmrt(axes[1], res_tau, TAU_DATA, "τ_max",  "MPa")

plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.savefig(OUTPUT_PNG, dpi=180, bbox_inches="tight")
print(f"Plot saved:  {OUTPUT_PNG}")
plt.close("all")
