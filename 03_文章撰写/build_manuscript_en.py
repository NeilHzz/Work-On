"""
Science Advances 格式 — 英文版
manuscript_results_sa.docx
"""

from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from pathlib import Path
import re
from shared_references import REFS

OUT = str(Path(__file__).with_name("manuscript260602v2.docx"))
FIG_BASE = Path(__file__).resolve().parent.parent / "02_可视化" / "260601" / "02_main_composed_figures"

REF_TEXTS = {}
for ref_text in REFS:
    match = re.match(r"^(\d+)\.\s+(.*)$", ref_text)
    if not match:
        raise ValueError(f"Invalid reference entry: {ref_text}")
    REF_TEXTS[int(match.group(1))] = match.group(2)

CITATION_ORDER = []
CITATION_MAP = {}

doc = Document()

# ── 页面 ─────────────────────────────────────────────────────────────────
s = doc.sections[0]
s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Cm(2.54)
s.page_width  = Cm(21.0)
s.page_height = Cm(29.7)

# ── 行号（连续，每页重置）
_lnNum = OxmlElement("w:lnNumType")
_lnNum.set(qn("w:countBy"), "1")
_lnNum.set(qn("w:restart"), "continuous")
_lnNum.set(qn("w:start"), "1")
s._sectPr.append(_lnNum)

# ── 辅助 ─────────────────────────────────────────────────────────────────
FONT = "Times New Roman"   # Science Advances: use universal fonts

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
    _set_font(rPr, FONT if not italic else "Times New Roman")

def spacing(p, before=0, after=120, line=24):
    """line in pt; double-spaced for Science Advances initial submission"""
    pPr = p._p.get_or_add_pPr()
    e = OxmlElement("w:spacing")
    e.set(qn("w:before"),   str(before))
    e.set(qn("w:after"),    str(after))
    e.set(qn("w:line"),     str(line * 20))
    e.set(qn("w:lineRule"), "auto")
    pPr.append(e)

def para(text, bold=False, italic=False, size=11,
         before=0, after=120, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    spacing(p, before=before, after=after)
    r = p.add_run(text)
    fmt(r, size=size, bold=bold, italic=italic)
    return p

def mixed(parts, before=0, after=120, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    """parts = [(text, bold, italic), ...]"""
    p = doc.add_paragraph()
    p.alignment = align
    spacing(p, before=before, after=after)
    for text, bold, italic in parts:
        r = p.add_run(text)
        fmt(r, bold=bold, italic=italic)
    return p

def head(text, size=11):
    """Bold subheading — no terminal period, sentence case"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    spacing(p, before=240, after=60)
    r = p.add_run(text)
    fmt(r, size=size, bold=True)
    return p

def headm(parts, size=11):
    """Bold subheading with mixed italic support. parts = [(text, italic), ...]"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    spacing(p, before=240, after=60)
    for text, italic in parts:
        r = p.add_run(text)
        fmt(r, size=size, bold=True, italic=italic)
    return p

def _citation_text(numbers):
    if not numbers:
        return ""
    mapped_numbers = []
    for number in numbers:
        if number not in REF_TEXTS:
            raise KeyError(f"Reference {number} not found in REFS")
        if number not in CITATION_MAP:
            CITATION_MAP[number] = len(CITATION_ORDER) + 1
            CITATION_ORDER.append(number)
        mapped_numbers.append(CITATION_MAP[number])
    sn = sorted(set(mapped_numbers))
    groups = []
    i = 0
    while i < len(sn):
        j = i
        while j + 1 < len(sn) and sn[j + 1] == sn[j] + 1:
            j += 1
        if j - i >= 2:
            groups.append(f"{sn[i]}\u2013{sn[j]}")
        elif j - i == 1:
            groups.append(f"{sn[i]}, {sn[j]}")
        else:
            groups.append(str(sn[i]))
        i = j + 1
    return " (" + ", ".join(groups) + ")"

def _add_citation_run(p, numbers):
    citation_text = _citation_text(numbers)
    if not citation_text:
        return
    r = p.add_run(citation_text)
    fmt(r, size=11)
    rPr = r._r.get_or_add_rPr()
    _set_font(rPr, FONT)

def spara(sentences, before=0, after=120, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    spacing(p, before=before, after=after)
    for text, numbers in sentences:
        r = p.add_run(text)
        fmt(r, size=11)
        _add_citation_run(p, numbers)
    return p

def smixed(sentences, before=0, after=120, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    p.alignment = align
    spacing(p, before=before, after=after)
    for parts, numbers in sentences:
        for text, bold, italic in parts:
            r = p.add_run(text)
            fmt(r, bold=bold, italic=italic)
        _add_citation_run(p, numbers)
    return p

def cite(p, numbers):
    _add_citation_run(p, numbers)

def add_centered_figure(image_name, width_cm, before=120, after=60):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    spacing(p, before=before, after=after, line=12)
    r = p.add_run()
    r.add_picture(str(FIG_BASE / image_name), width=Cm(width_cm))
    return p

def add_main_figure_legend(label, title, caption_parts, before=0, after=160):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    spacing(p, before=before, after=after)
    r = p.add_run(label + " ")
    fmt(r, bold=True)
    r = p.add_run(title + " ")
    fmt(r, bold=True)
    for text, bold, italic in caption_parts:
        r = p.add_run(text)
        fmt(r, bold=bold, italic=italic)
    return p

# ════════════════════════════════════════════════════════════════════════════
# Science Advances 必需元素：Title / Short title / Authors / Teaser
# ════════════════════════════════════════════════════════════════════════════

# Title (≤135 characters)
para(
    "Cross-species OVAL glycan states connect mammillary-layer organisation to local hatching resistance in avian eggshells",
    bold=True, size=14, before=0, after=160, align=WD_ALIGN_PARAGRAPH.LEFT
)

# Short title (≤50 characters)
para("OVAL glycans shape eggshell state",
     bold=False, size=11, after=60, align=WD_ALIGN_PARAGRAPH.LEFT)

para(
    "[Please add full author names, affiliations, ORCID identifiers, equal-contribution notes, and corresponding-author details before submission]",
    bold=False, size=10, before=80, after=80,
    align=WD_ALIGN_PARAGRAPH.LEFT
)

para("Abstract", bold=True, size=11, before=80, after=40,
     align=WD_ALIGN_PARAGRAPH.LEFT)

para(
    "Eggshell matrix proteins are key regulators of eggshell structural formation, but research has remained largely limited to protein inventories and posttranslational modification sites. Using matched multi-layer analyses, we asked how glycan states on conserved matrix proteins map onto cross-species shell divergence. "
    "We compared chicken, duck, and pigeon under a conserved egg-tooth interface by integrating micro-CT morphometry, eggshell-matrix proteomics, intact glycopeptide mass spectrometry, Re-Glyco structural modelling, electrostatic analysis, and finite-element simulation. "
    "Cross-species separation emerged first in mammillary-layer organisation, while the matrix-protein toolkit remained largely shared. "
    "Within that shared background, ovalbumin (OVAL) shifted from High Mannose-dominant glycans in chicken to Neutral Complex/Hybrid-dominant glycans in duck and Sialylated Complex/Hybrid-dominant glycans in pigeon. "
    "These glycan states predicted progressively stronger shielding of the Ca²⁺-relevant OVAL surface and were mirrored by a chicken-high versus duck/pigeon-low contrast in local hatching resistance. "
    "Together, the data identify OVAL glycan state as a molecular layer linking a chicken-like eggshell state to mammillary organisation and inside-out failure behaviour.",
    bold=False, size=10, before=0, after=80, align=WD_ALIGN_PARAGRAPH.JUSTIFY
)

# Teaser (≤125 characters, one sentence for non-specialist readers)
para(
    "Teaser: Cross-species OVAL glycan states expose a molecular axis behind chicken-like eggshell resistance.",
    bold=False, italic=True, size=10, before=80, after=160, align=WD_ALIGN_PARAGRAPH.LEFT
)

# ════════════════════════════════════════════════════════════════════════════
# Introduction
# ════════════════════════════════════════════════════════════════════════════
para("Introduction", bold=True, size=14, before=0, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT)

# §1 — Background value
p_s1a = spara([
    (" Bird hatching is a local failure event: the egg-tooth pushes on the inner shell surface rather than spreading force across the shell as a whole.", [16, 86]),
    (" Comparable hatching-assist structures recur across egg-laying amniotes, so biologically meaningful variation in hatching performance is more likely to lie in the shell than in the tool itself.", [16, 82, 83, 84, 85]),
    (" Yet current knowledge remains limited on how species with similar hatching mechanics produce distinct shell states across ecology and development.", [15, 26, 39, 40, 41]),
    (" The mammillary layer is the key entry point because it is the first mechanically consequential shell layer and the site where matrix-guided calcite growth begins. The mechanistic question follows directly: once the shell-breaking interface is held constant, which molecular regulators at the mammillary layer account for the distinct eggshell states recovered across species?", [1, 2, 4, 16, 28, 57]),
])

# §2 — Prior work and its limits
p_intro2 = spara([
    (" Eggshell matrix proteins regulate mammillary-layer mineralization, crystal growth, and mature shell architecture, and recurrent factors such as OC17, OC116, TRFE, and OVAL define a shared shell-building toolkit.", [1, 2, 4, 10, 19, 21, 29]),
    (" The unresolved issue is not toolkit presence, but how that toolkit is deployed across species.", [1, 2, 4]),
    (" This gap is sharpest for posttranslational modification. Phosphorylation and glycosylation sites are both catalogued, but phosphate side groups are comparatively similar whereas glycans vary widely in composition, size, and charge and can generate distinct molecular states on the same protein scaffold.", [17, 18, 21, 49, 50, 80]),
    (" Glycan class is therefore a mechanistic variable, not just a feature of site occupancy.", [49, 50]),
    (" Glycoproteomic studies have shown that eggshell matrix proteins carry distinct N-glycosylation states, including glycosylated Asn in OC116 and defined OVAL-associated glycan compositions, but most analyses remained within one species, one compartment, or one site inventory at a time.", [7, 8, 18, 21, 47, 48]),
    (" As a result, avian eggshell comparisons still rarely resolve matched glycan states on shared matrix proteins across species, leaving open whether that glycan layer explains why similar toolkits yield distinct shell states.", [2, 4, 18, 29, 66]),
])

p_intro_sig = spara([
    (" Glycosylation can alter protein stability, molecular recognition, and surface accessibility, and in other systems glycans act as dynamic shields that reshape accessible interfaces.", [42, 43, 44, 61, 63, 72, 78, 81]),
    (" Layer-resolved eggshell work further showed that the same matrix protein can occupy different N-glycosylation states across shell compartments, implying that glycan state may redistribute function rather than merely decorate a fixed scaffold.", [18]),
    (" OVAL was therefore a tractable test case because it is abundant, mineralization-relevant, and linked to Ca²⁺-responsive conformational behaviour during early shell formation.", [4, 11, 18, 29]),
    (" We anchored the comparison to the conserved egg-tooth interface and asked whether glycan-state differences on shared matrix proteins generate different Ca²⁺-accessible surfaces at mineralization onset.", [4, 16, 18]),
])

p_intro_gap = spara([
    (" The missing step is a direct bridge from glycan class to surface presentation on a shared matrix background, and OVAL provided that bridge because its dominant glycan classes could be followed from glycoproteomics into structural modelling.", [4, 18, 29, 42]),
])

# §4 — This study
p_intro4 = smixed([
    ([('Here, we compared ', False, False),
      ('Gallus gallus', False, True),
      (', ', False, False),
      ('Anas platyrhynchos', False, True),
      (', and ', False, False),
      ('Columba livia', False, True),
                        ('.', False, False)], []),
    ([(' We established an integrated approach that combines micro-CT morphometry, comparative proteomics, intact glycopeptide mass spectrometry, Re-Glyco modelling with electrostatic analysis, and finite-element simulation for cross-scale analysis of eggshell structure, glycan state, and hatching mechanics.', False, False)], []),
    ([(' Our analyses reveal that mammillary-layer organisation separates the species before the broader matrix-protein toolkit does, and that OVAL glycan state is the strongest signal linking molecular state to surface accessibility and local hatching resistance.', False, False)], []),
    ([(' Together, these findings establish a framework for connecting glycan-state variation to eggshell organisation and inside-out failure behaviour across birds.', False, False)], []),
])

# ═══════════════════════════════════════════════════════════════════════════
# "Results" section label
# ═══════════════════════════════════════════════════════════════════════════
para("Results", bold=True, size=14, before=320, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT)
# ════════════════════════════════════════════════════════════════════════════
# § Species selection — ecological and developmental niche analysis
# ════════════════════════════════════════════════════════════════════════════
head("The conserved hatching interface constrains shell variation")

p_ss1 = smixed([
    ([(' We placed extant birds into a comparative space using 10,993 AVONET species records and selected three deliberately separated model species from that space (Fig. 1A).', False, False)], [16, 22, 41]),
    ([(' This broader mapping prioritized two egg-relevant axes least likely to be secondary: nesting environment and offspring developmental state. Those axes span terrestrial-to-aquatic habitat use and a continuum from more precocial to more altricial young.', False, False)], [15, 22, 23]),
        ([(' Within this comparison space, ', False, False),
            ('Gallus gallus', False, True),
            (', ', False, False),
            ('Anas platyrhynchos', False, True),
            (', and ', False, False),
            ('Columba livia', False, True),
                (' were therefore chosen near contrasting regions of those ecological-developmental gradients, reducing blurring by intermediate combinations.', False, False)], [3, 22, 23, 41]),
    ([(' This functional grouping only partly overlaps with phylogeny. Chicken and duck remain closely related precocial taxa but separate along the habitat axis, whereas pigeon anchors the altricial end of the comparison (Fig. S2).', False, False)], [3, 22, 23]),
    ([(' The design keeps shared ancestry in view while still enforcing clear life-history separation within the same analytical frame.', False, False)], []),
    ([(' The focal species differed in beak-tip geometry, but the egg-tooth remained a similarly localized dorsal breaker in all three species and therefore pointed to the same inside-out shell-breaking event during hatching (Fig. 1B).', False, False)], [16, 37, 82, 86]),
    ([(' With that interface held constant, the next question is which eggshell layer first separates the species.', False, False)], []),
])

mixed([
    ("Viewed through that shared hatching context, the first eggshell level to show a clear contrast in the present comparison was mammillary-layer morphology (Fig. 1C). In ", False, False),
    ("G. gallus", False, True),
    (", mammillae were smoother overall and formed rounded projections. In ", False, False),
    ("A. platyrhynchos", False, True),
    (", mammillae showed more ridges and angular turns across the inner surface. ", False, False),
    ("C. livia", False, True),
    (" was dominated by discrete triangular-conical mammillae. Three-dimensional surface reconstructions agreed with the cross-sectional views, indicating that the sampled inner-shell regions differed in mammillary geometry rather than representing minor variants of a shared inner-surface template.", False, False),
])

p_s0b = mixed([
    ("Quantification resolved the sampled regions in two related but not identical ways (Fig. 1D). Mammillary knob density was highest in ", False, False),
    ("G. gallus", False, True),
    (" (171.36 ± 5.63 per mm²), exceeding both ", False, False),
    ("A. platyrhynchos", False, True),
    (" (155.22 ± 8.63 per mm²) and ", False, False),
    ("C. livia", False, True),
    (" (158.27 ± 11.39 per mm²), while duck and pigeon remained similar to each other. By contrast, crystal-unit proportion was highest in ", False, False),
    ("C. livia", False, True),
    (" (0.53 ± 0.04), intermediate in ", False, False),
    ("A. platyrhynchos", False, True),
    (" (0.44 ± 0.02), and lowest in ", False, False),
    ("G. gallus", False, True),
    (" (0.40 ± 0.01). Within this scanned-fragment comparison, chicken showed the highest local mammillary density, whereas pigeon devoted the largest share of shell volume to crystal units grown from individual mammillary knobs. Duck remained intermediate in crystal-unit proportion while resembling pigeon in density. The two metrics did not collapse into one monotonic axis, but together they indicated that a mammillary-level contrast was already detectable before later shell traits were considered. Because this layer is the earliest structural level linked to eggshell mechanics and matrix control, we then asked a narrower question: did the observed contrast reflect wholesale toolkit replacement or differential use of a largely shared system?", False, False),
])
cite(p_s0b, [1, 4, 28])

doc.add_page_break()
add_centered_figure("Fig1_composed.png", width_cm=10.1, before=0, after=20)
add_main_figure_legend(
    "Fig. 1.",
    "Comparative species space, hatching interface, and mammillary morphology in three model birds.",
    [
        ("(A) Three-dimensional AVONET comparison space built from 10,993 species records. Axes summarize aquatic association, lifestyle-habitat discordance, and developmental mode. Colors denote avian orders, and gray boxes indicate the sampled regions for ", False, False),
        ("Gallus gallus", False, True),
        (", ", False, False),
        ("Anas platyrhynchos", False, True),
        (", and ", False, False),
        ("Columba livia", False, True),
        (". (B) Lateral head views (top) and dorsal beak views (bottom) showing the egg-tooth-bearing tip in the three species. (C) Representative micro-CT sections and three-dimensional inner-surface reconstructions of the mammillary layer. Scale bars, 100 μm. (D) Box plots of mammillary density and unit-volume ratio across species. Points denote nine non-overlapping subfragments from one scanned fragment per species. P values were calculated by one-way ANOVA, and different letters indicate Tukey HSD groupings.", False, False),
    ],
    before=20,
    after=80,
)
doc.add_page_break()

p_sprot_bg = spara([
    ("Orthogroup analysis resolved the three eggshell matrix proteomes into a large shared core with smaller pairwise-shared and lineage-restricted complements (Fig. S3). At the overall level, the proteome still followed broad ancestry (Fig. S4), arguing against wholesale replacement of the eggshell-matrix toolkit.", []),
])

p_sprot_go = spara([
        (" The shared core therefore became the relevant comparison frame. The next question was whether the species separated through wholesale proteome turnover or through different glycan states on shared matrix proteins.", []),
])

p_sprot_focus = spara([
    (" The G. gallus-exclusive set was simultaneously enriched for protein N-linked glycosylation (BP; Fig. S5), shifting the comparison from protein presence to chemical deployment. The retained shared core thus became the relevant molecular background. Glycosylation on shared proteins emerged as a proximate candidate layer for explaining divergence in mammillary organisation and downstream shell behaviour.", [18]),
    (" Most recurrent eggshell matrix proteins emphasized in earlier studies were recovered in the broader proteomic and glycoproteomic background here, indicating substantial agreement with prior eggshell-matrix work. The present dataset also broadened that comparative background.", [1, 2, 4, 10, 19, 21, 29]),
])

head("OVAL glycosylation gives the clearest cross-species molecular contrast")

p_s2a = spara([
    ("Intact-glycopeptide profiling first showed that the three species differed in sampling depth yet still shared a stable comparison core (Fig. 2A to D). The cluster view recovered 25 clusters shared by all three species, with the largest additional pairwise overlap between duck and pigeon at 64 clusters, whereas chicken contributed little species-private cluster space (Fig. 2A).", []),
    ("The same asymmetry appeared in the catalog counts: duck yielded 321 glycoproteins, 547 glycosites, and 197 glycan compositions; pigeon yielded 192, 257, and 162; and chicken yielded 55, 88, and 105 (Fig. 2B). Shared-core Jensen-Shannon similarity nevertheless remained concentrated between 0.33 and 0.40, with the duck-pigeon pair highest (Fig. 2C). These values indicate divergence within a still comparable glycoproteomic background rather than three disconnected chemical spaces.", []),
    ("Glycan-class composition reinforced the same point at the chemical-deployment level. High-Mannose and Complex-Fucosylated glycans formed a broad cross-species background, whereas Complex-Sialylated and other more extended classes contributed more strongly to lineage separation (Fig. 2D).", []),
])

add_centered_figure("Fig2_composed.png", width_cm=14.6)
add_main_figure_legend(
    "Fig. 2.",
    "Shared-core glycoproteome architecture and glycan-class deployment across species.",
    [
        ("(A) Species-partitioned cluster counts in the glycoproteomic dataset. (B) Numbers of detected glycoproteins, glycosites, and glycan compositions in each species. (C) Shared-core Jensen-Shannon similarity among species. (D) Species-level distribution of glycan classes (High Mannose, Pauci-mannose, Hybrid, Complex-Plain, Complex-Fucosylated, Complex-Sialylated, and Other). (E) Ortholog-glycan chord map linking eggshell glycoproteins to dominant glycan classes in chicken, duck, and pigeon, with highlighted matrix proteins retained for downstream analyses.", False, False),
    ],
)

p_s2b = mixed([
    ("A stricter BlastP-based filter retained an orthologous glycoprotein subset suitable for structural comparison and summarized that shared candidate space in Fig. 2E. Using ", False, False),
    ("G. gallus", False, True),
    (" as the reference, non-reference candidates were retained only when the mean E-value was below 1 × 10⁻⁵ and sequence identity met the final comparability thresholds. This restricted the downstream comparison to high-confidence orthologs. Under that stricter mapping, OC17 was glycosylated only in chicken, whereas OC116, TRFE, and OVAL all retained glycosylation signals across the three species and served as shared anchors. Among them, OVAL showed a clear cross-species glycan shift and was prioritised for structural analysis.", False, False),
])
p_s2c = spara([
    ("Integrated protein and glycan abundance profiles further identified OVAL as the shared protein most closely aligned with the cross-species eggshell differences (Fig. 3A to C). Across the full dataset, protein-glycan coupling was weak in chicken but consistently positive in duck and pigeon, indicating lineage differences in how glycosylation scaled with protein output.", []),
    (" Among the highlighted eggshell-matrix proteins, OVAL remained abundant in all three species but differed sharply in glycan burden: relatively modest in chicken, stronger in duck, and strongest in pigeon. OC116 and TRFE remained informative shared proteins, but neither separated bulk protein abundance from glycan output as consistently as OVAL.", []),
    (" Pairwise enrichment plots then showed why OVAL remained the most interpretable discriminator (Fig. 3D to F). In the Gallus-versus-Anas and Gallus-versus-Columba planes, OVAL fell on the glycan-skewed side of the comparison. Its glycan shift outpaced, or even opposed, the corresponding protein-abundance shift rather than merely mirroring it. In the Anas-versus-Columba plane, OVAL again remained displaced from simple protein-glycan equivalence and preserved the same ordering beyond the chicken comparison.", []),
    (" Intact-glycopeptide assignments placed OVAL along a coherent cross-species progression. Chicken carried compact High-Mannose glycans, duck was enriched for Neutral Complex/Hybrid glycans, and pigeon carried more extended Sialylated Complex/Hybrid glycans. Taken together, Fig. 3A to F place OVAL among the shared proteins whose glycosylation aligns most closely with the phenotype ordering recovered here.", []),
])

p_s2d = spara([
    ("Because those OVAL glycan classes differ strongly in size and charge distribution, the more informative comparative variable was OVAL surface accessibility rather than OVAL abundance alone.", []),
    (" The relevant feature was how much of the acidic OVAL interface remained chemically reachable once decorated by different glycans. Ortholog control, abundance decoupling, and glycan-class progression together left OVAL as the shared candidate that was most directly comparable, chemically specific, and structurally actionable.", []),
])

add_centered_figure("Fig3_composed.png", width_cm=15.5)
add_main_figure_legend(
    "Fig. 3.",
    "Ortholog-restricted abundance-glycan analysis identifies OVAL as the leading shared discriminator.",
    [
        ("(A to C) Proteotype coevolution plots of log2-transformed protein abundance versus glycan abundance within chicken, duck, and pigeon. Insets report Spearman's ρ and two-sided p values. Highlighted labels indicate retained matrix proteins (OVAL, OC116, TRFE, and OC17). (D to F) Pairwise two-dimensional glycan-protein enrichment plots for Gallus versus Columba, Gallus versus Anas, and Anas versus Columba. The dashed diagonal indicates equal protein and glycan change; displacement toward the glycan-rich side indicates glycan change exceeding protein-abundance change.", False, False),
    ],
)

head("OVAL glycan state reshapes surface accessibility")

p_s3a = spara([
    ("OVAL was selected for structural analysis because it remained shared, chemically distinct, and directly comparable across species. Dominant glycosylated OVAL ensembles and matched apo references were rebuilt to test whether the three species differed mainly through glycan-dependent surface behavior rather than through backbone sequence alone.", [4, 11]),
    (" Representative rebuilt glycan conformations and species-specific surface maps showed that the dominant glycans occupied different spatial envelopes on the same folded protein scaffold (Fig. 4A and B). In panel A, points 1 and 2 mark the glycan end-to-end vector, point 3 marks the glycan centroid, point 4 marks the protein Cα centroid, and the translucent sphere shows the radius-of-gyration envelope centered on point 3. Panel B then translates that geometry into surface exposure by coloring Ca²⁺-relevant regions and blackening the same regions after shielding.", []),
])

p_s3b = spara([
    (" Pigeon first separated by occupying the largest overall glycan envelope, as shown by the higher radius of gyration in Fig. 4C and the longer end-to-end distances in Fig. 4E. In panel A terms, that means a longer 1-2 span and a larger sphere around point 3, with point 4 serving as the protein anchor that the glycan is measured against. That expansion occurred together with closer local approaches to the backbone in Fig. 4D and a broader glycan-protein distance distribution in Fig. 4F, consistent with extended glycans that sample a larger envelope while still folding back toward the OVAL surface.", []),
    (" Chicken defined the opposite endpoint, with compact glycans and the weakest geometric intrusion into the acidic interface. Duck remained closer to chicken in radius of gyration and overall glycan-protein spacing, but it separated from both species in end-to-end span and minimum backbone approach. Fig. 4C to F therefore translate glycan-class progression into a shielding geometry: a smaller sphere and shorter 1-2 span in panel A indicate a more compact glycan state, whereas a larger sphere and longer 1-2 span indicate a more extended, surface-engaging state.", []),
])

p_s3c = spara([
    (" Fig. 4G to J resolved the same acidic interface at progressively stricter levels. Viewed against panel B, the colored patches are the Ca²⁺-relevant regions that remain accessible, and black marks the same regions after shielding. Fig. 4G therefore measures gross interface shielding, Fig. 4H asks what fraction of candidate acidic residues remained hotspots, Fig. 4I measures the surface area retained by hotspot residues, and Fig. 4J counts the subset of Ca²⁺ hotspots that remained both electrostatically favorable and physically reachable.", []),
    (" Interface shielding increased stepwise from chicken to duck to pigeon, and the same ordering was retained across hotspot surface area, hotspot fraction, and net accessible Ca²⁺ hotspots. Together, these panels show progressive masking of the shared acidic OVAL face during early mineralization.", []),
])

p_s3d = spara([
    (" Matched glycosylated-versus-apo comparisons then showed that glycan addition changed the number of Ca²⁺-relevant hotspot residues and the exposed carboxylate surface most clearly in pigeon (Fig. 4K and L; Fig. S10). With panel B in mind, glycosylation preserves or hides the same Ca²⁺-relevant patches rather than creating new ones: the colored patches remain reachable, whereas the black patches are the same sites after shielding. Duck shifted in the same direction without a resolved structure-level significance call, and chicken could be assessed only descriptively because one glycosylated structure was available. This pattern is more consistent with a glycan-imposed shift in the acidic surface presented at mineralization onset than with a generic sequence effect alone.", []),
    (" Fig. 4K to N then collapse the same comparison to the whole-interface level. Across those panels, chicken preserved the most accessible Ca²⁺-relevant surface, pigeon shifted the largest share into a glycan-affected state, and duck trended toward the lower-accessibility side but did not separate from pigeon or apo references uniformly across metrics.", []),
    (" Chicken therefore retained the highest inferred Ca²⁺-capturing capacity and the state most compatible with earlier Ca²⁺-responsive opening of OVAL at mineralization onset. Duck and pigeon moved toward the lower-accessibility side from different structural backgrounds. The same ordering matched the phenotype sequence: chicken combined the densest mammillary field and the highest local hatching resistance, whereas duck and pigeon converged toward the lower-resistance side. Taken together, Fig. 4A to N link glycan-dependent separation, glycan geometry, interface masking, and Ca²⁺-relevant accessibility on a shared matrix protein.", [4, 11, 29]),
])

doc.add_page_break()
add_centered_figure("Fig4_composed.png", width_cm=15.2, before=0, after=20)
add_main_figure_legend(
    "Fig. 4.",
    "OVAL glycan classes reshape surface geometry and Ca²⁺-relevant interface accessibility.",
    [
        ("(A) Representative rebuilt OVAL-glycan conformations on the protein surface. The numbered markers indicate the start and end of the glycan end-to-end vector (1 and 2), the glycan centroid (3), and the protein Cα centroid (4). The translucent sphere denotes the glycan radius-of-gyration envelope centered on the glycan centroid. (B) Species-specific surface maps showing glycan positions in color and Ca²⁺-relevant regions in color, with shielded Ca²⁺-relevant regions shown in black. (C to F) comparisons of glycan radius of gyration, minimum glycan-backbone distance, glycan end-to-end distance, and glycan-protein distance across species. (G to J) comparisons of interface shielding, hotspot fraction, hotspot residue SASA, and net accessible Ca²⁺ hotspots. (K to N) glycosylated-versus-apo comparisons of Ca²⁺ hotspot residue counts, carboxylate surface accessibility, Ca²⁺ hotspot accessibility, and Ca²⁺ hotspot residue SASA. Species contrasts for ensemble-derived metrics used two-sided Mann–Whitney U tests. Glycosylated-versus-apo structure-level contrasts used one-sample Wilcoxon signed-rank tests when structure-level variation was present; different letters indicate Tukey HSD groupings at p < 0.05.", False, False),
    ],
    before=20,
    after=80,
)
doc.add_page_break()

head("Inside-out loading recovers local hatching resistance")

p_s4a = mixed([
    ("Finite-element testing translated the shared egg-tooth interface into an explicit inside-out loading design. Fig. 5A pairs species-specific dorsal beak views with micro-CT-derived finite-element setups and summary box plots of peak force and peak shear stress. The setups were built from the beak-tip geometry summarized in Fig. 1B. Because the meshes preserved species-specific shell geometry, the analysis remained anchored to the same mammillary context identified morphologically. Impact loading was sampled across multiple offset positions on the eggshell fragments, yielding independent contact shear-stress time courses for each species. We recorded both raw peak contact force (F_max) and peak contact shear stress (τ_max) so that thickness-driven effects could be separated from local interface resistance more explicitly. Peak τ_max was used as the direct readout of local hatching resistance at the mammillary contact interface. Species means ± s.d. were calculated across the sampled positions (Fig. S11A to F; eggshell thicknesses: ", False, False),
    ("G. gallus", False, True),
    (" 0.29 mm, ", False, False),
    ("A. platyrhynchos", False, True),
    (" 0.35 mm, and ", False, False),
    ("C. livia", False, True),
    (" 0.19 mm).", False, False),
])

doc.add_page_break()
add_centered_figure("Fig5_composed.png", width_cm=15.5, before=0, after=20)
add_main_figure_legend(
    "Fig. 5.",
    "Inside-out finite-element loading resolves local hatching resistance at the mammillary interface.",
    [
        ("(A) Species-specific dorsal beak views with dashed boxes marking egg-tooth position, paired with micro-CT-derived finite-element setups and summary box plots of peak contact force (F_max) and peak shear stress (τ_max). Species are ", False, False),
        ("Gallus gallus", False, True),
        (", ", False, False),
        ("Anas platyrhynchos", False, True),
        (", and ", False, False),
        ("Columba livia", False, True),
        (". For each species set, the left image shows dorsal beak view and the right image shows eggshell-fragment mesh, conical impactor, and representative contact output. (B) Mean contact-force time courses across nine impact positions with shaded ±1σ envelopes. (C) Mean contact shear-stress time courses across the same nine positions with shaded ±1σ envelopes. Box-plot points denote individual impact positions (n = 9 per species). P values were calculated by one-way ANOVA, and different letters indicate Tukey HSD groupings. Simulations were performed on reconstructed shell geometry rather than idealized shells.", False, False),
    ],
    before=20,
    after=80,
)
doc.add_page_break()

mixed([
    ("Peak F_max differed significantly among species (p = 1.64 × 10⁻¹³). ", False, False),
    ("G. gallus", False, True),
    (" reached 1.12 ± 0.11 N, ", False, False),
    ("A. platyrhynchos", False, True),
    (" reached 0.90 ± 0.09 N, and ", False, False),
    ("C. livia", False, True),
    (" reached 0.49 ± 0.04 N, and all pairwise differences were significant (Fig. 5A and B). By contrast, τ_max resolved a two-level pattern (p = 6.64 × 10⁻¹⁰). ", False, False),
    ("G. gallus", False, True),
    (" reached 551.60 ± 108.80 MPa and was significantly higher than ", False, False),
    ("A. platyrhynchos", False, True),
    (" at 404.00 ± 39.60 MPa and ", False, False),
    ("C. livia", False, True),
    (" at 393.00 ± 35.20 MPa. The latter two species did not differ significantly from each other (Fig. 5A and C).", False, False),
])

mixed([
    ("The difference between F_max and τ_max clarified the duck result. Its higher raw contact force was driven mainly by greater shell thickness (0.35 mm versus 0.19 mm in pigeon). It did not indicate superior unit-area material resistance. By contrast, ", False, False),
    ("G. gallus", False, True),
    (" exhibited a 36-40% increase in τ_max relative to the two other species, indicating higher local hatching resistance independent of shell thickness. This high-versus-low grouping, with ", False, False),
    ("G. gallus", False, True),
    (" alone in the high group and ", False, False),
    ("A. platyrhynchos", False, True),
    (" together with ", False, False),
    ("C. livia", False, True),
    (" in the low group, matched the grouping recovered for mammillary density by Tukey HSD (Fig. 1D). The mechanics therefore retained the contrast already recovered from mammillary organisation and OVAL accessibility.", False, False),
])

mixed([
    ("Whole-shell fracture force alone could make duck appear mechanically superior to chicken because of its greater shell thickness, despite the absence of the same high-density mammillary state. By focusing instead on local hatching resistance at the micro-CT-derived mammillary interface, τ_max removes that ambiguity. It shows that the high-density chicken state remains distinct, whereas duck and pigeon converge at lower resistance. This functional readout preserved the same asymmetry already visible in earlier sections and linked glycosylation-associated differences to local shell-breaking mechanics across the three model species.", False, False),
])

cite(p_s4a, [16, 37, 69])

# ════════════════════════════════════════════════════════════════════════════
# Discussion
# ════════════════════════════════════════════════════════════════════════════
para("Discussion", bold=True, size=14, before=320, after=160,
    align=WD_ALIGN_PARAGRAPH.LEFT)

p_disc_mam1 = smixed([
        ([('Cross-species divergence in this dataset resolved first at the mammillary layer, not at the level of wholesale matrix-protein turnover. ', False, False),
            ('Within a largely shared eggshell-matrix toolkit, OVAL glycan state provided the clearest molecular axis linking structure, surface accessibility, and local hatching resistance.', False, False)], [1, 16, 18]),
])

p_disc_regulator = spara([
    ("The three-species design matters because eggshell traits are organized along continuous ecological and developmental gradients rather than by one binary label.", [15, 39]),
    (" Nesting environment tracks a terrestrial-to-aquatic axis, and offspring condition spans a continuum from more precocial to more altricial young. Neither dimension is well represented by a simple yes-or-no partition.", [3, 23]),
    (" Duck is particularly informative in that design. It retains a broadly precocial developmental condition while shifting toward an intermediate OVAL glycan state and accessibility profile, and its τ_max outcome converges with pigeon rather than with chicken. The comparison therefore samples deliberately separated regions of a continuous ecological-developmental space while keeping the hatching interface itself comparable.", [3, 15, 22, 23]),
])

p_disc_axis = spara([
    ("Mammillary-layer mineralization mode remains the central structural level in the interpretation.", [1, 28]),
    (" Once early calcite crystal units are established, later eggshell regions inherit the spacing logic set in that first mineralization window. A dense mammillary field can therefore alter matrix retention, mineral continuity, local stress redistribution, and mature morphology.", [1, 30, 36]),
    (" That emphasis is consistent with earlier eggshell studies that place the mammillary layer at the intersection of crystal nucleation and matrix control. The present comparison extends that line by linking the layer to a cross-species glycan-state readout rather than to shell-quality descriptors alone.", [1, 28, 31, 32]),
    (" Recent poultry omics studies increasingly tie age, shell-gland transcription, extracellular-vesicle cargo, and other whole-shell quality traits to eggshell phenotype. Those descriptors, however, usually remain broader than the proximate material layer isolated here.", [33, 52, 57, 70]),
    (" For that reason, mammillary organisation is not merely another shell trait, but the earliest material context in which matrix chemistry can plausibly bias later mechanical outcome.", [1, 2]),
    (" That structural position is why mammillary organisation is the first cross-species difference that can be read as potentially consequential rather than merely descriptive.", [1, 28]),
])

p_disc_mam2 = spara([
    (" Among the molecular layers examined here, OVAL N-glycan architecture most closely tracked the structural contrast recovered across species.", []),
    (" Orthogroup turnover, gene-family change, and glycoprotein-network divergence still matter, but they mainly define comparative background rather than the nearest explanation. OVAL glycan state is especially informative because it is shared across species, chemically interpretable, and situated on an abundant matrix protein already implicated in mineralization.", [4, 18, 27]),
    (" Earlier work had already kept OVAL in view as an abundant eggshell glycoprotein and mineralization candidate. Prior glycoproteomic studies also showed that eggshell-matrix proteins can occupy different N-glycosylation states. The advance here is therefore not simply the detection of more glycopeptides; it is the ortholog-resolved comparison of which glycan states align most consistently with phenotype and how those assignments carry into structural and mechanical interpretation.", [4, 18]),
    (" Earlier chicken studies established a glycosite foundation for OVAL and identified glycosylated Asn in OC116. The present dataset resolved dominant glycan classes on the corresponding OVAL ortholog sequons carried into structural modelling (G. gallus N293; A. platyrhynchos and C. livia N97). Relative to earlier site-detection studies, this comparison extends breadth across species and into glycan-class interpretation rather than merely lengthening a within-species site inventory.", [8, 18, 21]),
    (" OVAL is useful not because it is unique, but because it remains comparable across species while retaining interpretable chemical divergence at the level of specific glycan classes.", [8, 18, 21]),
])

p_disc_other = spara([
    ("The non-OVAL signals still matter. OC116 and TRFE remained informative shared proteins, whereas OC17 appeared glycosylated only in chicken and may therefore represent a more lineage-restricted mineralization program.", []),
    (" Earlier eggshell studies had already assigned functional importance to OC17, OC116, and ovotransferrin-related matrix components, and the present dataset does not overturn that view. Instead, these proteins define the biological backdrop more consistently than they define the main cross-species discriminator recovered here.", [10, 19, 29]),
    (" For OC116 in particular, earlier biochemical work had already established glycosylated Asn in chicken eggshell matrix. More recent avian palaeoproteomic work showed that OC116 is among the more sequence-variable avian eggshell proteins. It shows substantial intraspecies variability rather than acting as a uniformly stable species marker. That broader context fits our comparison: retained glycosylation keeps OC116 biologically relevant, but it does not recover as stable a structure-linked contrast as OVAL.", [21, 66]),
    (" The same point also clarifies how the present study relates to earlier eggshell glycoproteomics. Those studies were essential for showing that eggshell matrix proteins can be glycosylated and that site-level inventories are experimentally accessible. Our contribution is the next comparative step: shared orthologs, dominant glycan classes, and the consequence of those classes for surface presentation across species.", [18, 21]),
    (" The shared toolkit therefore remains multicomponent, even though OVAL provides the most experimentally tractable entry point.", []),
])

p_disc_oval = spara([
    ("Re-Glyco and APBS analyses provide the structural bridge in the argument.", []),
    (" Compact chicken glycans left the critical acidic OVAL surface relatively exposed. Longer, more electronegative pigeon glycans reduced Ca²⁺ approach both sterically and electrostatically, with duck again occupying an intermediate state.", []),
    (" Earlier in vitro and structural work had already suggested that OVAL conformation and electrostatics matter during mineralization, but matched glycoform-resolved surface ensembles had not been compared across bird species.", [4, 11]),
    (" Glycan-state variation is therefore resolved here as a physically interpretable surface difference. Although this result does not establish direct causality, it supports a restrained inference: different glycan states on the same matrix protein can alter the chemical surface presented to the mineralizing environment and may thereby contribute to the structural divergence observed here.", []),
])

p_disc_mech = spara([
    ("The mechanical comparison was designed around the inside-out loading event of hatching rather than conventional outside compression or whole-shell breaking tests.", []),
    (" That distinction matters because eggshell thickness strongly influences absolute failure load, whereas τ_max is less confounded by thickness and more directly reflects load transfer through the mammillary interface itself.", [16, 34, 69]),
    (" The present analysis therefore complements recent finite-element and eggshell-strength studies by asking whether the inner mammillary interface preserves the same contrast already inferred from matrix state and morphology.", [16, 34, 35, 69]),
    (" Duck makes that separation especially clear because its thicker shell elevated F_max but did not recreate the high-τ_max state observed in chicken.", []),
])

p_disc_evo = para(
    "A second interpretive issue is that the mammillary layer can be partly resorbed during late incubation and hatching. That possibility does not erase the relevance of the present comparison because the quantified descriptors used here were mammillary density and crystal-unit organisation. Those features remain embedded in the shell even when part of the innermost material has been absorbed. The same consideration guided the mechanical readout. We emphasized the second characteristic peak rather than the first because the earliest force excursion is dominated more strongly by initial morphology-dependent contact, whereas the later peak more faithfully reflects stress transmission through the shell wall as a whole."
)

p_disc_discriminate = spara([
    ("These considerations help separate thickness buffering and developmental background from the material pathway emphasized here.", []),
    (" Eggshell thickness, body size, and broad reproductive ecology all contribute background variation, and lineage history undoubtedly matters.", [3, 14]),
    (" But thickness-based explanations do not account for the τ_max differences. Diffuse lineage-divergence explanations also do not explain why the same contrast recurs in glycan class, electrostatic accessibility, mammillary-layer organisation, and hatching-relevant mechanics.", [16, 37]),
    (" What recurs across this dataset is the alignment between glycan state, surface shielding, mammillary organisation, and τ_max under inside-out loading.", []),
    (" Ecology and phylogeny establish the design space, whereas matrix-protein glycan state remains the nearest chemically readable layer recovered here.", [4, 18]),
])

p_disc_function = para(
    "Taken together, the comparison converged on a chicken-like eggshell state in this dataset. Chicken combined the densest mammillary field, the least shielded Ca²⁺-relevant OVAL surface, and the highest local hatching resistance under inside-out loading. This pattern supports the inference that chemically specific states on reused matrix proteins can organise mineralised phenotypes more directly than proteome turnover alone in this comparison."
)
cite(p_disc_function, [67, 73, 74])

p_disc_selection = para(
    "Duck and pigeon remain essential because they define the bounds of that chicken-like state across both shell structure and ecological-developmental position. Duck combined greater shell thickness with intermediate OVAL accessibility and low τ_max, showing that thickness alone did not recreate the chicken state. Pigeon converged with duck at low τ_max, but did so from a thinner shell and a different mammillary background. Together, these contrasts make chicken a useful reference state within the sampled design space for linking glycan-dependent matrix behaviour to eggshell performance. In that framework, OVAL glycan state is the most directly readable molecular layer through which the state becomes mechanically interpretable."
)

p_disc_biomineral = para(
    "The same analytical sequence may extend beyond avian eggshells. Many biomineralization systems depend on organic matrices that regulate ion access, surface exposure, and mineral nucleation through chemically specific interfacial states rather than bulk composition alone. In that broader frame, the present workflow offers a way to move from glycoproteomic state to surface presentation and then to mesoscale function. Similar scale-bridging problems arise in other mineralized tissues and biomimetic materials. The same logic may also inform regenerative settings in which eggshell-derived materials or membrane proteins are being explored for tissue engineering and bone repair. More broadly, the study offers a template for testing how chemically specific matrix states organize biomineral behavior across biological and biomedical contexts."
)
cite(p_disc_biomineral, [64, 67, 68, 73])

p_disc_future = para(
    "The present scope remains bounded. We analyzed dominant glycoforms rather than the full in vivo glycan ensemble. We also treated each species as mechanically uniform at the scale of the mean eggshell and relied on incompletely constrained uterine ionic conditions in the APBS framework. The next decisive tests are defined-glycoform mineralization assays, direct manipulation of OVAL glycosylation in chicken, and site-resolved validation of the same inside-out mechanical contrast. These experiments should clarify whether the OVAL glycan state directly participates in shell mineralization or instead marks the chicken-like high-resistance state with unusual fidelity."
)

p_disc_close = para(
    "In summary, this study links mammillary organisation, glycoprotein state, surface accessibility, and local hatching mechanics across three avian eggshells. Chicken defined the high-resistance end of that axis, with dense mammillary organisation, compact OVAL glycans, greater Ca²⁺-relevant surface exposure, and the highest local resistance at the mammillary interface. As comparable glycoform assignments become available, the same framework can extend to other abundant eggshell matrix proteins. Across morphometric, glycoproteomic, structural, and mechanical layers, OVAL glycan state remains the most consistently aligned molecular feature of the chicken-like eggshell state."
)

p_disc_limits = p_disc_close

# ════════════════════════════════════════════════════════════════════════════
# Methods
# ════════════════════════════════════════════════════════════════════════════
para("Materials and Methods", bold=True, size=14, before=320, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT)

head("Biological materials")

p_m_bio = mixed([
    ("Fertilized eggs were collected during the mid-laying period from three avian lines: seven eggs from Chahua pink-shelled laying hens, seven eggs from Shaoxing spotted green-shelled laying ducks, and 19 eggs from White King egg pigeons. ", False, False),
    ("Gallus gallus", False, True),
    (" eggs were obtained from the Poultry Resources Conservation "
     "Farm, China Agricultural University (Beijing, China); ", False, False),
    ("Columba livia", False, True),
    (" eggs were provided by Prof. Chang Yu, College of Veterinary "
     "Medicine, China Agricultural University; and ", False, False),
    ("Anas platyrhynchos", False, True),
    (" eggs were supplied by Jinxing Duck Industry (Beijing, China). All eggs were stored at 16\u00b0C for 7 d under breeder-egg holding conditions before analysis.", False, False),
])

head("Eggshell matrix protein extraction")

mixed([
    ("Eggshell matrix proteins were extracted from the eggshell mammillary layer "
     "(EML) by an established EDTA demineralization protocol. Eggs were rinsed with "
    "deionized water and placed in sterile sealed bags. One egg from each species was reserved for micro-CT analysis; the remaining shells were used for matrix-protein extraction. The remaining six chicken eggs and six duck eggs were divided into three two-egg extraction units per species, whereas the remaining 18 pigeon eggs were divided into three six-egg extraction units. These pooled extraction units were used as the matched biological samples for both shotgun proteomics and intact glycopeptide analysis. For ", False, False),
    ("G.\u00a0gallus", False, True),
    (" and ", False, False),
    ("A.\u00a0platyrhynchos", False, True),
    (", the eggshell cuticle layer (ECL) was removed prior to EML "
     "extraction by treatment with 15 mL of 5% EDTA (0.13 mol/L, pH 7.6) supplemented "
     "with 2-mercaptoethanol (10 mmol/L) for 30 min at 20\u00b0C, with gentle manual "
    "kneading to separate the ECL; eggshells were subsequently rinsed with deionized "
     "water. No discrete cuticle layer was recognized in pigeon eggshells, so ", False, False),
    ("C.\u00a0livia", False, True),
    (" shells were rinsed with distilled water and entered the same extraction workflow directly. EML proteins from all three species were then solubilized under the same "
     "EDTA\u20132-mercaptoethanol conditions with the extraction duration extended to 12 h "
     "at 20\u00b0C. The resulting suspension was centrifuged at 1,000 \u00d7 g for 15 min; the "
     "pellet was resuspended and centrifuged a second time, and the pooled supernatant "
        "was stored at \u221280\u00b0C until analysis. Species were processed in parallel under the same extraction chemistry so that downstream differences were less likely to reflect handling drift.", False, False),
])

head("Micro-CT imaging and mammillary morphometry")

p_m_ct = para(
    "One eggshell fragment (4 mm \u00d7 4 mm) from each species was excised from the equatorial region near the blunt-half midpoint and scanned using a Phoenix V|tome|x\u00a0M "
    "microfocus CT system (GE Sensing and Inspection Technologies GmbH, Wunstorf, "
    "Germany). The X-ray source was operated at 85 kV tube voltage and 160 \u03bcA current without a beam filter; scan settings were held "
    "constant across all specimens, and a total of 1,800 projection images were collected for each eggshell. Reconstructed image volumes were exported as 16-bit unsigned isotropic datasets with a sampling distance of approximately 0.003836 mm along the x, y, and z axes (about 3.84 \u03bcm voxel size). After scanning, each fragment was subdivided evenly into nine subfragments for downstream regional quantification. Volumetric data were reconstructed in 3D Slicer, and the eggshell region was segmented with the Threshold module in the Segmentation workflow using operator-guided threshold correction after automatic selection. The same operator reviewed all three species side by side; grayscale thresholds were fine-tuned to retain all true shell voxels while preserving visible pore openings. Acquisition noise was suppressed by a 5 \u00d7 5 \u00d7 5 "
    "median filter, followed by largest-island isolation and 9 \u00d7 9 \u00d7 9 hole-filling. "
    "Within each subfragment, three morphometric parameters were then calculated from the labelmap. "
    "The segmented shell model was first duplicated as a single-copy volume and solid-filled with the Fill Holes operation; "
    "subtraction of the original shell model from the filled solid yielded the mammillary interspace layer, and closed voids appearing in that interspace plane were defined as mammillary knobs. "
    "Mammillary density was calculated as mammilla count divided by analysis-unit area. "
    "Total eggshell volume in the same analysis unit was obtained directly from the labelmap, and mean column-unit volume was defined as total shell volume divided by mammilla count; "
    "column-unit volume fraction was then calculated as mean column-unit volume divided by the total eggshell volume of the corresponding analysis unit. "
    "Because the columnar units initiated by mammillae are arranged as repetitive and approximately even planar units in normal avian eggshell microstructure, these parameters were treated as local average representatives of whole-shell organisation. The nine observations per species were non-overlapping regional subsamples from one scanned fragment and were used to quantify within-fragment spatial variation around that local mean rather than to represent nine independent eggs. The same segmentation and post-processing workflow was applied to all scans so that species contrasts reflected morphology rather than reconstruction settings."
)
cite(p_m_ct, [1, 30])

head("Shotgun proteomics of eggshell matrix proteins")

para(
    "For shotgun proteomics, eggshell-matrix extracts from the post-CT sample set were analyzed as three pooled biological samples per species, with each chicken and duck sample comprising two eggs and each pigeon sample comprising six eggs. Proteins were "
    "extracted by resuspension in lysis buffer (1% SDS, 1% protease inhibitor "
    "cocktail), sonication on ice, and clarification by centrifugation at "
    "12,000 \u00d7 g at 4\u00b0C for 10 min; protein concentration was determined with a "
    "BCA assay kit. Proteins were precipitated with pre-cooled acetone (5 volumes, "
    "\u221220\u00b0C, 2 h), washed twice with acetone, and redissolved in 200 mM TEAB. "
    "Disulfide bonds were reduced with 5 mM dithiothreitol (56\u00b0C, 30 min) and "
    "alkylated with 11 mM iodoacetamide (room temperature, 15 min, dark). They "
    "were digested overnight with sequencing-grade trypsin (enzyme:protein ratio "
    "1:50) and desalted with Strata X SPE columns. No offline HPLC fractionation was performed before LC-MS/MS analysis. For proteome acquisition, 20 \u03bcg peptide was injected per run."
)

mixed([
    ("Desalted peptides were dissolved in mobile phase A (0.1% formic acid in water) and separated on a "
     "home-made 15-cm \u00d7 100-\u03bcm i.d. reversed-phase C18 analytical column connected "
     "to a Vanquish Neo UPLC system (Thermo Fisher Scientific). Mobile phase B consisted of 0.1% formic acid in 80% acetonitrile, and the flow rate was maintained at 400 nl/min. The gradient program was 4% B for 0\u20130.5 min, 4\u20138% B for 0.5\u20130.6 min, 8\u201322.5% B for 0.6\u201313.6 min, 22.5\u201335% B for 13.6\u201320.5 min, 35\u201355% B for 20.5\u201320.9 min, 55\u201399% B for 20.9\u201321.4 min, and 99% B for 21.4\u201322.6 min. "
    "After UPLC separation, peptides were introduced into a nano-electrospray ionization source operated at 1,900 V and analyzed on an Orbitrap Astral mass spectrometer (Thermo Fisher Scientific). "
     "Full-MS spectra were acquired in the Orbitrap at 240,000 resolution over "
    "380\u2013980 m/z; MS/MS fragments were acquired in the Astral analyzer at 80,000 "
     "resolution using HCD fragmentation in DIA mode (NCE\u202f=\u202f25%), fixed first mass 150 m/z, "
     "AGC target 500%, and maximum injection time 3 ms. DIA data were processed with "
     "DIA-NN v1.8 against species-specific reference proteomes \u2014 ", False, False),
    ("G.\u00a0gallus", False, True),
    (" (43,711 entries), ", False, False),
    ("A.\u00a0platyrhynchos", False, True),
    (" (91,801 entries), and ", False, False),
    ("C.\u00a0livia", False, True),
    (" (17,309 entries), all downloaded August 2024 \u2014 "
     "concatenated with reverse decoy sequences. "
     "Using species-matched reference databases reduced the risk that peptide assignments would be biased toward the best-annotated proteome. "
     "Trypsin/P cleavage was specified with up to one missed cleavage; N-terminal "
     "methionine excision and carbamidomethylation of Cys were set as fixed "
     "modifications. Protein and peptide FDR were each controlled at < 1%.", False, False),
])

head("Intact glycopeptide mass spectrometry")

para(
    "For intact glycopeptide analysis, the same three pooled biological samples per species were carried forward, and 200 \u03bcg peptide digest from each pooled sample was used as input for enrichment. N-glycopeptides were enriched from tryptic digests by hydrophilic interaction "
    "liquid chromatography (HILIC). Peptide digests were redissolved in loading "
    "buffer (80% ACN, 5% TFA), loaded onto a HILIC column, washed three times with "
    "loading buffer, and glycopeptides were eluted twice with 0.1% TFA, 50 mM "
    "ammonium bicarbonate, and 50% ACN. Eluates were desalted with C18 Zip-Tips "
    "and vacuum-dried. Glycopeptide fractions were separated on the same nano-LC "
    "platform using a 34-min gradient (4\u201399% B at 400 nl/min). Full-MS spectra were "
    "acquired at 240,000 resolution over 700\u20132,000 m/z; MS/MS spectra were acquired "
    "at 80,000 resolution with fixed first mass 120 m/z, cycle time 0.6 s, AGC "
    "target 100%, intensity threshold 25,000 ions/s, and maximum injection time 5 ms. "
    "Raw DDA data were processed with MSFragger v3.4 against the same species-specific "
    "reference proteomes as above, with strict trypsin cleavage (up to 2 missed "
    "cleavages), peptide length 7\u201350 residues, fixed carbamidomethylation of Cys, "
    "variable N-terminal acetylation and Met oxidation, and default MSFragger "
    "glycosylation mass offsets. Protein, peptide, and PSM FDR were each controlled "
    "at < 1%. N-glycan structural classes were assigned using the Oxford nomenclature "
    "into six categories: High-Mannose, Paucimannose/Truncated, Neutral Complex/"
    "Hybrid, Fucosylated Complex/Hybrid, Sialylated Complex/Hybrid, and Other. "
    "Per-protein per-species class abundance was computed as the fraction of total "
    "glycan-site signal intensity. Structural classes were assigned after site-level identification so that shared glycan usage could be compared on a common protein background across species."
)

head("Comparative proteome analysis and gene-family evolution")

p_m_ortho = mixed([
    ("Protein sequences from all three species were assigned to orthogroups using "
     "OrthoFinder (all-versus-all BlastP; E-value threshold 1 \u00d7 10\u207b\u00b9\u2070; "
     "MCL inflation parameter 2.0), yielding a 3,250-orthogroup background set for "
     "all downstream enrichment analyses. Divergence times were taken from published "
     "timetrees: ", False, False),
    ("G. gallus", False, True),
    ("\u2013", False, False),
    ("A. platyrhynchos", False, True),
    (" 83.37 Mya and ", False, False),
    ("G. gallus", False, True),
    ("\u2013", False, False),
    ("C. livia", False, True),
    (" 90.84 Mya. Gene-family expansion and contraction rates were inferred with "
     "CAFE5 using the time-calibrated phylogeny. GO enrichment of pairwise-shared, "
     "species-exclusive, expanding, and contracting orthogroup sets was performed "
     "using the OrthoVenn3 web platform (https://orthovenn3.bioinfotoolkits.net) "
     "against the 3,250-orthogroup background; terms with adjusted p\u202f<\u202f0.05 were "
     "considered significant.", False, False),
])
cite(p_m_ortho, [3, 5, 14])

head("Cross-species glycoprotein ortholog identification")

mixed([
    ("High-confidence cross-species orthologues of four target eggshell glycoproteins "
     "(OVAL, OC116, TRFE, OC17) were identified by BlastP of each reference ", False, False),
    ("G.\u00a0gallus", False, True),
    (" sequence against the non-reference-species proteomes (E-value "
     "threshold 1 \u00d7 10\u207b\u2075; maximum 500 target sequences; 250 reported alignments). "
     "Candidate hits were retained at average maximum sequence identity \u2265 0.80; "
     "where query and subject non-overlapping HSP counts were unequal, a relaxed "
     "threshold of \u2265 0.50 was applied. Final UniProt ortholog identifiers used for "
     "downstream structural and quantitative analyses are listed in Supplementary "
     "Table\u00a01.", False, False),
])

head("Integrated protein-glycan abundance comparison")

para(
    "For Fig. 3A to C, protein-level and glycan-site quantification tables were "
    "loaded separately for each species from the Protein_quant and Site_quant sheets. "
    "When the Number Comparable field was present, protein entries and glycan-site entries with values < 2 were excluded so that only features detected in at least two of the three pooled biological samples were retained for downstream comparable-protein analysis. Mean protein intensity "
    "was calculated across all species-matched intensity columns for each accession, "
    "and mean glycan intensity was calculated for each quantified glycosylation site "
    "across the corresponding site-intensity columns. Only positive-intensity entries "
    "were retained. Glycan-site rows were then inner-joined to protein rows by protein "
    "accession so that each point represented one quantified glycosylated sequon with "
    "a matched protein-abundance measurement. Protein and glycan intensities were "
    "log2-transformed, and within-species protein-glycan coupling was summarized by "
    "Spearman rank correlation with two-sided p values. OVAL, OC116, TRFE, and OC17 "
    "were highlighted by the strict ortholog assignments summarized in Fig. 2E, and labels "
    "were annotated with the corresponding glycosylated Asn position.")

para(
    "For Fig. 3D to F, pairwise glycan-protein enrichment plots were built from "
    "ortholog-mapped protein and glycan abundance differences between species. Protein "
    "abundance for each accession was defined as the mean of nonzero replicate "
    "intensities after excluding proteins with Number Comparable < 2 when available. "
    "Glycan abundance was defined at the protein level as the sum of mean nonzero site "
    "intensities across all quantified glycosylation sites assigned to that accession after the same comparable-feature filtering. "
    "Gallus-versus-Anas and Gallus-versus-Columba comparison spaces were built from "
    "blastp outfmt 6 mappings, retaining the best hit per query when the mean E value "
    "was <= 1 × 10⁻⁵ and the average sequence identity was >= 0.40; when query and "
    "subject had different numbers of non-overlapping HSPs, the maximum identity "
    "threshold >= 0.40 was applied instead. The Anas-versus-Columba plane was bridged "
    "through shared Gallus orthologs that passed the same filter in both datasets. For "
    "each retained ortholog pair, the x coordinate was calculated as log2(I_ref) - "
    "log2(I_comp) and the y coordinate as log2(G_ref) - log2(G_comp), where I and G "
    "denote protein and glycan abundance, respectively. The y = x diagonal therefore "
    "marked matched protein-glycan change, whereas displacement toward the glycan-rich "
    "side identified proteins whose glycan shift exceeded the corresponding change in "
    "bulk protein abundance.")

head("N-glycan structural ensemble modelling")

p_m_reglyco = mixed([
    ("OVAL ortholog protein structures (AlphaFold2-predicted models) were "
     "accessed through the GlycoShape platform (glycoshape.org) via UniProt "
     "accession identifiers. "
     "Experimentally detected N-glycan compositions from IGP-MS were mapped "
     "to the GlycoShape glycan library by monoisotopic mass matching "
     "(tolerance \u00b10.5\u00a0Da), using per-residue masses of 203.0794\u00a0Da (HexNAc), "
     "162.0528\u00a0Da (Hex), 291.0954\u00a0Da (NeuAc), 146.0579\u00a0Da (dHex), and "
    "132.0423\u00a0Da (Pen) with an 18.0106\u00a0Da water correction; matched entries "
    "were retrieved as GlyTouCan accession identifiers. All experimentally detected glycoforms that could be matched to the GlycoShape library were retained for downstream modelling rather than pre-filtering to a dominant subset. "
     "Full conformational ensembles were then generated with the GlycoShape "
     "Re-Glyco Ensemble tool (glycoshape.org/ensemble), which restores missing "
     "glycans by aligning them to torsion angles from Privateer crystallographic "
     "standards and sampling conformations from the GlycoShape molecular-dynamics "
    "ensemble library. "
    "For each OVAL ortholog, glycan modelling was constrained to the experimentally detected glycopeptide site identified in the present dataset; each matched "
    "glycan was then submitted as an independent modelling job via the GlycoShape API and attached to the measured target sequon \u2014 ", False, False),
    ("G.\u00a0gallus", False, True),
    (" N293 and ", False, False),
    ("A.\u00a0platyrhynchos", False, True),
    (" / ", False, False),
    ("C.\u00a0livia", False, True),
    (" N97 \u2014 with ensemble size 50, random seed 42, and PDB output format. "
     "This procedure yielded 50 glycoprotein models for ", False, False),
    ("G.\u00a0gallus", False, True),
    (" (1 matched glycan type), 150 for ", False, False),
    ("A.\u00a0platyrhynchos", False, True),
    (" (3 types), and 700 for ", False, False),
    ("C.\u00a0livia", False, True),
    (" (14 types, "
     "including four NeuAc positional isomers resolved from the GlycoShape library). Using the same random seed and ensemble size for every submitted glycan maintained matched sampling depth across species. "
     "Ensemble geometric descriptors were calculated for each model from atomic "
     "coordinates using BioPython: the radius of gyration (Rg) of all glycan heavy "
     "atoms, the end-to-end distance of the glycan chain, and the minimum distance "
     "between any glycan heavy atom and protein C\u03b1 atoms (minimum C\u03b1 contact "
     "distance). Per-structure summary statistics (mean\u00a0\u00b1\u00a0s.d.) and pairwise species "
     "comparisons (Mann\u2013Whitney\u00a0U test, two-tailed) were performed for each descriptor.", False, False),
])
cite(p_m_reglyco, [11, 56, 65])

head("Electrostatic potential calculation")

p_m_apbs = para(
    "Electrostatic surface potentials were computed for each Re-Glyco ensemble "
    "model and a matched apo reference with glycans removed using APBS v3.4.1. Atomic "
    "partial charges and radii were assigned with PDB2PQR using the CHARMM36 force "
    "field and PROPKA protonation at pH 7.4; glycan heavy-atom partial charges were "
    "assigned from published GLYCAM06 values. APBS input grids were generated automatically from the PQR bounding box with 10 \u00c5 padding and a target grid spacing of 0.5 \u00c5; focusing grids were set to 70% of the coarse-grid lengths. The nonlinear Poisson\u2013Boltzmann equation was solved with single-ion boundary conditions, 0.15 mol/L monovalent salt (ion radii 2.0 and 1.8 \u00c5 for cation and anion, respectively), protein dielectric 2.0, solvent dielectric 78.54, solvent-accessible surface definition smol, charge discretization spl0, solvent probe radius 1.4 \u00c5, spline window 0.3 \u00c5, surface density 10.0, and temperature 298.15 K. Solvent-accessible surface areas were calculated by the "
    "Shrake\u2013Rupley algorithm; surface residues were defined by relative ASA "
    "\u2265 0.25. Ca\u00b2\u207a-binding electrostatic hotspots were defined as surface Asp or "
    "Glu residues with APBS potential < \u22125 kT/e. Ensemble-level metrics reported "
    "include hotspot count (N_hot), per-hotspot mean SASA, hotspot fraction of total "
    "surface Asp/Glu, and median surface electrostatic potential. The same electrostatic threshold and surface-definition rules were applied to all models to preserve cross-species comparability."
)
cite(p_m_apbs, [12, 42, 43])

head("Finite-element analysis")

p_m_fea = mixed([
    ("The region of interest used for downstream finite-element analysis was defined as a cylindrical volume of 1 mm radius during micro-CT reconstruction. ", False, False),
    ("Surface models derived from micro-CT were first exported as STL files and reverse-engineered in Geomagic Wrap for finite-element pre-processing by sequential de-noising (strength 2), triangle simplification to approximately 300,000 faces, mesh re-gridding at 0.01 mm, iterative defect correction to zero residual faults, and organic parametric surface fitting at minimum tolerance. The resulting eggshell surface models were then imported into Ansys Workbench 2023 R1 and solved with the explicit LS-DYNA module (unit system: mm/kg/N/s). To isolate structure-driven mechanical differences, identical eggshell material properties were assigned across species; parameter values were adopted from the avian eggshell elasticity study reported in Biology 10, 989 (2021; DOI: 10.3390/biology10100989) rather than re-estimated separately for each species. In the solver keyword deck, the eggshell was modeled with *MAT_PLASTIC_KINEMATIC and *SECTION_SOLID, using density 2770 kg/m^3, Young's modulus 3.0 \u00d7 10\u00b9\u2070 Pa, Poisson's ratio 0.33, yield strength 1.5 \u00d7 10\u2077 Pa, tangent modulus 0, and maximum equivalent plastic strain at failure 0.05. This explicit impact setup followed the general logic of crash-deformation simulations, but was rescaled to the local eggshell loading geometry studied here. The impactor, used to simulate the egg tooth, was a frustum (base radius 0.1 mm; top radius 0.5 mm; height 0.5 mm) assigned the library IRON-ARMCO explicit material and meshed as a separate solid part. Contact between the impactor and eggshell was defined with *CONTACT_AUTOMATIC_SURFACE_TO_SURFACE using a friction coefficient of 0.2. Eggshell mesh element sizes were 0.05 mm (", False, False),
    ("G. gallus", False, True),
    ("), 0.05 mm (", False, False),
    ("A. platyrhynchos", False, True),
    ("), and 0.03 mm (", False, False),
    ("C. livia", False, True),
    ("), ensuring at least six element layers across the eggshell cross-section; the impactor was meshed at 0.1 mm. The impactor was driven by an imposed initial velocity of 50,000 mm/s along the loading axis, whereas one boundary set on the fragment perimeter was fully fixed in all translational and rotational degrees of freedom. Analyses ran for 1.0 \u00d7 10\u207b\u2074 s with a time-step safety factor of 0.7, erosion enabled, a minimum time step of 1 \u00d7 10\u207b\u2078 s, and automatic mass scaling; solver outputs included GLSTAT, SPCFORC, RCFORC, NCFORC, BNDOUT, NODOUT, MATSUM, ELOUT, JNTFORC, and DEFORC at 1.0 \u00d7 10\u207b\u2077 s intervals, with D3PLOT and INTFOR written every 1.0 \u00d7 10\u207b\u2076 s. For the positional loading analysis, the impactor was sampled at nine lateral offsets arranged on a 3 \u00d7 3 grid with 0.5 mm spacing. Across these nine cases, only the impactor coordinates were translated; material definitions, contact settings, boundary conditions, fragment size, and all other solver controls were held constant. Peak contact force (F_max) and peak contact shear stress (\u03c4_max) were extracted for each position. Sampling nine offsets allowed local positional heterogeneity to be measured without changing fragment size or loading geometry between species.", False, False),
])
cite(p_m_fea, [16, 37, 89])

head("Statistical analysis")

mixed([
    ("All values are expressed as mean \u00b1 s.d. All statistical tests were two-tailed, "
     "and p < 0.05 was considered statistically significant throughout. "
    "Normality was evaluated by the Shapiro\u2013Wilk test and homogeneity of variance by Levene's test before parametric between-species analyses. Mammillary morphometric parameters were compared among species by one-way ANOVA "
    "followed by Tukey's honestly significant difference test (Tukey HSD; \u03b1\u202f=\u202f0.05). These nine morphometric observations per species were non-overlapping subfragments from one scanned fragment and should therefore be interpreted as within-fragment regional replicates rather than as nine independent biological samples. The same assumption checks supported one-way ANOVA with Tukey HSD for finite-element outcomes (F_max and \u03c4_max). In contrast, glycan ensemble geometric descriptors (Rg, end-to-end distance, minimum glycan\u2013protein contact distance) and hotspot-derived ensemble metrics did not satisfy normality and/or homoscedasticity across species, so pairwise species contrasts for these variables were evaluated with two-sided Mann\u2013Whitney U tests. "
     "Glycosylation-induced reduction in N_hot within ", False, False),
    ("C.\u00a0livia", False, True),
    (" was assessed by one-sample Wilcoxon signed-rank test versus the apo reference value; total Asp/Glu SASA at the whole-interface level was summarized descriptively because the structure-level values were invariant across ", False, False),
    ("C.\u00a0livia", False, True),
    (" glycoforms; shifts in median surface electrostatic potential were assessed by one-sample Wilcoxon signed-rank test against the apo reference value. No multiple-testing correction was applied, and no outliers were removed. All statistical analyses were "
     "conducted in Python using scipy.stats and statsmodels.", False, False),
])

# ════════════════════════════════════════════════════════════════════════════
# References
# ════════════════════════════════════════════════════════════════════════════
para("References", bold=True, size=14, before=320, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT)

for source_number in CITATION_ORDER:
    p_ref = doc.add_paragraph(style="Normal")
    p_ref.paragraph_format.space_before = Pt(0)
    p_ref.paragraph_format.space_after = Pt(4)
    p_ref.paragraph_format.left_indent = Pt(18)
    p_ref.paragraph_format.first_line_indent = Pt(-18)
    ref_text = f"{CITATION_MAP[source_number]}. {REF_TEXTS[source_number]}"
    r_ref = p_ref.add_run(ref_text)
    r_ref.font.size = Pt(9)
    rPr = r_ref._r.get_or_add_rPr()
    _set_font(rPr, FONT)

doc.save(OUT)
print(f"[OK]  {OUT}")
