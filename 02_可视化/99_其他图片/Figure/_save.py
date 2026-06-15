"""Shared save utility for Figure scripts.
Saves each figure as PNG (300 dpi), PDF, and SVG to the corresponding subfolders.
"""
import os
import re
import shutil
from functools import partial

_ROOT = os.path.dirname(os.path.abspath(__file__))
PNG_DIR = os.path.join(_ROOT, "PNG")
PDF_DIR = os.path.join(_ROOT, "PDF")
SVG_DIR = os.path.join(_ROOT, "SVG")

for _d in (PNG_DIR, PDF_DIR, SVG_DIR):
    os.makedirs(_d, exist_ok=True)


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
        old = obj.get_text()
        if old in {"Gallus", "Anas", "Columba"}:
            obj.set_fontfamily("Times New Roman")
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
    print(f"  Saved: {name} [PNG/PDF/SVG]")


def save_plotly(fig, name, width=1800, height=950, png_scale=3.0):
    """Save plotly figure as PNG, PDF, SVG."""
    fig.write_image(os.path.join(PNG_DIR, f"{name}.png"), width=width, height=height, scale=png_scale)
    fig.write_image(os.path.join(PDF_DIR, f"{name}.pdf"), width=width, height=height)
    fig.write_image(os.path.join(SVG_DIR, f"{name}.svg"), width=width, height=height)
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
    print(f"  Saved: {name} [PNG/PDF/SVG]")
