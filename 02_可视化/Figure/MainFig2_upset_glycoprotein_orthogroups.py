"""
Main Fig. 2 -- glycoprotein orthogroup UpSet plot.

Data source: 01_数据与计算/糖蛋白Ortho/Orthogroups.txt.gz.txt
Each line is treated as one orthogroup cluster; species membership is inferred
from GlyGallus/GlyColumba/GlyAnas prefixes.
"""
from collections import Counter
from pathlib import Path
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _save import save_fig

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.family"] = "Times New Roman"
matplotlib.rcParams["font.size"] = 12.5
matplotlib.rcParams["axes.linewidth"] = 1.0
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.offsetbox import AnnotationBbox, OffsetImage

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "01_数据与计算" / "糖蛋白Ortho" / "Orthogroups.txt.gz.txt"
ICON_DIR = ROOT / "02_可视化" / "eggtooth"

SPECIES_ORDER = ["GlyGallus", "GlyColumba", "GlyAnas"]
SPECIES_COLORS = {
    "GlyGallus": "#C46B83",
    "GlyAnas": "#93AACD",
    "GlyColumba": "#F3CE9D",
}
NODE_SIZE_MIN = 300
NODE_SIZE_MAX = 900
DISPLAY_LABELS = {
    "GlyGallus": "Gallus",
    "GlyColumba": "Columba",
    "GlyAnas": "Anas",
}
SPECIES_ICONS = {
    "GlyGallus": ICON_DIR / "icon_Gallus.jpg",
    "GlyColumba": ICON_DIR / "icon_Columba.jpg",
    "GlyAnas": ICON_DIR / "icon_Anas.jpg",
}

ALL_INTERSECTIONS = [
    frozenset(["GlyGallus", "GlyColumba", "GlyAnas"]),
    frozenset(["GlyColumba", "GlyAnas"]),
    frozenset(["GlyGallus", "GlyAnas"]),
    frozenset(["GlyGallus", "GlyColumba"]),
    frozenset(["GlyAnas"]),
    frozenset(["GlyColumba"]),
    frozenset(["GlyGallus"]),
]


def _hex_to_rgb(color):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#" + "".join(f"{value:02X}" for value in rgb)


def mixed_species_color(group):
    rgb_values = [_hex_to_rgb(SPECIES_COLORS[species]) for species in group]
    mixed = tuple(round(sum(channel) / len(rgb_values)) for channel in zip(*rgb_values))
    return _rgb_to_hex(mixed)


def load_memberships(path: Path):
    memberships = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            tokens = line.strip().split()
            if not tokens:
                continue
            present = frozenset(
                species
                for species in SPECIES_ORDER
                if any(token.startswith(f"{species}|") for token in tokens)
            )
            if present:
                protein_counts = Counter(
                    token.split("|", 1)[0]
                    for token in tokens
                    if "|" in token and token.split("|", 1)[0] in SPECIES_ORDER
                )
                memberships.append((present, protein_counts))
    return memberships


def ordered_intersections(memberships):
    counts = Counter(group for group, _ in memberships)
    return [(group, counts.get(group, 0)) for group in ALL_INTERSECTIONS]


def intersection_protein_counts(memberships):
    protein_counts = {group: Counter() for group in ALL_INTERSECTIONS}
    for group, counts in memberships:
        protein_counts.setdefault(group, Counter()).update(counts)
    return protein_counts


def draw_upset(memberships):
    intersections = ordered_intersections(memberships)
    protein_counts = intersection_protein_counts(memberships)
    set_counts = {species: sum(species in group for group, _ in memberships) for species in SPECIES_ORDER}
    avg_proteins = {
        (group, species): (protein_counts[group][species] / count if count else 0)
        for group, count in intersections
        for species in SPECIES_ORDER
        if species in group
    }
    max_avg_protein = max([value for value in avg_proteins.values() if value > 0] or [1])

    def node_size(group, species):
        avg = avg_proteins.get((group, species), 0)
        if avg <= 0:
            return NODE_SIZE_MIN
        scale = (avg - 1) / max(max_avg_protein - 1, 1)
        return NODE_SIZE_MIN + scale * (NODE_SIZE_MAX - NODE_SIZE_MIN)

    fig = plt.figure(figsize=(14.8, 6.9), dpi=300)
    gs = fig.add_gridspec(
        2, 2,
        width_ratios=[1.45, 5.9],
        height_ratios=[3.25, 1.65],
        left=0.068, right=0.988, bottom=0.13, top=0.948,
        wspace=0.06, hspace=0.07,
    )
    ax_top = fig.add_subplot(gs[0, 1])
    ax_left = fig.add_subplot(gs[1, 0])
    ax_matrix = fig.add_subplot(gs[1, 1], sharex=ax_top)

    x = list(range(len(intersections)))
    top_counts = [count for _, count in intersections]
    bar_width = 0.66
    for xi, (group, value) in zip(x, intersections):
        total_proteins = sum(protein_counts[group].values())
        bottom = 0
        for species in SPECIES_ORDER:
            if value <= 0 or total_proteins <= 0:
                continue
            segment_h = value * protein_counts[group][species] / total_proteins
            ax_top.bar(
                xi, segment_h, bottom=bottom, width=bar_width,
                color=SPECIES_COLORS[species], edgecolor="none", zorder=3,
            )
            bottom += segment_h
    for xi, value in zip(x, top_counts):
        offset = max(top_counts) * 0.025
        ax_top.text(xi, value + offset, str(value),
                    ha="center", va="bottom", fontsize=13.8)
    ax_top.set_ylabel("Cluster Count", fontsize=17.0)
    ax_top.set_xlim(-0.7, len(intersections) - 0.35)
    ax_top.set_ylim(0, max(top_counts) * 1.22)
    ax_top.yaxis.set_major_locator(ticker.MaxNLocator(5, integer=True))
    ax_top.grid(False)
    ax_top.tick_params(axis="x", bottom=False, labelbottom=False)
    ax_top.spines["top"].set_visible(False)
    ax_top.spines["right"].set_visible(False)

    y_positions = {species: len(SPECIES_ORDER) - 1 - idx for idx, species in enumerate(SPECIES_ORDER)}
    y_ticks = [y_positions[species] for species in SPECIES_ORDER]
    ax_matrix.set_ylim(-0.65, len(SPECIES_ORDER) - 0.35)
    ax_matrix.set_yticks(y_ticks)
    ax_matrix.set_yticklabels([])
    ax_matrix.tick_params(axis="y", length=0, pad=7)
    ax_matrix.tick_params(axis="x", bottom=False, labelbottom=False)
    label_x = -0.66
    icon_x = -0.86
    for species in SPECIES_ORDER:
        y = y_positions[species]
        icon_path = SPECIES_ICONS[species]
        if icon_path.exists():
            icon = plt.imread(icon_path)
            image_box = OffsetImage(icon, zoom=0.115)
            ax_matrix.add_artist(
                AnnotationBbox(
                    image_box,
                    (icon_x, y),
                    frameon=False,
                    box_alignment=(0.5, 0.5),
                    pad=0,
                    zorder=5,
                )
            )
        ax_matrix.text(
            label_x, y, DISPLAY_LABELS[species],
            ha="left", va="center", fontsize=13.6,
            color=SPECIES_COLORS[species], fontweight="bold",
        )
    for xi, (group, _) in zip(x, intersections):
        present_y = [y_positions[species] for species in SPECIES_ORDER if species in group]
        if len(present_y) > 1:
            ax_matrix.plot([xi, xi], [min(present_y), max(present_y)],
                           color=mixed_species_color(group), linewidth=2.6,
                           zorder=2.5, solid_capstyle="round")
        for species in SPECIES_ORDER:
            y = y_positions[species]
            if species in group:
                ax_matrix.scatter(xi, y, s=node_size(group, species), color=SPECIES_COLORS[species],
                                  edgecolor="white", linewidth=0.8, zorder=3)
            else:
                ax_matrix.scatter(xi, y, s=300, color="#D8D8D8",
                                  edgecolor="white", linewidth=0.8, zorder=2)
    ax_matrix.set_xlim(-0.9, len(intersections) - 0.35)
    ax_matrix.spines["top"].set_visible(False)
    ax_matrix.spines["right"].set_visible(False)
    ax_matrix.spines["left"].set_visible(False)
    ax_matrix.spines["bottom"].set_visible(False)

    left_values = [set_counts[species] for species in SPECIES_ORDER]
    ax_left.barh(
        y_ticks, left_values,
        height=0.64,
        color=[SPECIES_COLORS[species] for species in SPECIES_ORDER],
        edgecolor="none",
    )
    for y, value in zip(y_ticks, left_values):
        ax_left.text(value + max(left_values) * 0.065, y, str(value),
                 ha="right", va="center", fontsize=13.6)
    ax_left.set_yticks(y_ticks)
    ax_left.set_yticklabels([])
    ax_left.set_xlabel("Cluster count", fontsize=14.6)
    ax_left.set_xlim(max(left_values) * 1.20, 0)
    ax_left.xaxis.set_major_locator(ticker.MaxNLocator(4, integer=True))
    ax_left.tick_params(axis="x", labelsize=12.4)
    ax_left.tick_params(axis="y", length=0)
    ax_left.spines["top"].set_visible(False)
    ax_left.spines["right"].set_visible(False)
    ax_left.spines["left"].set_visible(False)

    return fig, intersections, set_counts


def main():
    memberships = load_memberships(DATA)
    fig, intersections, set_counts = draw_upset(memberships)
    save_fig(fig, "Fig2", dpi=300)
    plt.close(fig)
    print("Set counts:", set_counts)
    print("Intersections:", [(tuple(sorted(group)), count) for group, count in intersections])


if __name__ == "__main__":
    main()
