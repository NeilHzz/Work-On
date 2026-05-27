#!/usr/bin/env python
"""Render PyMOL-based explanatory structure panels for main Fig. 4.

Outputs:
  - Fig4_model_D_G.png: Gallus OVAL glycan geometry with four metric callouts.
  - Fig4_model_H_K.png: Gallus/Anas/Columba hotspot shielding examples.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import math
import shutil
import subprocess
import textwrap

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
REGLYCO = ROOT / "01_数据与计算" / "ReGlyco_Ensemble"
PDB_DIR = REGLYCO / "PDB"
CSV_DIR = REGLYCO / "csv"
OUT_DIR = Path(__file__).resolve().parent / "PNG"
OUT_DIR.mkdir(exist_ok=True)

PYMOL_PYTHON = Path(r"D:\PYMOL\python.exe")
TMP_DIR = ROOT / "_pymol_fig4_tmp"

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
    source_pdb: Path
    ca: np.ndarray
    ca_resseq: np.ndarray
    protein_atoms: np.ndarray
    glycan_atoms: np.ndarray
    glycan_residue_centers: list[np.ndarray]
    hotspot_resseq: set[int]


def hex_to_rgb01(hex_color: str) -> list[float]:
    text = hex_color.lstrip("#")
    return [int(text[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


def read_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/timesbd.ttf" if bold else "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def parse_first_model(pdb_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[np.ndarray]]:
    ca_coords: list[list[float]] = []
    ca_resseq: list[int] = []
    protein_atoms: list[list[float]] = []
    glycan_atoms: list[list[float]] = []
    glycan_residues: dict[tuple[str, str, str], list[list[float]]] = {}
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
            if not line.startswith(("ATOM", "HETATM")) or len(line) < 54:
                continue

            chain = line[21].strip()
            atom = line[12:16].strip()
            resname = line[17:20].strip()
            element = (line[76:78].strip() or atom[0]).upper()
            if element in {"H", "D"} or atom.startswith("H"):
                continue

            xyz = [float(line[30:38]), float(line[38:46]), float(line[46:54])]
            if chain == GLYCAN_CHAIN:
                glycan_atoms.append(xyz)
                key = (chain, resname, line[22:26].strip())
                glycan_residues.setdefault(key, []).append(xyz)
            elif resname in AA_RESNAMES:
                protein_atoms.append(xyz)
                if atom == "CA":
                    ca_coords.append(xyz)
                    ca_resseq.append(int(line[22:26]))

    residue_centers = [np.asarray(coords, dtype=float).mean(axis=0) for coords in glycan_residues.values()]
    return (
        np.asarray(ca_coords, dtype=float),
        np.asarray(ca_resseq, dtype=int),
        np.asarray(protein_atoms, dtype=float),
        np.asarray(glycan_atoms, dtype=float),
        residue_centers,
    )


def load_hotspots(short_name: str) -> set[int]:
    csv_path = CSV_DIR / f"{short_name}_APBS_glycanAware.csv"
    if not csv_path.exists():
        return set()
    df = pd.read_csv(csv_path)
    surface = df[(df["Type"] == "Protein") & (df["SurfaceLabel"] == "Surface")]
    acidic = surface[surface["ResName"].isin(ACIDIC_RESNAMES)]
    hotspots = acidic[acidic["APBS_kT_e"] < -5.0]
    return set(hotspots["ResSeq"].astype(int))


def load_structures() -> list[Structure]:
    structures: list[Structure] = []
    for species, short_name, filename in MODEL_SPECS:
        pdb_path = PDB_DIR / filename
        ca, ca_resseq, protein_atoms, glycan_atoms, glycan_residue_centers = parse_first_model(pdb_path)
        structures.append(
            Structure(
                species=species,
                short_name=short_name,
                source_pdb=pdb_path,
                ca=ca,
                ca_resseq=ca_resseq,
                protein_atoms=protein_atoms,
                glycan_atoms=glycan_atoms,
                glycan_residue_centers=glycan_residue_centers,
                hotspot_resseq=load_hotspots(short_name),
            )
        )
    return structures


def closest_point_to_radius(points: np.ndarray, center: np.ndarray, radius: float) -> np.ndarray:
    distances = np.linalg.norm(points - center, axis=1)
    return points[int(np.argmin(np.abs(distances - radius)))]


def nearest_pair(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    deltas = a[:, None, :] - b[None, :, :]
    distances = np.sum(deltas * deltas, axis=2)
    i, j = np.unravel_index(int(np.argmin(distances)), distances.shape)
    return a[i], b[j]


def ca_coords_for_residues(structure: Structure, residues: set[int]) -> np.ndarray:
    if not residues:
        return np.empty((0, 3))
    mask = np.array([int(resseq) in residues for resseq in structure.ca_resseq])
    return structure.ca[mask]


def split_hotspots(structure: Structure) -> tuple[np.ndarray, np.ndarray]:
    hotspots = ca_coords_for_residues(structure, structure.hotspot_resseq)
    if len(hotspots) == 0 or len(structure.glycan_atoms) == 0:
        return hotspots, np.empty((0, 3))
    distances = np.sqrt(((hotspots[:, None, :] - structure.glycan_atoms[None, :, :]) ** 2).sum(axis=2)).min(axis=1)
    accessible = hotspots[distances > SHIELD_DISTANCE]
    shielded = hotspots[distances <= SHIELD_DISTANCE]
    return accessible, shielded


def build_jobs(structures: list[Structure]) -> tuple[list[dict], list[dict]]:
    TMP_DIR.mkdir(exist_ok=True)
    for old in TMP_DIR.glob("*"):
        if old.is_file():
            old.unlink()

    pdb_map = {}
    for structure in structures:
        dst = TMP_DIR / f"{structure.species}.pdb"
        shutil.copyfile(structure.source_pdb, dst)
        pdb_map[structure.species] = dst

    gallus = next(s for s in structures if s.species == "Gallus")
    glycan = gallus.glycan_atoms
    ca = gallus.ca
    protein_ca_center = ca.mean(axis=0)
    glycan_center = glycan.mean(axis=0)
    rg = math.sqrt(float(np.mean(np.sum((glycan - glycan_center) ** 2, axis=1))))
    rg_edge = closest_point_to_radius(glycan, glycan_center, rg)
    end_a = gallus.glycan_residue_centers[0]
    end_b = gallus.glycan_residue_centers[-1]
    glycan_near_ca, ca_near_glycan = nearest_pair(glycan, ca)

    dg_specs = [
        ("D", "Glycan Rg", glycan_center, rg_edge, "#D69200"),
        ("E", "End-to-end", end_a, end_b, "#0072B2"),
        ("F", "Glycan-protein distance", glycan_center, protein_ca_center, "#009E73"),
        ("G", "Min. glycan-C-alpha", glycan_near_ca, ca_near_glycan, "#CC79A7"),
    ]
    dg_jobs = []
    for panel, label, a, b, color in dg_specs:
        dg_jobs.append({
            "panel": panel,
            "label": label,
            "pdb": str(pdb_map["Gallus"]),
            "out": str(TMP_DIR / f"metric_{panel}.png"),
            "species_color": hex_to_rgb01(SPECIES_COLORS["Gallus"]),
            "metric_color": hex_to_rgb01(color),
            "point_a": [float(x) for x in a],
            "point_b": [float(x) for x in b],
        })

    hk_jobs = []
    for structure in structures:
        accessible, shielded = split_hotspots(structure)
        hk_jobs.append({
            "pdb": str(pdb_map[structure.species]),
            "out": str(TMP_DIR / f"shielding_{structure.species}.png"),
            "species": structure.species,
            "species_color": hex_to_rgb01(SPECIES_COLORS[structure.species]),
            "accessible": accessible.astype(float).tolist(),
            "shielded": shielded.astype(float).tolist(),
        })
    return dg_jobs, hk_jobs


def write_pymol_renderer(dg_jobs: list[dict], hk_jobs: list[dict]) -> Path:
    data_path = TMP_DIR / "jobs.json"
    data_path.write_text(json.dumps({"dg": dg_jobs, "hk": hk_jobs}, ensure_ascii=False), encoding="utf-8")
    script_path = TMP_DIR / "render_fig4_models.py"
    script_path.write_text(textwrap.dedent(r'''
        from pathlib import Path
        import json
        import pymol

        pymol.finish_launching(['pymol', '-cq'])
        from pymol import cmd

        HERE = Path(__file__).resolve().parent
        JOBS = json.loads((HERE / 'jobs.json').read_text(encoding='utf-8'))

        def set_color(name, rgb):
            cmd.set_color(name, [float(x) for x in rgb])

        def midpoint(a, b):
            return [(float(a[i]) + float(b[i])) / 2.0 for i in range(3)]

        def base_scene(job):
            cmd.reinitialize()
            set_color('species_color', job['species_color'])
            cmd.load(job['pdb'], 'oval')
            cmd.remove('hydrogens')
            cmd.hide('everything')
            cmd.bg_color('white')
            cmd.set('opaque_background', 1)
            cmd.set('ray_opaque_background', 1)
            cmd.set('antialias', 2)
            cmd.set('ambient', 0.55)
            cmd.set('specular', 0.25)
            cmd.set('shininess', 18)
            cmd.set('depth_cue', 0)
            cmd.show('cartoon', 'oval and chain A')
            cmd.color('gray80', 'oval and chain A')
            cmd.set('cartoon_transparency', 0.18, 'oval and chain A')
            cmd.show('sticks', 'oval and chain B')
            cmd.show('spheres', 'oval and chain B')
            cmd.color('species_color', 'oval and chain B')
            cmd.set('stick_radius', 0.20, 'oval and chain B')
            cmd.set('sphere_scale', 0.34, 'oval and chain B')
            cmd.orient('oval')
            cmd.turn('x', -14)
            cmd.turn('y', 28)
            cmd.turn('z', -8)
            cmd.zoom('oval', 8)

        def render_metric(job):
            base_scene(job)
            set_color('metric_color', job['metric_color'])
            cmd.pseudoatom('metric_a', pos=job['point_a'])
            cmd.pseudoatom('metric_b', pos=job['point_b'])
            cmd.show('spheres', 'metric_a or metric_b')
            cmd.color('metric_color', 'metric_a or metric_b')
            cmd.set('sphere_scale', 0.56, 'metric_a or metric_b')
            cmd.distance('metric_line', 'metric_a', 'metric_b')
            cmd.hide('labels', 'metric_line')
            cmd.set('dash_color', 'metric_color', 'metric_line')
            cmd.set('dash_width', 4.5, 'metric_line')
            cmd.set('dash_gap', 0.20, 'metric_line')
            cmd.png(job['out'], width=1800, height=1250, dpi=300, ray=0)

        def add_points(object_name, points, color_name, scale):
            for point in points:
                cmd.pseudoatom(object_name, pos=point)
            if points:
                cmd.show('spheres', object_name)
                cmd.color(color_name, object_name)
                cmd.set('sphere_scale', scale, object_name)

        def render_shielding(job):
            base_scene(job)
            set_color('accessible_red', [0.82, 0.12, 0.10])
            set_color('shielded_black', [0.05, 0.05, 0.05])
            add_points('accessible_hotspots', job.get('accessible', []), 'accessible_red', 0.62)
            add_points('shielded_hotspots', job.get('shielded', []), 'shielded_black', 0.70)
            cmd.png(job['out'], width=1800, height=1250, dpi=300, ray=0)

        for item in JOBS['dg']:
            render_metric(item)
        for item in JOBS['hk']:
            render_shielding(item)
        cmd.quit()
    '''), encoding="utf-8")
    return script_path


def run_pymol(script_path: Path) -> None:
    if not PYMOL_PYTHON.exists():
        raise FileNotFoundError(f"PyMOL Python not found: {PYMOL_PYTHON}")
    subprocess.run([str(PYMOL_PYTHON), str(script_path)], check=True, cwd=str(TMP_DIR))


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def add_header(panel: Image.Image, title: str, color: str) -> Image.Image:
    top = 150
    out = Image.new("RGB", (panel.width, panel.height + top), "white")
    out.paste(panel.convert("RGB"), (0, top))
    draw = ImageDraw.Draw(out)
    font = read_font(64, bold=True)
    w, _ = text_size(draw, title, font)
    draw.text(((panel.width - w) // 2, 38), title, fill=color, font=font)
    return out


def trim_white(img: Image.Image, pad: int = 48, threshold: int = 248) -> Image.Image:
    rgb = img.convert("RGB")
    data = np.asarray(rgb)
    mask = np.any(data < threshold, axis=2)
    if not mask.any():
        return rgb
    ys, xs = np.where(mask)
    left = max(0, int(xs.min()) - pad)
    right = min(rgb.width, int(xs.max()) + pad + 1)
    top = max(0, int(ys.min()) - pad)
    bottom = min(rgb.height, int(ys.max()) + pad + 1)
    return rgb.crop((left, top, right, bottom))


def fit_to_box(img: Image.Image, width: int, height: int) -> Image.Image:
    fitted = Image.new("RGB", (width, height), "white")
    scale = min(width / img.width, height / img.height)
    new_size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
    resized = img.resize(new_size, Image.LANCZOS)
    fitted.paste(resized, ((width - new_size[0]) // 2, (height - new_size[1]) // 2))
    return fitted


def metric_panel(job: dict, width: int = 1180, body_h: int = 760) -> Image.Image:
    body = fit_to_box(trim_white(Image.open(job["out"]).convert("RGB")), width, body_h)
    top = 124
    panel = Image.new("RGB", (width, body_h + top), "white")
    panel.paste(body, (0, top))
    draw = ImageDraw.Draw(panel)
    title_font = read_font(52, bold=True)
    subtitle_font = read_font(34, bold=False)
    title = f"{job['panel']}  {job['label']}"
    tw, _ = text_size(draw, title, title_font)
    draw.text(((width - tw) // 2, 26), title, fill="#222222", font=title_font)
    if job["panel"] == "D":
        subtitle = "distance from glycan centroid to Rg shell"
    elif job["panel"] == "E":
        subtitle = "terminal residue-center distance"
    elif job["panel"] == "F":
        subtitle = "glycan centroid to protein C-alpha centroid"
    else:
        subtitle = "nearest glycan atom to backbone C-alpha"
    sw, _ = text_size(draw, subtitle, subtitle_font)
    draw.text(((width - sw) // 2, 82), subtitle, fill="#555555", font=subtitle_font)
    return panel


def combine_dg(dg_jobs: list[dict]) -> None:
    panels = [metric_panel(job) for job in dg_jobs]
    gap = 34
    width = sum(p.width for p in panels) + gap * (len(panels) - 1)
    height = max(p.height for p in panels)
    canvas = Image.new("RGB", (width, height), "white")
    x = 0
    for panel in panels:
        canvas.paste(panel, (x, (height - panel.height) // 2))
        x += panel.width + gap
    canvas.save(OUT_DIR / "Fig4_model_D_G.png", dpi=(300, 300))
    print(f"Saved {OUT_DIR / 'Fig4_model_D_G.png'}")


def combine_hk(hk_jobs: list[dict]) -> None:
    panels = []
    for job in hk_jobs:
        img = fit_to_box(trim_white(Image.open(job["out"]).convert("RGB")), 1320, 820)
        panels.append(add_header(img, job["species"], SPECIES_COLORS[job["species"]]))
    gap = 44
    legend_h = 180
    width = sum(p.width for p in panels) + gap * (len(panels) - 1)
    height = max(p.height for p in panels) + legend_h
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    title_font = read_font(68, bold=True)
    legend_font = read_font(46, bold=False)
    draw.text((40, 34), "H-K  glycan shielding and hotspot accessibility examples", fill="#222222", font=title_font)
    y_legend = 108
    draw.ellipse((44, y_legend, 86, y_legend + 42), fill="#D11F1A")
    draw.text((102, y_legend - 3), "accessible Ca2+ hotspot", fill="#222222", font=legend_font)
    draw.ellipse((730, y_legend, 772, y_legend + 42), fill="#111111")
    draw.text((788, y_legend - 3), "glycan-shielded hotspot", fill="#222222", font=legend_font)
    x = 0
    for panel in panels:
        canvas.paste(panel, (x, legend_h))
        x += panel.width + gap
    canvas.save(OUT_DIR / "Fig4_model_H_K.png", dpi=(300, 300))
    print(f"Saved {OUT_DIR / 'Fig4_model_H_K.png'}")


def transform_points(structure: Structure):
    center = structure.ca.mean(axis=0)
    _, _, vh = np.linalg.svd(structure.ca - center, full_matrices=False)
    rot = vh.T

    def apply(points):
        arr = np.asarray(points, dtype=float)
        original_shape = arr.shape
        arr = arr.reshape(-1, 3)
        out = (arr - center) @ rot
        if len(structure.glycan_atoms):
            glycan = (structure.glycan_atoms - center) @ rot
            ca = (structure.ca - center) @ rot
            if glycan[:, 1].mean() < ca[:, 1].mean():
                out[:, 1] *= -1
            if glycan[:, 2].mean() < ca[:, 2].mean():
                out[:, 2] *= -1
        return out.reshape(original_shape)

    return apply


def setup_clean_axis(ax, points: np.ndarray, elev: float = 18, azim: float = -62) -> None:
    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    centers = (mins + maxs) / 2
    radius = max(maxs - mins) / 2 + 4
    ax.set_xlim(centers[0] - radius, centers[0] + radius)
    ax.set_ylim(centers[1] - radius, centers[1] + radius)
    ax.set_zlim(centers[2] - radius, centers[2] + radius)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_facecolor("white")


def draw_clean_structure(ax, ca: np.ndarray, glycan: np.ndarray, species_color: str, alpha: float = 0.74) -> None:
    segments = np.stack([ca[:-1], ca[1:]], axis=1)
    ax.add_collection3d(Line3DCollection(segments, colors="#B8B8B8", linewidths=2.2, alpha=alpha))
    if len(glycan):
        ax.scatter(glycan[:, 0], glycan[:, 1], glycan[:, 2], s=22, c=species_color, alpha=0.90, depthshade=True)
        gly_segments = np.stack([glycan[:-1], glycan[1:]], axis=1)
        ax.add_collection3d(Line3DCollection(gly_segments, colors=species_color, linewidths=1.1, alpha=0.38))


def render_clean_dg(structures: list[Structure]) -> None:
    gallus = next(s for s in structures if s.species == "Gallus")
    apply = transform_points(gallus)
    ca = apply(gallus.ca)
    glycan = apply(gallus.glycan_atoms)
    residue_centers = [apply(center) for center in gallus.glycan_residue_centers]

    glycan_center = glycan.mean(axis=0)
    protein_center = ca.mean(axis=0)
    rg = math.sqrt(float(np.mean(np.sum((glycan - glycan_center) ** 2, axis=1))))
    rg_edge = closest_point_to_radius(glycan, glycan_center, rg)
    end_a = residue_centers[0]
    end_b = residue_centers[-1]
    glycan_near_ca, ca_near_glycan = nearest_pair(glycan, ca)

    specs = [
        ("D", "Glycan Rg", "centroid to Rg shell", glycan_center, rg_edge, "#D69200"),
        ("E", "End-to-end", "terminal residue centers", end_a, end_b, "#0072B2"),
        ("F", "Glycan-protein distance", "glycan centroid to protein C-alpha centroid", glycan_center, protein_center, "#009E73"),
        ("G", "Min. glycan-C-alpha", "nearest glycan atom to backbone C-alpha", glycan_near_ca, ca_near_glycan, "#CC79A7"),
    ]

    plt.rcParams["font.family"] = "Times New Roman"
    fig = plt.figure(figsize=(19.2, 4.6), dpi=300)
    fig.patch.set_facecolor("white")
    for index, (panel, title, subtitle, point_a, point_b, color) in enumerate(specs, start=1):
        ax = fig.add_subplot(1, 4, index, projection="3d")
        draw_clean_structure(ax, ca, glycan, SPECIES_COLORS["Gallus"])
        ax.plot([point_a[0], point_b[0]], [point_a[1], point_b[1]], [point_a[2], point_b[2]],
                color=color, linewidth=4.2, solid_capstyle="round")
        ax.scatter([point_a[0], point_b[0]], [point_a[1], point_b[1]], [point_a[2], point_b[2]],
                   s=70, c=color, depthshade=True)
        setup_clean_axis(ax, np.vstack([ca, glycan, point_a.reshape(1, 3), point_b.reshape(1, 3)]))
        ax.set_title(f"{panel}  {title}\n{subtitle}", fontsize=16, fontweight="bold", pad=8)
    plt.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.02, wspace=0.00)
    out = OUT_DIR / "Fig4_model_D_G.png"
    fig.savefig(out, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"Saved {out}")


def render_clean_hk(structures: list[Structure]) -> None:
    plt.rcParams["font.family"] = "Times New Roman"
    fig = plt.figure(figsize=(16.5, 5.2), dpi=300)
    fig.patch.set_facecolor("white")
    fig.text(0.018, 0.965, "H-K  glycan shielding and hotspot accessibility examples",
             ha="left", va="top", fontsize=23, fontweight="bold")
    fig.text(0.025, 0.875, "●", color="#D11F1A", fontsize=22, ha="left", va="center")
    fig.text(0.047, 0.875, "accessible Ca2+ hotspot", color="#222222", fontsize=15, ha="left", va="center")
    fig.text(0.265, 0.875, "●", color="#111111", fontsize=22, ha="left", va="center")
    fig.text(0.287, 0.875, "glycan-shielded hotspot", color="#222222", fontsize=15, ha="left", va="center")

    for index, structure in enumerate(structures, start=1):
        apply = transform_points(structure)
        ca = apply(structure.ca)
        glycan = apply(structure.glycan_atoms)
        accessible, shielded = split_hotspots(structure)
        accessible = apply(accessible) if len(accessible) else np.empty((0, 3))
        shielded = apply(shielded) if len(shielded) else np.empty((0, 3))

        ax = fig.add_subplot(1, 3, index, projection="3d")
        draw_clean_structure(ax, ca, glycan, SPECIES_COLORS[structure.species], alpha=0.70)
        if len(accessible):
            ax.scatter(accessible[:, 0], accessible[:, 1], accessible[:, 2], s=58, c="#D11F1A", depthshade=True)
        if len(shielded):
            ax.scatter(shielded[:, 0], shielded[:, 1], shielded[:, 2], s=72, c="#111111", depthshade=True)
        all_points = np.vstack([ca, glycan, accessible, shielded])
        setup_clean_axis(ax, all_points)
        ax.set_title(structure.species, color=SPECIES_COLORS[structure.species], fontsize=22, fontweight="bold", pad=4)
    plt.subplots_adjust(left=0.01, right=0.99, top=0.78, bottom=0.02, wspace=-0.06)
    out = OUT_DIR / "Fig4_model_H_K.png"
    fig.savefig(out, dpi=300, facecolor="white")
    plt.close(fig)
    print(f"Saved {out}")


def main() -> None:
    structures = load_structures()
    render_clean_dg(structures)
    render_clean_hk(structures)


if __name__ == "__main__":
    main()
