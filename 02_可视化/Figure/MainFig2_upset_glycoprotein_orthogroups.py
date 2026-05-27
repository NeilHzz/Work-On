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
matplotlib.rcParams["font.size"] = 11
matplotlib.rcParams["axes.linewidth"] = 1.0
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "01_数据与计算" / "糖蛋白Ortho" / "Orthogroups.txt.gz.txt"

SPECIES_ORDER = ["GlyGallus", "GlyColumba", "GlyAnas"]
SPECIES_COLORS = {
    "GlyGallus": "#C46B83",
    "GlyAnas": "#93AACD",
    "GlyColumba": "#F3CE9D",
}
DISPLAY_LABELS = {
    "GlyGallus": "Gallus",
    "GlyColumba": "Columba",
    "GlyAnas": "Anas",
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
                memberships.append(present)
    return memberships


def ordered_intersections(memberships):
    counts = Counter(memberships)
    return [(group, counts.get(group, 0)) for group in ALL_INTERSECTIONS]


def draw_upset(memberships):
    intersections = ordered_intersections(memberships)
    set_counts = {species: sum(species in group for group in memberships) for species in SPECIES_ORDER}

    fig = plt.figure(figsize=(13.8, 6.2), dpi=300)
    gs = fig.add_gridspec(
        2, 2,
        width_ratios=[1.45, 5.9],
        height_ratios=[2.45, 1.95],
        left=0.075, right=0.985, bottom=0.14, top=0.94,
        wspace=0.12, hspace=0.07,
    )
    ax_top = fig.add_subplot(gs[0, 1])
    ax_left = fig.add_subplot(gs[1, 0])
    ax_matrix = fig.add_subplot(gs[1, 1], sharex=ax_top)

    x = list(range(len(intersections)))
    top_counts = [count for _, count in intersections]
    ax_top.bar(
        x, top_counts,
        width=0.66,
        facecolor="white",
        edgecolor="#222222",
        linewidth=1.15,
        zorder=3,
    )
    for xi, value in zip(x, top_counts):
        offset = max(top_counts) * 0.025
        ax_top.text(xi, value + offset, str(value),
                    ha="center", va="bottom", fontsize=10)
    ax_top.set_ylabel("Cluster Count", fontsize=13)
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
    ax_matrix.set_yticklabels([DISPLAY_LABELS[species] for species in SPECIES_ORDER], fontsize=10)
    ax_matrix.tick_params(axis="y", length=0, pad=7)
    ax_matrix.tick_params(axis="x", bottom=False, labelbottom=False)
    for xi, (group, _) in zip(x, intersections):
        present_y = [y_positions[species] for species in SPECIES_ORDER if species in group]
        if len(present_y) > 1:
            ax_matrix.plot([xi, xi], [min(present_y), max(present_y)],
                           color=mixed_species_color(group), linewidth=2.6,
                           zorder=2.5, solid_capstyle="round")
        for species in SPECIES_ORDER:
            y = y_positions[species]
            if species in group:
                ax_matrix.scatter(xi, y, s=260, color=SPECIES_COLORS[species],
                                  edgecolor="white", linewidth=0.8, zorder=3)
            else:
                ax_matrix.scatter(xi, y, s=260, color="#D8D8D8",
                                  edgecolor="white", linewidth=0.8, zorder=2)
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
        ax_left.text(value + max(left_values) * 0.035, y, str(value),
                     ha="left", va="center", fontsize=10)
    ax_left.set_yticks(y_ticks)
    ax_left.set_yticklabels([])
    ax_left.set_xlabel("Cluster count", fontsize=11)
    ax_left.set_xlim(max(left_values) * 1.20, 0)
    ax_left.xaxis.set_major_locator(ticker.MaxNLocator(4, integer=True))
    ax_left.tick_params(axis="x", labelsize=9)
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
