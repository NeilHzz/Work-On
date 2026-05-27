#!/usr/bin/env python
"""Standalone 3D OVAL Ca2+ hotspot / glycan / SASA schematic for Fig. 4H-K.

This script renders three representative ReGlyco OVAL models as transparent
protein surfaces. Accessible Ca2+-relevant acidic hotspot residues are colored
with the species color, glycan-shielded hotspots are black, the remaining
surface is gray, glycan residues are simplified as square blocks, and a dashed
outer envelope marks the whole protein+glycan SASA schematic.

Outputs are written to 02_可视化/Figure/PNG and are intentionally not wired into
compose_manuscript_figures.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import math
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
TMP_DIR = ROOT / "_pymol_fig4_hk_sasa"

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
    df = pd.read_csv(csv_path)
    surface = df[(df["Type"] == "Protein") & (df["SurfaceLabel"] == "Surface")]
    acidic = surface[surface["ResName"].isin(ACIDIC_RESNAMES)]
    hotspots = acidic[acidic["APBS_kT_e"] < -5.0]
    return set(hotspots["ResSeq"].astype(int))


def load_structures() -> list[Structure]:
    structures: list[Structure] = []
    for species, short_name, filename in MODEL_SPECS:
        pdb_path = PDB_DIR / filename
        ca, ca_resseq, protein_atoms, glycan_atoms, residue_centers = parse_first_model(pdb_path)
        structures.append(
            Structure(
                species=species,
                short_name=short_name,
                source_pdb=pdb_path,
                ca=ca,
                ca_resseq=ca_resseq,
                protein_atoms=protein_atoms,
                glycan_atoms=glycan_atoms,
                glycan_residue_centers=residue_centers,
                hotspot_resseq=load_hotspots(short_name),
            )
        )
    return structures


def split_hotspot_residues(structure: Structure) -> tuple[list[int], list[int]]:
    if not structure.hotspot_resseq or len(structure.glycan_atoms) == 0:
        return sorted(structure.hotspot_resseq), []
    hotspot_mask = np.array([int(resseq) in structure.hotspot_resseq for resseq in structure.ca_resseq])
    hotspot_ca = structure.ca[hotspot_mask]
    hotspot_resseq = structure.ca_resseq[hotspot_mask]
    if len(hotspot_ca) == 0:
        return [], []
    distances = np.sqrt(((hotspot_ca[:, None, :] - structure.glycan_atoms[None, :, :]) ** 2).sum(axis=2)).min(axis=1)
    accessible = hotspot_resseq[distances > SHIELD_DISTANCE]
    shielded = hotspot_resseq[distances <= SHIELD_DISTANCE]
    return sorted(int(x) for x in accessible), sorted(int(x) for x in shielded)


def extract_first_model(source: Path, destination: Path) -> None:
    lines: list[str] = []
    in_model = False
    saw_model = False
    with source.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("MODEL"):
                if saw_model:
                    break
                saw_model = True
                in_model = True
                lines.append("MODEL        1\n")
                continue
            if line.startswith("ENDMDL") and in_model:
                lines.append("ENDMDL\n")
                break
            if in_model or not saw_model:
                if line.startswith(("ATOM", "HETATM", "TER", "END")):
                    lines.append(line)
    destination.write_text("".join(lines), encoding="utf-8")


def residue_selection(residues: list[int]) -> str:
    if not residues:
        return "none"
    return "+".join(str(residue) for residue in residues)


def build_jobs(structures: list[Structure]) -> list[dict]:
    TMP_DIR.mkdir(exist_ok=True)
    for old in TMP_DIR.glob("*"):
        if old.is_file():
            old.unlink()
    jobs = []
    for structure in structures:
        pdb_path = TMP_DIR / f"{structure.species}.pdb"
        extract_first_model(structure.source_pdb, pdb_path)
        accessible, shielded = split_hotspot_residues(structure)
        all_points = np.vstack([structure.protein_atoms, structure.glycan_atoms])
        center = all_points.mean(axis=0)
        radius = float(np.linalg.norm(all_points - center, axis=1).max() * 1.10)
        jobs.append({
            "species": structure.species,
            "pdb": str(pdb_path),
            "out": str(TMP_DIR / f"{structure.species}_3d_sasa.png"),
            "species_color": hex_to_rgb01(SPECIES_COLORS[structure.species]),
            "accessible_resi": residue_selection(accessible),
            "shielded_resi": residue_selection(shielded),
            "accessible_count": len(accessible),
            "shielded_count": len(shielded),
            "glycan_centers": [[float(v) for v in center] for center in structure.glycan_residue_centers],
            "protein_atoms": structure.protein_atoms.astype(float).tolist(),
            "envelope_center": [float(v) for v in center],
            "envelope_radius": radius,
        })
    return jobs


def write_pymol_renderer(jobs: list[dict]) -> Path:
    jobs_path = TMP_DIR / "jobs.json"
    jobs_path.write_text(json.dumps(jobs, ensure_ascii=False), encoding="utf-8")
    script_path = TMP_DIR / "render_fig4_hk_sasa.py"
    script_path.write_text(textwrap.dedent(r'''
        from pathlib import Path
        import json
        import math
        import pymol
        from pymol.cgo import BEGIN, TRIANGLES, COLOR, VERTEX, END, CYLINDER

        pymol.finish_launching(['pymol', '-cq'])
        from pymol import cmd

        HERE = Path(__file__).resolve().parent
        JOBS = json.loads((HERE / 'jobs.json').read_text(encoding='utf-8'))

        def set_color(name, rgb):
            cmd.set_color(name, [float(x) for x in rgb])

        def nearest_point(point, candidates):
            best = None
            best_d2 = None
            px, py, pz = [float(x) for x in point]
            for item in candidates:
                dx = px - float(item[0])
                dy = py - float(item[1])
                dz = pz - float(item[2])
                d2 = dx * dx + dy * dy + dz * dz
                if best_d2 is None or d2 < best_d2:
                    best = item
                    best_d2 = d2
            return [float(x) for x in best]

        def add_cylinder(name, start, end, color, radius=0.055):
            sx, sy, sz = [float(v) for v in start]
            ex, ey, ez = [float(v) for v in end]
            r, g, b = [float(v) for v in color]
            cmd.load_cgo([CYLINDER, sx, sy, sz, ex, ey, ez, radius, r, g, b, r, g, b], name, zoom=0)

        def add_cube(name, center, size, color):
            cx, cy, cz = [float(v) for v in center]
            s = float(size) / 2.0
            vertices = [
                (cx - s, cy - s, cz - s), (cx + s, cy - s, cz - s), (cx + s, cy + s, cz - s), (cx - s, cy + s, cz - s),
                (cx - s, cy - s, cz + s), (cx + s, cy - s, cz + s), (cx + s, cy + s, cz + s), (cx - s, cy + s, cz + s),
            ]
            faces = [(0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6), (0, 4, 5), (0, 5, 1),
                     (1, 5, 6), (1, 6, 2), (2, 6, 7), (2, 7, 3), (3, 7, 4), (3, 4, 0)]
            r, g, b = [float(v) for v in color]
            obj = [BEGIN, TRIANGLES, COLOR, r, g, b]
            for face in faces:
                for index in face:
                    obj.extend([VERTEX, vertices[index][0], vertices[index][1], vertices[index][2]])
            obj.append(END)
            cmd.load_cgo(obj, name, zoom=0)

        def add_square_glycan(job):
            centers = job.get('glycan_centers', [])
            color = job['species_color']
            if not centers:
                return
            previous = None
            for index, center in enumerate(centers):
                add_cube('glycan_square_' + str(index), center, 1.05, color)
                if previous is not None:
                    add_cylinder('glycan_link_' + str(index), previous, center, color, radius=0.085)
                previous = center
            anchor = nearest_point(centers[0], job['protein_atoms'])
            add_cylinder('glycan_protein_anchor', anchor, centers[0], color, radius=0.065)

        def add_camera_dashed_envelope(job, name='sasa_outline'):
            center = [float(v) for v in job['envelope_center']]
            radius = float(job['envelope_radius'])
            view = cmd.get_view()
            right = [view[0], view[1], view[2]]
            up = [view[3], view[4], view[5]]
            obj = []
            segments = 96
            for i in range(segments):
                if i % 2 == 1:
                    continue
                a0 = 2.0 * math.pi * i / segments
                a1 = 2.0 * math.pi * (i + 0.62) / segments
                p0 = [center[j] + radius * math.cos(a0) * right[j] + radius * math.sin(a0) * up[j] for j in range(3)]
                p1 = [center[j] + radius * math.cos(a1) * right[j] + radius * math.sin(a1) * up[j] for j in range(3)]
                obj.extend([CYLINDER, p0[0], p0[1], p0[2], p1[0], p1[1], p1[2], 0.055, 0.06, 0.06, 0.06, 0.06, 0.06, 0.06])
            cmd.load_cgo(obj, name, zoom=0)

        def select_regions(job):
            accessible = 'oval and chain A and resi ' + job['accessible_resi'] if job['accessible_resi'] != 'none' else 'none'
            shielded = 'oval and chain A and resi ' + job['shielded_resi'] if job['shielded_resi'] != 'none' else 'none'
            cmd.select('accessible_region', accessible)
            cmd.select('shielded_region', shielded)

        def setup_scene(job):
            print('setup ' + job['species'], flush=True)
            cmd.reinitialize()
            set_color('species_color', job['species_color'])
            set_color('neutral_gray', [0.70, 0.70, 0.70])
            set_color('shield_black', [0.02, 0.02, 0.02])
            cmd.load(job['pdb'], 'oval')
            cmd.remove('hydrogens')
            cmd.hide('everything')
            cmd.bg_color('white')
            cmd.set('opaque_background', 1)
            cmd.set('ray_opaque_background', 1)
            cmd.set('orthoscopic', 1)
            cmd.set('transparency_mode', 3)
            cmd.set('two_sided_lighting', 1)
            cmd.set('depth_cue', 0)
            cmd.set('ambient', 0.66)
            cmd.set('specular', 0.16)
            cmd.set('shininess', 12)
            cmd.set('antialias', 2)
            cmd.set('surface_quality', 2)
            cmd.set('sphere_quality', 3)
            cmd.show('surface', 'oval and chain A')
            cmd.color('neutral_gray', 'oval and chain A')
            cmd.set('transparency', 0.58, 'oval and chain A')
            select_regions(job)
            cmd.color('species_color', 'accessible_region')
            cmd.color('shield_black', 'shielded_region')
            cmd.set('transparency', 0.20, 'accessible_region')
            cmd.set('transparency', 0.04, 'shielded_region')
            cmd.show('sticks', 'accessible_region or shielded_region')
            cmd.set('stick_radius', 0.13, 'accessible_region or shielded_region')
            cmd.show('spheres', 'accessible_region and name CA')
            cmd.show('spheres', 'shielded_region and name CA')
            cmd.set('sphere_scale', 0.38, 'accessible_region and name CA')
            cmd.set('sphere_scale', 0.44, 'shielded_region and name CA')
            add_square_glycan(job)
            cmd.orient('oval')
            cmd.turn('x', -14)
            cmd.turn('y', 30)
            cmd.turn('z', -8)
            cmd.zoom('oval', buffer=8, complete=1)
            cmd.clip('slab', 300)
            add_camera_dashed_envelope(job)

        for item in JOBS:
            setup_scene(item)
            print('png ' + item['species'], flush=True)
            cmd.png(item['out'], width=1200, height=920, dpi=220, ray=0)
            print('saved ' + item['species'], flush=True)
        cmd.quit()
    '''), encoding="utf-8")
    return script_path


def run_pymol(script_path: Path) -> None:
    if not PYMOL_PYTHON.exists():
        raise FileNotFoundError(f"PyMOL Python was not found: {PYMOL_PYTHON}")
    print(f"Running PyMOL renderer: {script_path}", flush=True)
    subprocess.run([str(PYMOL_PYTHON), str(script_path)], cwd=str(TMP_DIR), check=True)


def trim_white(img: Image.Image, pad: int = 40, threshold: int = 248) -> Image.Image:
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


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def fit_panel(path: str | Path, species: str, width: int = 1320, height: int = 1040) -> Image.Image:
    panel = Image.new("RGB", (width, height), "white")
    body = trim_white(Image.open(path).convert("RGB"), pad=54)
    scale = min((width - 80) / body.width, (height - 170) / body.height)
    resized = body.resize((int(body.width * scale), int(body.height * scale)), Image.LANCZOS)
    panel.paste(resized, ((width - resized.width) // 2, 130 + (height - 170 - resized.height) // 2))
    draw = ImageDraw.Draw(panel)
    font = read_font(58, bold=True)
    tw, _ = text_size(draw, species, font)
    draw.text(((width - tw) // 2, 30), species, fill=SPECIES_COLORS[species], font=font)
    return panel


def combine_outputs(jobs: list[dict]) -> None:
    panels = [fit_panel(job["out"], job["species"]) for job in jobs]
    gap = 54
    top_h = 190
    legend_h = 130
    width = sum(panel.width for panel in panels) + gap * (len(panels) - 1)
    height = top_h + panels[0].height + legend_h
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    title_font = read_font(66, bold=True)
    legend_font = read_font(36, bold=False)
    title = "Fig. 4H-K  3D Ca2+ hotspot accessibility and SASA schematic"
    draw.text((34, 26), title, fill="#171717", font=title_font)

    y = 112
    x = 44
    entries = [
        ("species-colored Ca2+ binding region", "#C46B83", "square"),
        ("glycan-shielded region", "#111111", "circle"),
        ("remaining protein surface", "#AFAFAF", "circle"),
        ("dashed SASA envelope", "#111111", "dash"),
        ("square glycan blocks", "#C46B83", "square"),
    ]
    for label, color, kind in entries:
        if kind == "square":
            draw.rectangle((x, y + 10, x + 38, y + 48), fill=color)
        elif kind == "dash":
            for offset in range(0, 72, 24):
                draw.line((x + offset, y + 30, x + offset + 14, y + 30), fill=color, width=6)
        else:
            draw.ellipse((x, y + 10, x + 38, y + 48), fill=color)
        draw.text((x + 54, y + 5), label, fill="#303030", font=legend_font)
        lw, _ = text_size(draw, label, legend_font)
        x += 112 + lw

    x = 0
    for panel in panels:
        canvas.paste(panel, (x, top_h))
        x += panel.width + gap
    combined = OUT_DIR / "Fig4H_K_3D_sasa_standalone.png"
    canvas.save(combined, dpi=(300, 300))
    print(f"Saved {combined}")
    for job, panel in zip(jobs, panels):
        out = OUT_DIR / f"Fig4H_K_3D_sasa_{job['species']}.png"
        panel.save(out, dpi=(300, 300))
        print(f"Saved {out}")


def main() -> None:
    structures = load_structures()
    jobs = build_jobs(structures)
    script_path = write_pymol_renderer(jobs)
    run_pymol(script_path)
    combine_outputs(jobs)


if __name__ == "__main__":
    main()