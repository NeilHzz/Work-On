"""
Science Advances 格式 — 英文版 补充材料 (Supplementary Materials)
输出: supplementary_materials_en.docx

SA 规范要点：
- 补充材料正文单倍行距
- 封面：Supplementary Materials for [Title] + 作者 + 对应作者邮箱 + This PDF file includes
- 图：图在上，Fig. Sx. 加粗标题在下，不加粗说明在最下
- 每张图单独分页
- 不在 SM 中建立独立参考文献列表
"""

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from pathlib import Path

FIG_BASE = Path(r"D:\system_folder\Desktop\Work On\Supplementary\Figures")
OUT = str(Path(__file__).with_name("supplementary_materials_en.docx"))

doc = Document()

# ── 页面设置 ──────────────────────────────────────────────────────────
s = doc.sections[0]
s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Cm(2.54)
s.page_width  = Cm(21.0)
s.page_height = Cm(29.7)

FONT = "Times New Roman"

# ── 基础工具 ──────────────────────────────────────────────────────────
def _set_font(rPr, name=FONT):
    rFonts = OxmlElement("w:rFonts")
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rFonts.set(qn(attr), name)
    rPr.insert(0, rFonts)

def fmt(run, size=11, bold=False, italic=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    _set_font(run._r.get_or_add_rPr())

def sp(p, before=0, after=80, line=12):
    """line in pt; SA SM 使用单倍行距 (line=12)"""
    pPr = p._p.get_or_add_pPr()
    e = OxmlElement("w:spacing")
    e.set(qn("w:before"),   str(before))
    e.set(qn("w:after"),    str(after))
    e.set(qn("w:line"),     str(line * 20))
    e.set(qn("w:lineRule"), "auto")
    pPr.append(e)

def para(text, bold=False, italic=False, size=11,
         before=0, after=80, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    sp(p, before=before, after=after)
    r = p.add_run(text)
    fmt(r, size=size, bold=bold, italic=italic)
    return p

def mpara(parts, before=0, after=80, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    """parts = [(text, bold, italic), ...]"""
    p = doc.add_paragraph()
    p.alignment = align
    sp(p, before=before, after=after)
    for text, bold, italic in parts:
        r = p.add_run(text)
        fmt(r, bold=bold, italic=italic)
    return p

def section_head(text):
    """Supplementary Text / Figures 等一级节标题"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    sp(p, before=360, after=120)
    r = p.add_run(text)
    fmt(r, size=12, bold=True)
    return p

def st_head(text):
    """Supplementary Text n. 子节标题（加粗）"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    sp(p, before=240, after=80)
    r = p.add_run(text)
    fmt(r, size=11, bold=True)
    return p

def add_image(img_path, width_cm=15.5):
    """居中插入图片"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sp(p, before=60, after=60, line=12)
    p.add_run().add_picture(str(img_path), width=Cm(width_cm))
    return p

def add_images_row(img_paths, width_cm=7.5):
    """同一段并排插入多张图片"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sp(p, before=60, after=60, line=12)
    for i, ip in enumerate(img_paths):
        p.add_run().add_picture(str(ip), width=Cm(width_cm))
        if i < len(img_paths) - 1:
            p.add_run("  ")
    return p

def fig_title(label, title):
    """Fig. S1. 加粗标题段落（图之后）"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    sp(p, before=80, after=40)
    r = p.add_run(label + " ")
    fmt(r, bold=True)
    r2 = p.add_run(title)
    fmt(r2, bold=True)
    return p

def fig_caption(parts, before=0, after=240):
    """图注正文（不加粗）; parts = [(text, bold, italic), ...]"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    sp(p, before=before, after=after)
    for text, bold, italic in parts:
        r = p.add_run(text)
        fmt(r, bold=bold, italic=italic)
    return p

# ════════════════════════════════════════════════════════════════════
# 封面页  （SA 模板标准格式）
# ════════════════════════════════════════════════════════════════════
para("Supplementary Materials for", bold=False, size=11,
     before=0, after=40, align=WD_ALIGN_PARAGRAPH.CENTER)

para(
    "Glycan-state divergence in matrix proteins links to avian eggshell structure "
    "and biomineralization",
    bold=True, size=12, before=0, after=160, align=WD_ALIGN_PARAGRAPH.CENTER
)

para("[Author 1], [Author 2], [Author 3], [Corresponding Author]*",
     bold=False, size=10, before=0, after=40, align=WD_ALIGN_PARAGRAPH.CENTER)

para("*Corresponding author. Email: [corresponding@email.edu]",
     bold=False, italic=True, size=10, before=0, after=360,
     align=WD_ALIGN_PARAGRAPH.CENTER)

# "This PDF file includes:" 清单
para("This PDF file includes:", bold=True, size=11,
     before=0, after=60, align=WD_ALIGN_PARAGRAPH.LEFT)

for line in [
    "Supplementary Text 1 to 2",
    "Figs. S1 to S8",
    "Table S1 to S7 (uploaded separately as Excel files)",
]:
    p = doc.add_paragraph(style="List Bullet")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    sp(p, before=0, after=20)
    r = p.add_run(line)
    fmt(r, size=11)

doc.add_page_break()

# ════════════════════════════════════════════════════════════════════
# SUPPLEMENTARY TEXT
# ════════════════════════════════════════════════════════════════════
section_head("Supplementary Text")

# ── ST 1 ─────────────────────────────────────────────────────────────
st_head("Supplementary Text 1. Species selection and sensitivity analysis.")

mpara([
    ("Principal component analysis of AVONET ecological trait scores (Body Mass, Beak Length, "
     "Beak Width, Beak Depth, Tarsus Length, Wing Length, Kipps Distance, Hand-Wing Index, "
     "Tail Length; plus Primary Lifestyle, Habitat, Trophic Niche encoded numerically) "
     "separated ", False, False),
    ("Gallus gallus", False, True),
    (", ", False, False),
    ("Anas platyrhynchos", False, True),
    (", and ", False, False),
    ("Columba livia", False, True),
    (" into three distinct, non-overlapping regions of avian ecological space (Fig. S1), "
     "corresponding respectively to terrestrial ground-nesting precocial, semi-aquatic "
     "precocial, and elevated-nesting altricial life-history strategies. Species selection "
     "was therefore driven by the aim of simultaneously spanning both the precocial–altricial "
     "and terrestrial–semi-aquatic comparison axes, rather than by any single phylogenetic or "
     "morphological criterion.", False, False),
])

mpara([
    ("To verify that the three-cluster separation was not an artefact of the numerical encoding "
     "scheme applied to categorical variables, 500 randomized perturbation iterations were "
     "performed in which all encoding weights were independently shifted within ±30% of their "
     "original values. Across all 500 iterations, both the variance explained by the first two "
     "principal components and the cluster silhouette coefficient remained tightly concentrated "
     "around their unperturbed baseline values (Fig. S1). This indicated that the species-group "
     "assignments are robust to the subjective component of the numerical coding scheme, and "
     "that the three focal species genuinely occupy distinct ecological niches under any "
     "reasonable encoding.", False, False),
], before=80)

# ── ST 2 ─────────────────────────────────────────────────────────────
st_head("Supplementary Text 2. Eggshell matrix proteome orthogroup analysis.")

mpara([
    ("Proteomics-identified eggshell matrix proteins were organized with an "
     "OrthoFinder-based orthology workflow into 2,620, 2,921, and 3,219 orthogroups in ", False, False),
    ("G. gallus", False, True),
    (", ", False, False),
    ("A. platyrhynchos", False, True),
    (", and ", False, False),
    ("C. livia", False, True),
    (", respectively. Using all-versus-all protein similarity relationships and graph-based "
     "clustering, the workflow partitioned these into a conserved three-species "
     "shared core of 1,997 orthogroups (Fig. S2), pairwise-shared but not universally shared "
     "complements of 180 (", False, False),
    ("G. gallus", False, True),
    ("–", False, False),
    ("A. platyrhynchos", False, True),
    ("), 434 (", False, False),
    ("G. gallus", False, True),
    ("–", False, False),
    ("C. livia", False, True),
    ("), and 716 (", False, False),
    ("A. platyrhynchos", False, True),
    ("–", False, False),
    ("C. livia", False, True),
    ("), and lineage-restricted (species-exclusive) sets of 9, 28, and 72 orthogroups for "
     "chicken, duck, and pigeon, respectively. The topology of the orthogroup partition "
     "indicated that cross-species comparison was shaped by differential deployment within a "
     "common protein repertoire, not by wholesale protein replacement.", False, False),
])

mpara([
    ("Gene Ontology (GO) enrichment of pairwise-shared sets revealed functional stratification "
     "along ecological axes (Fig. S4). The ", False, False),
    ("A. platyrhynchos", False, True),
    ("–", False, False),
    ("C. livia", False, True),
    ("-shared set—proteins shared between the two lineages that depend primarily on food- or "
     "water-borne calcium sources—was most significantly enriched for calcium-ion binding and "
     "metal-ion binding (MF; both ", False, False),
    ("p", False, True),
    (" < 10⁻²⁵), as well as Wnt signaling and signal transduction (BP). The ", False, False),
    ("G. gallus", False, True),
    ("–", False, False),
    ("A. platyrhynchos", False, True),
    ("-shared set (both precocial Galloanserae) was enriched for adaptive immune response and "
     "spermatogenesis (BP), consistent with precocial reproductive programs.", False, False),
], before=80)

mpara([
    ("Lineage-restricted GO signals sharpened the cross-species contrast (Fig. S4). The ", False, False),
    ("G. gallus", False, True),
    ("-exclusive set (9 orthogroups) was significantly enriched for protein N-linked "
     "glycosylation (BP), indicating that glycan-processing capacity represents a "
     "chicken-specific functional expansion absent from the other two proteomes—an "
     "observation that directly motivated the subsequent comparative glycoproteomics analysis. "
     "The ", False, False),
    ("A. platyrhynchos", False, True),
    ("-exclusive set (", False, False),
    ("n", False, True),
    (" = 28) was enriched for immune response regulation, B-cell activation, and iron "
     "response, consistent with higher pathogen exposure in an aquatic foraging context. "
     "The ", False, False),
    ("C. livia", False, True),
    ("-exclusive set (", False, False),
    ("n", False, True),
    (" = 72) was enriched for nervous system development, ubiquitin-dependent protein "
     "catabolism, and proteolysis, reflecting the developmental complexity required for rapid "
     "organ maturation in an altricial hatchling.", False, False),
], before=80)

mpara([
    ("Gene-family expansion and contraction inferred by CAFE5 further confirmed asymmetric "
     "lineage divergence (Fig. S5): ", False, False),
    ("G. gallus", False, True),
    (" showed net family contraction, ", False, False),
    ("A. platyrhynchos", False, True),
    (" was intermediate, and ", False, False),
    ("C. livia", False, True),
    (" showed net expansion. Contracted families in chicken were enriched for immune-related "
     "functions; expanded families in pigeon were enriched for transmembrane transport, Rho "
     "signaling, and synapse-related processes. Together, these patterns confirmed broad "
     "evolutionary divergence among the three eggshell-formation systems while simultaneously "
     "establishing that N-linked glycosylation is a chicken-specific elaboration—a finding "
     "that focused the analysis toward glycan-state differences rather than "
     "protein-presence differences.", False, False),
], before=80)

doc.add_page_break()

# ════════════════════════════════════════════════════════════════════
# FIGURES
# ════════════════════════════════════════════════════════════════════
section_head("Figures")

# ── Fig. S1 ───────────────────────────────────────────────────────────
add_image(FIG_BASE / "SuppFig1_Species_Selection" / "Sensitivity_Analysis_Results.png",
          width_cm=15.5)
fig_title("Fig. S1.",
          "Sensitivity analysis validating the macroecological species-selection framework.")
fig_caption([
    ("Distribution of variance explained (R²) and cluster silhouette coefficients from "
     "500 randomized perturbation iterations applied to the AVONET-based principal-component "
     "space used to select ", False, False),
    ("Gallus gallus", False, True),
    (", ", False, False),
    ("Anas platyrhynchos", False, True),
    (", and ", False, False),
    ("Columba livia", False, True),
    (" as focal species. Categorical ecological variables (Primary Lifestyle, Habitat, "
     "Trophic Niche) were numerically encoded; each iteration introduced independent random "
     "shifts to all encoding weights within ±30% of the original values. The tight "
     "concentration of both metrics around the baseline confirms that species-group "
     "assignments are robust to the subjective encoding component.", False, False),
])

doc.add_page_break()

# ── Fig. S2 ───────────────────────────────────────────────────────────
add_image(FIG_BASE / "SuppFig2_Venn_Orthogroups" / "Fig_venn_orthogroups.png",
          width_cm=12.0)
fig_title("Fig. S2.",
          "Three-species Venn diagram of shared and lineage-restricted eggshell matrix orthogroups.")
fig_caption([
    ("OrthoFinder-based orthogroup analysis partitions the three eggshell matrix proteomes "
     "into a large three-species shared core, three pairwise-shared sectors, and three "
     "lineage-restricted sectors. Numbers indicate orthogroup counts per sector. The large "
     "shared core indicates that cross-species comparison is shaped by differential "
     "deployment within a common protein repertoire rather than wholesale protein "
     "replacement.", False, False),
])

doc.add_page_break()

# ── Fig. S3 ───────────────────────────────────────────────────────────
add_image(FIG_BASE / "SuppFig3_Phylo_Tree" / "Fig_phylo_tree.png", width_cm=14.0)
fig_title("Fig. S3.",
          "Maximum-likelihood phylogenetic tree of the three focal species "
          "reconstructed from single-copy orthologs.")
fig_caption([
    ("Phylogenetic tree inferred by IQ-TREE from a concatenated alignment of single-copy "
     "orthologous protein sequences. Branch lengths reflect substitutions per site. "
     "Ultrafast bootstrap support values (1000 replicates) are shown at internal nodes. "
     "The topology—Galliformes and Anseriformes as sister clades within Galloanseres, "
     "Columbiformes as the more distant outgroup—is consistent with published avian "
     "phylogenies and underpins the comparative framework used throughout the main text.", False, False),
])

doc.add_page_break()

# ── Fig. S4 ───────────────────────────────────────────────────────────
add_image(FIG_BASE / "SuppFig4_GO_Enrichment" / "Fig_GO_heatmap_single_species.png",
          width_cm=15.5)
add_image(FIG_BASE / "SuppFig4_GO_Enrichment" / "Fig_GO_bubble_pairwise_combined.png",
          width_cm=15.5)
add_image(FIG_BASE / "SuppFig4_GO_Enrichment" / "Legend_GO_Category.png", width_cm=9.0)
fig_title("Fig. S4.",
          "GO enrichment across lineage-restricted and pairwise eggshell matrix protein sets.")
fig_caption([
    ("(A–C) Gene Ontology (GO) enrichment heatmap for biological process (BP) and molecular "
     "function (MF) categories across the three lineage-restricted protein sets (", False, False),
    ("G. gallus", False, True),
    (", ", False, False),
    ("A. platyrhynchos", False, True),
    (", ", False, False),
    ("C. livia", False, True),
    ("). Color intensity reflects −log₁₀(adjusted ", False, False),
    ("p", False, True),
    ("-value); only terms with adjusted ", False, False),
    ("p", False, True),
    (" < 0.05 are shown. (D–F) GO bubble plots for pairwise-shared sectors "
     "(Gallus–Anas, Gallus–Columba, Anas–Columba); bubble area is proportional to the number "
     "of proteins in the term and color reflects significance. The ", False, False),
    ("G. gallus", False, True),
    ("-exclusive set is significantly enriched for protein N-linked glycosylation (BP), "
     "motivating the cross-species glycoproteomics analysis. GO enrichment was performed with "
     "the R package ", False, False),
    ("clusterProfiler", False, True),
    (" (v4.x); ", False, False),
    ("p", False, True),
    ("-values were corrected by the Benjamini–Hochberg method.", False, False),
])

doc.add_page_break()

# ── Fig. S5 ───────────────────────────────────────────────────────────
add_image(FIG_BASE / "SuppFig5_CAFE5_Gene_Family_Turnover" / "Fig_cafe5_expansion_contraction.png",
          width_cm=14.0)
fig_title("Fig. S5.",
          "Gene-family expansion and contraction inferred by CAFE5 across the three species.")
fig_caption([
    ("Phylogenetic tree annotated with lineage-specific gene-family expansion (red) and "
     "contraction (blue) events inferred by CAFE5 using the species divergence time tree. "
     "Numbers at nodes indicate estimated ancestral gene-family size; numbers on branches "
     "indicate the net change. Only gene families with per-family Viterbi ", False, False),
    ("p", False, True),
    (" < 0.05 are shown. ", False, False),
    ("G. gallus", False, True),
    (" shows net contraction overall (enriched for immune-related functions); ", False, False),
    ("C. livia", False, True),
    (" shows net expansion (enriched for transmembrane transport and synaptic processes); "
     "", False, False),
    ("A. platyrhynchos", False, True),
    (" is intermediate. Core eggshell matrix gene families are broadly conserved "
     "across all three lineages.", False, False),
])

doc.add_page_break()

# ── Fig. S6 ───────────────────────────────────────────────────────────
add_image(FIG_BASE / "SuppFig6_Mammilla_Microstructure" / "Fig_mammilla_microstructure_panels.png",
          width_cm=15.5)
fig_title("Fig. S6.",
          "Micro-CT cross-sectional and top-view panels of the mammillary layer "
          "in the three focal species.")
fig_caption([
    ("Representative micro-CT images of eggshell sections from ", False, False),
    ("G. gallus", False, True),
    (" (chicken), ", False, False),
    ("A. platyrhynchos", False, True),
    (" (duck), and ", False, False),
    ("C. livia", False, True),
    (" (pigeon). Top row: transverse cross-sections showing the full mammillary-layer "
     "thickness. Bottom row: en face (inner-surface) reconstructions showing the "
     "spatial arrangement of mammillary knobs. Scale bars are indicated in each panel. "
     "Images were acquired at 10-µm isotropic voxel resolution. 3D reconstructions were "
     "produced in 3D Slicer using threshold segmentation, 5 × 5 × 5 median filtering, "
     "and largest-island retention.", False, False),
])

doc.add_page_break()

# ── Fig. S7 ───────────────────────────────────────────────────────────
add_image(FIG_BASE / "SuppFig7_Glycosylation_Hotspot" / "Fig_hotspot_ensemble_1.png",
          width_cm=15.5)
fig_title("Fig. S7.",
          "Re-Glyco ensemble analysis of OVAL glycan geometry and "
          "apo-versus-glycosylated comparison.")
fig_caption([
    ("(A) Glycan radius of gyration (R", False, False),
    ("g", False, False),
    (") distributions across conformational ensemble replicates for the three "
     "species-specific OVAL–glycan complexes (", False, False),
    ("G. gallus", False, True),
    (" orange; ", False, False),
    ("A. platyrhynchos", False, True),
    (" blue; ", False, False),
    ("C. livia", False, True),
    (" green). (B) Glycan end-to-end distance distributions for the same complexes. "
     "(C) Per-conformation Ca²⁺ hotspot count (", False, False),
    ("N", False, True),
    ("hot", False, False),
    (") comparing the glycosylated and apo (deglycosylated) OVAL structures for each "
     "species. ", False, False),
    ("C. livia", False, True),
    (" occupies the largest conformational space and exhibits the most extensive glycan "
     "shielding; ", False, False),
    ("G. gallus", False, True),
    (" shows the smallest conformational envelope and least shielding; ", False, False),
    ("A. platyrhynchos", False, True),
    (" is intermediate. Apo structures serve as an internal control: removing N-glycans "
     "collapses the cross-species separation in hotspot count and surface electrostatics, "
     "confirming that the ordered signal originates from the glycan layer rather than the "
     "protein scaffold. Species differences in hotspot count and hotspot SASA were assessed "
     "by one-way ANOVA followed by Tukey post hoc test.", False, False),
])

doc.add_page_break()

# ── Fig. S8 ───────────────────────────────────────────────────────────
add_images_row([
    FIG_BASE / "SuppFig8_FEA_Force_Analysis" / "chicken_rcforc_3x3.png",
    FIG_BASE / "SuppFig8_FEA_Force_Analysis" / "chicken_rcforc_yforce.png",
], width_cm=7.5)
add_images_row([
    FIG_BASE / "SuppFig8_FEA_Force_Analysis" / "duck_rcforc_3x3.png",
    FIG_BASE / "SuppFig8_FEA_Force_Analysis" / "duck_rcforc_yforce.png",
], width_cm=7.5)
add_images_row([
    FIG_BASE / "SuppFig8_FEA_Force_Analysis" / "pigeon_rcforc_3x3.png",
    FIG_BASE / "SuppFig8_FEA_Force_Analysis" / "pigeon_rcforc_yforce.png",
], width_cm=7.5)
fig_title("Fig. S8.",
          "Per-species finite-element reaction-force time courses across all nine "
          "offset positions.")
fig_caption([
    ("Left column (A, C, E): contact force (", False, False),
    ("F", False, True),
    (") time-course curves for all nine parametric impact positions (3 × 3 lateral-offset "
     "grid, 0.5-mm spacing) for ", False, False),
    ("G. gallus", False, True),
    (" (A), ", False, False),
    ("A. platyrhynchos", False, True),
    (" (C), and ", False, False),
    ("C. livia", False, True),
    (" (E). Each curve represents one simulation from contact onset to peak force. "
     "Right column (B, D, F): corresponding Y-direction reaction-force (", False, False),
    ("F", False, True),
    ("Y", False, False),
    (") time courses. Species means ± s.d. of peak contact force (", False, False),
    ("F", False, True),
    ("max", False, False),
    (") and peak contact shear stress (τ", False, False),
    ("max", False, False),
    (") computed from these nine replicates per species are reported in the main text and "
     "Fig. 6. Simulations used explicit dynamic FEA (LS-DYNA, Ansys); eggshell thicknesses "
     "were set to species-specific values measured from micro-CT reconstructions.", False, False),
])

# ════════════════════════════════════════════════════════════════════
# 保存
# ════════════════════════════════════════════════════════════════════
doc.save(OUT)
print(f"Saved → {OUT}")


from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from pathlib import Path

FIG_BASE = Path(r"D:\system_folder\Desktop\Work On\Supplementary\Figures")

OUT = str(Path(__file__).with_name("supplementary_materials_en.docx"))

doc = Document()

# ── 页面 ─────────────────────────────────────────────────────────────────
s = doc.sections[0]
s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Cm(2.54)
s.page_width  = Cm(21.0)
s.page_height = Cm(29.7)

FONT = "Times New Roman"

def _set_font(rPr, name):
    rFonts = OxmlElement("w:rFonts")
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rFonts.set(qn(attr), name)
    rPr.insert(0, rFonts)

def fmt(run, size=11, bold=False, italic=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    rPr = run._r.get_or_add_rPr()
    _set_font(rPr, FONT)

def spacing(p, before=0, after=120, line=24):
    pPr = p._p.get_or_add_pPr()
    e = OxmlElement("w:spacing")
    e.set(qn("w:before"),   str(before))
    e.set(qn("w:after"),    str(after))
    e.set(qn("w:line"),     str(line * 20))
    e.set(qn("w:lineRule"), "auto")
    pPr.append(e)

def keep_with_next(p):
    pPr = p._p.get_or_add_pPr()
    e = OxmlElement("w:keepNext")
    pPr.append(e)

def para(text, bold=False, italic=False, size=11,
         before=0, after=120, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    spacing(p, before=before, after=after)
    r = p.add_run(text)
    fmt(r, size=size, bold=bold, italic=italic)
    return p

def fig_legend(label, title):
    """
    label: e.g. "Fig. S1."
    title: bold title text (after label)
    """
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    spacing(p, before=200, after=120)
    keep_with_next(p)
    # Label + title — all bold
    r_label = p.add_run(label + " ")
    fmt(r_label, bold=True)
    r_title = p.add_run(title)
    fmt(r_title, bold=True)
    return p

def fig_caption(parts, before=0, after=200):
    """parts = [(text, bold, italic), ...]"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    spacing(p, before=before, after=after)
    for text, bold, italic in parts:
        r = p.add_run(text)
        fmt(r, bold=bold, italic=italic)
    return p

def add_image(img_path, width_cm=15.5):
    """插入居中图片段落"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    spacing(p, before=60, after=60, line=12)
    run = p.add_run()
    run.add_picture(str(img_path), width=Cm(width_cm))
    return p

def add_images_row(img_paths, width_cm=7.5):
    """在同一段落中并排插入多张图片"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    spacing(p, before=60, after=60, line=12)
    for i, ip in enumerate(img_paths):
        run = p.add_run()
        run.add_picture(str(ip), width=Cm(width_cm))
        if i < len(img_paths) - 1:
            p.add_run("  ")
    return p

# ════════════════════════════════════════════════════════════════════
# COVER / HEADER
# ════════════════════════════════════════════════════════════════════
para("Supplementary Materials", bold=True, size=14,
     before=0, after=240, align=WD_ALIGN_PARAGRAPH.CENTER)

para(
    "Glycan-state divergence in matrix proteins links to avian eggshell structure "
    "and biomineralization",
    bold=False, italic=True, size=11, before=0, after=360,
    align=WD_ALIGN_PARAGRAPH.CENTER
)

para("Contents", bold=True, size=11, before=0, after=60,
     align=WD_ALIGN_PARAGRAPH.LEFT)
for line in [
    "Supplementary Text 1.  Species selection and sensitivity analysis",
    "Supplementary Text 2.  Eggshell matrix proteome orthogroup analysis",
    "",
    "Fig. S1.  Sensitivity analysis validating the macroecological species-selection framework",
    "Fig. S2.  Three-species Venn diagram of shared and lineage-restricted eggshell matrix orthogroups",
    "Fig. S3.  Maximum-likelihood phylogenetic tree of the three focal species",
    "Fig. S4.  GO enrichment and gene-family turnover across species-specific and pairwise eggshell matrix protein sets",
    "Fig. S5.  CAFE5 gene-family expansion and contraction across the three species",
    "Fig. S6.  Micro-CT cross-sectional and top-view panels of the mammillary layer",
    "Fig. S7.  Re-Glyco ensemble analysis of OVAL glycan geometry and apo-versus-glycosylated comparison",
    "Fig. S8.  Per-species finite-element reaction-force time courses across all nine offset positions",
]:
    para(line, bold=False, size=11, before=0, after=40, align=WD_ALIGN_PARAGRAPH.LEFT)

doc.add_page_break()

# ════════════════════════════════════════════════════════════════════
# SUPPLEMENTARY TEXT
# ════════════════════════════════════════════════════════════════════
para("Supplementary Text", bold=True, size=12,
     before=0, after=240, align=WD_ALIGN_PARAGRAPH.LEFT)

# ── ST1: Species selection ──────────────────────────────────────────
para("Supplementary Text 1. Species selection and sensitivity analysis.",
     bold=True, size=11, before=0, after=60, align=WD_ALIGN_PARAGRAPH.LEFT)

fig_caption([
    ("Principal component analysis of AVONET ecological trait scores (Body Mass, Beak Length, "
     "Beak Width, Beak Depth, Tarsus Length, Wing Length, Kipps Distance, Hand-Wing Index, "
     "Tail Length; plus Primary Lifestyle, Habitat, Trophic Niche encoded numerically) "
     "separated ", False, False),
    ("Gallus gallus", False, True),
    (", ", False, False),
    ("Anas platyrhynchos", False, True),
    (", and ", False, False),
    ("Columba livia", False, True),
    (" into three distinct regions of avian ecological space, corresponding respectively to "
     "terrestrial ground-nesting precocial, semi-aquatic precocial, and elevated-nesting "
     "altricial life-history strategies. Species selection was therefore driven by the aim of "
     "spanning both the precocial–altricial and terrestrial–semi-aquatic comparison axes "
     "simultaneously, rather than by any single phylogenetic or morphological criterion. "
     "To verify that this selection was not an artefact of the numerical encoding scheme, "
     "500 randomized perturbation iterations were run in which all encoding weights were "
     "independently shifted within ±30% of their original values. Both variance explained "
     "and cluster silhouette scores remained tightly concentrated around their unperturbed "
     "baseline values across all 500 iterations (Fig. S1), confirming that the "
     "three-species framework is robust to the subjective encoding component.", False, False),
])

# ── ST2: Proteome background ────────────────────────────────────────
para("Supplementary Text 2. Eggshell matrix proteome orthogroup analysis.",
     bold=True, size=11, before=240, after=60, align=WD_ALIGN_PARAGRAPH.LEFT)

fig_caption([
    ("Proteomics-identified eggshell matrix proteins were organized with an OrthoFinder-based "
     "orthology workflow into 2,620, 2,921, and 3,219 orthogroups in ", False, False),
    ("G. gallus", False, True),
    (", ", False, False),
    ("A. platyrhynchos", False, True),
    (", and ", False, False),
    ("C. livia", False, True),
    (", respectively (Fig. S2). Using all-versus-all protein similarity relationships and "
     "graph-based clustering, the workflow resolved 1,997 orthogroups shared across all three "
     "species and constituted the conserved eggshell matrix-protein core. Pairwise-shared "
     "but not universally shared orthogroup counts were 180 (", False, False),
    ("G. gallus", False, True),
    ("–", False, False),
    ("A. platyrhynchos", False, True),
    ("), 434 (", False, False),
    ("G. gallus", False, True),
    ("–", False, False),
    ("C. livia", False, True),
    ("), and 716 (", False, False),
    ("A. platyrhynchos", False, True),
    ("–", False, False),
    ("C. livia", False, True),
    ("). Lineage-restricted (species-exclusive) sets comprised 9, 28, and 72 orthogroups "
     "for chicken, duck, and pigeon, respectively.", False, False),
])

fig_caption([
    ("GO enrichment of pairwise-shared sets revealed functional stratification along "
     "ecological axes rather than simple phylogenetic proximity. The ", False, False),
    ("A. platyrhynchos", False, True),
    ("–", False, False),
    ("C. livia", False, True),
    ("-shared set—proteins present in both aquatic/semi-aquatic species but absent in "
     "chicken—was most significantly enriched for calcium-ion binding and metal-ion binding "
     "(MF; both ", False, False),
    ("p", False, True),
    (" < 10⁻²⁵), as well as Wnt signaling and signal transduction (BP). This calcium-binding "
     "co-enrichment in two lineages that rely on food or water-borne calcium sources, but not "
     "in chicken which can supplement soil calcium, reflects differential molecular strategies "
     "for environmental calcium acquisition. The ", False, False),
    ("G. gallus", False, True),
    ("–", False, False),
    ("A. platyrhynchos", False, True),
    ("-shared set (two precocial Galloanserae, absent in altricial pigeon) was enriched for "
     "adaptive immune response and spermatogenesis (BP), consistent with precocial "
     "reproductive programs.", False, False),
])

fig_caption([
    ("Lineage-restricted GO signals further sharpened the cross-species contrast. The ", False, False),
    ("G. gallus", False, True),
    ("-exclusive set (9 orthogroups) was significantly enriched for protein N-linked "
     "glycosylation (BP), indicating that glycan-processing capacity represents a chicken-specific "
     "functional expansion absent from the other two proteomes. The ", False, False),
    ("A. platyrhynchos", False, True),
    ("-exclusive set (", False, False),
    ("n", False, True),
    (" = 28) was primarily enriched for immune response regulation, B-cell activation, and iron "
     "response—consistent with higher pathogen exposure and mineral metabolism demands associated "
     "with aquatic foraging. The ", False, False),
    ("C. livia", False, True),
    ("-exclusive set (", False, False),
    ("n", False, True),
    (" = 72, the largest lineage-restricted pool) was enriched for nervous system development, "
     "ubiquitin-dependent protein catabolism, and proteolysis, reflecting the developmental "
     "complexity required for rapid organ maturation in an altricial hatchling.", False, False),
])

fig_caption([
    ("Gene-family expansion and contraction analysis (CAFE5), applied to orthogroup family sizes "
     "together with the species divergence-time tree, further indicated asymmetric "
     "lineage divergence: ", False, False),
    ("G. gallus", False, True),
    (" showed net family contraction overall, ", False, False),
    ("A. platyrhynchos", False, True),
    (" was intermediate, and ", False, False),
    ("C. livia", False, True),
    (" showed net expansion (Fig. S5). Contracted families in chicken were enriched for "
     "immune-related functions; expanded families in pigeon were enriched for transmembrane "
     "transport, Rho signaling, and synapse-related processes. Together, these proteome-level "
     "patterns confirmed broad evolutionary divergence among the three eggshell formation "
     "systems, while simultaneously highlighting that the core shared toolkit was conserved "
     "and that N-linked glycosylation was a chicken-specific elaboration—the observation that "
     "focused the subsequent comparative analysis on glycan-state differences at the "
     "modification rather than the protein-presence level.", False, False),
])

doc.add_page_break()
fig_legend(
    "Fig. S1.",
    "Sensitivity analysis validating the macroecological species-selection framework."
)
add_image(FIG_BASE / "SuppFig1_Species_Selection" / "Sensitivity_Analysis_Results.png", width_cm=15.5)
fig_caption([
    ("Distribution of variance explained (R²) and cluster silhouette coefficients from "
     "500 randomized perturbation iterations applied to the AVONET-based principal-component "
     "space used to select ", False, False),
    ("Gallus gallus", False, True),
    (", ", False, False),
    ("Anas platyrhynchos", False, True),
    (", and ", False, False),
    ("Columba livia", False, True),
    (" as focal species. Categorical ecological variables (Primary Lifestyle, Habitat, "
     "Trophic Niche) were numerically encoded; each iteration introduced independent random "
     "shifts to all encoding weights within ±30% of the original values. The high concentration "
     "of both metrics around the baseline values indicates that species-group assignments are "
     "robust and not sensitive to the subjective component of the numerical coding scheme.", False, False),
])

# ════════════════════════════════════════════════════════════════════
# Fig. S2
# ════════════════════════════════════════════════════════════════════
doc.add_page_break()
fig_legend(
    "Fig. S2.",
    "Three-species Venn diagram of shared and lineage-restricted eggshell matrix orthogroups."
)
add_image(FIG_BASE / "SuppFig2_Venn_Orthogroups" / "Fig_venn_orthogroups.png", width_cm=12.0)
fig_caption([
    ("OrthoFinder-based orthogroup clustering of the detected eggshell matrix proteomes. "
     "Following all-versus-all protein similarity comparison and graph-based clustering, "
     "the diagram partitions detected orthogroups into a large three-species shared core, "
     "three pairwise-shared sectors, and three lineage-restricted sectors. Numbers indicate "
     "orthogroup counts in each sector. This partition is the basis for the comparative "
     "framing described in the main text.", False, False),
])

# ════════════════════════════════════════════════════════════════════
# Fig. S3
# ════════════════════════════════════════════════════════════════════
doc.add_page_break()
fig_legend(
    "Fig. S3.",
    "Maximum-likelihood phylogenetic tree of the three focal species reconstructed from single-copy orthologs."
)
add_image(FIG_BASE / "SuppFig3_Phylo_Tree" / "Fig_phylo_tree.png", width_cm=14.0)
fig_caption([
    ("Maximum-likelihood species tree reconstructed from the single-copy ortholog set returned "
     "by the orthology workflow. Single-copy orthologous protein sequences were aligned and "
     "used to infer the species relationships shown here. Branch lengths reflect substitutions "
     "per site. Node support values (1000 replicates) are indicated at internal nodes. "
     "The tree topology is consistent with published avian phylogenies and confirms the "
     "expected relatedness ordering (Galliformes and Anseriformes as sister clades within "
     "Galloanseres, Columbiformes as the more distant outgroup) used to frame the comparative "
     "analysis.", False, False),
])

# ════════════════════════════════════════════════════════════════════
# Fig. S4
# ════════════════════════════════════════════════════════════════════
doc.add_page_break()
fig_legend(
    "Fig. S4.",
    "GO enrichment and gene-family turnover across species-specific and pairwise eggshell matrix protein sets."
)
add_image(FIG_BASE / "SuppFig4_GO_Enrichment" / "Fig_GO_heatmap_single_species.png", width_cm=15.5)
add_image(FIG_BASE / "SuppFig4_GO_Enrichment" / "Fig_GO_bubble_pairwise_combined.png", width_cm=15.5)
add_image(FIG_BASE / "SuppFig4_GO_Enrichment" / "Legend_GO_Category.png", width_cm=10.0)
fig_caption([
    ("(A–C) Gene Ontology (GO) enrichment heatmap for biological process (BP) and molecular "
     "function (MF) categories across the three lineage-restricted protein sets (", False, False),
    ("G. gallus", False, True),
    (", ", False, False),
    ("A. platyrhynchos", False, True),
    (", ", False, False),
    ("C. livia", False, True),
    ("). Color intensity reflects −log₁₀(adjusted ", False, False),
    ("p", False, True),
    ("-value); only terms with adjusted ", False, False),
    ("p", False, True),
    (" < 0.05 are shown. (D–F) GO bubble plots for the three pairwise-shared sectors "
     "(Gallus–Anas, Gallus–Columba, Anas–Columba), with bubble area proportional to the "
     "number of proteins in the term and color reflecting statistical significance. "
     "The ", False, False),
    ("G. gallus", False, True),
    ("-exclusive set was significantly enriched for protein N-linked glycosylation (BP), "
     "providing the direct motivation for cross-species glycoproteomics. Immune and "
     "defense-related GO terms were differentially distributed across lineages. GO terms from "
     "the lineage-restricted and pairwise-shared orthogroup sectors were summarized as the "
     "heatmap and bubble plots shown here.", False, False),
])

# ════════════════════════════════════════════════════════════════════
# Fig. S5
# ════════════════════════════════════════════════════════════════════
doc.add_page_break()
fig_legend(
    "Fig. S5.",
    "CAFE5 gene-family expansion and contraction across the three species."
)
add_image(FIG_BASE / "SuppFig5_CAFE5_Gene_Family_Turnover" / "Fig_cafe5_expansion_contraction.png", width_cm=14.0)
fig_caption([
    ("Phylogenetic tree annotated with lineage-specific gene-family expansion (red) and "
     "contraction (blue) events inferred by CAFE5 using the species divergence time tree. "
     "Numbers at nodes indicate the estimated ancestral gene-family size; numbers on branches "
     "indicate the net change. Only gene families with a per-family ", False, False),
    ("p", False, True),
    (" < 0.05 (Viterbi ", False, False),
    ("p", False, True),
    ("-value) are shown. The pattern is consistent with the GO enrichment results: lineages "
     "differed in the turnover of immune and defense-related gene families, while core "
     "eggshell matrix families were broadly conserved.", False, False),
])

# ════════════════════════════════════════════════════════════════════
# Fig. S6
# ════════════════════════════════════════════════════════════════════
doc.add_page_break()
fig_legend(
    "Fig. S6.",
    "Micro-CT cross-sectional and top-view panels of the mammillary layer in the three focal species."
)
add_image(FIG_BASE / "SuppFig6_Mammilla_Microstructure" / "Fig_mammilla_microstructure_panels.png", width_cm=15.5)
fig_caption([
    ("Representative micro-CT images of eggshell sections from ", False, False),
    ("G. gallus", False, True),
    (" (chicken), ", False, False),
    ("A. platyrhynchos", False, True),
    (" (duck), and ", False, False),
    ("C. livia", False, True),
    (" (pigeon). Top row: cross-sectional views showing the full thickness of the "
     "mammillary layer. Bottom row: top-view (inner-surface) reconstructions showing the "
     "spatial arrangement of mammillary knobs. Scale bars are indicated in each panel. "
     "Images were acquired at 10-µm isotropic voxel resolution; 3D reconstruction was "
     "performed in 3D Slicer with threshold segmentation, median filtering (5 × 5 × 5 "
     "kernel), and largest-island retention.", False, False),
])

# ════════════════════════════════════════════════════════════════════
# Fig. S7
# ════════════════════════════════════════════════════════════════════
doc.add_page_break()
fig_legend(
    "Fig. S7.",
    "Re-Glyco ensemble analysis of OVAL glycan geometry and apo-versus-glycosylated comparison."
)
add_image(FIG_BASE / "SuppFig7_Glycosylation_Hotspot" / "Fig_hotspot_ensemble_1.png", width_cm=15.5)
fig_caption([
    ("(A) Distribution of glycan radius of gyration (R", False, False),
    ("g", False, False),
    (") across conformational ensemble replicates for the three species-specific "
     "OVAL–glycan complexes, colored by species (", False, False),
    ("G. gallus", False, True),
    (" orange, ", False, False),
    ("A. platyrhynchos", False, True),
    (" blue, ", False, False),
    ("C. livia", False, True),
    (" green). (B) Glycan end-to-end distance distributions across conformations for the "
     "same three complexes. (C) Per-conformation Ca²⁺ hotspot count (N", False, False),
    ("hot", False, False),
    (") comparing the glycosylated and apo (deglycosylated) OVAL structures for each "
     "species. ", False, False),
    ("C. livia", False, True),
    (" showed the largest conformational space and the most extensive glycan shielding; "
     "", False, False),
    ("G. gallus", False, True),
    (" showed the smallest conformational space and the least shielding; "
     "", False, False),
    ("A. platyrhynchos", False, True),
    (" was intermediate. The apo comparison serves as an internal control: once N-glycans "
     "were removed, cross-species separation in hotspot count and electrostatic surface "
     "potential largely collapsed, confirming that the divergence detected in the glycosylated "
     "states arises from the glycan layer rather than from the protein scaffold alone. "
     "Species differences in hotspot and SASA metrics were assessed by one-way ANOVA "
     "followed by Tukey post hoc test.", False, False),
])

# ════════════════════════════════════════════════════════════════════
# Fig. S8
# ════════════════════════════════════════════════════════════════════
doc.add_page_break()
fig_legend(
    "Fig. S8.",
    "Per-species finite-element reaction-force time courses across all nine offset positions."
)
add_images_row([
    FIG_BASE / "SuppFig8_FEA_Force_Analysis" / "chicken_rcforc_3x3.png",
    FIG_BASE / "SuppFig8_FEA_Force_Analysis" / "chicken_rcforc_yforce.png",
], width_cm=7.5)
add_images_row([
    FIG_BASE / "SuppFig8_FEA_Force_Analysis" / "duck_rcforc_3x3.png",
    FIG_BASE / "SuppFig8_FEA_Force_Analysis" / "duck_rcforc_yforce.png",
], width_cm=7.5)
add_images_row([
    FIG_BASE / "SuppFig8_FEA_Force_Analysis" / "pigeon_rcforc_3x3.png",
    FIG_BASE / "SuppFig8_FEA_Force_Analysis" / "pigeon_rcforc_yforce.png",
], width_cm=7.5)
fig_caption([
    ("(A–C) Contact force (", False, False),
    ("F", False, True),
    (") time-course curves for all nine parametric impact positions (3 × 3 lateral offset "
     "grid) for ", False, False),
    ("G. gallus", False, True),
    (" (A), ", False, False),
    ("A. platyrhynchos", False, True),
    (" (B), and ", False, False),
    ("C. livia", False, True),
    (" (C). Each curve represents one simulation; curves are shown from the onset of "
     "contact to peak force. Insets show the peak contact force (", False, False),
    ("F", False, True),
    ("max", False, False),
    (") distribution across the nine positions for each species. (D–F) Corresponding "
     "Y-direction reaction-force (", False, False),
    ("F", False, True),
    ("Y", False, False),
    (") time courses. Species means ± s.d. of ", False, False),
    ("F", False, True),
    ("max", False, False),
    (" and peak shear stress (τ", False, False),
    ("max", False, False),
    (") computed from these nine replicates per species are reported in the main text and "
     "Fig. 6. Simulations were run in LS-DYNA (Ansys) using explicit dynamic finite-element "
     "analysis; eggshell thicknesses were set to species-specific values measured from "
     "micro-CT.", False, False),
])

# ════════════════════════════════════════════════════════════════════
# 保存
# ════════════════════════════════════════════════════════════════════
doc.save(OUT)
print(f"Saved → {OUT}")
