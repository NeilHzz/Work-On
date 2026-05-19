#!/usr/bin/env python
"""
compose_manuscript_figures.py
==============================
Assembles individual panel PNGs into 6 manuscript composite figures
matching the layout from Figure260421/ reference images.

Panel sources   : 02_可视化/Figure/PNG/
FEM renders     : 01_数据与计算/LS-DYNA_原始模型/
Bird illustrations: 01_数据与计算/乳突层形态结构/
Old panels      : 02_可视化/Sci_Adv_Figure/PNG/Fig1/  (for Fig1C)
Output          : 02_可视化/Composed/

Panel mapping (script file → manuscript figure / panel):
  Fig1A.png          → Fig1  A  (CVA 3D scatter)
  Fig1B.png          → Fig1  B  (Phylogenetic tree + heatmap)
  [old mammilla]     → Fig1  C  (SEM + egg shell + mammilla structure)
  Fig1D.png          → Fig1  D  (Mammilla density + volume boxplots)
  Fig3A.png          → Fig2     (Glycotype radial network, no letter)
  Fig3B.png          → Fig3  A  (Chord diagram)
  Fig4A.png          → Fig3  B  (Gallus Proteotype Coevolution scatter)
  Fig4B.png          → Fig3  C  (Anas Proteotype Coevolution scatter)
  Fig4C.png          → Fig3  D  (Columba Proteotype Coevolution scatter)
  Fig4H.png          → Fig3  E  (2D Enrichment scatter)
  Fig4I.png          → Fig3  F  (2D Enrichment scatter)
  Fig4J.png          → Fig3  G  (2D Enrichment scatter)
  Fig5B.png          → Fig4  A  (Ca²⁺ hotspot residues bar)
  Fig5C.png          → Fig4  B  (Carboxylate surface accessibility bar)
  Fig5D.png          → Fig4  C  (Surface potential violin)
  Fig5E.png          → Fig4  D  (Glycan radius of gyration)
  Fig5F.png          → Fig4  E  (Glycan end-to-end distance)
  Fig5G.png          → Fig4  F  (Glycan–protein distance)
  Fig5H.png          → Fig4  G  (Glycan–backbone proximity)
  Fig5I.png          → Fig4  H  (Interface shielding)
  Fig5J.png          → Fig4  I  (Hotspot residue SASA)
  Fig5K.png          → Fig4  J  (Hotspot fraction)
  Fig5L.png          → Fig4  K  (Net accessible Ca²⁺)
  Fig5M.png          → Fig4  L  (Stacked bar – species comparison)
  Fig5N.png          → Fig4  M  (Stacked bar – glycosite comparison)
  T_Pigeon.png + pigeon_model_render.png → Fig5  A
  T_Duck.png   + duck_model_render.png   → Fig5  B
  T_Chicken.png+ chicken_model_render.png→ Fig5  C
  Fig6A.png          → Fig6  (left 65%  – force & shear timeseries)
  Fig6B.png          → Fig6  (right 35% – DMRT bar charts)
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys

# ─────────────────────────────────────────────────────────────────────────────
# Directory paths
# ─────────────────────────────────────────────────────────────────────────────
BASE   = Path(__file__).resolve().parent.parent          # …/Work On/
PNG    = Path(__file__).resolve().parent / "Figure" / "PNG"
FEM    = BASE / "01_数据与计算" / "LS-DYNA_原始模型"
ILLUS  = BASE / "01_数据与计算" / "乳突层形态结构"
OLD_F1 = Path(__file__).resolve().parent / "Sci_Adv_Figure" / "PNG" / "Fig1"
OUT    = Path(__file__).resolve().parent / "Composed"
OUT.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Layout constants
# ─────────────────────────────────────────────────────────────────────────────
CANVAS_W = 7200   # total canvas width (px) – matches 600 DPI × 12 cm
MARGIN   = 80     # outer margin (px)
GAP      = 50     # gap between adjacent panels in a row
DPI      = 300    # output DPI tag

# ─────────────────────────────────────────────────────────────────────────────
# Font helpers
# ─────────────────────────────────────────────────────────────────────────────
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/timesbd.ttf",                            # Windows Times New Roman Bold
    "C:/Windows/Fonts/Times New Roman Bold.ttf",
    "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Bold.ttf",
    "/Library/Fonts/Times New Roman Bold.ttf",
]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for fp in _FONT_CANDIDATES:
        if Path(fp).exists():
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


FONT_XL  = _load_font(120)   # full-width panels
FONT_LG  = _load_font(100)   # half-width panels
FONT_MD  = _load_font(80)    # third-width panels
FONT_SM  = _load_font(64)    # quarter-width panels

# ─────────────────────────────────────────────────────────────────────────────
# Image utilities
# ─────────────────────────────────────────────────────────────────────────────

def load_img(path) -> Image.Image | None:
    """Load an image as RGBA.  Returns None with a warning if the file is missing."""
    p = Path(path)
    if not p.exists():
        print(f"  [WARN] File not found: {p}", file=sys.stderr)
        return None
    img = Image.open(p)
    img.load()                 # eagerly read so the file handle is released
    return img.convert("RGBA")


def make_placeholder(w: int, h: int, text: str = "") -> Image.Image:
    """Light-grey placeholder rectangle with centred text."""
    img = Image.new("RGBA", (w, h), (220, 220, 220, 255))
    if text:
        draw = ImageDraw.Draw(img)
        fnt = _load_font(max(18, h // 10))
        draw.text((w // 2, h // 2), text, fill=(110, 110, 110, 255),
                  font=fnt, anchor="mm")
    return img


def scale_to_w(img: Image.Image, target_w: int) -> Image.Image:
    """Proportionally resize *img* so its width equals *target_w*."""
    if img is None:
        return None
    nh = max(1, round(img.height * target_w / img.width))
    return img.resize((target_w, nh), Image.LANCZOS)


def scale_to_h(img: Image.Image, target_h: int) -> Image.Image:
    """Proportionally resize *img* so its height equals *target_h*."""
    if img is None:
        return None
    nw = max(1, round(img.width * target_h / img.height))
    return img.resize((nw, target_h), Image.LANCZOS)


def add_label(img: Image.Image, label: str,
              font: ImageFont.FreeTypeFont | None = None,
              offset: tuple[int, int] = (14, 8),
              cover: bool = False,
              cover_px: tuple[int, int] = (90, 110)) -> Image.Image:
    """
    Draw a bold panel letter at the top-left corner of *img*.

    Parameters
    ----------
    cover : bool
        If True, first paint a white rectangle over *cover_px* to hide any
        existing label that was embedded by the source script.
    cover_px : (width, height)
        Size of the white rectangle used when *cover=True*.
    """
    img = img.copy()
    draw = ImageDraw.Draw(img)
    if cover:
        draw.rectangle([(0, 0), cover_px], fill=(255, 255, 255, 255))
    fnt = font or FONT_MD
    draw.text(offset, label, fill=(0, 0, 0, 255), font=fnt)
    return img


def paste(canvas: Image.Image, img: Image.Image, x: int, y: int):
    """Paste an RGBA *img* onto *canvas* at *(x, y)* using alpha compositing."""
    if img is None:
        return
    canvas.paste(img, (x, y), img)


def save_fig(img: Image.Image, name: str):
    """Flatten to RGB (white background) and save as PNG."""
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bg.paste(img, mask=img.split()[3])
    out = OUT / f"{name}.png"
    bg.save(out, dpi=(DPI, DPI))
    print(f"  Saved → {out}")


def row_images(files_labels: list[tuple[str, str]], ncols: int,
               inner_w: int, label_font: ImageFont.FreeTypeFont | None = None,
               cover_old_label: bool = False
               ) -> tuple[list[Image.Image], int]:
    """
    Build a list of panel images for one row.

    Parameters
    ----------
    files_labels : list of (filename, manuscript_label)
        *filename* is relative to PNG directory.
    ncols : int
        Number of columns in this row (determines panel width).
    inner_w : int
        Total inner canvas width (excluding outer margins).
    cover_old_label : bool
        Whether to white-out the existing embedded label before drawing the
        new manuscript label (needed for panels from Fig5A_D.py).

    Returns
    -------
    (panels, col_w) where *col_w* is the width of each column in px.
    """
    col_w = (inner_w - (ncols - 1) * GAP) // ncols
    font  = label_font or FONT_MD
    panels = []
    for fname, lbl in files_labels:
        raw = load_img(PNG / fname)
        if raw is None:
            img = make_placeholder(col_w, int(col_w * 0.9), lbl)
        else:
            img = scale_to_w(raw, col_w)
        img = add_label(img, lbl, font=font, cover=cover_old_label)
        panels.append(img)
    return panels, col_w


def paste_row(canvas: Image.Image,
              panels: list[Image.Image],
              col_w: int,
              y: int,
              x_start: int | None = None) -> int:
    """
    Paste a row of equally-wide panels onto *canvas*.

    Returns the y coordinate directly below the pasted row (y + row_height + GAP).
    """
    x = x_start if x_start is not None else MARGIN
    row_h = max(p.height for p in panels if p is not None)
    for p in panels:
        if p is not None:
            paste(canvas, p, x, y)
        x += col_w + GAP
    return y + row_h + GAP


# ─────────────────────────────────────────────────────────────────────────────
# Fig 1  (4 rows, all full-width)
# ─────────────────────────────────────────────────────────────────────────────

def compose_fig1():
    print("\n=== Composing Fig 1 ===")
    inner_w = CANVAS_W - 2 * MARGIN

    def full(fname, label, font=FONT_XL):
        raw = load_img(PNG / fname) if fname else None
        if raw is None:
            raw = make_placeholder(inner_w, int(inner_w * 0.3), f"Panel {label}")
        img = scale_to_w(raw, inner_w)
        return add_label(img, label, font=font)

    # Panel A: CVA 3D scatter (no pre-existing corner label from script)
    A = full("Fig1A.png", "A")

    # Panel B: Phylogenetic tree + heatmap
    B = full("Fig1B.png", "B")

    # Panel C: SEM + egg shell + mammilla microstructure (from old Sci_Adv panel)
    raw_c = load_img(OLD_F1 / "2-2Fig_mammilla_microstructure_panels.png")
    if raw_c is None:
        raw_c = make_placeholder(inner_w, int(inner_w * 0.25),
                                 "Panel C — mammilla microstructure\n"
                                 "(02_可视化/Sci_Adv_Figure/PNG/Fig1/"
                                 "2-2Fig_mammilla_microstructure_panels.png)")
    C = scale_to_w(raw_c, inner_w)
    C = add_label(C, "C", font=FONT_XL)

    # Panel D: Mammilla density + unit volume ratio boxplots
    D = full("Fig1D.png", "D")

    rows = [A, B, C, D]
    total_h = (2 * MARGIN
               + sum(r.height for r in rows)
               + GAP * (len(rows) - 1))
    canvas = Image.new("RGBA", (CANVAS_W, total_h), (255, 255, 255, 255))

    y = MARGIN
    for row in rows:
        paste(canvas, row, MARGIN, y)
        y += row.height + GAP

    save_fig(canvas, "Fig1_composed")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 2  (single panel, no panel letter)
# ─────────────────────────────────────────────────────────────────────────────

def compose_fig2():
    print("\n=== Composing Fig 2 ===")
    inner_w = CANVAS_W - 2 * MARGIN

    # The glycotype radial network is saved by Fig3A.py as "Fig3A.png"
    raw = load_img(PNG / "Fig3A.png")
    if raw is None:
        raw = make_placeholder(inner_w, inner_w,
                               "Fig 2 — Glycotype radial network\n"
                               "(02_可视化/Figure/PNG/Fig3A.png)")
    img = scale_to_w(raw, inner_w)

    # No panel letter for Fig 2
    total_h = 2 * MARGIN + img.height
    canvas = Image.new("RGBA", (CANVAS_W, total_h), (255, 255, 255, 255))
    paste(canvas, img, MARGIN, MARGIN)
    save_fig(canvas, "Fig2_composed")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 3  (A = left ~38 %, full height; B–G = right ~62 %, 2 rows × 3 cols)
# ─────────────────────────────────────────────────────────────────────────────

def compose_fig3():
    print("\n=== Composing Fig 3 ===")
    inner_w = CANVAS_W - 2 * MARGIN
    left_frac = 0.38
    left_w  = int(inner_w * left_frac)
    right_w = inner_w - left_w - GAP
    col_w   = (right_w - 2 * GAP) // 3     # 3 equal columns on the right

    def rp(fname, label):
        """Right-side panel: scale to col_w, add label."""
        raw = load_img(PNG / fname)
        if raw is None:
            raw = make_placeholder(col_w, int(col_w * 1.05), label)
        img = scale_to_w(raw, col_w)
        return add_label(img, label, font=FONT_SM)

    # Top row (B, C, D) — Proteotype Coevolution scatters
    B = rp("Fig4A.png", "B")
    C = rp("Fig4B.png", "C")
    D = rp("Fig4C.png", "D")

    # Bottom row (E, F, G) — 2D Enrichment scatters
    E = rp("Fig4H.png", "E")
    F = rp("Fig4I.png", "F")
    G = rp("Fig4J.png", "G")

    top_h = max(B.height, C.height, D.height)
    bot_h = max(E.height, F.height, G.height)
    right_h = top_h + GAP + bot_h

    # Panel A: chord diagram — scale to left_w preserving aspect ratio
    raw_a = load_img(PNG / "Fig3B.png")
    if raw_a is None:
        A = make_placeholder(left_w, right_h, "A")
    else:
        # Scale proportionally to left_w; if shorter than right_h, pad at bottom
        A_nat = scale_to_w(raw_a, left_w)
        if A_nat.height < right_h:
            A = Image.new("RGBA", (left_w, right_h), (255, 255, 255, 0))
            A.paste(A_nat, (0, 0), A_nat)
        else:
            # Crop to right_h from top
            A = A_nat.crop((0, 0, left_w, right_h))
    A = add_label(A, "A", font=FONT_LG)

    total_h = 2 * MARGIN + right_h
    canvas = Image.new("RGBA", (CANVAS_W, total_h), (255, 255, 255, 255))

    # Paste A (left column)
    paste(canvas, A, MARGIN, MARGIN)

    # Paste right top row
    x_right = MARGIN + left_w + GAP
    for img in [B, C, D]:
        paste(canvas, img, x_right, MARGIN)
        x_right += col_w + GAP

    # Paste right bottom row
    x_right = MARGIN + left_w + GAP
    y_bot = MARGIN + top_h + GAP
    for img in [E, F, G]:
        paste(canvas, img, x_right, y_bot)
        x_right += col_w + GAP

    save_fig(canvas, "Fig3_composed")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 4  (4 rows: 3 + 4 + 4 + 2 panels → labels A–M)
# ─────────────────────────────────────────────────────────────────────────────

def compose_fig4():
    print("\n=== Composing Fig 4 ===")
    inner_w = CANVAS_W - 2 * MARGIN

    def build_row(files_labels, ncols, cover_old=False):
        col_w = (inner_w - (ncols - 1) * GAP) // ncols
        font  = FONT_MD if ncols <= 3 else FONT_SM
        imgs  = []
        for fname, lbl in files_labels:
            raw = load_img(PNG / fname)
            if raw is None:
                img = make_placeholder(col_w, int(col_w * 0.9), lbl)
            else:
                img = scale_to_w(raw, col_w)
            img = add_label(img, lbl, font=font, cover=cover_old)
            imgs.append(img)
        return imgs, col_w

    # Row 1 (A, B, C) — 3 panels each 1/3 width
    # Source panels Fig5B/C/D already have embedded B/C/D labels → cover and relabel
    r1, cw1 = build_row([
        ("Fig5B.png", "A"),   # Ca²⁺ hotspot bar    (script label B)
        ("Fig5C.png", "B"),   # Carboxylate SASA bar (script label C)
        ("Fig5D.png", "C"),   # Surface potential    (script label D)
    ], ncols=3, cover_old=True)

    # Row 2 (D, E, F, G) — 4 panels each 1/4 width
    # Source panels Fig5E–H have NO embedded corner labels (labels were removed)
    r2, cw2 = build_row([
        ("Fig5E.png", "D"),   # Glycan Rg
        ("Fig5F.png", "E"),   # Glycan end-to-end
        ("Fig5G.png", "F"),   # Glycan–protein distance
        ("Fig5H.png", "G"),   # Glycan–backbone proximity
    ], ncols=4, cover_old=False)

    # Row 3 (H, I, J, K) — 4 panels
    # Source panels Fig5I–L have embedded labels I/J/K/L → cover and relabel
    r3, cw3 = build_row([
        ("Fig5I.png", "H"),
        ("Fig5J.png", "I"),
        ("Fig5K.png", "J"),
        ("Fig5L.png", "K"),
    ], ncols=4, cover_old=True)

    # Row 4 (L, M) — 2 panels each 1/2 width
    # Source panels Fig5M/N have embedded labels M/N → cover and relabel
    r4, cw4 = build_row([
        ("Fig5M.png", "L"),
        ("Fig5N.png", "M"),
    ], ncols=2, cover_old=True)

    def row_h(panels):
        return max(p.height for p in panels if p is not None)

    total_h = (2 * MARGIN
               + row_h(r1) + row_h(r2) + row_h(r3) + row_h(r4)
               + 3 * GAP)
    canvas = Image.new("RGBA", (CANVAS_W, total_h), (255, 255, 255, 255))

    y = MARGIN
    for row, cw in [(r1, cw1), (r2, cw2), (r3, cw3), (r4, cw4)]:
        y = paste_row(canvas, row, cw, y)

    save_fig(canvas, "Fig4_composed")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 5  (3 rows; each row: left ~22 % bird illustration + right ~78 % FEM)
#         Row A = Columba (pigeon), B = Anas (duck), C = Gallus (chicken)
# ─────────────────────────────────────────────────────────────────────────────

def compose_fig5():
    print("\n=== Composing Fig 5 ===")
    inner_w  = CANVAS_W - 2 * MARGIN
    left_frac = 0.22
    left_w   = int(inner_w * left_frac)
    right_w  = inner_w - left_w - GAP

    # All FEM renders are 1900×1400.  Scale to right_w, height follows naturally.
    species_data = [
        ("A", ILLUS / "T_Pigeon.png",  FEM / "pigeon_model_render.png",  "Columba (pigeon)"),
        ("B", ILLUS / "T_Duck.png",    FEM / "duck_model_render.png",    "Anas (duck)"),
        ("C", ILLUS / "T_Chicken.png", FEM / "chicken_model_render.png", "Gallus (chicken)"),
    ]

    rows = []
    for lbl, illus_path, fem_path, sp_name in species_data:
        fem_raw = load_img(fem_path)
        if fem_raw is None:
            fem_img = make_placeholder(right_w, int(right_w * 0.74),
                                       f"{sp_name} FEM render\n(file not found)")
        else:
            fem_img = scale_to_w(fem_raw, right_w)

        row_h = fem_img.height   # row height driven by FEM render

        illus_raw = load_img(illus_path)
        if illus_raw is None:
            illus_img = make_placeholder(left_w, row_h,
                                         f"{sp_name}\nillustration not found")
        else:
            # Scale illustration to left_w; centre it vertically if shorter than row_h
            illus_scaled = scale_to_w(illus_raw, left_w)
            if illus_scaled.height <= row_h:
                y_off = (row_h - illus_scaled.height) // 2
                illus_img = Image.new("RGBA", (left_w, row_h), (255, 255, 255, 0))
                illus_img.paste(illus_scaled, (0, y_off), illus_scaled)
            else:
                illus_img = illus_scaled.crop((0, 0, left_w, row_h))

        # Add panel letter to the illustration (left panel)
        illus_img = add_label(illus_img, lbl, font=FONT_LG)

        # Combine illustration + FEM into one row strip
        row_strip = Image.new("RGBA", (inner_w, row_h), (255, 255, 255, 0))
        row_strip.paste(illus_img, (0, 0), illus_img)
        row_strip.paste(fem_img,   (left_w + GAP, 0), fem_img)
        rows.append(row_strip)

    total_h = 2 * MARGIN + sum(r.height for r in rows) + GAP * (len(rows) - 1)
    canvas = Image.new("RGBA", (CANVAS_W, total_h), (255, 255, 255, 255))

    y = MARGIN
    for row in rows:
        paste(canvas, row, MARGIN, y)
        y += row.height + GAP

    save_fig(canvas, "Fig5_composed")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 6  (left ~65 % = force+shear timeseries; right ~35 % = DMRT bars)
# ─────────────────────────────────────────────────────────────────────────────

def compose_fig6():
    print("\n=== Composing Fig 6 ===")
    inner_w = CANVAS_W - 2 * MARGIN
    left_w  = int(inner_w * 0.65)
    right_w = inner_w - left_w - GAP

    # Fig6A contains both timeseries subplots (force F top, shear τ bottom)
    left_raw = load_img(PNG / "Fig6A.png")
    if left_raw is None:
        left_img = make_placeholder(left_w, int(left_w * 0.83),
                                    "Fig6A — timeseries (not found)")
    else:
        left_img = scale_to_w(left_raw, left_w)

    # Fig6B contains both DMRT bar charts
    right_raw = load_img(PNG / "Fig6B.png")
    if right_raw is None:
        right_img = make_placeholder(right_w, left_img.height,
                                     "Fig6B — DMRT bars (not found)")
    else:
        right_img = scale_to_w(right_raw, right_w)

    # Use the taller column to determine canvas height; shorter one aligns to top
    canvas_h = 2 * MARGIN + max(left_img.height, right_img.height)
    canvas = Image.new("RGBA", (CANVAS_W, canvas_h), (255, 255, 255, 255))

    paste(canvas, left_img,  MARGIN, MARGIN)
    paste(canvas, right_img, MARGIN + left_w + GAP, MARGIN)

    save_fig(canvas, "Fig6_composed")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    compose_fig1()
    compose_fig2()
    compose_fig3()
    compose_fig4()
    compose_fig5()
    compose_fig6()
    print("\nAll manuscript figures composed successfully.")
    print(f"Output directory: {OUT}")
