"""Shared save utility for Figure scripts.
Saves each figure as PNG (300 dpi), PDF, and SVG to the corresponding subfolders.
"""
import os
import shutil

_ROOT = os.path.dirname(os.path.abspath(__file__))
PNG_DIR = os.path.join(_ROOT, "PNG")
PDF_DIR = os.path.join(_ROOT, "PDF")
SVG_DIR = os.path.join(_ROOT, "SVG")

for _d in (PNG_DIR, PDF_DIR, SVG_DIR):
    os.makedirs(_d, exist_ok=True)


def save_fig(fig, name, dpi=300):
    """Save figure as PNG, PDF, SVG to the three subfolders."""
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
