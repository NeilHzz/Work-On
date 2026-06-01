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
    Fig5E.png          → Fig4  C  (Glycan radius of gyration)
    Fig5H.png          → Fig4  D  (Glycan–backbone proximity)
    Fig5F.png          → Fig4  E  (Glycan end-to-end distance)
    Fig5G.png          → Fig4  F  (Glycan–protein distance)
    Fig5I.png          → Fig4  G  (Interface shielding)
    Fig5K.png          → Fig4  H  (Hotspot fraction)
    Fig5J.png          → Fig4  I  (Hotspot residue SASA)
    Fig5L.png          → Fig4  J  (Net accessible Ca²⁺)
    Fig5M.png          → Fig4  K  (Stacked bar – species comparison)
    Fig5N.png          → Fig4  L  (Stacked bar – glycosite comparison)
  eggtooth/鸡（喙）.png + chicken_model_render.png → Fig5  A  (Gallus)
  eggtooth/鸭（喙）.png + duck_model_render.png    → Fig5  B  (Anas)
  eggtooth/鸽子（喙）.png + pigeon_model_render.png→ Fig5  C  (Columba)
    Fig6A_Force.png + Fig6B_Fmax.png   → Fig6 A
    Fig6A_Shear.png + Fig6B_Taumax.png → Fig6 B
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
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


def scale_to_fit(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    """Proportionally resize *img* to fit inside max_w × max_h."""
    if img is None:
        return None
    scale = min(max_w / img.width, max_h / img.height)
    nw = max(1, round(img.width * scale))
    nh = max(1, round(img.height * scale))
    return img.resize((nw, nh), Image.LANCZOS)


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


def smooth_fem_render(img: Image.Image) -> Image.Image:
    """Soften FEM mesh speckle while preserving the colorbar and labels."""
    rgba = img.convert("RGBA")
    rgb = rgba.convert("RGB")
    width, height = rgba.size

    # The model occupies the left/middle of each render; the right edge contains
    # the colorbar and text, which should stay crisp.
    model_limit_x = int(width * 0.78)
    hard_mask = Image.new("L", (width, height), 0)
    mask_px = hard_mask.load()
    rgb_px = rgb.load()
    for y in range(height):
        for x in range(model_limit_x):
            r, g, b = rgb_px[x, y]
            if r < 248 or g < 248 or b < 248:
                mask_px[x, y] = 255

    mask = hard_mask.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(9))
    mask = mask.filter(ImageFilter.GaussianBlur(1.3))
    softened = rgb.filter(ImageFilter.MedianFilter(3)).filter(ImageFilter.GaussianBlur(0.65))
    out_rgb = Image.composite(softened, Image.new("RGB", (width, height), (255, 255, 255)), mask)

    # Put the untouched legend/colorbar strip back on top.
    out_rgb.paste(rgb.crop((model_limit_x, 0, width, height)), (model_limit_x, 0))
    out = out_rgb.convert("RGBA")
    out.putalpha(rgba.getchannel("A"))
    return out


def _stress_color(t: float) -> tuple[int, int, int]:
    stops = [
        (0.00, (0, 0, 190)),
        (0.25, (0, 105, 255)),
        (0.50, (0, 235, 220)),
        (0.67, (130, 255, 80)),
        (0.78, (255, 240, 0)),
        (0.90, (255, 115, 0)),
        (1.00, (185, 0, 0)),
    ]
    t = max(0.0, min(1.0, t))
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            f = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            return tuple(round(c0[i] + f * (c1[i] - c0[i])) for i in range(3))
    return stops[-1][1]


def make_stress_legend_bottom(width: int, height: int) -> Image.Image:
    legend = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    draw = ImageDraw.Draw(legend)
    title_font = _load_font(max(34, height // 4))
    tick_font = _load_font(max(28, height // 5))

    title = "Von Mises Stress (MPa)"
    bar_w = int(width * 0.58)
    bar_h = max(28, height // 7)
    bar_x = (width - bar_w) // 2
    title_y = max(8, height // 16)
    bar_y = int(height * 0.42)

    draw.text((width // 2, title_y), title, fill=(35, 35, 35, 255),
              font=title_font, anchor="ma")
    for i in range(bar_w):
        color = _stress_color(i / max(1, bar_w - 1))
        draw.line([(bar_x + i, bar_y), (bar_x + i, bar_y + bar_h)], fill=color + (255,))
    draw.rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h),
                   outline=(70, 70, 70, 255), width=2)

    ticks = [(0.00, "0.00"), (0.25, "3.75"), (0.50, "7.50"),
             (0.75, "11.25"), (1.00, "15.00")]
    tick_top = bar_y + bar_h
    for pos, label in ticks:
        x = bar_x + round(pos * bar_w)
        draw.line([(x, tick_top), (x, tick_top + 12)], fill=(70, 70, 70, 255), width=2)
        draw.text((x, tick_top + 16), label, fill=(55, 55, 55, 255),
                  font=tick_font, anchor="ma")
    return legend


def make_fem_panel_with_bottom_legend(img: Image.Image, target_w: int, target_h: int,
                                      show_legend: bool = True) -> Image.Image:
    model_limit_x = int(img.width * 0.78)
    model = smooth_fem_render(img).crop((0, 0, model_limit_x, img.height))
    model = trim_white(model, pad=28, threshold=248)

    legend_h = min(280, max(210, int(target_h * 0.11))) if show_legend else 0
    model_area_h = target_h - legend_h
    panel = Image.new("RGBA", (target_w, target_h), (255, 255, 255, 255))

    model = scale_to_fit(model, int(target_w * 0.88), int(model_area_h * 0.96))
    model_x = (target_w - model.width) // 2
    model_y = max(0, (model_area_h - model.height) // 2)
    panel.paste(model, (model_x, model_y), model)

    if show_legend:
        legend = make_stress_legend_bottom(target_w, legend_h)
        panel.paste(legend, (0, target_h - legend_h), legend)
    return panel


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

    def panel(source, label, target_w=None, target_h=None, font=FONT_PUB_LABEL, trim=False):
        source_path = source if isinstance(source, Path) else PNG / source
        raw = load_img(source_path)
        if raw is None:
            placeholder_w = target_w or max(800, int((target_h or 800) * 1.15))
            placeholder_h = target_h or int(placeholder_w * 0.65)
            raw = make_placeholder(placeholder_w, placeholder_h, f"Panel {label}\n{source_path.name}")
        if trim:
            raw = trim_white(raw)
        if target_h is not None:
            img = scale_to_h(raw, target_h)
        else:
            img = scale_to_w(raw, target_w)
        return add_label(img, label, font=font)

    def fit_row(panel_specs, target_row_w):
        raws = []
        aspect_sum = 0.0
        for source, label, trim in panel_specs:
            source_path = source if isinstance(source, Path) else PNG / source
            raw = load_img(source_path)
            if raw is None:
                raw = make_placeholder(1200, 900, f"Panel {label}\n{source_path.name}")
            if trim:
                raw = trim_white(raw)
            raws.append((raw, label))
            aspect_sum += raw.width / raw.height
        row_h = max(1, int((target_row_w - GAP * (len(panel_specs) - 1)) / aspect_sum))
        panels = [add_label(scale_to_h(raw, row_h), label, font=FONT_PUB_LABEL) for raw, label in raws]
        row_w = sum(panel.width for panel in panels) + GAP * (len(panels) - 1)
        row = Image.new("RGBA", (inner_w, row_h), (255, 255, 255, 0))
        x = max(0, (inner_w - row_w) // 2)
        for panel_img in panels:
            row.paste(panel_img, (x, 0), panel_img)
            x += panel_img.width + GAP
        return row

    # Fig 2 layout: A on the upper left; B/C combined panel and D below; E on the right.
    right_w = int((inner_w - GAP) * 0.36)
    left_w = inner_w - right_w - GAP

    A = panel("Fig2.png", "A", left_w, trim=False)
    row1 = Image.new("RGBA", (left_w, A.height), (255, 255, 255, 0))
    paste(row1, A, 0, 0)

    bd_w = (left_w - GAP) // 2
    BC = panel("Fig2_cluster_glycotype_consistency.png", "", target_w=bd_w, trim=True)
    D = panel("Fig2_species_glycotype_proportion.png", "D", target_w=left_w - bd_w - GAP, trim=True)
    row2_h = max(BC.height, D.height)
    row2 = Image.new("RGBA", (left_w, row2_h), (255, 255, 255, 0))
    paste(row2, BC, 0, 0)
    paste(row2, D, bd_w + GAP, 0)

    left_block_h = row1.height + GAP + row2.height
    left_block = Image.new("RGBA", (left_w, left_block_h), (255, 255, 255, 0))
    paste(left_block, row1, 0, 0)
    paste(left_block, row2, 0, row1.height + GAP)

    E = panel(FINAL_MAIN_SUBFIGS / "Fig3A.png", "E", target_w=right_w, trim=True)

    content_h = max(left_block.height, E.height)
    content = Image.new("RGBA", (inner_w, content_h), (255, 255, 255, 0))
    paste(content, left_block, 0, 0)
    paste(content, E, left_w + GAP, max(0, (content_h - E.height) // 2))

    total_h = 2 * MARGIN + content.height
    canvas = Image.new("RGBA", (CANVAS_W, total_h), (255, 255, 255, 255))

    paste(canvas, content, MARGIN, MARGIN)
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
# Fig 4  (grouped layout → labels A–N)
# ─────────────────────────────────────────────────────────────────────────────

def compose_fig4():
    print("\n=== Composing Fig 4 ===")
    inner_w = CANVAS_W - 2 * MARGIN

    group_gap = 90
    sub_gap = 36

    def make_panel(fname, label=None, *, ncols=None, target_w=None, cover_old=False,
                   trim=False, max_h=None, zoom=1.0, label_offset=(14, 8),
                   cover_px=(90, 110)):
        if target_w is None and ncols is not None:
            target_w = (inner_w - (ncols - 1) * GAP) // ncols
        raw = load_img(PNG / fname)
        if raw is None:
            placeholder_w = target_w or 1200
            placeholder_h = max_h or int(placeholder_w * 0.8)
            raw = make_placeholder(placeholder_w, placeholder_h, fname)
        if trim:
            raw = trim_white(raw, pad=24, threshold=250)
        slot_w = target_w
        if target_w is not None and zoom != 1.0:
            target_w = max(1, round(target_w * zoom))
        if target_w is not None and max_h is not None:
            img = scale_to_fit(raw, target_w, max_h)
        elif target_w is not None:
            img = scale_to_w(raw, target_w)
        elif max_h is not None:
            img = scale_to_h(raw, max_h)
        else:
            img = raw
        if slot_w is not None and zoom != 1.0 and img.width > slot_w:
            left = max(0, (img.width - slot_w) // 2)
            img = img.crop((left, 0, left + slot_w, img.height))
        if label is not None:
            img = add_label(img, label, font=FONT_FIG4_LABEL,
                            offset=label_offset, cover=cover_old,
                            cover_px=cover_px)
        return img

    def compose_centered_row(images, gap=GAP, row_width=None):
        row_width = row_width or inner_w
        row_h = max(img.height for img in images if img is not None)
        row_w = sum(img.width for img in images if img is not None) + gap * (len(images) - 1)
        row = Image.new("RGBA", (row_width, row_h), (255, 255, 255, 0))
        x = max(0, (row_width - row_w) // 2)
        for img in images:
            paste(row, img, x, (row_h - img.height) // 2)
            x += img.width + gap
        return row

    def compose_vertical_block(rows, block_width, gap=sub_gap):
        block_h = sum(row.height for row in rows) + gap * (len(rows) - 1)
        block = Image.new("RGBA", (block_width, block_h), (255, 255, 255, 0))
        y = 0
        for row in rows:
            paste(block, row, (block_width - row.width) // 2, y)
            y += row.height + gap
        return block

    def draw_dashed_line(draw, start, end, *, dash=34, gap=22, width=5,
                         fill=(175, 175, 175, 255)):
        x1, y1 = start
        x2, y2 = end
        if x1 == x2:
            step = dash + gap
            y = min(y1, y2)
            y_stop = max(y1, y2)
            while y < y_stop:
                draw.line((x1, y, x2, min(y + dash, y_stop)), fill=fill, width=width)
                y += step
            return
        if y1 == y2:
            step = dash + gap
            x = min(x1, x2)
            x_stop = max(x1, x2)
            while x < x_stop:
                draw.line((x, y1, min(x + dash, x_stop), y2), fill=fill, width=width)
                x += step
            return
        raise ValueError("draw_dashed_line only supports horizontal or vertical lines")

    def make_shared_final_legend():
        legend_w = min(2600, inner_w // 2)
        legend_h = 120
        legend = Image.new("RGBA", (legend_w, legend_h), (255, 255, 255, 0))
        draw = ImageDraw.Draw(legend)
        font = _load_font(52)
        text_color = (40, 40, 40, 255)
        y = 58

        draw.line((28, y, 128, y), fill=(120, 120, 120, 255), width=10)
        draw.ellipse((22, y - 16, 54, y + 16), fill=(120, 120, 120, 255),
                     outline=(35, 35, 35, 255), width=2)
        draw.text((152, y - 28), "retained / accessible", fill=text_color, font=font)

        x2 = legend_w // 2 + 12
        draw.line((x2, y, x2 + 100, y), fill=(120, 120, 120, 255), width=10)
        draw.ellipse((x2 + 70, y - 16, x2 + 102, y + 16), fill=(255, 255, 255, 255),
                     outline=(120, 120, 120, 255), width=3)
        draw.text((x2 + 126, y - 28), "total / full state", fill=text_color, font=font)
        return legend

    group_w = (inner_w - GAP) // 2
    group_panel_w = (group_w - sub_gap) // 2
    group_three_panel_w = (group_w - 2 * sub_gap) // 3
    bottom_panel_w = (inner_w - 3 * GAP) // 4

    dg_context_row = compose_centered_row([
        make_panel("Fig4D-G_Gallus.png", target_w=group_panel_w, trim=True),
        make_panel("Fig4D-G_Columba.png", target_w=group_panel_w, trim=True, zoom=0.9),
    ], gap=sub_gap, row_width=group_w)
    dg_context_row = add_label(dg_context_row, "A", font=FONT_FIG4_LABEL)
    cf_plot_row = compose_centered_row([
        make_panel("Fig5E.png", "C", target_w=group_panel_w, cover_old=True, cover_px=(120, 130)),
        make_panel("Fig5H.png", "D", target_w=group_panel_w, cover_old=True, cover_px=(120, 130)),
    ], gap=sub_gap, row_width=group_w)

    de_plot_row = compose_centered_row([
        make_panel("Fig5F.png", "E", target_w=group_panel_w, cover_old=True, cover_px=(120, 130)),
        make_panel("Fig5G.png", "F", target_w=group_panel_w, cover_old=True, cover_px=(120, 130)),
    ], gap=sub_gap, row_width=group_w)

    group_a = compose_vertical_block([dg_context_row, cf_plot_row, de_plot_row], group_w)

    gi_plot_row = compose_centered_row([
        make_panel("Fig5I.png", "G", target_w=group_panel_w, cover_old=True, cover_px=(120, 130)),
        make_panel("Fig5K.png", "H", target_w=group_panel_w, cover_old=True, cover_px=(120, 130)),
    ], gap=sub_gap, row_width=group_w)

    hj_plot_row = compose_centered_row([
        make_panel("Fig5J.png", "I", target_w=group_panel_w, cover_old=True, cover_px=(120, 130)),
        make_panel("Fig5L.png", "J", target_w=group_panel_w, cover_old=True, cover_px=(120, 130)),
    ], gap=sub_gap, row_width=group_w)

    hk_context_row = compose_centered_row([
        make_panel("Fig4H_K_3D_sasa_Gallus.png", target_w=group_three_panel_w, trim=True),
        make_panel("Fig4H_K_3D_sasa_Anas.png", target_w=group_three_panel_w, trim=True),
        make_panel("Fig4H_K_3D_sasa_Columba.png", target_w=group_three_panel_w, trim=True),
    ], gap=sub_gap, row_width=group_w)
    hk_context_row = add_label(hk_context_row, "B", font=FONT_FIG4_LABEL)
    group_b = compose_vertical_block([hk_context_row, gi_plot_row, hj_plot_row], group_w)

    group_row = compose_centered_row([group_a, group_b], gap=GAP, row_width=inner_w)
    bottom_row = compose_centered_row([
        make_panel("Fig5B.png", "K", target_w=bottom_panel_w, cover_old=True, cover_px=(120, 130)),
        make_panel("Fig5C.png", "L", target_w=bottom_panel_w, cover_old=True, cover_px=(120, 130)),
        make_panel("Fig5M.png", "M", target_w=bottom_panel_w, cover_old=True, cover_px=(120, 130)),
        make_panel("Fig5N.png", "N", target_w=bottom_panel_w, cover_old=True, cover_px=(120, 130)),
    ], row_width=inner_w)

    rows = [group_row, bottom_row]
    gaps = [group_gap]
    total_h = 2 * MARGIN + sum(row.height for row in rows) + sum(gaps)
    canvas = Image.new("RGBA", (CANVAS_W, total_h), (255, 255, 255, 255))

    y = MARGIN
    for idx, row in enumerate(rows):
        paste(canvas, row, MARGIN, y)
        y += row.height
        if idx < len(gaps):
            y += gaps[idx]

    draw = ImageDraw.Draw(canvas)
    group_row_w = group_a.width + group_b.width + GAP
    group_row_left = MARGIN + max(0, (inner_w - group_row_w) // 2)
    vertical_sep_x = group_row_left + group_a.width + GAP // 2
    draw_dashed_line(
        draw,
        (vertical_sep_x, MARGIN + 20),
        (vertical_sep_x, MARGIN + group_row.height - 20),
    )

    horizontal_sep_y = MARGIN + group_row.height + group_gap // 2
    draw_dashed_line(
        draw,
        (MARGIN + 20, horizontal_sep_y),
        (CANVAS_W - MARGIN - 20, horizontal_sep_y),
    )

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
    for idx, (lbl, illus_path, fem_path, sp_name) in enumerate(species_data):
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
            fem_img = make_fem_panel_with_bottom_legend(
                fem_raw, right_w, row_h, show_legend=(idx == len(species_data) - 1)
            )

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
# Supplementary Fig S7  (merged glycosylation profiling + surface potential)
# ─────────────────────────────────────────────────────────────────────────────

def compose_supp_fig7():
    print("\n=== Composing Supplementary Fig S7 ===")
    outer_gap = 80

    raw_glyco = load_img(PNG / "Fig4D_G.png")
    raw_surface = load_img(PNG / "Fig5A.png")

    if raw_glyco is None:
        raw_glyco = make_placeholder(3563, 1774, "Fig4D_G not found")
    if raw_surface is None:
        raw_surface = make_placeholder(5203, 3133, "Fig5A not found")

    target_w = max(raw_glyco.width, raw_surface.width)
    glyco = scale_to_w(raw_glyco, target_w)
    surface = scale_to_w(raw_surface, target_w)

    glyco = add_label(glyco, "A", font=FONT_PUB_LABEL)
    surface = add_label(surface, "B", font=FONT_PUB_LABEL,
                        cover=True, cover_px=(120, 120))

    canvas_w = target_w + 2 * MARGIN
    canvas_h = glyco.height + surface.height + 2 * MARGIN + outer_gap
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))

    y = MARGIN
    paste(canvas, glyco, (canvas_w - glyco.width) // 2, y)
    y += glyco.height + outer_gap
    paste(canvas, surface, (canvas_w - surface.width) // 2, y)

    save_fig(canvas, "FigS7")


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
    compose_supp_fig7()
    print("\nAll manuscript figures composed successfully.")
    print(f"Output directory: {OUT}")
