#!/usr/bin/env python
"""Generate standalone PyMOL glycan-overview examples for Fig. 4D-G.

This script selects two geometry-extreme ReGlyco models from
csv/glycan_conformation_detail.csv, extracts the target MODEL records, and uses
PyMOL to render overview panels that locate the glycan on the protein surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import shutil
import subprocess
import textwrap

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
REGLYCO = ROOT / "01_数据与计算" / "ReGlyco_Ensemble"
PDB_DIR = REGLYCO / "PDB"
CSV_DIR = REGLYCO / "csv"
OUT_DIR = Path(__file__).resolve().parent / "PNG"
OUT_DIR.mkdir(exist_ok=True)

PYMOL_PYTHON = Path(r"D:\PYMOL\python.exe")
TMP_DIR = ROOT / "_pymol_fig4_dg_extremes"
TMP_DIR.mkdir(exist_ok=True)

AA_RESNAMES = {
    "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
    "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
}
GLYCAN_CHAIN = "B"

SPECIES_COLORS = {
    "Gallus": "#C46B83",
    "Anas": "#93AACD",
    "Columba": "#F3CE9D",
}

METRIC_COLORS = {
    "Rg turn": "#D69200",
    "End-to-End": "#0072B2",
    "Glycan-Protein": "#009E73",
    "Glycan-Backbone": "#CC79A7",
}

METRIC_SHORT_LABELS = {
    "Rg turn": "Rg turn",
    "End-to-End": "End-to-End",
    "Glycan-Protein": "Glycan-Protein",
    "Glycan-Backbone": "Glycan-Backbone",
}


@dataclass
class ExtremeModel:
    role: str
    structure: str
    species: str
    model: int
    score: float
    pdb_path: Path
    extracted_pdb: Path
    protein_atoms: np.ndarray
    ca_atoms: np.ndarray
    glycan_atoms: np.ndarray
    glycan_residue_centers: list[np.ndarray]
    metrics: dict[str, tuple[np.ndarray, np.ndarray]]


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


def choose_extremes() -> pd.DataFrame:
    df = pd.read_csv(CSV_DIR / "glycan_conformation_detail.csv")
    metric_cols = ["glycan_rg", "glycan_end2end", "glycan_dist", "glycan_min_dist_to_ca"]
    z = df[metric_cols].apply(lambda s: (s - s.mean()) / s.std())
    df = df.copy()
    df["extreme_score"] = z["glycan_rg"] + z["glycan_end2end"] + z["glycan_dist"] - z["glycan_min_dist_to_ca"]
    compact = df.nsmallest(1, "extreme_score").copy()
    compact["role"] = "Compact / near-backbone glycan"
    extended = df.nlargest(1, "extreme_score").copy()
    extended["role"] = "Extended / far-reaching glycan"
    return pd.concat([compact, extended], ignore_index=True)


def extract_model(source: Path, model_number: int, destination: Path) -> None:
    lines: list[str] = []
    in_target = False
    with source.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("MODEL"):
                parts = line.split()
                current = int(parts[1]) if len(parts) > 1 else 1
                in_target = current == model_number
                if in_target:
                    lines.append("MODEL        1\n")
                continue
            if line.startswith("ENDMDL"):
                if in_target:
                    lines.append("ENDMDL\n")
                    break
                in_target = False
                continue
            if in_target:
                lines.append(line)
    destination.write_text("".join(lines), encoding="utf-8")


def parse_model(pdb_path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[np.ndarray]]:
    protein_atoms: list[list[float]] = []
    ca_atoms: list[list[float]] = []
    glycan_atoms: list[list[float]] = []
    glycan_residues: dict[tuple[str, str, str], list[list[float]]] = {}

    with pdb_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
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
                    ca_atoms.append(xyz)

    residue_centers = [np.asarray(coords, dtype=float).mean(axis=0) for coords in glycan_residues.values()]
    return (
        np.asarray(protein_atoms, dtype=float),
        np.asarray(ca_atoms, dtype=float),
        np.asarray(glycan_atoms, dtype=float),
        residue_centers,
    )


def nearest_pair(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    distances = np.sum((a[:, None, :] - b[None, :, :]) ** 2, axis=2)
    i, j = np.unravel_index(int(np.argmin(distances)), distances.shape)
    return a[i], b[j]


def closest_point_to_radius(points: np.ndarray, center: np.ndarray, radius: float) -> np.ndarray:
    distances = np.linalg.norm(points - center, axis=1)
    return points[int(np.argmin(np.abs(distances - radius)))]


def metric_segments(protein_atoms: np.ndarray, ca_atoms: np.ndarray, glycan_atoms: np.ndarray, residue_centers: list[np.ndarray]):
    glycan_center = glycan_atoms.mean(axis=0)
    rg = float(np.sqrt(np.mean(np.sum((glycan_atoms - glycan_center) ** 2, axis=1))))
    rg_edge = closest_point_to_radius(glycan_atoms, glycan_center, rg)
    end_a = residue_centers[0]
    end_b = residue_centers[-1]
    glycan_near_protein, protein_near_glycan = nearest_pair(glycan_atoms, protein_atoms)
    glycan_near_ca, ca_near_glycan = nearest_pair(glycan_atoms, ca_atoms)
    return {
        "Rg turn": (glycan_center, rg_edge),
        "End-to-End": (end_a, end_b),
        "Glycan-Protein": (glycan_center, protein_near_glycan),
        "Glycan-Backbone": (glycan_near_ca, ca_near_glycan),
    }


def build_models() -> list[ExtremeModel]:
    for old in TMP_DIR.glob("*"):
        if old.is_file():
            old.unlink()
    selected = choose_extremes()
    models: list[ExtremeModel] = []
    for _, row in selected.iterrows():
        source = PDB_DIR / f"{row['structure']}.pdb"
        extracted = TMP_DIR / f"{row['structure']}_model{int(row['model'])}.pdb"
        extract_model(source, int(row["model"]), extracted)
        protein_atoms, ca_atoms, glycan_atoms, residue_centers = parse_model(extracted)
        models.append(
            ExtremeModel(
                role=str(row["role"]),
                structure=str(row["structure"]),
                species=str(row["species"]),
                model=int(row["model"]),
                score=float(row["extreme_score"]),
                pdb_path=source,
                extracted_pdb=extracted,
                protein_atoms=protein_atoms,
                ca_atoms=ca_atoms,
                glycan_atoms=glycan_atoms,
                glycan_residue_centers=residue_centers,
                metrics=metric_segments(protein_atoms, ca_atoms, glycan_atoms, residue_centers),
            )
        )
    return models


def pymol_jobs(models: list[ExtremeModel]) -> list[dict]:
    jobs = []
    for index, model in enumerate(models, start=1):
        jobs.append({
            "role": model.role,
            "structure": model.structure,
            "species": model.species,
            "model": model.model,
            "score": model.score,
            "pdb": str(model.extracted_pdb),
            "overview_out": str(TMP_DIR / f"pymol_extreme_{index}_overview.png"),
            "species_color": hex_to_rgb01(SPECIES_COLORS.get(model.species, "#777777")),
            "glycan_center": [float(x) for x in model.glycan_atoms.mean(axis=0)],
            "glycan_radius": float(np.max(np.linalg.norm(model.glycan_atoms - model.glycan_atoms.mean(axis=0), axis=1))),
            "glycan_rg": float(np.linalg.norm(model.metrics["Rg turn"][1] - model.metrics["Rg turn"][0])),
            "overview_turns": [-24, -12, -78] if model.role.startswith("Compact") else [-24, -12, 10],
            "is_focus": index == 2,
            "metrics": [
                {
                    "name": name,
                    "color": hex_to_rgb01(METRIC_COLORS[name]),
                    "start": [float(x) for x in points[0]],
                    "end": [float(x) for x in points[1]],
                }
                for name, points in model.metrics.items()
            ],
        })
    return jobs


def write_pymol_script(jobs: list[dict]) -> Path:
    jobs_path = TMP_DIR / "jobs.json"
    jobs_path.write_text(json.dumps(jobs, ensure_ascii=False), encoding="utf-8")
    script_path = TMP_DIR / "render_glycan_extremes.py"
    script_path.write_text(textwrap.dedent(r'''
        from pathlib import Path
        import json
        import math
        import pymol
        from pymol.cgo import CYLINDER, CONE, BEGIN, LINES, COLOR, VERTEX, END

        pymol.finish_launching(['pymol', '-cq'])
        from pymol import cmd

        HERE = Path(__file__).resolve().parent
        JOBS = json.loads((HERE / 'jobs.json').read_text(encoding='utf-8'))

        def set_color(name, rgb):
            cmd.set_color(name, [float(x) for x in rgb])

        def add_arrow(name, start, end, color, radius=0.018, head_radius=0.065, head_length=0.24):
            sx, sy, sz = [float(v) for v in start]
            ex, ey, ez = [float(v) for v in end]
            vx, vy, vz = ex - sx, ey - sy, ez - sz
            length = math.sqrt(vx * vx + vy * vy + vz * vz)
            if length < 1e-6:
                return
            head_length = min(head_length, length * 0.32)
            ux, uy, uz = vx / length, vy / length, vz / length
            shaft_end = [ex - ux * head_length, ey - uy * head_length, ez - uz * head_length]
            r, g, b = [float(c) for c in color]
            obj = [
                CYLINDER, sx, sy, sz, shaft_end[0], shaft_end[1], shaft_end[2], radius, r, g, b, r, g, b,
                CONE, shaft_end[0], shaft_end[1], shaft_end[2], ex, ey, ez, head_radius, 0.0, r, g, b, r, g, b, 1.0, 0.0,
            ]
            cmd.load_cgo(obj, name)

        def add_line(name, start, end, color, radius=0.016):
            sx, sy, sz = [float(v) for v in start]
            ex, ey, ez = [float(v) for v in end]
            r, g, b = [float(c) for c in color]
            cmd.load_cgo([CYLINDER, sx, sy, sz, ex, ey, ez, radius, r, g, b, r, g, b], name)

        def add_camera_circle(name, center, radius, color=(0.0, 0.0, 0.0), segments=144):
            view = cmd.get_view()
            right = [view[0], view[1], view[2]]
            up = [view[3], view[4], view[5]]
            center = [float(v) for v in center]
            r, g, b = [float(c) for c in color]
            obj = [BEGIN, LINES, COLOR, r, g, b]
            for i in range(segments):
                a0 = 2.0 * math.pi * i / segments
                a1 = 2.0 * math.pi * (i + 1) / segments
                p0 = [center[j] + radius * math.cos(a0) * right[j] + radius * math.sin(a0) * up[j] for j in range(3)]
                p1 = [center[j] + radius * math.cos(a1) * right[j] + radius * math.sin(a1) * up[j] for j in range(3)]
                obj.extend([VERTEX, p0[0], p0[1], p0[2], VERTEX, p1[0], p1[1], p1[2]])
            obj.append(END)
            cmd.load_cgo(obj, name)

        def add_rg_sphere(job):
            center = [float(v) for v in job['glycan_center']]
            rg = float(job['glycan_rg'])
            set_color('rg_gold', [1.0, 0.58, 0.04])
            set_color('rg_orange', [0.95, 0.34, 0.00])
            cmd.pseudoatom('rg_centroid', pos=center, vdw=0.30)
            cmd.show('spheres', 'rg_centroid')
            cmd.color('rg_gold', 'rg_centroid')
            cmd.pseudoatom('rg_shell', pos=center, vdw=rg)
            cmd.show('spheres', 'rg_shell')
            cmd.color('rg_gold', 'rg_shell')
            cmd.set('sphere_transparency', 0.90 if job.get('is_focus') else 0.86, 'rg_shell')
            cmd.set('sphere_quality', 3, 'rg_shell')
            rg_metric = next((metric for metric in job['metrics'] if metric['name'] == 'Rg turn'), None)
            if rg_metric:
                target = rg_metric['end']
                if job.get('is_focus'):
                    vx = target[0] - center[0] + 0.65 * rg
                    vy = target[1] - center[1] - 0.18 * rg
                    vz = target[2] - center[2] + 0.45 * rg
                    length = math.sqrt(vx * vx + vy * vy + vz * vz) or 1.0
                    target = [center[0] + rg * vx / length, center[1] + rg * vy / length, center[2] + rg * vz / length]
                    add_arrow('rg_radius_arrow', center, target, [1.0, 0.47, 0.0], radius=0.082, head_radius=0.25, head_length=0.58)
                else:
                    add_arrow('rg_radius_arrow', center, target, [1.0, 0.47, 0.0], radius=0.030, head_radius=0.115, head_length=0.34)

        def add_focus_metrics(job):
            metric_specs = {
                'End-to-End': {'radius': 0.070, 'head_radius': 0.210, 'head_length': 0.56, 'color': [0.00, 0.44, 0.70]},
                'Glycan-Protein': {'radius': 0.060, 'head_radius': 0.185, 'head_length': 0.46, 'color': [0.00, 0.62, 0.36]},
                'Glycan-Backbone': {'radius': 0.060, 'head_radius': 0.185, 'head_length': 0.46, 'color': [0.80, 0.25, 0.55]},
            }
            for metric in job['metrics']:
                name = metric['name']
                if name not in metric_specs:
                    continue
                spec = metric_specs[name]
                add_arrow(
                    'focus_' + name.replace('-', '_').replace(' ', '_'),
                    metric['start'],
                    metric['end'],
                    spec['color'],
                    radius=spec['radius'],
                    head_radius=spec['head_radius'],
                    head_length=spec['head_length'],
                )

        def setup_scene(job):
            cmd.reinitialize()
            set_color('species_color', job['species_color'])
            for metric in job['metrics']:
                set_color('metric_' + metric['name'].replace('-', '_').replace(' ', '_'), metric['color'])
            cmd.load(job['pdb'], 'oval')
            cmd.remove('hydrogens')
            cmd.hide('everything')
            cmd.bg_color('white')
            cmd.set('opaque_background', 1)
            cmd.set('antialias', 2)
            cmd.set('ambient', 0.62)
            cmd.set('specular', 0.12)
            cmd.set('shininess', 10)
            cmd.set('depth_cue', 0)
            cmd.set('line_smooth', 1)
            cmd.set('stick_quality', 18)
            cmd.set('sphere_quality', 2)
            cmd.set('surface_quality', 1)
            cmd.set('ray_trace_mode', 1)
            cmd.set('ray_opaque_background', 1)
            cmd.set('orthoscopic', 1)
            cmd.set('two_sided_lighting', 1)
            cmd.set('transparency_mode', 3)

        def color_full_glycan():
            cmd.show('sticks', 'oval and chain B')
            cmd.show('spheres', 'oval and chain B')
            cmd.color('species_color', 'oval and chain B and elem C')
            cmd.color('red', 'oval and chain B and elem O')
            cmd.color('blue', 'oval and chain B and elem N')
            cmd.color('white', 'oval and chain B and elem H')
            cmd.set('stick_radius', 0.10, 'oval and chain B')
            cmd.set('sphere_scale', 0.12, 'oval and chain B')
            cmd.set('stick_ball', 1, 'oval and chain B')
            cmd.set('stick_ball_ratio', 1.55, 'oval and chain B')

        def scene_overview(job):
            setup_scene(job)
            cmd.show('surface', 'oval and chain A')
            cmd.color('gray85', 'oval and chain A')
            cmd.set('transparency', 0.50, 'oval and chain A')
            cmd.select('protein_anchor', 'byres (oval and chain A within 4 of (oval and chain B))')
            cmd.color('gray62', 'protein_anchor')
            cmd.set('transparency', 0.32, 'protein_anchor')
            cmd.color('gray65', 'oval and chain A')
            color_full_glycan()
            add_rg_sphere(job)
            if job.get('is_focus'):
                add_focus_metrics(job)
            cmd.orient('oval and chain B')
            cmd.turn('x', job['overview_turns'][0])
            cmd.turn('y', job['overview_turns'][1])
            cmd.turn('z', job['overview_turns'][2])
            cmd.zoom('oval and chain A', buffer=46, complete=1)
            cmd.clip('slab', 420)
            add_camera_circle('glycan_locator', job['glycan_center'], max(9.0, job['glycan_radius'] * 1.75), color=(0.18, 0.18, 0.18))
            cmd.png(job['overview_out'], width=2200, height=1800, dpi=300, ray=1)

        def scene_zoom(job, out_path, rotate_y=0, show_metrics=True):
            setup_scene(job)

            cmd.select('protein_context', 'byres (oval and chain A within 8 of (oval and chain B))')
            cmd.show('lines', 'protein_context')
            cmd.color('gray70', 'protein_context')
            cmd.set('line_width', 1.35, 'protein_context')
            color_full_glycan()
            cmd.orient('oval and chain B')
            cmd.turn('x', -14)
            cmd.turn('y', 18 + float(rotate_y))
            cmd.turn('z', -8)
            cmd.zoom('oval and chain B', buffer=10, complete=1)
            cmd.clip('slab', 160)

            if show_metrics:
                for index, metric in enumerate(job['metrics']):
                    if metric['name'] == 'Glycan-Protein':
                        add_line('metric_' + str(index), metric['start'], metric['end'], metric['color'], radius=0.012)
                    else:
                        add_arrow('metric_' + str(index), metric['start'], metric['end'], metric['color'])

            cmd.png(out_path, width=2200, height=2200, dpi=300, ray=1)

        for item in JOBS:
            scene_overview(item)
        cmd.quit()
    '''), encoding="utf-8")
    return script_path


def run_pymol(script_path: Path) -> None:
    if not PYMOL_PYTHON.exists():
        raise FileNotFoundError(f"PyMOL Python was not found: {PYMOL_PYTHON}")
    subprocess.run([str(PYMOL_PYTHON), str(script_path)], cwd=str(TMP_DIR), check=True)


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def trim_white(img: Image.Image, pad: int = 30, threshold: int = 248) -> Image.Image:
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


def fit_image(path: str | Path, width: int, height: int, pad: int = 60) -> Image.Image:
    image = trim_white(Image.open(path).convert("RGB"), pad=pad)
    scale = min(width / image.width, height / image.height)
    resized = image.resize((int(image.width * scale), int(image.height * scale)), Image.LANCZOS)
    canvas = Image.new("RGB", (width, height), "white")
    canvas.paste(resized, ((width - resized.width) // 2, (height - resized.height) // 2))
    return canvas


def circular_view(path: str | Path, diameter: int, pad: int = 130) -> Image.Image:
    raw = Image.open(path).convert("RGB")
    image = trim_white(raw, pad=pad)
    content_d = int(diameter * 0.90)
    scale = min(content_d / image.width, content_d / image.height)
    resized = image.resize((int(image.width * scale), int(image.height * scale)), Image.LANCZOS)
    square = Image.new("RGB", (diameter, diameter), "white")
    square.paste(resized, ((diameter - resized.width) // 2, (diameter - resized.height) // 2))
    mask = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, diameter - 1, diameter - 1), fill=255)
    result = Image.new("RGBA", (diameter, diameter), (255, 255, 255, 0))
    result.paste(square.convert("RGBA"), (0, 0), mask)
    return result


def draw_rotation_marker(draw: ImageDraw.ImageDraw, center_x: int, center_y: int) -> None:
    font = read_font(54, bold=False)
    label = "180 deg"
    lw, lh = text_size(draw, label, font)
    draw.text((center_x - lw // 2, center_y - 88), label, fill="#111111", font=font)
    arc_box = (center_x - 48, center_y - 30, center_x + 48, center_y + 66)
    draw.arc(arc_box, start=45, end=330, fill="#111111", width=6)
    draw.polygon(
        [(center_x + 27, center_y - 28), (center_x + 63, center_y - 24), (center_x + 43, center_y + 5)],
        fill="#111111",
    )


def draw_metric_legend(draw: ImageDraw.ImageDraw, y: int, x: int = 120) -> None:
    legend_font = read_font(38, bold=True)
    for name, color in METRIC_COLORS.items():
        draw.line((x, y + 20, x + 98, y + 20), fill=color, width=10)
        draw.polygon([(x + 98, y + 20), (x + 72, y + 6), (x + 72, y + 34)], fill=color)
        label = METRIC_SHORT_LABELS[name]
        draw.text((x + 118, y - 5), label, fill="#222222", font=legend_font)
        lw, _ = text_size(draw, label, legend_font)
        x += 170 + lw


def draw_focus_metric_key(draw: ImageDraw.ImageDraw, y: int, x: int = 95) -> None:
    font = read_font(24, bold=True)
    entries = [
        ("D Rg", METRIC_COLORS["Rg turn"]),
        ("E End-to-End", METRIC_COLORS["End-to-End"]),
        ("F Glycan-Protein", METRIC_COLORS["Glycan-Protein"]),
        ("G Glycan-Backbone", METRIC_COLORS["Glycan-Backbone"]),
    ]
    for label, color in entries:
        draw.line((x, y + 14, x + 54, y + 14), fill=color, width=7)
        draw.text((x + 66, y), label, fill="#222222", font=font)
        lw, _ = text_size(draw, label, font)
        x += 108 + lw


def panel_with_title(job: dict) -> Image.Image:
    target_w, target_h = 1550, 1250
    panel = Image.new("RGB", (target_w, target_h), "white")
    draw = ImageDraw.Draw(panel)
    title_font = read_font(48, bold=True)
    sub_font = read_font(30, bold=False)
    title = job["role"]
    subtitle = f"{job['species']} | {job['structure']} model {job['model']}"
    tw, _ = text_size(draw, title, title_font)
    sw, _ = text_size(draw, subtitle, sub_font)
    draw.text(((target_w - tw) // 2, 28), title, fill="#111111", font=title_font)
    draw.text(((target_w - sw) // 2, 88), subtitle, fill=SPECIES_COLORS.get(job["species"], "#555555"), font=sub_font)

    overview = fit_image(job["overview_out"], 1370, 970, pad=140)
    overview_x, overview_y = 90, 200
    panel.paste(overview, (overview_x, overview_y))
    if job.get("is_focus"):
        draw_focus_metric_key(draw, 1188, x=105)
    return panel


def combine_outputs(jobs: list[dict]) -> None:
    panels = [panel_with_title(job) for job in jobs]
    gap = 100
    canvas = Image.new("RGB", (panels[0].width, panels[0].height * 2 + gap), "white")
    canvas.paste(panels[0], (0, 0))
    canvas.paste(panels[1], (0, panels[0].height + gap))
    combined = OUT_DIR / "Fig4D_G_pymol_glycan_extremes.png"
    canvas.save(combined, dpi=(300, 300))
    print(f"Saved {combined}")
    for index, panel in enumerate(panels, start=1):
        path = OUT_DIR / f"Fig4D_G_pymol_glycan_extreme_{index}.png"
        panel.save(path, dpi=(300, 300))
        print(f"Saved {path}")


def main() -> None:
    models = build_models()
    jobs = pymol_jobs(models)
    script_path = write_pymol_script(jobs)
    run_pymol(script_path)
    combine_outputs(jobs)


if __name__ == "__main__":
    main()
