"""Visualize glycan-type diversity within Fig. 2 glycoprotein orthogroups.

The script reuses the seven glycan-type classes from the original Fig2 Circle
analysis and summarizes two related questions:
    1. How diverse are glycan-type assignments within each orthogroup?
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
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
from scipy.spatial.distance import braycurtis, jensenshannon

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
    "High Mannose": "#4F8FB5",
    "Pauci-mannose": "#D6A64A",
    "Hybrid": "#4FA582",
    "Complex-Plain": "#BE7EA5",
    "Complex-Fucosylated": "#C9793C",
    "Complex-Sialylated": "#7DB8D8",
    "Other": "#777777",
}
DIVERSITY_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "fig2_diversity_muted", ["#F4D57B", "#E8B45B", "#D98C4D", "#C9694A", "#B64D57"]
)
HEATMAP_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "fig2_heatmap_option3", ["#FFF5D6", "#EFD37A", "#DFA078", "#C5798E", "#9B6A9E", "#70578B"]
)

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


def clean_text(value: object) -> str:
    """Return a stripped string while normalizing empty Excel cells."""
    text = str(value).strip()
    return "" if not text or text.lower() == "nan" else text


def load_glycan_type_annotations() -> tuple[dict[str, set[str]], dict[str, str]]:
    """Load accession-to-glycan-type annotations from the three MS workbooks."""
    protein_to_types: dict[str, set[str]] = defaultdict(set)
    protein_to_species: dict[str, str] = {}
    for species, path in MS_FILES.items():
        df_igp = pd.read_excel(path, sheet_name="IGP_quant")
        for _, row in df_igp.iterrows():
            accession = clean_text(row.get("Protein accession", ""))
            modification = clean_text(row.get("Observed Modification", ""))
            if accession and modification:
                protein_to_types[accession].add(classify_glycan(modification))
                protein_to_species[accession] = species

        df_site = pd.read_excel(path, sheet_name="Site_quant")
        if "N-glycan modifications" not in df_site.columns:
            continue
        for _, row in df_site.iterrows():
            accession = clean_text(row.get("Protein accession", ""))
            modifications = clean_text(row.get("N-glycan modifications", ""))
            if not accession or not modifications:
                continue
            for entry in re.split(r";\s*", modifications):
                entry = clean_text(entry)
                if entry:
                    protein_to_types[accession].add(classify_glycan(entry))
                    protein_to_species[accession] = species
    return dict(protein_to_types), protein_to_species


def build_identification_overview() -> pd.DataFrame:
    """Summarize per-species glycoprotein, glycosite, and glycan coverage."""
    rows = []
    for species, path in MS_FILES.items():
        df_igp = pd.read_excel(path, sheet_name="IGP_quant")
        df_site = pd.read_excel(path, sheet_name="Site_quant")

        glycoproteins: set[str] = set()
        glycosites: set[tuple[str, str]] = set()
        glycan_compositions: set[str] = set()

        for _, row in df_igp.iterrows():
            accession = clean_text(row.get("Protein accession", ""))
            position = clean_text(row.get("Position", ""))
            modification = clean_text(row.get("Observed Modification", ""))
            if not accession or not modification:
                continue
            glycoproteins.add(accession)
            glycan_compositions.add(modification)
            if position:
                glycosites.add((accession, position))

        if "N-glycan modifications" in df_site.columns:
            for _, row in df_site.iterrows():
                accession = clean_text(row.get("Protein accession", ""))
                position = clean_text(row.get("Position", ""))
                modifications = clean_text(row.get("N-glycan modifications", ""))
                if not accession or not modifications:
                    continue
                glycoproteins.add(accession)
                if position:
                    glycosites.add((accession, position))
                for entry in re.split(r";\s*", modifications):
                    entry = clean_text(entry)
                    if entry:
                        glycan_compositions.add(entry)

        rows.append(
            {
                "species": species,
                "glycoproteins": len(glycoproteins),
                "glycosites": len(glycosites),
                "glycan_compositions": len(glycan_compositions),
            }
        )

    return pd.DataFrame(rows)


def build_shared_core_similarity_matrices(
    groups: list[dict[str, object]], protein_to_types: dict[str, set[str]]
) -> tuple[dict[str, pd.DataFrame], int]:
    """Measure composition-aware shared-core similarity across orthogroup-type profiles."""
    species_vectors = {species: [] for species in SPECIES_ORDER}
    shared_group_count = 0

    for group in groups:
        species_type_counts = {species: Counter() for species in SPECIES_ORDER}
        for species, accession, _ in group["members"]:
            if accession not in protein_to_types:
                continue
            for glycan_type in protein_to_types[accession]:
                species_type_counts[species][glycan_type] += 1

        if not all(sum(species_type_counts[species].values()) > 0 for species in SPECIES_ORDER):
            continue

        shared_group_count += 1
        for species in SPECIES_ORDER:
            counts = np.array(
                [species_type_counts[species][glycan_type] for glycan_type in GLYCAN_TYPES_ORDER],
                dtype=float,
            )
            counts /= counts.sum()
            species_vectors[species].extend(counts.tolist())

    if shared_group_count == 0:
        raise ValueError("No shared orthogroups with annotated glycan types were found across all species.")

    normalized_vectors = {}
    for species in SPECIES_ORDER:
        vector = np.array(species_vectors[species], dtype=float)
        normalized_vectors[species] = vector / vector.sum()

    js_similarity = pd.DataFrame(index=SPECIES_ORDER, columns=SPECIES_ORDER, dtype=float)
    bc_similarity = pd.DataFrame(index=SPECIES_ORDER, columns=SPECIES_ORDER, dtype=float)
    for species_a in SPECIES_ORDER:
        vector_a = normalized_vectors[species_a]
        for species_b in SPECIES_ORDER:
            if species_a == species_b:
                js_similarity.loc[species_a, species_b] = 1.0
                bc_similarity.loc[species_a, species_b] = 1.0
                continue
            vector_b = normalized_vectors[species_b]
            js_similarity.loc[species_a, species_b] = 1.0 - float(
                jensenshannon(vector_a, vector_b, base=2.0)
            )
            bc_similarity.loc[species_a, species_b] = 1.0 - float(braycurtis(vector_a, vector_b))
    return {"js": js_similarity, "bc": bc_similarity}, shared_group_count


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
        assignment_counts = Counter(
            glycan_type
            for _, _, types in annotated
            for glycan_type in types
        )
        total_assignments = sum(assignment_counts.values())
        shannon_index = 0.0
        if total_assignments:
            proportions = np.array(list(assignment_counts.values()), dtype=float) / total_assignments
            shannon_index = float(-(proportions * np.log2(proportions)).sum())

        cluster_rows.append(
            {
                "cluster_line": group["line"],
                "annotated_proteins": len(annotated),
                "species_count": len({species for species, _, _ in annotated}),
                "union_type_count": len(union_types),
                "glycan_type_richness": len(union_types),
                "shannon_index": shannon_index,
                "union_types": "; ".join(gt for gt in GLYCAN_TYPES_ORDER if gt in union_types),
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
    ax.tick_params(axis="both", labelsize=12.2, length=3.6, width=0.85)


def draw_similarity_heatmap(
    ax: plt.Axes,
    similarity_df: pd.DataFrame,
    title: str,
    note: str,
    vmin: float | None = None,
) -> None:
    """Render a small species-by-species similarity heatmap."""
    similarity_matrix = similarity_df.reindex(index=SPECIES_ORDER, columns=SPECIES_ORDER)
    values = similarity_matrix.to_numpy(dtype=float)
    off_diagonal = values[~np.eye(len(SPECIES_ORDER), dtype=bool)]
    min_value = float(off_diagonal.min()) if off_diagonal.size else 0.0
    heatmap_vmin = min(min_value, 0.55) if vmin is None else vmin
    ax.imshow(values, cmap=HEATMAP_CMAP, aspect="equal", vmin=heatmap_vmin, vmax=1.0)
    ax.set_xticks(np.arange(len(SPECIES_ORDER)))
    ax.set_yticks(np.arange(len(SPECIES_ORDER)))
    ax.set_xticklabels(SPECIES_ORDER, fontsize=12.8)
    ax.set_yticklabels(SPECIES_ORDER, fontsize=12.8)
    for tick, species in zip(ax.get_xticklabels(), SPECIES_ORDER):
        tick.set_color(SPECIES_COLORS[species])
        tick.set_fontweight("bold")
    for tick, species in zip(ax.get_yticklabels(), SPECIES_ORDER):
        tick.set_color(SPECIES_COLORS[species])
        tick.set_fontweight("bold")
    for row_index in range(len(SPECIES_ORDER)):
        for col_index in range(len(SPECIES_ORDER)):
            value = values[row_index, col_index]
            text_color = "white" if value >= heatmap_vmin + (1.0 - heatmap_vmin) * 0.58 else "#1F1F1F"
            ax.text(
                col_index,
                row_index,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=11.8,
                color=text_color,
            )
    ax.set_title(title, fontsize=15.2, pad=8)
    ax.tick_params(axis="both", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks(np.arange(-0.5, len(SPECIES_ORDER), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(SPECIES_ORDER), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.2)
    ax.tick_params(which="minor", bottom=False, left=False)
    ax.text(
        0.5,
        -0.16,
        note,
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=11.2,
    )


def draw_coverage_overview(ax_left: plt.Axes, overview_df: pd.DataFrame) -> None:
    """Render the per-species identification coverage as a compact lollipop chart."""
    metric_keys = ["glycoproteins", "glycosites", "glycan_compositions"]
    metric_labels = ["Glycoproteins", "Glycosites", "Glycan\ncompositions"]
    overview_matrix = overview_df.set_index("species").reindex(SPECIES_ORDER)
    y = np.arange(len(metric_keys), dtype=float)
    max_value = overview_matrix[metric_keys].to_numpy().max()
    species_offsets = {"Gallus": -0.18, "Columba": 0.0, "Anas": 0.18}
    for row_index, metric_key in enumerate(metric_keys):
        ax_left.hlines(y[row_index], 0, max_value * 1.02, color="#E7E7E7", linewidth=0.8, zorder=0)
        values = overview_matrix[metric_key].to_numpy(dtype=float)
        for species, value in zip(SPECIES_ORDER, values):
            y_pos = y[row_index] + species_offsets[species]
            ax_left.hlines(
                y_pos,
                0,
                value,
                color=SPECIES_COLORS[species],
                linewidth=1.8,
                alpha=0.9,
                zorder=2,
            )
            ax_left.scatter(
                value,
                y_pos,
                s=74,
                color=SPECIES_COLORS[species],
                edgecolors="white",
                linewidths=0.8,
                zorder=3,
                label=species if row_index == 0 else None,
            )
            ax_left.text(
                value + max_value * 0.015,
                y_pos,
                f"{int(value)}",
                ha="left",
                va="center",
                fontsize=11.2,
            )
    ax_left.set_yticks(y)
    ax_left.set_yticklabels(metric_labels, fontsize=12.6)
    ax_left.set_xlabel("Count", fontsize=14.0)
    ax_left.grid(axis="x", color="#E2E2E2", linewidth=0.6)
    ax_left.set_axisbelow(True)
    ax_left.set_xlim(0, max_value * 1.22)
    ax_left.set_ylim(-0.55, len(metric_keys) - 0.45)
    ax_left.invert_yaxis()
    clean_axes(ax_left)
    ax_left.spines["left"].set_visible(False)
    legend = ax_left.legend(
        loc="upper center",
        bbox_to_anchor=(0.49, 1.08),
        ncol=3,
        frameon=False,
        fontsize=10.6,
        handlelength=1.1,
        handletextpad=0.4,
        columnspacing=1.0,
    )
    for handle in legend.legend_handles:
        handle.set_linewidth(0)


def plot_coverage_overview(overview_df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(4.5, 3.95))
    draw_coverage_overview(ax, overview_df)
    fig.subplots_adjust(top=0.90, bottom=0.18, left=0.28, right=0.99)
    save_fig(fig, "Fig2_coverage_overview")
    plt.close(fig)


def plot_shared_core_similarity(similarity_df: pd.DataFrame, shared_group_count: int) -> None:
    fig, ax = plt.subplots(figsize=(4.1, 4.1))
    draw_similarity_heatmap(
        ax,
        similarity_df,
        title="Shared-core JS",
        note=f"1 - Jensen-Shannon distance; n={shared_group_count}",
    )
    fig.subplots_adjust(top=0.89, bottom=0.22, left=0.18, right=0.99)
    save_fig(fig, "Fig2_shared_core_js")
    plt.close(fig)


def plot_cluster_consistency(
    overview_df: pd.DataFrame, similarity_df: pd.DataFrame, shared_group_count: int
) -> None:
    fig, (ax_left, ax_right) = plt.subplots(
        1,
        2,
        figsize=(7.5, 3.7),
        gridspec_kw={"width_ratios": [1.04, 1.0], "wspace": 0.30},
    )

    draw_coverage_overview(ax_left, overview_df)

    draw_similarity_heatmap(
        ax_right,
        similarity_df,
        title="Shared-core JS",
        note=f"1 - Jensen-Shannon distance; n={shared_group_count}",
    )

    fig.subplots_adjust(top=0.88, bottom=0.18)
    save_fig(fig, "Fig2_cluster_glycotype_consistency")
    plt.close(fig)


def plot_similarity_metric_comparison(
    js_similarity_df: pd.DataFrame, bc_similarity_df: pd.DataFrame, shared_group_count: int
) -> None:
    """Export a side-by-side metric comparison for selecting the main-panel distance."""
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 3.2), gridspec_kw={"wspace": 0.32})
    shared_vmin = min(
        float(js_similarity_df.to_numpy()[~np.eye(len(SPECIES_ORDER), dtype=bool)].min()),
        float(bc_similarity_df.to_numpy()[~np.eye(len(SPECIES_ORDER), dtype=bool)].min()),
        0.55,
    )
    draw_similarity_heatmap(
        axes[0],
        js_similarity_df,
        title="Jensen-Shannon",
        note=f"1 - JS distance; n={shared_group_count}",
        vmin=shared_vmin,
    )
    draw_similarity_heatmap(
        axes[1],
        bc_similarity_df,
        title="Bray-Curtis",
        note="1 - Bray-Curtis distance",
        vmin=shared_vmin,
    )
    fig.subplots_adjust(top=0.88, bottom=0.22)
    save_fig(fig, "Fig2_shared_core_metric_comparison")
    plt.close(fig)


def plot_species_proportions(type_count_df: pd.DataFrame) -> None:
    matrix = (
        type_count_df.pivot(index="species", columns="glycan_type", values="protein_count")
        .reindex(index=SPECIES_ORDER, columns=GLYCAN_TYPES_ORDER)
        .fillna(0)
    )
    proportions = matrix.div(matrix.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(8.4, 4.55))
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
                red, green, blue, _ = mcolors.to_rgba(GLYCAN_TYPE_COLORS[glycan_type])
                luminance = 0.299 * red + 0.587 * green + 0.114 * blue
                text_color = "black" if luminance > 0.62 else "white"
                ax.text(
                    left[idx] + value / 2,
                    bar.get_y() + bar.get_height() / 2,
                    f"{value:.0f}%",
                    ha="center",
                    va="center",
                    fontsize=11.0,
                    color=text_color,
                )
        left += values

    ax.set_xlim(0, 100)
    ax.set_yticks(y)
    ax.set_yticklabels(SPECIES_ORDER, fontsize=13.2)
    for tick, species in zip(ax.get_yticklabels(), SPECIES_ORDER):
        tick.set_color(SPECIES_COLORS[species])
        tick.set_fontweight("bold")
    ax.invert_yaxis()
    ax.set_xlabel("Protein-glycan type assignments (%)", fontsize=13.8)
    ax.grid(axis="x", color="#D9D9D9", linewidth=0.6)
    ax.set_axisbelow(True)
    clean_axes(ax)
    ax.spines["left"].set_visible(False)

    totals = matrix.sum(axis=1).astype(int)
    for idx, species in enumerate(SPECIES_ORDER):
        ax.text(101.0, idx, f"n={totals.loc[species]}", ha="left", va="center", fontsize=11.4)
    ax.set_xlim(0, 112)

    fig.subplots_adjust(left=0.10, right=0.985, bottom=0.15, top=0.82)
    legend = ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.08),
        ncol=len(GLYCAN_TYPES_ORDER),
        frameon=False,
        fontsize=9.8,
        handlelength=1.1,
        handletextpad=0.45,
        labelspacing=0.6,
        columnspacing=1.1,
        borderaxespad=0.0,
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

    fig, ax = plt.subplots(figsize=(7.6, 3.45))
    image = ax.imshow(percentages.to_numpy(), cmap=HEATMAP_CMAP, aspect="auto", vmin=0)
    ax.set_xticks(np.arange(len(GLYCAN_TYPES_ORDER)))
    ax.set_xticklabels(
        [label.replace("Complex-", "Complex\n") for label in GLYCAN_TYPES_ORDER],
        rotation=0,
        ha="center",
        fontsize=8.6,
    )
    ax.set_yticks(np.arange(len(SPECIES_ORDER)))
    ax.set_yticklabels(SPECIES_ORDER, fontsize=10.5)
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
                fontsize=8.0,
                color=text_color,
            )

    ax.set_title("Protein counts and within-species percentages", fontsize=12, pad=8)
    ax.tick_params(axis="both", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xticks(np.arange(-0.5, len(GLYCAN_TYPES_ORDER), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(SPECIES_ORDER), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.2)
    ax.tick_params(which="minor", bottom=False, left=False)

    cbar = fig.colorbar(image, ax=ax, fraction=0.032, pad=0.025)
    cbar.set_label("Within-species percentage", fontsize=9.5)
    cbar.ax.tick_params(labelsize=8.5, length=2)

    save_fig(fig, "Fig2_species_glycotype_heatmap")
    plt.close(fig)


def main() -> None:
    orthogroup_path = locate_glycoprotein_orthogroups()
    protein_to_types, _ = load_glycan_type_annotations()
    groups = parse_orthogroups(orthogroup_path)
    cluster_df, type_count_df, protein_df = build_summary_tables(groups, protein_to_types)
    overview_df = build_identification_overview()
    similarity_matrices, shared_group_count = build_shared_core_similarity_matrices(groups, protein_to_types)
    js_similarity_df = similarity_matrices["js"]
    bc_similarity_df = similarity_matrices["bc"]

    print(f"Orthogroup file: {orthogroup_path}")
    print(f"Annotated clusters: {len(cluster_df)}")
    print(f"Annotated proteins in current orthogroups: {len(protein_df)}")
    print("Identification overview:")
    print(overview_df.set_index("species"))
    print(f"Shared annotated orthogroups across all three species: {shared_group_count}")
    print("Shared-core Jensen-Shannon similarity matrix:")
    print(js_similarity_df.round(3))
    print("Shared-core Bray-Curtis similarity matrix:")
    print(bc_similarity_df.round(3))
    print("Species protein-type assignment counts:")
    print(type_count_df.pivot(index="species", columns="glycan_type", values="protein_count").fillna(0).astype(int))

    plot_coverage_overview(overview_df)
    plot_shared_core_similarity(js_similarity_df, shared_group_count)
    plot_cluster_consistency(overview_df, js_similarity_df, shared_group_count)
    plot_similarity_metric_comparison(js_similarity_df, bc_similarity_df, shared_group_count)
    plot_species_proportions(type_count_df)


if __name__ == "__main__":
    main()