"""
截断 23 μs 后数据，整合 Chicken + Pigeon + Duck rcforc Y 力
提取第二峰值，进行物种间显著性检验
更新 Excel 和三张曲线图
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
from scipy import stats

# ─────────────────────────────────────────
# 配置
# ─────────────────────────────────────────
CHICKEN_DIR  = r"D:\system_folder\Desktop\LS-DYNA\chicken_results"
PIGEON_DIR   = r"D:\system_folder\Desktop\LS-DYNA\pigeon_results"
DUCK_DIR     = r"D:\system_folder\Desktop\LS-DYNA\duck_results"
OUTPUT_EXCEL = r"D:\system_folder\Desktop\LS-DYNA\combined_rcforc_yforce.xlsx"
OUTPUT_PNG_C = r"D:\system_folder\Desktop\LS-DYNA\chicken_rcforc_yforce.png"
OUTPUT_PNG_P = r"D:\system_folder\Desktop\LS-DYNA\pigeon_rcforc_yforce.png"
OUTPUT_PNG_D = r"D:\system_folder\Desktop\LS-DYNA\duck_rcforc_yforce.png"
T_MAX        = 23.0   # μs 截断点

# 壳参数（mm）
D_SHELL      = 2.0    # mm，三物种相同
T_CHICKEN    = 0.29   # mm
T_PIGEON     = 0.19   # mm
T_DUCK       = 0.3462 # mm  实测值 346.2 μm

def tau(F_N, D_mm, T_mm):
    """接触正应力 τ = F / (π·D·T)，单位 MPa（F in N, D/T in mm）"""
    return F_N / (3.141592653589793 * D_mm * T_mm)

CASES = [
    ("pos_p1_p1", "dX=+0.5, dZ=+0.5 mm"),
    ("pos_p1_n1", "dX=+0.5, dZ=-0.5 mm"),
    ("pos_n1_p1", "dX=-0.5, dZ=+0.5 mm"),
    ("pos_n1_n1", "dX=-0.5, dZ=-0.5 mm"),
    ("pos_p0_p1", "dX= 0.0, dZ=+0.5 mm"),
    ("pos_p0_n1", "dX= 0.0, dZ=-0.5 mm"),
    ("pos_p1_p0", "dX=+0.5, dZ= 0.0 mm"),
    ("pos_n1_p0", "dX=-0.5, dZ= 0.0 mm"),
    ("pos_p0_p0", "dX= 0.0, dZ= 0.0 mm"),
]
COLORS = ["#d62728","#1f77b4","#2ca02c","#ff7f0e",
          "#9467bd","#8c564b","#e377c2","#333333", "#bcbd22"]

# ─────────────────────────────────────────
# 解析 rcforc（截断 T_MAX）
# ─────────────────────────────────────────
RE_MASTER = re.compile(
    r'master\s+\d+\s+time\s+([\d.E+\-]+)\s+x\s+[\d.E+\-]+\s+y\s+([\d.E+\-]+)'
)

def parse_rcforc(filepath, sign=-1.0):
    """sign=-1.0 用于 Chicken/Pigeon（raw 值为负，取反变正）
       sign=+1.0 用于 Duck（raw 值已为正）"""
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

def load_all(results_dir, sign=-1.0):
    data = {}
    for case_key, _ in CASES:
        fpath = os.path.join(results_dir, case_key, "rcforc")
        if os.path.exists(fpath):
            data[case_key] = parse_rcforc(fpath, sign=sign)
    return data

print("=== Chicken ===")
chicken_data = load_all(CHICKEN_DIR, sign=+1.0)
for k, (t, y) in chicken_data.items():
    print(f"  {k}: {len(t)} pts, max Y = {y.max():.4f} N")

print("=== Pigeon ===")
pigeon_data = load_all(PIGEON_DIR, sign=-1.0)
for k, (t, y) in pigeon_data.items():
    print(f"  {k}: {len(t)} pts, max Y = {y.max():.4f} N")

print("=== Duck ===")
duck_data = load_all(DUCK_DIR, sign=+1.0)
for k, (t, y) in duck_data.items():
    print(f"  {k}: {len(t)} pts, max Y = {y.max():.4f} N")

# ─────────────────────────────────────────
# 找第二峰值
# ─────────────────────────────────────────
def find_second_peak(t, y):
    pks, _ = find_peaks(y, height=0.02, distance=4, prominence=0.02)
    if len(pks) < 2:
        return np.nan, np.nan
    sorted_pks = pks[np.argsort(y[pks])[::-1]]
    peak2_idx = sorted_pks[1]
    return float(y[peak2_idx]), float(t[peak2_idx])

print(f"\n{'Case':<14} {'Chicken 2nd (N)':>17} {'t(μs)':>7}  |  {'Pigeon 2nd (N)':>15} {'t(μs)':>7}  |  {'Duck 2nd (N)':>13} {'t(μs)':>7}")
print("-" * 95)
c_peak2_vals, p_peak2_vals, d_peak2_vals = [], [], []
c_peak2_info, p_peak2_info, d_peak2_info = {}, {}, {}

for case_key, _ in CASES:
    cv, ct = find_second_peak(*chicken_data[case_key]) if case_key in chicken_data else (np.nan, np.nan)
    pv, pt = find_second_peak(*pigeon_data[case_key])  if case_key in pigeon_data  else (np.nan, np.nan)
    dv, dt = find_second_peak(*duck_data[case_key])    if case_key in duck_data    else (np.nan, np.nan)
    print(f"{case_key:<14}  {cv:>15.4f} N  {ct:>6.2f}μs  |  {pv:>13.4f} N  {pt:>6.2f}μs  |  {dv:>11.4f} N  {dt:>6.2f}μs")
    if not np.isnan(cv):
        c_peak2_vals.append(cv); c_peak2_info[case_key] = (cv, ct)
    if not np.isnan(pv):
        p_peak2_vals.append(pv); p_peak2_info[case_key] = (pv, pt)
    if not np.isnan(dv):
        d_peak2_vals.append(dv); d_peak2_info[case_key] = (dv, dt)

c_arr = np.array(c_peak2_vals)
p_arr = np.array(p_peak2_vals)
d_arr = np.array(d_peak2_vals) if d_peak2_vals else np.array([])

# ─────────────────────────────────────────
# 显著性检验
# ─────────────────────────────────────────
def sig_label(p):
    if p < 0.001: return "*** (p<0.001)"
    if p < 0.01:  return "**  (p<0.01)"
    if p < 0.05:  return "*   (p<0.05)"
    return "ns  (p≥0.05)"

def pairwise_t(a, b):
    if len(a) < 2 or len(b) < 2:
        return np.nan, np.nan
    return stats.ttest_ind(a, b, equal_var=True)

# τ_normal 换算（2nd peak）
c_tau = np.array([tau(v, D_SHELL, T_CHICKEN) for v in c_arr])
p_tau = np.array([tau(v, D_SHELL, T_PIGEON)  for v in p_arr])
d_tau = np.array([tau(v, D_SHELL, T_DUCK)    for v in d_arr]) if len(d_arr) else np.array([])

# 全局峰值
c_max_arr = np.array([np.max(chicken_data[k][1]) for k, _ in CASES if k in chicken_data])
p_max_arr = np.array([np.max(pigeon_data[k][1])  for k, _ in CASES if k in pigeon_data])
d_max_arr = np.array([np.max(duck_data[k][1])    for k, _ in CASES if k in duck_data])  if duck_data  else np.array([])
c_max_tau_arr = np.array([tau(v, D_SHELL, T_CHICKEN) for v in c_max_arr])
p_max_tau_arr = np.array([tau(v, D_SHELL, T_PIGEON)  for v in p_max_arr])
d_max_tau_arr = np.array([tau(v, D_SHELL, T_DUCK)    for v in d_max_arr]) if len(d_max_arr) else np.array([])

print(f"\nChicken 2nd peak: mean={c_arr.mean():.4f} N ± {c_arr.std():.4f}  →  τ: {c_tau.mean():.4f} ± {c_tau.std():.4f} MPa")
print(f"Pigeon  2nd peak: mean={p_arr.mean():.4f} N ± {p_arr.std():.4f}  →  τ: {p_tau.mean():.4f} ± {p_tau.std():.4f} MPa")
if len(d_arr):
    print(f"Duck    2nd peak: mean={d_arr.mean():.4f} N ± {d_arr.std():.4f}  →  τ: {d_tau.mean():.4f} ± {d_tau.std():.4f} MPa")

# 两两显著性检验（F_2nd）
t_cp, p_cp = pairwise_t(c_arr, p_arr)
t_cd, p_cd = pairwise_t(c_arr, d_arr)
t_pd, p_pd = pairwise_t(p_arr, d_arr)
print(f"\nt-test F_2nd  Chicken vs Pigeon: t={t_cp:.4f}  p={p_cp:.4e}  {sig_label(p_cp)}")
print(f"t-test F_2nd  Chicken vs Duck:   t={t_cd:.4f}  p={p_cd:.4e}  {sig_label(p_cd)}")
print(f"t-test F_2nd  Pigeon  vs Duck:   t={t_pd:.4f}  p={p_pd:.4e}  {sig_label(p_pd)}")

# τ_2nd 两两检验
tt2_cp, tp2_cp = pairwise_t(c_tau, p_tau)
tt2_cd, tp2_cd = pairwise_t(c_tau, d_tau)
tt2_pd, tp2_pd = pairwise_t(p_tau, d_tau)
print(f"\nt-test τ_2nd  Chicken vs Pigeon: t={tt2_cp:.4f}  p={tp2_cp:.4e}  {sig_label(tp2_cp)}")
print(f"t-test τ_2nd  Chicken vs Duck:   t={tt2_cd:.4f}  p={tp2_cd:.4e}  {sig_label(tp2_cd)}")
print(f"t-test τ_2nd  Pigeon  vs Duck:   t={tt2_pd:.4f}  p={tp2_pd:.4e}  {sig_label(tp2_pd)}")

# F_max 两两检验
tmF_cp, tpF_cp = pairwise_t(c_max_arr, p_max_arr)
tmF_cd, tpF_cd = pairwise_t(c_max_arr, d_max_arr)
tmF_pd, tpF_pd = pairwise_t(p_max_arr, d_max_arr)
tmT_cp, tpT_cp = pairwise_t(c_max_tau_arr, p_max_tau_arr)
tmT_cd, tpT_cd = pairwise_t(c_max_tau_arr, d_max_tau_arr)
tmT_pd, tpT_pd = pairwise_t(p_max_tau_arr, d_max_tau_arr)

print(f"\nChicken max F:  mean={c_max_arr.mean():.4f} N ± {c_max_arr.std():.4f}  →  τ: {c_max_tau_arr.mean():.4f} ± {c_max_tau_arr.std():.4f} MPa")
print(f"Pigeon  max F:  mean={p_max_arr.mean():.4f} N ± {p_max_arr.std():.4f}  →  τ: {p_max_tau_arr.mean():.4f} ± {p_max_tau_arr.std():.4f} MPa")
if len(d_max_arr):
    print(f"Duck    max F:  mean={d_max_arr.mean():.4f} N ± {d_max_arr.std():.4f}  →  τ: {d_max_tau_arr.mean():.4f} ± {d_max_tau_arr.std():.4f} MPa")
print(f"t-test F_max  Chicken vs Pigeon: t={tmF_cp:.4f}  p={tpF_cp:.4e}  {sig_label(tpF_cp)}")
print(f"t-test F_max  Chicken vs Duck:   t={tmF_cd:.4f}  p={tpF_cd:.4e}  {sig_label(tpF_cd)}")
print(f"t-test F_max  Pigeon  vs Duck:   t={tmF_pd:.4f}  p={tpF_pd:.4e}  {sig_label(tpF_pd)}")
print(f"t-test τ_max  Chicken vs Pigeon: t={tmT_cp:.4f}  p={tpT_cp:.4e}  {sig_label(tpT_cp)}")
print(f"t-test τ_max  Chicken vs Duck:   t={tmT_cd:.4f}  p={tpT_cd:.4e}  {sig_label(tpT_cd)}")
print(f"t-test τ_max  Pigeon  vs Duck:   t={tmT_pd:.4f}  p={tpT_pd:.4e}  {sig_label(tpT_pd)}")

# ─────────────────────────────────────────
# 写 Excel
# ─────────────────────────────────────────
def make_summary(data):
    ref_key = next((k for k, _ in CASES if k in data), None)
    if not ref_key: return pd.DataFrame()
    t_ref, _ = data[ref_key]
    df = pd.DataFrame({"Time (μs)": t_ref})
    for case_key, label in CASES:
        if case_key not in data: continue
        t, y = data[case_key]
        df[label] = np.interp(t_ref, t, y, left=0, right=0)
    return df

peak2_rows = []
for case_key, label in CASES:
    cv, ct = c_peak2_info.get(case_key, (np.nan, np.nan))
    pv, pt = p_peak2_info.get(case_key, (np.nan, np.nan))
    dv, dt = d_peak2_info.get(case_key, (np.nan, np.nan))
    c_mx = np.max(chicken_data[case_key][1]) if case_key in chicken_data else np.nan
    p_mx = np.max(pigeon_data[case_key][1])  if case_key in pigeon_data  else np.nan
    d_mx = np.max(duck_data[case_key][1])    if case_key in duck_data    else np.nan
    peak2_rows.append({
        "Case": case_key, "Offset": label,
        "Chicken max F (N)":    c_mx,
        "Chicken τ_max (MPa)":  tau(c_mx, D_SHELL, T_CHICKEN) if not np.isnan(c_mx) else np.nan,
        "Chicken 2nd F (N)":    cv,
        "Chicken t2 (μs)":      ct,
        "Chicken τ_2nd (MPa)":  tau(cv, D_SHELL, T_CHICKEN) if not np.isnan(cv) else np.nan,
        "Pigeon max F (N)":     p_mx,
        "Pigeon τ_max (MPa)":   tau(p_mx, D_SHELL, T_PIGEON) if not np.isnan(p_mx) else np.nan,
        "Pigeon 2nd F (N)":     pv,
        "Pigeon t2 (μs)":       pt,
        "Pigeon τ_2nd (MPa)":   tau(pv, D_SHELL, T_PIGEON) if not np.isnan(pv) else np.nan,
        "Duck max F (N)":       d_mx,
        "Duck τ_max (MPa)":     tau(d_mx, D_SHELL, T_DUCK) if not np.isnan(d_mx) else np.nan,
        "Duck 2nd F (N)":       dv,
        "Duck t2 (μs)":         dt,
        "Duck τ_2nd (MPa)":     tau(dv, D_SHELL, T_DUCK) if not np.isnan(dv) else np.nan,
    })

def _r(arr): return arr

peak2_rows += [
    {"Case": "――"},
    {"Case": "MEAN",
     "Chicken max F (N)": c_max_arr.mean(),     "Chicken τ_max (MPa)": c_max_tau_arr.mean(),
     "Chicken 2nd F (N)": c_arr.mean(),         "Chicken τ_2nd (MPa)": c_tau.mean(),
     "Pigeon max F (N)":  p_max_arr.mean(),     "Pigeon τ_max (MPa)":  p_max_tau_arr.mean(),
     "Pigeon 2nd F (N)":  p_arr.mean(),         "Pigeon τ_2nd (MPa)":  p_tau.mean(),
     **({"Duck max F (N)": d_max_arr.mean(),    "Duck τ_max (MPa)":  d_max_tau_arr.mean(),
         "Duck 2nd F (N)": d_arr.mean(),        "Duck τ_2nd (MPa)":  d_tau.mean()} if len(d_arr) else {})},
    {"Case": "STD",
     "Chicken max F (N)": c_max_arr.std(),      "Chicken τ_max (MPa)": c_max_tau_arr.std(),
     "Chicken 2nd F (N)": c_arr.std(),          "Chicken τ_2nd (MPa)": c_tau.std(),
     "Pigeon max F (N)":  p_max_arr.std(),      "Pigeon τ_max (MPa)":  p_max_tau_arr.std(),
     "Pigeon 2nd F (N)":  p_arr.std(),          "Pigeon τ_2nd (MPa)":  p_tau.std(),
     **({"Duck max F (N)": d_max_arr.std(),     "Duck τ_max (MPa)":  d_max_tau_arr.std(),
         "Duck 2nd F (N)": d_arr.std(),         "Duck τ_2nd (MPa)":  d_tau.std()} if len(d_arr) else {})},
    {"Case": "――"},
    {"Case": "t-test F_max  C vs P",  "Offset": sig_label(tpF_cp), "Chicken max F (N)": tpF_cp},
    {"Case": "t-test F_max  C vs D",  "Offset": sig_label(tpF_cd), "Chicken max F (N)": tpF_cd},
    {"Case": "t-test F_max  P vs D",  "Offset": sig_label(tpF_pd), "Pigeon max F (N)":  tpF_pd},
    {"Case": "――"},
    {"Case": "t-test τ_max  C vs P",  "Offset": sig_label(tpT_cp), "Chicken τ_max (MPa)": tpT_cp},
    {"Case": "t-test τ_max  C vs D",  "Offset": sig_label(tpT_cd), "Chicken τ_max (MPa)": tpT_cd},
    {"Case": "t-test τ_max  P vs D",  "Offset": sig_label(tpT_pd), "Pigeon τ_max (MPa)":  tpT_pd},
    {"Case": "――"},
    {"Case": "t-test F_2nd  C vs P",  "Offset": sig_label(p_cp), "Chicken 2nd F (N)": p_cp},
    {"Case": "t-test F_2nd  C vs D",  "Offset": sig_label(p_cd), "Chicken 2nd F (N)": p_cd},
    {"Case": "t-test F_2nd  P vs D",  "Offset": sig_label(p_pd), "Pigeon 2nd F (N)":  p_pd},
    {"Case": "――"},
    {"Case": "t-test τ_2nd  C vs P",  "Offset": sig_label(tp2_cp), "Chicken τ_2nd (MPa)": tp2_cp},
    {"Case": "t-test τ_2nd  C vs D",  "Offset": sig_label(tp2_cd), "Chicken τ_2nd (MPa)": tp2_cd},
    {"Case": "t-test τ_2nd  P vs D",  "Offset": sig_label(tp2_pd), "Pigeon τ_2nd (MPa)":  tp2_pd},
]

with pd.ExcelWriter(OUTPUT_EXCEL, engine="openpyxl") as writer:
    make_summary(chicken_data).to_excel(writer, sheet_name="Chicken_Summary", index=False)
    make_summary(pigeon_data ).to_excel(writer, sheet_name="Pigeon_Summary",  index=False)
    make_summary(duck_data   ).to_excel(writer, sheet_name="Duck_Summary",    index=False)
    pd.DataFrame(peak2_rows).to_excel(writer, sheet_name="3Species_Comparison", index=False)
    for case_key, _ in CASES:
        if case_key in chicken_data:
            t, y = chicken_data[case_key]
            pd.DataFrame({"Time (μs)": t, "Y-Force (N)": y}).to_excel(
                writer, sheet_name=f"C_{case_key}"[:31], index=False)
        if case_key in pigeon_data:
            t, y = pigeon_data[case_key]
            pd.DataFrame({"Time (μs)": t, "Y-Force (N)": y}).to_excel(
                writer, sheet_name=f"P_{case_key}"[:31], index=False)
        if case_key in duck_data:
            t, y = duck_data[case_key]
            pd.DataFrame({"Time (μs)": t, "Y-Force (N)": y}).to_excel(
                writer, sheet_name=f"D_{case_key}"[:31], index=False)

print(f"\nExcel saved: {OUTPUT_EXCEL}")

# ─────────────────────────────────────────
# 绘图
# ─────────────────────────────────────────
matplotlib.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.linewidth": 1.2})

def plot_case(data, peak2_info, title, output_png, ylim=(-0.2, 1.4), xlim=(0, 22)):
    fig, ax = plt.subplots(figsize=(14, 7))
    peak_firsts, peak_maxs = [], []

    for idx, (case_key, label) in enumerate(CASES):
        if case_key not in data: continue
        t, y = data[case_key]
        color = COLORS[idx]
        t_s = np.linspace(t[0], t[-1], len(t) * 10)
        y_s = PchipInterpolator(t, y)(t_s)
        ax.plot(t_s, y_s, color=color, linewidth=1.6, label=label)

        # 第一峰（≤6μs）
        mask = t <= 6.0
        if mask.any():
            pks, _ = find_peaks(y[mask], height=0.01, distance=3)
            i1 = pks[np.argmax(y[mask][pks])] if len(pks) else np.argmax(y[mask])
            v1, t1 = y[mask][i1], t[mask][i1]
            # 用样条曲线在该时点附近的最大值作为标注（保持与视觉一致）
            mask_s1 = (t_s >= t1 - 1.0) & (t_s <= t1 + 1.0)
            vs1_idx = np.argmax(y_s[mask_s1])
            t1_s = t_s[mask_s1][vs1_idx]
            v1_s  = y_s[mask_s1][vs1_idx]
            ax.plot(t1_s, v1_s, marker="*", markersize=13, color=color,
                    markeredgewidth=0.5, markeredgecolor="white", zorder=5)
            ax.annotate(f"{v1_s:.2f}", xy=(t1_s, v1_s), xytext=(t1_s+0.1, v1_s+0.03),
                        fontsize=9, color=color, fontweight="bold")
            peak_firsts.append(v1_s)

        # 全局最大峰 —— 从样条曲线取峰位，保证标注与视觉曲线一致
        imax_s = np.argmax(y_s)
        t_peak, v_peak = t_s[imax_s], y_s[imax_s]
        ax.plot(t_peak, v_peak, marker="*", markersize=13, color=color,
                markeredgewidth=0.5, markeredgecolor="white", zorder=5)
        ax.annotate(f"{v_peak:.2f}", xy=(t_peak, v_peak),
                    xytext=(t_peak+0.15, v_peak+0.025),
                    fontsize=9, color=color, fontweight="bold")
        peak_maxs.append(v_peak)

        # 第二峰（空心★）
        if case_key in peak2_info:
            pv, pt = peak2_info[case_key]
            ax.plot(pt, pv, marker="*", markersize=14, color=color,
                    markeredgewidth=1.5, markeredgecolor=color,
                    markerfacecolor="none", zorder=6)
            ax.annotate(f"{pv:.2f}", xy=(pt, pv), xytext=(pt+0.1, pv+0.03),
                        fontsize=9, color=color, fontweight="bold", style="italic")

    # 统计框
    p2_vals = [v for v, _ in peak2_info.values()]
    mu1 = np.mean(peak_firsts) if peak_firsts else np.nan
    s1  = np.std(peak_firsts)  if peak_firsts else np.nan
    mu2, s2 = (np.mean(p2_vals), np.std(p2_vals)) if p2_vals else (np.nan, np.nan)
    mum, sm = (np.mean(peak_maxs), np.std(peak_maxs)) if peak_maxs else (np.nan, np.nan)
    ax.text(0.99, 0.04,
            f"9-case statistics (N)\n"
            f"1st peak : {mu1:.3f} ± {s1:.3f}\n"
            f"Peak (max): {mum:.3f} ± {sm:.3f}\n"
            f"2nd peak : {mu2:.3f} ± {s2:.3f}",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=10, family="monospace",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                      edgecolor="#aaaaaa", alpha=0.9))

    ax.set_xlabel("Time (μs)", fontsize=13)
    ax.set_ylabel("Y-Force (N)", fontsize=13)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.axhline(0, color="black", linewidth=1.0, zorder=0)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.6)
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.legend(loc="upper right", fontsize=9.5, framealpha=0.85,
              edgecolor="#cccccc", borderpad=0.8, handlelength=2.0)
    plt.tight_layout()
    plt.savefig(output_png, dpi=180, bbox_inches="tight")
    print(f"Plot saved: {output_png}")
    plt.close('all')

plot_case(
    chicken_data, c_peak2_info,
    "Contact Y-Force vs Time — Gallus Egg Parametric Study\n"
    "(Target plate horizontal offset, grid = 0.5 mm)",
    OUTPUT_PNG_C, ylim=(-0.2, 1.4), xlim=(0, 22)
)
plot_case(
    pigeon_data, p_peak2_info,
    "Contact Y-Force vs Time — Columba Egg Parametric Study\n"
    "(Target plate horizontal offset, grid = 0.5 mm)",
    OUTPUT_PNG_P, ylim=(-0.2, 1.4), xlim=(0, 22)
)
if duck_data:
    plot_case(
        duck_data, d_peak2_info,
        f"Contact Y-Force vs Time — Anas Egg Parametric Study\n"
        f"(Target plate horizontal offset, grid = 0.5 mm  |  T_shell = {T_DUCK*1000:.1f} μm)",
        OUTPUT_PNG_D, ylim=(-0.2, 1.4), xlim=(0, 22)
    )
