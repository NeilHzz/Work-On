#!/usr/bin/env python
"""Render compact OVAL Re-Glyco structure context panels for main Fig. 4.

The output panels are intentionally lightweight: they use the existing PDB
coordinates directly, avoiding external molecular-rendering dependencies while
still preserving the relative protein backbone, glycan position, and hotspot
context needed for the grouped Fig. 4 metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from mpl_toolkits.mplot3d.art3d import Line3DCollection


ROOT = Path(__file__).resolve().parents[2]
REGLYCO = ROOT / "01_数据与计算" / "ReGlyco_Ensemble"
PDB_DIR = REGLYCO / "PDB"
CSV_DIR = REGLYCO / "csv"
OUT_DIR = Path(__file__).resolve().parent / "PNG"
OUT_DIR.mkdir(exist_ok=True)

SPECIES_COLORS = {
    "Gallus": "#C46B83",
    "Anas": "#93AACD",
    "Columba": "#F3CE9D",
}

MODEL_SPECS = [
    ("Gallus", "G1", "Gallus_G80966KZ.pdb"),
    ("Anas", "A1", "Anas_G20030CU.pdb"),
    ("Columba", "C1", "Columba_Hex11_GS00635.pdb"),
]

AA_RESNAMES = {
    "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
    "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
}

ACIDIC_RESNAMES = {"ASP", "GLU"}
GLYCAN_CHAIN = "B"
SHIELD_DISTANCE = 15.0


@dataclass
class Structure:
    species: str
    short_name: str
    ca: np.ndarray
    ca_resseq: np.ndarray
    protein_atoms: np.ndarray
    glycan_atoms: np.ndarray
    hotspot_resseq: set[int]
    acidic_resseq: set[int]


def parse_first_model(pdb_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    ca_coords: list[list[float]] = []
    ca_resseq: list[int] = []
    protein_atoms: list[list[float]] = []
    glycan_atoms: list[list[float]] = []
    in_model = False

    with pdb_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("MODEL"):
                if in_model:
                    break
                in_model = True
                continue
            if line.startswith("ENDMDL") and in_model:
                break
            if not line.startswith(("ATOM", "HETATM")):
                continue

            chain = line[21].strip()
            atom = line[12:16].strip()
            resname = line[17:20].strip()
            element = (line[76:78].strip() or atom[0]).upper()
            if element == "H":
                continue

            xyz = [float(line[30:38]), float(line[38:46]), float(line[46:54])]
            if chain == GLYCAN_CHAIN:
                glycan_atoms.append(xyz)
            elif resname in AA_RESNAMES:
                protein_atoms.append(xyz)
                if atom == "CA":
                    ca_coords.append(xyz)
                    ca_resseq.append(int(line[22:26]))

    return (
        np.asarray(ca_coords, dtype=float),
        np.asarray(ca_resseq, dtype=int),
        np.asarray(protein_atoms, dtype=float),
        np.asarray(glycan_atoms, dtype=float),
    )


def load_hotspot_sets(short_name: str) -> tuple[set[int], set[int]]:
    csv_path = CSV_DIR / f"{short_name}_APBS_glycanAware.csv"
    if not csv_path.exists():
        return set(), set()
    df = pd.read_csv(csv_path)
    protein_surface = df[(df["Type"] == "Protein") & (df["SurfaceLabel"] == "Surface")]
    acidic = protein_surface[protein_surface["ResName"].isin(ACIDIC_RESNAMES)]
    hotspots = acidic[acidic["APBS_kT_e"] < -5.0]
    return set(hotspots["ResSeq"].astype(int)), set(acidic["ResSeq"].astype(int))


def load_structures() -> list[Structure]:
    structures: list[Structure] = []
    for species, short_name, filename in MODEL_SPECS:
        ca, ca_resseq, protein_atoms, glycan_atoms = parse_first_model(PDB_DIR / filename)
        hotspots, acidic = load_hotspot_sets(short_name)
        structures.append(
            Structure(
                species=species,
                short_name=short_name,
                ca=ca,
                ca_resseq=ca_resseq,
                protein_atoms=protein_atoms,
                glycan_atoms=glycan_atoms,
                hotspot_resseq=hotspots,
                acidic_resseq=acidic,
            )
        )
    return structures


def pca_transform(structure: Structure) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    center = structure.ca.mean(axis=0)
    centered_ca = structure.ca - center
    _, _, vh = np.linalg.svd(centered_ca, full_matrices=False)
    rot = vh.T

    ca = centered_ca @ rot
    protein = (structure.protein_atoms - center) @ rot
    glycan = (structure.glycan_atoms - center) @ rot

    if len(glycan) and glycan[:, 1].mean() < ca[:, 1].mean():
        ca[:, 1] *= -1
        protein[:, 1] *= -1
        glycan[:, 1] *= -1
    if len(glycan) and glycan[:, 2].mean() < ca[:, 2].mean():
        ca[:, 2] *= -1
        protein[:, 2] *= -1
        glycan[:, 2] *= -1
    return ca, protein, glycan, structure.ca_resseq


def set_axis_equal(ax, points: np.ndarray, pad: float = 4.0) -> None:
    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    centers = (mins + maxs) / 2
    radius = max(maxs - mins) / 2 + pad
    ax.set_xlim(centers[0] - radius, centers[0] + radius)
    ax.set_ylim(centers[1] - radius, centers[1] + radius)
    ax.set_zlim(centers[2] - radius, centers[2] + radius)
    ax.set_box_aspect((1, 1, 1))


def draw_trace(ax, ca: np.ndarray, color: str, lw: float = 3.0, alpha: float = 0.80) -> None:
    segments = np.stack([ca[:-1], ca[1:]], axis=1)
    collection = Line3DCollection(segments, colors=color, linewidths=lw, alpha=alpha)
    ax.add_collection3d(collection)


def draw_glycan(ax, glycan: np.ndarray, color: str, mode: str) -> None:
    if len(glycan) == 0:
        return
    if mode == "glycan_zoom":
        ax.scatter(glycan[:, 0], glycan[:, 1], glycan[:, 2], s=26, c=color, alpha=0.95, depthshade=True)
        segments = np.stack([glycan[:-1], glycan[1:]], axis=1)
        ax.add_collection3d(Line3DCollection(segments, colors=color, linewidths=1.7, alpha=0.45))
    else:
        ax.scatter(glycan[:, 0], glycan[:, 1], glycan[:, 2], s=13, c=color, alpha=0.82, depthshade=True)


def hotspot_coords(structure: Structure, ca: np.ndarray, residues: set[int]) -> np.ndarray:
    if not residues:
        return np.empty((0, 3))
    mask = np.array([int(resseq) in residues for resseq in structure.ca_resseq])
    return ca[mask]


def split_hotspots_by_glycan(structure: Structure, ca: np.ndarray, glycan: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    hs = hotspot_coords(structure, ca, structure.hotspot_resseq)
    if len(hs) == 0 or len(glycan) == 0:
        return hs, np.empty((0, 3))
    distances = np.sqrt(((hs[:, None, :] - glycan[None, :, :]) ** 2).sum(axis=2)).min(axis=1)
    shielded = hs[distances <= SHIELD_DISTANCE]
    accessible = hs[distances > SHIELD_DISTANCE]
    return accessible, shielded


def style_axis(ax) -> None:
    ax.set_axis_off()
    ax.view_init(elev=18, azim=-62, roll=0)
    ax.set_facecolor("white")


def draw_structure(ax, structure: Structure, mode: str) -> None:
    color = SPECIES_COLORS[structure.species]
    ca, protein, glycan, _ = pca_transform(structure)
    style_axis(ax)

    if mode == "glycan_zoom" and len(glycan):
        contact = ca[np.argmin(((ca[:, None, :] - glycan[None, :, :]) ** 2).sum(axis=2).min(axis=1))]
        points_for_limits = np.vstack([glycan, contact[None, :]])
        draw_trace(ax, ca, "#B8B8B8", lw=1.7, alpha=0.28)
        draw_glycan(ax, glycan, color, mode)
        ax.scatter([contact[0]], [contact[1]], [contact[2]], s=48, c="#4A4A4A", depthshade=True)
        set_axis_equal(ax, points_for_limits, pad=8.0)
    else:
        draw_trace(ax, ca, "#AFAFAF", lw=2.8, alpha=0.72)
        if mode in {"surface", "shielding"}:
            hs = hotspot_coords(structure, ca, structure.hotspot_resseq)
            if len(hs):
                ax.scatter(hs[:, 0], hs[:, 1], hs[:, 2], s=35, c="#D0473C", alpha=0.95, depthshade=True)
        if mode == "partition":
            accessible, shielded = split_hotspots_by_glycan(structure, ca, glycan)
            if len(accessible):
                ax.scatter(accessible[:, 0], accessible[:, 1], accessible[:, 2], s=36, c="#D0473C", alpha=0.95, depthshade=True)
            if len(shielded):
                ax.scatter(shielded[:, 0], shielded[:, 1], shielded[:, 2], s=42, c="#404040", alpha=0.95, depthshade=True)
        draw_glycan(ax, glycan, color, mode)
        set_axis_equal(ax, np.vstack([protein, glycan]), pad=3.0)

    ax.text2D(0.02, 0.84, structure.species, transform=ax.transAxes,
              color=color, fontsize=10, fontweight="bold", family="Times New Roman")


def render_group(filename: str, title: str, mode: str, structures: list[Structure]) -> None:
    plt.rcParams["font.family"] = "Times New Roman"
    fig = plt.figure(figsize=(11.0, 2.05), dpi=300)
    fig.patch.set_facecolor("white")
    fig.text(0.5, 0.98, title, ha="center", va="top", fontsize=13, fontweight="bold")

    for index, structure in enumerate(structures, start=1):
        ax = fig.add_subplot(1, 3, index, projection="3d")
        draw_structure(ax, structure, mode)

    plt.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.89, wspace=-0.18)
    out = OUT_DIR / filename
    fig.savefig(out, dpi=300, facecolor="white", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print(f"Saved {out}")


def main() -> None:
    structures = load_structures()
    render_group("Fig4_model_A_C.png", "A-C surface state", "surface", structures)
    render_group("Fig4_model_D_G.png", "D-G glycan geometry", "glycan_zoom", structures)
    render_group("Fig4_model_H_K.png", "H-K shielding interface", "shielding", structures)
    render_group("Fig4_model_L_M.png", "L-M accessible hotspots", "partition", structures)


if __name__ == "__main__":
    main()