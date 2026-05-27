#!/usr/bin/env python
"""
compose_manuscript_figures.py
==============================
Assembles individual panel PNGs into 6 manuscript composite figures
matching the layout from Figure260421/ reference images.

Panel sources   : 02_可视化/Figure/PNG/
FEM renders     : 01_数据与计算/LS-DYNA_原始模型/
Bird illustrations (eggtooth): 02_可视化/eggtooth/
Output          : 02_可视化/Composed/

Panel mapping (source image → manuscript figure / panel):
  Fig1A.png          → Fig1  A  (CVA 3D scatter)
  eggtooth/鸡.png + 鸭.png + 鸽子.png (top row)
  + 鸡（喙）.png + 鸭（喙）.png + 鸽子（喙）.png (bottom row)
                     → Fig1  B  (2×3 bird illustration grid)
    eggtooth/Gallus.jpg + Anas.jpg + Columba.jpg
                                         → Fig1  C  (SEM + egg shell + mammilla structure)
  Fig1D.png          → Fig1  D  (Mammilla density + volume boxplots)
    Fig2.png           → Fig2     (Glycoprotein orthogroup UpSet plot, no letter)
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
  eggtooth/鸡（喙）.png + chicken_model_render.png → Fig5  A  (Gallus)
  eggtooth/鸭（喙）.png + duck_model_render.png    → Fig5  B  (Anas)
  eggtooth/鸽子（喙）.png + pigeon_model_render.png→ Fig5  C  (Columba)
    Fig6A_Force.png + Fig6B_Fmax.png   → Fig6 A
    Fig6A_Shear.png + Fig6B_Taumax.png → Fig6 B
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys

# ─────────────────────────────────────────────────────────────────────────────
# Directory paths
# ─────────────────────────────────────────────────────────────────────────────
BASE   = Path(__file__).resolve().parent.parent          # …/Work On/
PNG    = Path(__file__).resolve().parent / "Figure" / "PNG"
FEM      = BASE / "01_数据与计算" / "LS-DYNA_原始模型"
ILLUS    = BASE / "01_数据与计算" / "乳突层形态结构"
EGGTOOTH = Path(__file__).resolve().parent / "eggtooth"
OUT    = Path(__file__).resolve().parent / "Composed"
OUT.mkdir(exist_ok=True)
FINAL_MAIN_SUBFIGS = Path(__file__).resolve().parent / "260526" / "01_main_subfigures_matched_to_composed"

# ─────────────────────────────────────────────────────────────────────────────
# Layout constants
# ─────────────────────────────────────────────────────────────────────────────
CANVAS_W = 7200   # total canvas width (px) – matches 600 DPI × 12 cm
MARGIN   = 80     # outer margin (px)
GAP      = 50     # gap between adjacent panels in a row
DPI      = 300    # output DPI tag for individual subfigures
PUBLICATION_DPI = 1000  # 7200 px wide -> ~18.3 cm at native size

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
FONT_FIG4_LABEL = _load_font(120)
FONT_PUB_LABEL = _load_font(120)

SPECIES_COLORS = {
    "Gallus": "#C46B83",
    "Anas": "#93AACD",
    "Columba": "#F3CE9D",
}

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


def trim_white(img: Image.Image, pad: int = 24, threshold: int = 248) -> Image.Image:
    """Trim near-white margins while preserving a small publication-safe pad."""
    rgba = img.convert("RGBA")
    rgb = rgba.convert("RGB")
    pixels = rgb.load()
    xs = []
    ys = []
    for y in range(rgb.height):
        for x in range(rgb.width):
            r, g, b = pixels[x, y]
            if r < threshold or g < threshold or b < threshold:
                xs.append(x)
                ys.append(y)
    if not xs:
        return rgba
    left = max(0, min(xs) - pad)
    top = max(0, min(ys) - pad)
    right = min(rgba.width, max(xs) + pad + 1)
    bottom = min(rgba.height, max(ys) + pad + 1)
    return rgba.crop((left, top, right, bottom))


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


def save_fig(img: Image.Image, name: str, dpi: int = PUBLICATION_DPI):
    """Flatten to RGB (white background) and save as PNG."""
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bg.paste(img, mask=img.split()[3])
    out = OUT / f"{name}.png"
    bg.save(out, dpi=(dpi, dpi))
    print(f"  Saved → {out}")


def make_fig1c_triptych(target_w: int) -> Image.Image:
    """Build Fig. 1C from the three species-specific mammillary structure panels."""
    inner_gap = 32
    col_w = (target_w - 2 * inner_gap) // 3
    panels = []
    for species in ["Gallus", "Anas", "Columba"]:
        raw = load_img(EGGTOOTH / f"{species}.jpg")
        if raw is None:
            img = make_placeholder(col_w, int(col_w * 1.15), species)
        else:
            img = scale_to_w(raw, col_w)
        draw = ImageDraw.Draw(img)
        draw.text((col_w // 2, 18), species,
                  fill=SPECIES_COLORS[species], font=FONT_MD, anchor="mt")
        panels.append(img)

    panel_h = max(img.height for img in panels)
    triptych = Image.new("RGBA", (target_w, panel_h), (255, 255, 255, 0))
    x = 0
    for img in panels:
        triptych.paste(img, (x, (panel_h - img.height) // 2), img)
        x += col_w + inner_gap
    return triptych


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
        new manuscript label (needed for panels from MainFig4A_C_SuppFigS8_reglyco_apbs.py).

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

    def panel(fname, label, target_w, font=FONT_PUB_LABEL):
        raw = load_img(PNG / fname) if fname else None
        if raw is None:
            raw = make_placeholder(target_w, int(target_w * 0.7), f"Panel {label}")
        img = scale_to_w(raw, target_w)
        return add_label(img, label, font=font)

    top_left_w = int(inner_w * 0.58)
    top_right_w = inner_w - top_left_w - GAP

    # Panel A: CVA 3D scatter (no pre-existing corner label from script)
    A = panel("Fig1A.png", "A", top_left_w)

    # Panel B: 2×3 bird illustration grid
    #   Row 1 (top)    = full bird head portraits  (鸡 / 鸭 / 鸽子)
    #   Row 2 (bottom) = beak / egg-tooth closeups (鸡（喙）/ 鸭（喙）/ 鸽子（喙）)
    col_w_b = (top_right_w - 2 * GAP) // 3
    top_names = ["鸡.png", "鸭.png", "鸽子.png"]
    bot_names = ["鸡（喙）.png", "鸭（喙）.png", "鸽子（喙）.png"]

    def _eg(name):
        raw = load_img(EGGTOOTH / name)
        if raw is None:
            return make_placeholder(col_w_b, col_w_b, name)
        return scale_to_w(raw, col_w_b)

    row_top_imgs = [_eg(n) for n in top_names]
    row_bot_imgs = [_eg(n) for n in bot_names]
    top_row_h = max(img.height for img in row_top_imgs)
    bot_row_h = max(img.height for img in row_bot_imgs)
    b_h = top_row_h + GAP + bot_row_h
    B = Image.new("RGBA", (top_right_w, b_h), (255, 255, 255, 0))
    x = 0
    for img in row_top_imgs:
        B.paste(img, (x, 0), img)
        x += col_w_b + GAP
    x = 0
    for img in row_bot_imgs:
        B.paste(img, (x, top_row_h + GAP), img)
        x += col_w_b + GAP
    B = add_label(B, "B", font=FONT_PUB_LABEL)

    top_h = max(A.height, B.height)
    top_strip = Image.new("RGBA", (inner_w, top_h), (255, 255, 255, 0))
    top_strip.paste(A, (0, (top_h - A.height) // 2), A)
    top_strip.paste(B, (top_left_w + GAP, (top_h - B.height) // 2), B)

    bottom_left_w = int(inner_w * 0.56)
    bottom_right_w = inner_w - bottom_left_w - GAP

    # Panel C: species-specific SEM + egg shell + mammilla microstructure panels
    C = make_fig1c_triptych(bottom_left_w)
    C = add_label(C, "C", font=FONT_PUB_LABEL)

    # Panel D: Mammilla density + unit volume ratio boxplots
    D = panel("Fig1D.png", "D", bottom_right_w)

    bottom_h = max(C.height, D.height)
    bottom_strip = Image.new("RGBA", (inner_w, bottom_h), (255, 255, 255, 0))
    bottom_strip.paste(C, (0, (bottom_h - C.height) // 2), C)
    bottom_strip.paste(D, (bottom_left_w + GAP, (bottom_h - D.height) // 2), D)

    rows = [top_strip, bottom_strip]
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
# Fig 2  (A-E: UpSet, glycan network, and glycan-type summaries)
# ─────────────────────────────────────────────────────────────────────────────

def compose_fig2():
    print("\n=== Composing Fig 2 ===")
    inner_w = CANVAS_W - 2 * MARGIN

    def panel(source, label, target_w, font=FONT_PUB_LABEL, trim=False):
        source_path = source if isinstance(source, Path) else PNG / source
        raw = load_img(source_path)
        if raw is None:
            raw = make_placeholder(target_w, int(target_w * 0.65), f"Panel {label}\n{source_path.name}")
        if trim:
            raw = trim_white(raw)
        img = scale_to_w(raw, target_w)
        return add_label(img, label, font=font)

    # A: current glycoprotein orthogroup UpSet plot, full width for readability.
    A = panel("Fig2.png", "A", inner_w, trim=False)

    # B-C: requested BLAST ortholog chord diagram plus within-cluster glycan-type consistency.
    left_w = int(inner_w * 0.40)
    right_w = inner_w - left_w - GAP
    B = panel(FINAL_MAIN_SUBFIGS / "Fig3A.png", "B", left_w, trim=False)
    C = panel("Fig2_cluster_glycotype_consistency.png", "C", right_w, trim=False)
    row2_h = max(B.height, C.height)
    row2 = Image.new("RGBA", (inner_w, row2_h), (255, 255, 255, 0))
    row2.paste(B, (0, (row2_h - B.height) // 2), B)
    row2.paste(C, (left_w + GAP, (row2_h - C.height) // 2), C)

    # D-E: keep composition and heatmap separated, each wide enough for readable text.
    col_w = (inner_w - GAP) // 2
    D = panel("Fig2_species_glycotype_proportion.png", "D", col_w, trim=False)
    E = panel("Fig2_species_glycotype_heatmap.png", "E", col_w, trim=False)
    row3_h = max(D.height, E.height)
    row3 = Image.new("RGBA", (inner_w, row3_h), (255, 255, 255, 0))
    row3.paste(D, (0, (row3_h - D.height) // 2), D)
    row3.paste(E, (col_w + GAP, (row3_h - E.height) // 2), E)

    rows = [A, row2, row3]
    total_h = 2 * MARGIN + sum(row.height for row in rows) + GAP * (len(rows) - 1)
    canvas = Image.new("RGBA", (CANVAS_W, total_h), (255, 255, 255, 255))

    y = MARGIN
    for row in rows:
        paste(canvas, row, MARGIN, y)
        y += row.height + GAP
    save_fig(canvas, "Fig2_composed")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 3  (B-G only; B-C-D first row, E-F-G second row)
# ─────────────────────────────────────────────────────────────────────────────

def compose_fig3():
    print("\n=== Composing Fig 3 ===")
    inner_w = CANVAS_W - 2 * MARGIN
    col_w = (inner_w - 2 * GAP) // 3

    def panel(fname, label):
        raw = load_img(PNG / fname)
        if raw is None:
            raw = make_placeholder(col_w, int(col_w * 0.92), f"Panel {label}\n{fname}")
        img = scale_to_w(raw, col_w)
        return add_label(img, label, font=FONT_PUB_LABEL)

    rows = [
        [panel("Fig4A.png", "B"), panel("Fig4B.png", "C"), panel("Fig4C.png", "D")],
        [panel("Fig4H.png", "E"), panel("Fig4I.png", "F"), panel("Fig4J.png", "G")],
    ]
    row_heights = [max(img.height for img in row) for row in rows]
    total_h = 2 * MARGIN + sum(row_heights) + GAP * (len(rows) - 1)
    canvas = Image.new("RGBA", (CANVAS_W, total_h), (255, 255, 255, 255))

    y = MARGIN
    for row, row_h in zip(rows, row_heights):
        x = MARGIN
        for img in row:
            paste(canvas, img, x, y + (row_h - img.height) // 2)
            x += col_w + GAP
        y += row_h + GAP

    save_fig(canvas, "Fig3_composed")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 4  (4 rows: 3 + 4 + 4 + 2 panels → labels A–M)
# ─────────────────────────────────────────────────────────────────────────────

def compose_fig4():
    print("\n=== Composing Fig 4 ===")
    inner_w = CANVAS_W - 2 * MARGIN

    def build_row(files_labels, ncols, cover_old=False):
        col_w = (inner_w - (ncols - 1) * GAP) // ncols
        font  = FONT_FIG4_LABEL
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

    # Row 4 (L, M) — center two panels on the same four-column grid
    # Source panels Fig5M/N have embedded labels M/N → cover and relabel
    r4, cw4 = build_row([
        ("Fig5M.png", "L"),
        ("Fig5N.png", "M"),
    ], ncols=4, cover_old=True)

    def row_h(panels):
        return max(p.height for p in panels if p is not None)

    total_h = (2 * MARGIN
               + row_h(r1) + row_h(r2) + row_h(r3) + row_h(r4)
               + 3 * GAP)
    canvas = Image.new("RGBA", (CANVAS_W, total_h), (255, 255, 255, 255))

    y = MARGIN
    for row, cw in [(r1, cw1), (r2, cw2), (r3, cw3)]:
        y = paste_row(canvas, row, cw, y)

    row4_w = 2 * cw4 + GAP
    row4_x = (CANVAS_W - row4_w) // 2
    y = paste_row(canvas, r4, cw4, y, x_start=row4_x)

    save_fig(canvas, "Fig4_composed")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 5  (3 rows; each row: left ~35 % bird illustration + right ~65 % FEM)
#         Row A = Gallus (chicken), B = Anas (duck), C = Columba (pigeon)
# ─────────────────────────────────────────────────────────────────────────────

def compose_fig5():
    print("\n=== Composing Fig 5 ===")
    inner_w   = CANVAS_W - 2 * MARGIN
    left_frac = 0.35                        # ~35 % matches reference (983/2776)
    left_w    = int(inner_w * left_frac)
    right_w   = inner_w - left_w           # no gap between illustration and FEM

    # Left column: beak/egg-tooth illustrations (2048×2048 square) from eggtooth/
    # Right column: FEM renders (1900×1400) — scale to right_w, crop bottom to row_h
    # Row order: A = Gallus (chicken), B = Anas (duck), C = Columba (pigeon)
    species_data = [
        ("A", EGGTOOTH / "鸡（喙）.png",   FEM / "chicken_model_render.png", "Gallus (chicken)"),
        ("B", EGGTOOTH / "鸭（喙）.png",   FEM / "duck_model_render.png",    "Anas (duck)"),
        ("C", EGGTOOTH / "鸽子（喙）.png", FEM / "pigeon_model_render.png",  "Columba (pigeon)"),
    ]

    rows = []
    for lbl, illus_path, fem_path, sp_name in species_data:
        # Scale illustration to left_w; it is 2048×2048 so height == left_w → row height
        illus_raw = load_img(illus_path)
        if illus_raw is None:
            illus_img = make_placeholder(left_w, left_w, f"{sp_name}\nillustration not found")
        else:
            illus_img = scale_to_w(illus_raw, left_w)

        row_h = illus_img.height   # row height driven by the square illustration

        # Scale FEM to right_w, then crop bottom excess so it matches row_h
        fem_raw = load_img(fem_path)
        if fem_raw is None:
            fem_img = make_placeholder(right_w, row_h, f"{sp_name} FEM render\n(file not found)")
        else:
            fem_img = scale_to_w(fem_raw, right_w)
            if fem_img.height > row_h:
                fem_img = fem_img.crop((0, 0, right_w, row_h))

        # Add panel letter to the illustration (top-left)
        illus_img = add_label(illus_img, lbl, font=FONT_LG)

        # Combine illustration + FEM into one row strip (no gap between columns)
        row_strip = Image.new("RGBA", (inner_w, row_h), (255, 255, 255, 0))
        row_strip.paste(illus_img, (0, 0), illus_img)
        row_strip.paste(fem_img,   (left_w, 0), fem_img)
        rows.append(row_strip)

    total_h = 2 * MARGIN + sum(r.height for r in rows) + GAP * (len(rows) - 1)
    canvas = Image.new("RGBA", (CANVAS_W, total_h), (255, 255, 255, 255))

    y = MARGIN
    for row in rows:
        paste(canvas, row, MARGIN, y)
        y += row.height + GAP

    save_fig(canvas, "Fig5_composed")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 6  (2-row × 2-column grid — uses individually saved panels)
#   Row A: Force timeseries  (Fig6A_Force.png, left ~65 %) | F_max bars  (Fig6B_Fmax.png)
#   Row B: Shear timeseries  (Fig6A_Shear.png, left ~65 %) | τ_max bars  (Fig6B_Taumax.png)
#   Generate source panels first: run  02_可视化/Figure/MainFig6_mechanics_force_shear.py
# ─────────────────────────────────────────────────────────────────────────────

def compose_fig6():
    print("\n=== Composing Fig 6 ===")
    inner_w   = CANVAS_W - 2 * MARGIN
    left_frac = 0.65               # timeseries column ~65 % (figsize 12/18)
    left_w    = int(inner_w * left_frac)
    right_w   = inner_w - left_w - GAP

    # ── load individually generated panels ──────────────────────────────────
    raw_force  = load_img(PNG / "Fig6A_Force.png")
    raw_shear  = load_img(PNG / "Fig6A_Shear.png")
    raw_fmax   = load_img(PNG / "Fig6B_Fmax.png")
    raw_taumax = load_img(PNG / "Fig6B_Taumax.png")

    if raw_force  is None: raw_force  = make_placeholder(2400, 1134, "Fig6A_Force not found\nrun MainFig6_mechanics_force_shear.py first")
    if raw_shear  is None: raw_shear  = make_placeholder(2400, 1134, "Fig6A_Shear not found\nrun MainFig6_mechanics_force_shear.py first")
    if raw_fmax   is None: raw_fmax   = make_placeholder(1200, 1300, "Fig6B_Fmax not found\nrun MainFig6_mechanics_force_shear.py first")
    if raw_taumax is None: raw_taumax = make_placeholder(1200, 1300, "Fig6B_Taumax not found\nrun MainFig6_mechanics_force_shear.py first")

    # ── scale left (timeseries) panels to left_w → row heights ──────────────
    force_s = scale_to_w(raw_force, left_w)
    shear_s = scale_to_w(raw_shear, left_w)
    row_A_h = force_s.height
    row_B_h = shear_s.height

    # ── panel labels ─────────────────────────────────────────────────────────
    force_s = add_label(force_s, "A", font=FONT_PUB_LABEL)
    shear_s = add_label(shear_s, "B", font=FONT_PUB_LABEL)

    # ── scale right (bar) panels to match row heights ─────────────────────────
    fmax_s   = scale_to_h(raw_fmax,   row_A_h)
    taumax_s = scale_to_h(raw_taumax, row_B_h)

    # ── compose canvas ────────────────────────────────────────────────────────
    total_h = 2 * MARGIN + row_A_h + GAP + row_B_h
    canvas  = Image.new("RGBA", (CANVAS_W, total_h), (255, 255, 255, 255))

    y = MARGIN
    paste(canvas, force_s, MARGIN, y)
    bx_A = MARGIN + left_w + GAP + max(0, (right_w - fmax_s.width) // 2)
    paste(canvas, fmax_s, bx_A, y)

    y += row_A_h + GAP
    paste(canvas, shear_s, MARGIN, y)
    bx_B = MARGIN + left_w + GAP + max(0, (right_w - taumax_s.width) // 2)
    paste(canvas, taumax_s, bx_B, y)

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
