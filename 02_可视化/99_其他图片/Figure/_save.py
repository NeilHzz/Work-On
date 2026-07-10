"""Shared save utility for Figure scripts.
Saves each figure as PNG (300 dpi), PDF, and SVG to the corresponding subfolders.
"""
import os
import re
import shutil
from functools import partial
from pathlib import Path

_ROOT = os.path.dirname(os.path.abspath(__file__))
PNG_DIR = os.path.join(_ROOT, "PNG")
PDF_DIR = os.path.join(_ROOT, "PDF")
SVG_DIR = os.path.join(_ROOT, "SVG")
FONT_FAMILY = "Minion Pro"
MINION_REGULAR = Path("C:/Windows/Fonts/MinionPro-Regular.otf")
MINION_ITALIC = Path("C:/Windows/Fonts/MinionPro-It.otf")

for _d in (PNG_DIR, PDF_DIR, SVG_DIR):
    os.makedirs(_d, exist_ok=True)

COMPAT_PANEL_ALIASES = {
    "Fig2A": ["Fig2"],
    "Fig2BC_glycotype_consistency": ["Fig2_cluster_glycotype_consistency"],
    "Fig2D_glycotype_proportion": ["Fig2_species_glycotype_proportion"],
    "glycotype_coverage_overview": ["Fig2_coverage_overview"],
    "glycotype_shared_core_js": ["Fig2_shared_core_js"],
    "glycotype_shared_core_metric_comparison": ["Fig2_shared_core_metric_comparison"],
    "glycotype_species_heatmap": ["Fig2_species_glycotype_heatmap"],
    "Fig3A_ortholog_circos": ["Fig3B"],
    "Fig3B_proteotype_Gallus": ["Fig4A"],
    "Fig3C_proteotype_Anas": ["Fig4B"],
    "Fig3D_proteotype_Columba": ["Fig4C"],
    "Fig3E_enrichment_Gallus_vs_Columba": ["Fig4H"],
    "Fig3F_enrichment_Gallus_vs_Anas": ["Fig4I"],
    "Fig3G_enrichment_Anas_vs_Columba": ["Fig4J"],
    "protein_enrichment_legend": ["Fig4H-J_Legend"],
    "reglyco_surface_summary": ["Fig5A"],
    "Fig4K_hotspot_residues": ["Fig5B"],
    "Fig4L_carboxylate_surface_accessibility": ["Fig5C"],
    "reglyco_apbs_strip": ["Fig5D"],
    "Fig4C_glycan_radius_of_gyration": ["Fig5E"],
    "Fig4E_glycan_end_to_end_distance": ["Fig5F"],
    "Fig4F_glycan_protein_distance": ["Fig5G"],
    "Fig4D_glycan_backbone_proximity": ["Fig5H"],
    "Fig4G_interface_shielding": ["Fig5I"],
    "Fig4I_hotspot_residue_sasa": ["Fig5J"],
    "Fig4H_hotspot_fraction": ["Fig5K"],
    "Fig4J_net_accessible_hotspots": ["Fig5L"],
    "Fig4M_hotspot_accessibility": ["Fig5M"],
    "Fig4N_hotspot_residue_sasa": ["Fig5N"],
}


def _copy_compat_aliases(name):
    for alias in COMPAT_PANEL_ALIASES.get(name, []):
        for directory, suffix in ((PNG_DIR, ".png"), (PDF_DIR, ".pdf"), (SVG_DIR, ".svg")):
            src = os.path.join(directory, f"{name}{suffix}")
            dst = os.path.join(directory, f"{alias}{suffix}")
            if os.path.exists(src):
                shutil.copy2(src, dst)


def apply_research_font_settings():
    try:
        import matplotlib
        from matplotlib import font_manager
    except Exception:
        return
    for font_path in [
        MINION_REGULAR,
        MINION_ITALIC,
        Path("C:/Windows/Fonts/MinionPro-Bold.otf"),
        Path("C:/Windows/Fonts/MinionPro-BoldIt.otf"),
    ]:
        if font_path.exists():
            font_manager.fontManager.addfont(str(font_path))
    matplotlib.rcParams["font.family"] = FONT_FAMILY
    matplotlib.rcParams["font.serif"] = [FONT_FAMILY]
    matplotlib.rcParams["font.sans-serif"] = [FONT_FAMILY, "DejaVu Sans"]
    matplotlib.rcParams["mathtext.fontset"] = "custom"
    matplotlib.rcParams["mathtext.rm"] = FONT_FAMILY
    matplotlib.rcParams["mathtext.it"] = f"{FONT_FAMILY}:italic"
    matplotlib.rcParams["pdf.fonttype"] = 42
    matplotlib.rcParams["svg.fonttype"] = "none"


apply_research_font_settings()


def _italicize_species_text(text):
    if not isinstance(text, str) or not any(sp in text for sp in ("Gallus", "Anas", "Columba")):
        return text
    if text in {"Gallus", "Anas", "Columba"}:
        return text
    for species in ("Gallus", "Anas", "Columba"):
        text = re.sub(rf"(?<!it\{{)\b{species}\b", rf"$\\it{{{species}}}$", text)
    return text


def _italicize_species_names(fig):
    try:
        from matplotlib.text import Text
    except Exception:
        return
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            for formatter in (axis.get_major_formatter(), axis.get_minor_formatter()):
                seq = getattr(formatter, "seq", None)
                if seq:
                    formatter.seq = [_italicize_species_text(item) for item in seq]
                func = getattr(formatter, "func", None)
                if isinstance(func, partial) and func.args and isinstance(func.args[0], dict):
                    labels = func.args[0]
                    for key, value in list(labels.items()):
                        labels[key] = _italicize_species_text(value)
    for obj in fig.findobj(match=Text):
        obj.set_fontfamily(FONT_FAMILY)
        old = obj.get_text()
        if old in {"Gallus", "Anas", "Columba"}:
            obj.set_fontstyle("italic")
            continue
        new = _italicize_species_text(old)
        if new != old:
            obj.set_text(new)


def save_fig(fig, name, dpi=300):
    """Save figure as PNG, PDF, SVG to the three subfolders."""
    _italicize_species_names(fig)
    fig.savefig(os.path.join(PNG_DIR, f"{name}.png"), dpi=dpi, bbox_inches='tight', facecolor='white')
    fig.savefig(os.path.join(PDF_DIR, f"{name}.pdf"), bbox_inches='tight', facecolor='white')
    fig.savefig(os.path.join(SVG_DIR, f"{name}.svg"), bbox_inches='tight', facecolor='white')
    _copy_compat_aliases(name)
    print(f"  Saved: {name} [PNG/PDF/SVG]")


def save_plotly(fig, name, width=1800, height=950, png_scale=3.0):
    """Save plotly figure as PNG, PDF, SVG."""
    fig.write_image(os.path.join(PNG_DIR, f"{name}.png"), width=width, height=height, scale=png_scale)
    fig.write_image(os.path.join(PDF_DIR, f"{name}.pdf"), width=width, height=height)
    fig.write_image(os.path.join(SVG_DIR, f"{name}.svg"), width=width, height=height)
    _copy_compat_aliases(name)
    print(f"  Saved: {name} [PNG/PDF/SVG]")


def save_prerendered(src_png, name):
    """Copy a pre-rendered PNG and convert to PDF (raster). SVG embeds the raster."""
    from PIL import Image
    import base64
    # PNG
    dst_png = os.path.join(PNG_DIR, f"{name}.png")
    shutil.copy2(src_png, dst_png)
    # PDF via Pillow
    img = Image.open(src_png).convert("RGB")
    img.save(os.path.join(PDF_DIR, f"{name}.pdf"), "PDF", resolution=300)
    # SVG (embedded raster)
    with open(src_png, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    w, h = img.size
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">'
           f'<image href="data:image/png;base64,{b64}" width="{w}" height="{h}"/>'
           f'</svg>')
    with open(os.path.join(SVG_DIR, f"{name}.svg"), "w") as f:
        f.write(svg)
    _copy_compat_aliases(name)
    print(f"  Saved: {name} [PNG/PDF/SVG]")
