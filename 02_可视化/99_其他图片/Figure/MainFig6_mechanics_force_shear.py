"""
Science Advances 格式 — 力学结果图
Fig_force_tukey.png      : Tukey HSD bar chart (F_max & τ_max)
Fig_force_timeseries.png : Mean ± 1σ force time-series (3 species)

数据源: combined_rcforc_yforce.xlsx
字体: Times New Roman (SA requirement)
"""
import os
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _save import save_fig
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.family"] = "Times New Roman"
matplotlib.rcParams["font.size"] = 18
matplotlib.rcParams["axes.linewidth"] = 1.3
matplotlib.rcParams["mathtext.fontset"] = "custom"
matplotlib.rcParams["mathtext.rm"] = "Times New Roman"
matplotlib.rcParams["mathtext.it"] = "Times New Roman:italic"
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.interpolate import PchipInterpolator
from scipy import stats

SINGLE_PANEL_ADJUST = dict(left=0.13, right=0.97, bottom=0.13, top=0.86)

# ─────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
def find_work_root() -> Path:
    for parent in Path(SCRIPT_DIR).resolve().parents:
        names = [path.name for path in parent.iterdir() if path.is_dir()]
        if any(name.startswith("01_") for name in names) and any(name.startswith("02_") for name in names):
            return parent
    raise RuntimeError("Work On root not found")


WORK_ROOT = find_work_root()
XLSX_CANDIDATES = sorted(WORK_ROOT.glob("01_*/**/combined_rcforc_yforce.xlsx"))
if not XLSX_CANDIDATES:
    raise FileNotFoundError("combined_rcforc_yforce.xlsx not found under 01_*")
XLSX       = str(XLSX_CANDIDATES[-1])
OUT_DIR    = os.path.join(SCRIPT_DIR, "PNG")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_TUKEY  = os.path.join(OUT_DIR, "Fig_force_tukey.png")
OUT_TS     = os.path.join(OUT_DIR, "Fig_force_timeseries.png")

FIXED_PNG_DIR = os.path.join(SCRIPT_DIR, "PNG")
FIXED_PDF_DIR = os.path.join(SCRIPT_DIR, "PDF")
FIXED_SVG_DIR = os.path.join(SCRIPT_DIR, "SVG")
for _fixed_dir in (FIXED_PNG_DIR, FIXED_PDF_DIR, FIXED_SVG_DIR):
    os.makedirs(_fixed_dir, exist_ok=True)

def save_fig_fixed(fig, name, dpi=200):
    fig.savefig(os.path.join(FIXED_PNG_DIR, f"{name}.png"), dpi=dpi, facecolor="white")
    fig.savefig(os.path.join(FIXED_PDF_DIR, f"{name}.pdf"), facecolor="white")
    fig.savefig(os.path.join(FIXED_SVG_DIR, f"{name}.svg"), facecolor="white")
    print(f"  Saved: {name} [PNG/PDF/SVG]")

# ─────────────────────────────────────────────────────────────
# Parameters
# ─────────────────────────────────────────────────────────────
SPECIES  = ["Gallus",   "Columba",  "Anas"]
T_MMS    = [0.29,       0.19,       0.3462]   # shell thickness mm
D_SHELL  = 2.0   # mm
STANDARD_SPECIES_COLORS = {
    "Gallus": "#C46B83",
    "Anas": "#93AACD",
    "Columba": "#F3CE9D",
}
COLORS   = [STANDARD_SPECIES_COLORS[sp] for sp in SPECIES]

def style_species_text(texts):
    for text in texts:
        if text.get_text() in SPECIES:
            text.set_fontfamily("Times New Roman")
            text.set_fontstyle("italic")

CASES = [
    "pos_p1_p1", "pos_p1_n1", "pos_n1_p1", "pos_n1_n1",
    "pos_p0_p1", "pos_p0_n1", "pos_p1_p0", "pos_n1_p0", "pos_p0_p0",
]
# Prefix in sheet names: Chicken=C, Pigeon=P, Duck=D
SP_PREFIX = {"Gallus": "C", "Columba": "P", "Anas": "D"}

def to_tau(F_N, T_mm):
    return F_N / (np.pi * D_SHELL * T_mm)

# ─────────────────────────────────────────────────────────────
# Load 3Species_Comparison for Tukey data
# ─────────────────────────────────────────────────────────────
df3 = pd.read_excel(XLSX, sheet_name="3Species_Comparison", engine="openpyxl")
cases_df = df3[df3["Case"].isin(CASES)].copy()

col_map = {
    "Gallus":  ("Chicken max F (N)",  "Chicken τ_max (MPa)"),
    "Columba": ("Pigeon max F (N)",   "Pigeon τ_max (MPa)"),
    "Anas":    ("Duck max F (N)",     "Duck τ_max (MPa)"),
}
F_DATA, TAU_DATA = [], []
for sp in SPECIES:
    fc, tc = col_map[sp]
    F_DATA.append(cases_df[fc].dropna().values.astype(float))
    TAU_DATA.append(cases_df[tc].dropna().values.astype(float))

# ─────────────────────────────────────────────────────────────
# Load time-series from per-case sheets
# ─────────────────────────────────────────────────────────────
def load_timeseries(prefix):
    """Returns (t_ref, matrix) shape (n_cases, n_timepoints)"""
    all_t, all_y = [], []
    for case in CASES:
        sheet = f"{prefix}_{case}"
        try:
            df_c = pd.read_excel(XLSX, sheet_name=sheet, engine="openpyxl")
            t = df_c.iloc[:, 0].values.astype(float)
            y = df_c.iloc[:, 1].values.astype(float)
            all_t.append(t); all_y.append(y)
        except Exception:
            pass
    if not all_t:
        return None, None
    t_ref = all_t[0]
    matrix = np.vstack([np.interp(t_ref, t, y) for t, y in zip(all_t, all_y)])
    return t_ref, matrix

ts_data = {}
for sp in SPECIES:
    pref = SP_PREFIX[sp]
    t_ref, mat = load_timeseries(pref)
    if t_ref is not None:
        ts_data[sp] = (t_ref, mat)

# ─────────────────────────────────────────────────────────────
# Tukey HSD
# ─────────────────────────────────────────────────────────────
def _cld3(names, sig):
    s01, s02, s12 = bool(sig[0,1]), bool(sig[0,2]), bool(sig[1,2])
    table = {
        (False,False,False): ("a","a","a"),   (False,False,True): ("ab","a","b"),
        (False,True, False): ("a","ab","b"),  (False,True, True): ("a","a","b"),
        (True, False,False): ("a","b","ab"),  (True, False,True): ("a","b","a"),
        (True, True, False): ("a","b","b"),   (True, True, True): ("a","b","c"),
    }
    ltrs = table[(s01, s02, s12)]
    return {names[i]: ltrs[i] for i in range(3)}

def _letters_highest_as_a(letters, ordered_names):
    reverse_map = {"a": "c", "b": "b", "c": "a"}
    reversed_letters = {
        name: "".join(sorted({reverse_map[ch] for ch in value}))
        for name, value in letters.items()
    }
    compact_map = {}
    next_code = ord("a")
    for name in reversed(ordered_names):
        for ch in reversed_letters[name]:
            if ch not in compact_map:
                compact_map[ch] = chr(next_code)
                next_code += 1
    return {
        name: "".join(compact_map[ch] for ch in reversed_letters[name])
        for name in letters
    }

def tukey_hsd(groups, names, alpha=0.05):
    k = len(groups)
    ns = [len(g) for g in groups]
    means = np.array([g.mean() for g in groups])
    f_stat, p_anova = stats.f_oneway(*groups)
    SS_e = sum(float(np.sum((g - g.mean())**2)) for g in groups)
    df_e = sum(ns) - k
    MSE  = SS_e / df_e
    order = np.argsort(means)
    s_means  = means[order]
    s_names  = [names[i] for i in order]
    s_groups = [groups[i] for i in order]
    s_stds   = np.array([groups[i].std(ddof=1) for i in order])
    s_ns     = [ns[i] for i in order]
    sig = np.zeros((k, k), dtype=bool)
    diffs = np.zeros((k, k), dtype=float)
    q_crit = stats.studentized_range.ppf(1.0 - alpha, k=k, df=df_e)
    for i in range(k):
        for j in range(i+1, k):
            diff = s_means[j] - s_means[i]
            se = np.sqrt(MSE / 2.0 * (1.0 / s_ns[i] + 1.0 / s_ns[j]))
            threshold = q_crit * se
            sig[i, j] = sig[j, i] = bool(diff > threshold)
            diffs[i, j] = diff
            diffs[j, i] = -diff
    letters = _letters_highest_as_a(_cld3(s_names, sig), s_names)
    return dict(f_stat=f_stat, p_anova=p_anova,
                order=order, s_names=s_names, s_means=s_means, s_stds=s_stds,
                s_groups=s_groups, s_ns=s_ns, sig=sig, diffs=diffs,
                letters=letters)

res_F   = tukey_hsd(F_DATA,   SPECIES)
res_tau = tukey_hsd(TAU_DATA, SPECIES)

# ─────────────────────────────────────────────────────────────
# Fig 1 — Tukey HSD bar chart
# ─────────────────────────────────────────────────────────────
fig1, axes = plt.subplots(1, 2, figsize=(12, 6.5))
fig1.suptitle(
    "Tukey's HSD — Egg Shell Impact Simulation\n"
    "(n = 9 per species, α = 0.05;  same letter = no significant difference)",
    fontsize=20, fontweight="bold"
)
rng = np.random.default_rng(42)

def plot_tukey(ax, res, data_orig, metric_label, unit):
    orig_means = np.array([g.mean() for g in data_orig])
    orig_stds  = np.array([g.std(ddof=1) for g in data_orig])
    x = np.arange(len(SPECIES))

    bars = ax.bar(x, orig_means, width=0.5,
                  color=COLORS, alpha=1.0,
                  edgecolor="k", linewidth=1.0, zorder=2)
    ax.errorbar(x, orig_means, yerr=orig_stds,
                fmt="none", ecolor="k",
                elinewidth=1.8, capsize=7, capthick=1.8, zorder=3)
    for xi, sp_data, color in zip(x, data_orig, COLORS):
        jitter = rng.uniform(-0.14, 0.14, size=len(sp_data))
        ax.scatter(xi + jitter, sp_data, s=36,
                   color=color, edgecolors="k",
                   linewidths=0.5, zorder=4, alpha=1.0)

    # Tukey letter labels only
    y_top = orig_means + orig_stds
    y_max = float(y_top.max())
    for i, sp in enumerate(SPECIES):
        ltr = res['letters'].get(sp, '')
        ht = orig_means[i] + orig_stds[i]
        ax.text(i, ht + y_max * 0.02, ltr,
                ha='center', va='bottom', fontsize=20, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(SPECIES, fontsize=20)
    style_species_text(ax.get_xticklabels())
    ax.set_ylabel(f"{metric_label} ({unit})", fontsize=20)
    ax.set_ylim(0, y_max * 1.30)
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.5, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_title(
        f"{metric_label} ({unit})\np = {res['p_anova']:.2e}",
        fontsize=16,
        pad=6,
    )

plot_tukey(axes[0], res_F,   F_DATA,   "F_max",  "N")
plot_tukey(axes[1], res_tau, TAU_DATA, "τ_max",  "MPa")
plt.tight_layout(rect=[0, 0, 1, 0.86])
save_fig(plt.gcf(), "Fig6B", dpi=200)
plt.close("all")

# ── Individual Tukey panels ────────────────────────────────────────────────
rng = np.random.default_rng(42)
fig_fmax, ax_fmax = plt.subplots(1, 1, figsize=(6, 5.67))
plot_tukey(ax_fmax, res_F, F_DATA, "F_max", "N")
fig_fmax.subplots_adjust(**SINGLE_PANEL_ADJUST)
save_fig_fixed(plt.gcf(), "Fig6B_Fmax", dpi=200)
plt.close("all")

rng = np.random.default_rng(42)
fig_taumax, ax_taumax = plt.subplots(1, 1, figsize=(6, 5.67))
plot_tukey(ax_taumax, res_tau, TAU_DATA, "τ_max", "MPa")
fig_taumax.subplots_adjust(**SINGLE_PANEL_ADJUST)
save_fig_fixed(plt.gcf(), "Fig6B_Taumax", dpi=200)
plt.close("all")

# ─────────────────────────────────────────────────────────────
# Fig 2 — Time-series mean ± 1σ
# ─────────────────────────────────────────────────────────────
if ts_data:
    fig2, (ax_f, ax_tau) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    fig2.suptitle(
        "Contact Force and Shear Stress — Mean ± 1\u03c3 across 9 impact positions",
        fontsize=22, fontweight="bold"
    )

    def smooth(t, y):
        t_s = np.linspace(t[0], t[-1], len(t)*5)
        return t_s, PchipInterpolator(t, y)(t_s)

    def _is_sig(sp_name, res):
        ltr = res['letters'].get(sp_name, '')
        return any(res['letters'].get(s, '') != ltr for s in SPECIES if s != sp_name)

    tau_merge_peaks = {}   # sp -> (tx, ty) for Columba & Anas merged dot
    for sp, color, T_mm in zip(SPECIES, COLORS, T_MMS):
        if sp not in ts_data:
            continue
        t_ref, mat = ts_data[sp]
        mean_f = mat.mean(axis=0)
        std_f  = mat.std(axis=0)

        # Force
        ts_s, ms_f = smooth(t_ref, mean_f)
        _, lo_f = smooth(t_ref, np.clip(mean_f - std_f, 0, None))
        _, hi_f = smooth(t_ref, mean_f + std_f)
        ax_f.fill_between(ts_s, lo_f, hi_f, color=color, alpha=0.15)
        ax_f.plot(ts_s, ms_f, color=color, lw=2.2,
                  label=sp)
        # Peak marker: ⭐ if significantly different from any other species, else •
        pk_f = np.argmax(ms_f)
        marker_f = '⭐' if _is_sig(sp, res_F) else '•'
        ax_f.text(ts_s[pk_f], ms_f[pk_f], marker_f,
                  color=color, ha='center', va='bottom', fontsize=20, zorder=10,
                  fontfamily='Segoe UI Emoji')

        # Tau
        ts_s2, ms_tau = smooth(t_ref, to_tau(mean_f, T_mm))
        _, lo_tau = smooth(t_ref, to_tau(np.clip(mean_f - std_f, 0, None), T_mm))
        _, hi_tau = smooth(t_ref, to_tau(mean_f + std_f, T_mm))
        ax_tau.fill_between(ts_s2, lo_tau, hi_tau, color=color, alpha=0.15)
        ax_tau.plot(ts_s2, ms_tau, color=color, lw=2.2,
                    label=sp)
        pk_tau = np.argmax(ms_tau)
        if sp in ('Columba', 'Anas'):
            # Collect peaks for merged single dot
            tau_merge_peaks[sp] = (ts_s2[pk_tau], ms_tau[pk_tau])
        else:
            # Peak marker: ⭐ if significantly different from any other species, else •
            marker_tau = '⭐' if _is_sig(sp, res_tau) else '•'
            ax_tau.text(ts_s2[pk_tau], ms_tau[pk_tau], marker_tau,
                        color=color, ha='center', va='bottom', fontsize=20, zorder=10,
                        fontfamily='Segoe UI Emoji')

    # Draw a single merged dot for Columba + Anas in τ
    if tau_merge_peaks:
        merged_x = np.mean([v[0] for v in tau_merge_peaks.values()])
        merged_y = np.mean([v[1] for v in tau_merge_peaks.values()])
        ax_tau.plot(merged_x, merged_y, marker='o', markersize=9,
                    color='#888888', markeredgecolor='white', markeredgewidth=1.2,
                    zorder=10, linestyle='none')

    for ax, ylabel in [(ax_f, "Contact force F (N)"),
                       (ax_tau, "Shear stress τ (MPa)")]:
        ax.set_ylabel(ylabel, fontsize=20)
        ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.4)
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    legend = ax_f.legend(fontsize=18, framealpha=0.9)
    style_species_text(legend.get_texts())

    ax_tau.set_xlabel("Time (μs)", fontsize=20)
    plt.tight_layout()
    save_fig(plt.gcf(), "Fig6A", dpi=200)
    plt.close("all")
    print("[OK] Time-series: Fig6A")

    # ── Individual timeseries panels (figsize=(12,5.67) → AR≈2.12 匹配参考) ──
    # Force only
    fig_force, ax_f_only = plt.subplots(1, 1, figsize=(12, 5.67))
    for sp, color, T_mm in zip(SPECIES, COLORS, T_MMS):
        if sp not in ts_data:
            continue
        t_ref, mat = ts_data[sp]
        mean_f = mat.mean(axis=0)
        std_f  = mat.std(axis=0)
        ts_s, ms_f = smooth(t_ref, mean_f)
        _, lo_f = smooth(t_ref, np.clip(mean_f - std_f, 0, None))
        _, hi_f = smooth(t_ref, mean_f + std_f)
        ax_f_only.fill_between(ts_s, lo_f, hi_f, color=color, alpha=0.15)
        ax_f_only.plot(ts_s, ms_f, color=color, lw=2.2,
                       label=sp)
        pk_f = np.argmax(ms_f)
        marker_f = '⭐' if _is_sig(sp, res_F) else '•'
        ax_f_only.text(ts_s[pk_f], ms_f[pk_f], marker_f,
                       color=color, ha='center', va='bottom', fontsize=20, zorder=10,
                       fontfamily='Segoe UI Emoji')
    ax_f_only.set_ylabel("Contact force F (N)", fontsize=20)
    ax_f_only.set_xlabel("Time (μs)", fontsize=20)
    legend = ax_f_only.legend(fontsize=18, framealpha=0.9)
    style_species_text(legend.get_texts())
    ax_f_only.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.4)
    ax_f_only.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax_f_only.spines['top'].set_visible(False)
    ax_f_only.spines['right'].set_visible(False)
    fig_force.subplots_adjust(**SINGLE_PANEL_ADJUST)
    save_fig_fixed(plt.gcf(), "Fig6A_Force", dpi=200)
    plt.close("all")

    # Shear only
    fig_shear, ax_tau_only = plt.subplots(1, 1, figsize=(12, 5.67))
    _tau_merge_peaks = {}
    for sp, color, T_mm in zip(SPECIES, COLORS, T_MMS):
        if sp not in ts_data:
            continue
        t_ref, mat = ts_data[sp]
        mean_f = mat.mean(axis=0)
        std_f  = mat.std(axis=0)
        ts_s2, ms_tau = smooth(t_ref, to_tau(mean_f, T_mm))
        _, lo_tau = smooth(t_ref, to_tau(np.clip(mean_f - std_f, 0, None), T_mm))
        _, hi_tau = smooth(t_ref, to_tau(mean_f + std_f, T_mm))
        ax_tau_only.fill_between(ts_s2, lo_tau, hi_tau, color=color, alpha=0.15)
        ax_tau_only.plot(ts_s2, ms_tau, color=color, lw=2.2,
                         label=sp)
        pk_tau = np.argmax(ms_tau)
        if sp in ('Columba', 'Anas'):
            _tau_merge_peaks[sp] = (ts_s2[pk_tau], ms_tau[pk_tau])
        else:
            marker_tau = '⭐' if _is_sig(sp, res_tau) else '•'
            ax_tau_only.text(ts_s2[pk_tau], ms_tau[pk_tau], marker_tau,
                             color=color, ha='center', va='bottom', fontsize=20, zorder=10,
                             fontfamily='Segoe UI Emoji')
    if _tau_merge_peaks:
        merged_x = np.mean([v[0] for v in _tau_merge_peaks.values()])
        merged_y = np.mean([v[1] for v in _tau_merge_peaks.values()])
        ax_tau_only.plot(merged_x, merged_y, marker='o', markersize=9,
                         color='#888888', markeredgecolor='white', markeredgewidth=1.2,
                         zorder=10, linestyle='none')
    ax_tau_only.set_ylabel("Shear stress τ (MPa)", fontsize=20)
    ax_tau_only.set_xlabel("Time (μs)", fontsize=20)
    ax_tau_only.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.4)
    ax_tau_only.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
    ax_tau_only.spines['top'].set_visible(False)
    ax_tau_only.spines['right'].set_visible(False)
    fig_shear.subplots_adjust(**SINGLE_PANEL_ADJUST)
    save_fig_fixed(plt.gcf(), "Fig6A_Shear", dpi=200)
    plt.close("all")
    print("[OK] Individual panels: Fig6A_Force, Fig6A_Shear, Fig6B_Fmax, Fig6B_Taumax")
else:
    print("[SKIP] Time-series: no per-case data available")

print("\nForce figure generation complete.")
