"""Visualize glycan-type consistency within Fig. 2 glycoprotein orthogroups.

The script reuses the seven glycan-type classes from the original Fig2 Circle
analysis and summarizes two related questions:
  1. Are proteins within an orthogroup assigned to the same glycan-type set?
  2. What is the glycan-type composition within each species?
"""

from __future__ import annotations

import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _save import save_fig

matplotlib.rcParams["font.family"] = "Times New Roman"
matplotlib.rcParams["font.sans-serif"] = ["Times New Roman", "DejaVu Sans"]
matplotlib.rcParams["mathtext.fontset"] = "stix"
matplotlib.rcParams["axes.linewidth"] = 0.8
matplotlib.rcParams["svg.fonttype"] = "none"
matplotlib.rcParams["pdf.fonttype"] = 42

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = next(path for path in ROOT.iterdir() if path.is_dir() and path.name.startswith("01_"))
MS_DIR = DATA_ROOT / "Raw_Data" / "MS_DATA"

SPECIES_ORDER = ["Gallus", "Anas", "Columba"]
SPECIES_COLORS = {
    "Gallus": "#C46B83",
    "Anas": "#93AACD",
    "Columba": "#F3CE9D",
}
PREFIX_TO_SPECIES = {
    "GlyGallus": "Gallus",
    "GlyAnas": "Anas",
    "GlyColumba": "Columba",
    "Gallus": "Gallus",
    "Anas": "Anas",
    "Columba": "Columba",
}

GLYCAN_TYPES_ORDER = [
    "High Mannose",
    "Pauci-mannose",
    "Hybrid",
    "Complex-Plain",
    "Complex-Fucosylated",
    "Complex-Sialylated",
    "Other",
]
GLYCAN_TYPE_COLORS = {
    "High Mannose": "#0072B2",
    "Pauci-mannose": "#E69F00",
    "Hybrid": "#009E73",
    "Complex-Plain": "#CC79A7",
    "Complex-Fucosylated": "#D55E00",
    "Complex-Sialylated": "#56B4E9",
    "Other": "#666666",
}
CONSISTENCY_COLORS = {
    "Single glycan type": "#4C9F70",
    "Same multi-type set": "#4C78A8",
    "Mixed type sets": "#C44E52",
}

MS_FILES = {
    "Gallus": MS_DIR / "Glycan_MS_Gallus.xlsx",
    "Anas": MS_DIR / "Glycan_MS_Anas.xlsx",
    "Columba": MS_DIR / "Glycan_MS_Columba.xlsx",
}


def locate_glycoprotein_orthogroups() -> Path:
    """Find the current Fig. 2 glycoprotein orthogroup file."""
    candidates = list(DATA_ROOT.rglob("Orthogroups.txt.gz.txt"))
    scored = []
    for path in candidates:
        text = path.read_text(encoding="utf-8", errors="ignore")[:12000]
        score = sum(text.count(prefix) for prefix in ("GlyGallus", "GlyAnas", "GlyColumba"))
        if score:
            scored.append((score, path))
    if not scored:
        raise FileNotFoundError("Could not find a Gly-prefixed Orthogroups.txt.gz.txt file.")
    return sorted(scored, reverse=True)[0][1]


def classify_glycan(glycan: str) -> str:
    """Classify a glycan composition string into the seven Fig2 Circle classes."""
    comp = {}
    for key in ("HexNAc", "Hex", "Fuc", "NeuAc"):
        match = re.search(rf"{key}\((\d+)\)", str(glycan))
        comp[key] = int(match.group(1)) if match else 0
    hexnac, hexose, fucose, sialic = comp["HexNAc"], comp["Hex"], comp["Fuc"], comp["NeuAc"]
    if hexnac == 2 and hexose >= 5 and fucose == 0 and sialic == 0:
        return "High Mannose"
    if hexnac <= 2 and hexose <= 4:
        return "Pauci-mannose"
    if hexnac == 3 and hexose >= 5:
        return "Hybrid"
    if hexnac >= 3 and sialic >= 1:
        return "Complex-Sialylated"
    if hexnac >= 3 and fucose >= 1 and sialic == 0:
        return "Complex-Fucosylated"
    if hexnac >= 3 and fucose == 0 and sialic == 0:
        return "Complex-Plain"
    return "Other"


def load_glycan_type_annotations() -> tuple[dict[str, set[str]], dict[str, str]]:
    """Load accession-to-glycan-type annotations from the three MS workbooks."""
    protein_to_types: dict[str, set[str]] = defaultdict(set)
    protein_to_species: dict[str, str] = {}
    for species, path in MS_FILES.items():
        df_igp = pd.read_excel(path, sheet_name="IGP_quant")
        for _, row in df_igp.iterrows():
            accession = str(row.get("Protein accession", "")).strip()
            modification = str(row.get("Observed Modification", "")).strip()
            if accession and modification and modification != "nan":
                protein_to_types[accession].add(classify_glycan(modification))
                protein_to_species[accession] = species

        df_site = pd.read_excel(path, sheet_name="Site_quant")
        if "N-glycan modifications" not in df_site.columns:
            continue
        for _, row in df_site.iterrows():
            accession = str(row.get("Protein accession", "")).strip()
            modifications = str(row.get("N-glycan modifications", "")).strip()
            if not accession or not modifications or modifications == "nan":
                continue
            for entry in re.split(r";\s*", modifications):
                if entry.strip():
                    protein_to_types[accession].add(classify_glycan(entry.strip()))
                    protein_to_species[accession] = species
    return dict(protein_to_types), protein_to_species


def parse_orthogroups(path: Path) -> list[dict[str, object]]:
    """Parse orthogroups into line-numbered member records."""
    groups = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            members = []
            for token in line.strip().split():
                if "|" not in token:
                    continue
                prefix, accession = token.split("|", 1)
                species = PREFIX_TO_SPECIES.get(prefix, prefix)
                if species in SPECIES_ORDER:
                    members.append((species, accession, token))
            if members:
                groups.append({"line": line_number, "members": members})
    return groups


def build_summary_tables(
    groups: list[dict[str, object]], protein_to_types: dict[str, set[str]]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return cluster summary, species/type counts, and protein-level records."""
    cluster_rows = []
    protein_records = set()

    for group in groups:
        annotated = []
        for species, accession, _ in group["members"]:
            if accession in protein_to_types:
                annotated.append((species, accession, frozenset(protein_to_types[accession])))
                protein_records.add((species, accession))
        if not annotated:
            continue

        type_sets = [types for _, _, types in annotated]
        union_types = set().union(*type_sets)
        if len(union_types) == 1:
            category = "Single glycan type"
        elif len(set(type_sets)) == 1:
            category = "Same multi-type set"
        else:
            category = "Mixed type sets"

        cluster_rows.append(
            {
                "cluster_line": group["line"],
                "annotated_proteins": len(annotated),
                "species_count": len({species for species, _, _ in annotated}),
                "union_type_count": len(union_types),
                "union_types": "; ".join(gt for gt in GLYCAN_TYPES_ORDER if gt in union_types),
                "consistency_category": category,
            }
        )

    type_count_rows = []
    protein_rows = []
    for species, accession in sorted(protein_records):
        types = protein_to_types[accession]
        protein_rows.append(
            {
                "species": species,
                "accession": accession,
                "type_count": len(types),
                "types": "; ".join(gt for gt in GLYCAN_TYPES_ORDER if gt in types),
            }
        )
        for glycan_type in types:
            type_count_rows.append({"species": species, "glycan_type": glycan_type, "protein_count": 1})

    cluster_df = pd.DataFrame(cluster_rows)
    protein_df = pd.DataFrame(protein_rows)
    type_count_df = (
        pd.DataFrame(type_count_rows)
        .groupby(["species", "glycan_type"], as_index=False)["protein_count"]
        .sum()
    )
    return cluster_df, type_count_df, protein_df


def clean_axes(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="both", labelsize=9, length=3, width=0.7)


def plot_cluster_consistency(cluster_df: pd.DataFrame) -> None:
    total = len(cluster_df)
    fig, (ax_left, ax_right) = plt.subplots(
        1,
        2,
        figsize=(7.4, 3.8),
        gridspec_kw={"width_ratios": [1.08, 1.0], "wspace": 0.34},
    )

    category_order = ["Single glycan type", "Same multi-type set", "Mixed type sets"]
    counts = cluster_df["consistency_category"].value_counts().reindex(category_order, fill_value=0)
    x = np.arange(len(category_order))
    bars = ax_left.bar(
        x,
        counts.values,
        width=0.64,
        color=[CONSISTENCY_COLORS[item] for item in category_order],
        edgecolor="#2E2E2E",
        linewidth=0.7,
    )
    for bar, count in zip(bars, counts.values):
        ax_left.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(total * 0.018, 1.0),
            f"{count}\n{count / total * 100:.1f}%",
            ha="center",
            va="bottom",
            fontsize=8.5,
        )
    ax_left.set_xticks(x)
    ax_left.set_xticklabels(["Single\ntype", "Same\nmulti-type set", "Mixed\ntype sets"], fontsize=8.5)
    ax_left.set_ylabel("Cluster count", fontsize=10)
    ax_left.set_title("Within-cluster glycan-type consistency", fontsize=11, pad=8)
    ax_left.set_ylim(0, max(counts.values) * 1.18)
    clean_axes(ax_left)

    union_counts = Counter(cluster_df["union_type_count"])
    union_x = np.arange(1, len(GLYCAN_TYPES_ORDER) + 1)
    union_y = [union_counts.get(value, 0) for value in union_x]
    colors = plt.cm.YlOrRd(np.linspace(0.28, 0.86, len(union_x)))
    bars = ax_right.bar(
        union_x,
        union_y,
        width=0.68,
        color=colors,
        edgecolor="#2E2E2E",
        linewidth=0.7,
    )
    for bar, count in zip(bars, union_y):
        if count:
            ax_right.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(max(union_y) * 0.025, 0.45),
                str(count),
                ha="center",
                va="bottom",
                fontsize=8.5,
            )
    ax_right.set_xticks(union_x)
    ax_right.set_xlabel("Glycan types observed per cluster", fontsize=10)
    ax_right.set_ylabel("Cluster count", fontsize=10)
    ax_right.set_title("Cluster glycan-type diversity", fontsize=11, pad=8)
    ax_right.set_ylim(0, max(union_y) * 1.18)
    clean_axes(ax_right)

    fig.text(0.01, 0.98, "A", fontsize=14, fontweight="bold", ha="left", va="top")
    fig.text(0.515, 0.98, "B", fontsize=14, fontweight="bold", ha="left", va="top")
    save_fig(fig, "Fig2_cluster_glycotype_consistency")
    plt.close(fig)


def plot_species_proportions(type_count_df: pd.DataFrame) -> None:
    matrix = (
        type_count_df.pivot(index="species", columns="glycan_type", values="protein_count")
        .reindex(index=SPECIES_ORDER, columns=GLYCAN_TYPES_ORDER)
        .fillna(0)
    )
    proportions = matrix.div(matrix.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(7.2, 3.45))
    y = np.arange(len(SPECIES_ORDER))
    left = np.zeros(len(SPECIES_ORDER))
    for glycan_type in GLYCAN_TYPES_ORDER:
        values = proportions[glycan_type].to_numpy()
        bars = ax.barh(
            y,
            values,
            left=left,
            height=0.56,
            color=GLYCAN_TYPE_COLORS[glycan_type],
            edgecolor="white",
            linewidth=0.8,
            label=glycan_type,
        )
        for idx, (bar, value) in enumerate(zip(bars, values)):
            if value >= 7.0:
                red, green, blue, _ = matplotlib.colors.to_rgba(GLYCAN_TYPE_COLORS[glycan_type])
                luminance = 0.299 * red + 0.587 * green + 0.114 * blue
                text_color = "black" if luminance > 0.62 else "white"
                ax.text(
                    left[idx] + value / 2,
                    bar.get_y() + bar.get_height() / 2,
                    f"{value:.0f}%",
                    ha="center",
                    va="center",
                    fontsize=8,
                    color=text_color,
                )
        left += values

    ax.set_xlim(0, 100)
    ax.set_yticks(y)
    ax.set_yticklabels(SPECIES_ORDER, fontsize=10)
    for tick, species in zip(ax.get_yticklabels(), SPECIES_ORDER):
        tick.set_color(SPECIES_COLORS[species])
        tick.set_fontweight("bold")
    ax.invert_yaxis()
    ax.set_xlabel("Protein-glycan type assignments (%)", fontsize=10)
    ax.set_title("Species-level glycan-type composition in Fig. 2 orthogroups", fontsize=11, pad=8)
    ax.grid(axis="x", color="#D9D9D9", linewidth=0.6)
    ax.set_axisbelow(True)
    clean_axes(ax)
    ax.spines["left"].set_visible(False)

    totals = matrix.sum(axis=1).astype(int)
    for idx, species in enumerate(SPECIES_ORDER):
        ax.text(101.0, idx, f"n={totals.loc[species]}", ha="left", va="center", fontsize=8.5)
    ax.set_xlim(0, 112)

    legend = ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, -0.44),
        ncol=3,
        frameon=False,
        fontsize=8.2,
        handlelength=1.0,
        columnspacing=1.1,
    )
    for handle in legend.legend_handles:
        handle.set_linewidth(0)

    save_fig(fig, "Fig2_species_glycotype_proportion")
    plt.close(fig)


def plot_species_type_heatmap(type_count_df: pd.DataFrame) -> None:
    counts = (
        type_count_df.pivot(index="species", columns="glycan_type", values="protein_count")
        .reindex(index=SPECIES_ORDER, columns=GLYCAN_TYPES_ORDER)
        .fillna(0)
        .astype(int)
    )
    percentages = counts.div(counts.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(7.4, 3.2))
    image = ax.imshow(percentages.to_numpy(), cmap="YlGnBu", aspect="auto", vmin=0)
    ax.set_xticks(np.arange(len(GLYCAN_TYPES_ORDER)))
    ax.set_xticklabels(
        [label.replace("Complex-", "Complex\n") for label in GLYCAN_TYPES_ORDER],
        rotation=0,
        ha="center",
        fontsize=8,
    )
    ax.set_yticks(np.arange(len(SPECIES_ORDER)))
    ax.set_yticklabels(SPECIES_ORDER, fontsize=10)
    for tick, species in zip(ax.get_yticklabels(), SPECIES_ORDER):
        tick.set_color(SPECIES_COLORS[species])
        tick.set_fontweight("bold")

    for row_idx, species in enumerate(SPECIES_ORDER):
        for col_idx, glycan_type in enumerate(GLYCAN_TYPES_ORDER):
            value = counts.loc[species, glycan_type]
            pct = percentages.loc[species, glycan_type]
            text_color = "white" if pct >= percentages.to_numpy().max() * 0.52 else "#1F1F1F"
            ax.text(
                col_idx,
                row_idx,
                f"{value}\n{pct:.1f}%",
                ha="center",
                va="center",
                fontsize=7.5,
                color=text_color,
            )

    ax.set_title("Protein counts and within-species percentages", fontsize=11, pad=8)
    ax.tick_params(axis="both", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks(np.arange(-0.5, len(GLYCAN_TYPES_ORDER), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(SPECIES_ORDER), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.2)
    ax.tick_params(which="minor", bottom=False, left=False)

    cbar = fig.colorbar(image, ax=ax, fraction=0.032, pad=0.025)
    cbar.set_label("Within-species percentage", fontsize=9)
    cbar.ax.tick_params(labelsize=8, length=2)

    save_fig(fig, "Fig2_species_glycotype_heatmap")
    plt.close(fig)


def main() -> None:
    orthogroup_path = locate_glycoprotein_orthogroups()
    protein_to_types, _ = load_glycan_type_annotations()
    groups = parse_orthogroups(orthogroup_path)
    cluster_df, type_count_df, protein_df = build_summary_tables(groups, protein_to_types)

    print(f"Orthogroup file: {orthogroup_path}")
    print(f"Annotated clusters: {len(cluster_df)}")
    print("Consistency categories:", cluster_df["consistency_category"].value_counts().to_dict())
    print("Union type-count distribution:", dict(sorted(Counter(cluster_df["union_type_count"]).items())))
    print(f"Annotated proteins in current orthogroups: {len(protein_df)}")
    print("Species protein-type assignment counts:")
    print(type_count_df.pivot(index="species", columns="glycan_type", values="protein_count").fillna(0).astype(int))

    plot_cluster_consistency(cluster_df)
    plot_species_proportions(type_count_df)
    plot_species_type_heatmap(type_count_df)


if __name__ == "__main__":
    main()