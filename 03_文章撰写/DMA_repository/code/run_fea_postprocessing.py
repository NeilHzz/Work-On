"""Reproduce finite-element summary statistics from packaged source tables.

This script reads data/finite_element/combined_rcforc_yforce.xlsx and writes
outputs/finite_element_recomputed_summary.xlsx. It does not create image files.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


PACKAGE_DIR = Path(__file__).resolve().parents[1]
DATA_FILE = PACKAGE_DIR / "data" / "finite_element" / "combined_rcforc_yforce.xlsx"
OUT_DIR = PACKAGE_DIR / "outputs"
OUT_FILE = OUT_DIR / "finite_element_recomputed_summary.xlsx"

SPECIES_COLUMNS = {
    "Gallus": ("Chicken max F (N)", "Chicken tau_max (MPa)", "Chicken 2nd F (N)", "Chicken tau_2nd (MPa)"),
    "Columba": ("Pigeon max F (N)", "Pigeon tau_max (MPa)", "Pigeon 2nd F (N)", "Pigeon tau_2nd (MPa)"),
    "Anas": ("Duck max F (N)", "Duck tau_max (MPa)", "Duck 2nd F (N)", "Duck tau_2nd (MPa)"),
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for col in df.columns:
        new = str(col).replace("τ", "tau").replace("蟿", "tau").replace("渭", "u")
        rename[col] = new
    return df.rename(columns=rename)


def _case_rows(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["Case"].astype(str).str.startswith("pos_")].copy()


def _summary(cases: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for species, cols in SPECIES_COLUMNS.items():
        for metric_col in cols:
            if metric_col not in cases.columns:
                continue
            values = pd.to_numeric(cases[metric_col], errors="coerce").dropna().to_numpy()
            rows.append(
                {
                    "species": species,
                    "metric": metric_col,
                    "n": len(values),
                    "mean": float(np.mean(values)),
                    "sd": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                }
            )
    return pd.DataFrame(rows)


def _pairwise_tests(cases: pd.DataFrame) -> pd.DataFrame:
    rows = []
    metric_groups = [
        ("F_max (N)", ["Chicken max F (N)", "Pigeon max F (N)", "Duck max F (N)"]),
        ("tau_max (MPa)", ["Chicken tau_max (MPa)", "Pigeon tau_max (MPa)", "Duck tau_max (MPa)"]),
        ("F_2nd (N)", ["Chicken 2nd F (N)", "Pigeon 2nd F (N)", "Duck 2nd F (N)"]),
        ("tau_2nd (MPa)", ["Chicken tau_2nd (MPa)", "Pigeon tau_2nd (MPa)", "Duck tau_2nd (MPa)"]),
    ]
    labels = ["Gallus", "Columba", "Anas"]
    for metric, cols in metric_groups:
        arrays = [pd.to_numeric(cases[c], errors="coerce").dropna().to_numpy() for c in cols if c in cases]
        if len(arrays) == 3 and all(len(a) > 1 for a in arrays):
            f_stat, p_anova = stats.f_oneway(*arrays)
            rows.append({"metric": metric, "comparison": "one-way ANOVA", "statistic": f_stat, "p_value": p_anova})
            for i in range(3):
                for j in range(i + 1, 3):
                    t_stat, p_val = stats.ttest_ind(arrays[i], arrays[j], equal_var=True)
                    rows.append(
                        {
                            "metric": metric,
                            "comparison": f"{labels[i]} vs {labels[j]}",
                            "statistic": t_stat,
                            "p_value": p_val,
                        }
                    )
    return pd.DataFrame(rows)


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    df = pd.read_excel(DATA_FILE, sheet_name="3Species_Comparison")
    df = _normalize_columns(df)
    cases = _case_rows(df)
    with pd.ExcelWriter(OUT_FILE, engine="openpyxl") as writer:
        cases.to_excel(writer, sheet_name="case_source_data", index=False)
        _summary(cases).to_excel(writer, sheet_name="summary", index=False)
        _pairwise_tests(cases).to_excel(writer, sheet_name="tests", index=False)
    print(f"Wrote {OUT_FILE}")


if __name__ == "__main__":
    main()
