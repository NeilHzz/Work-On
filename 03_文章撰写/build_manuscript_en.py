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

OUT = str(Path(__file__).with_name("manuscript260424v2.docx"))
FIG_BASE = Path(__file__).resolve().parent.parent / "Figure260421"

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
    "Glycan-state divergence in matrix proteins links to avian eggshell structure and biomineralization",
    bold=True, size=14, before=0, after=160, align=WD_ALIGN_PARAGRAPH.LEFT
)

# Short title (≤50 characters)
para("Glycan states link eggshell biomineralization",
     bold=False, size=11, after=60, align=WD_ALIGN_PARAGRAPH.LEFT)

para("Abstract", bold=True, size=11, before=80, after=40,
     align=WD_ALIGN_PARAGRAPH.LEFT)

para(
    "Comparative biomineralization studies often reveal lineage differences but less often identify the molecular layer most proximate to ordered phenotype. "
    "Here, integrating micro-CT morphometry, eggshell-matrix proteomics, glycopeptide mass spectrometry, structural ensemble modeling, and finite-element simulation across chicken, duck, and pigeon, we found that local hatching resistance under simulated chick escape loading recapitulated the mammillary hierarchy, separating chicken from duck and pigeon. "
    "Comparative glycoproteomics then identified a species-ordered shift in matrix-protein glycan states, most clearly on ovalbumin, from high-mannose in chicken to neutral complex-hybrid in duck and sialylated complex-hybrid in pigeon. "
    "Re-Glyco and electrostatic analyses linked this shift to progressively reduced Ca²⁺-accessible surface exposure, matching the ordering in mineralization mode and mechanics. "
    "These results identify matrix-protein glycan-state divergence as a mechanistically informative layer linking comparative molecular divergence to avian eggshell structure, biomineralization, and function.",
    bold=False, size=10, before=0, after=80, align=WD_ALIGN_PARAGRAPH.JUSTIFY
)

# Teaser (≤125 characters, one sentence for non-specialist readers)
para(
    "Teaser: Matrix-protein glycan-state divergence links avian eggshell biomineralization to local hatching resistance.",
    bold=False, italic=True, size=10, before=80, after=160, align=WD_ALIGN_PARAGRAPH.LEFT
)

# ════════════════════════════════════════════════════════════════════════════
# Introduction
# ════════════════════════════════════════════════════════════════════════════
para("Introduction", bold=True, size=14, before=0, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT)

# §1 — Background value
p_s1a = spara([
    (" The eggshell is a key biomineralized structure that protects the egg against environmental pathogens and provides the embryo with an essential calcium source, and its mechanical behavior is first established in the mammillary layer.", [1, 4, 28, 38]),
    (" Mammillary knobs, positioned by eggshell matrix proteins within the mammillary layer, determine where calcite growth begins and therefore help define the microstructural architecture of the mature eggshell.", [1, 4, 28]),
    (" Although the eggshell also mediates gas exchange, antimicrobial defense, and embryonic calcium supply, its resistance to fracture depends to a large extent on mammillary features and on how mineral is organized around the mammillae.", [1, 4, 38]),
    (" The mammillary layer is therefore not merely the innermost eggshell layer; it is the structural origin of whole-eggshell mechanics.", [1, 28, 38]),
])

p_s1b = spara([
    (" Against that backdrop, developmental strategy and habitat-linked reproductive setting impose different demands on the structural protection that the eggshell must provide.", [15, 16, 23, 26, 41]),
    (" Precocial lineages generally require eggshells that support relatively independent hatchlings and prolonged pre-hatch loading, whereas altricial lineages often develop in more protected nest contexts.", [15, 16, 23, 26]),
    (" Meanwhile, aquatic or semi-aquatic versus terrestrial egg-laying environments define a second ecological contrast along which eggshell architecture evolves.", [15, 23, 40, 41]),
    (" For that reason, mammillary-layer structure is a suitable core comparative phenotype, yet these life-history and ecological differences still do not explain why interspecific differences in mammillary-layer morphology are so pronounced.", [1, 16, 41]),
])

# §2 — Prior work and its limits
p_intro2 = spara([
    ("Work over the past two decades has identified uterine matrix proteins as major regulators of mammillary-layer mineralization, crystal growth orientation, and eggshell architecture, with ovocleidin-17 (OC17), ovocleidin-116 (OC116), ovotransferrin (TRFE), and ovalbumin (OVAL) among the best-characterized examples.", [1, 2, 4, 6, 7, 8, 9, 10, 19, 20, 21, 29]),
    (" OC17 has been linked to early crystal mineralization and calcite habit control, OC116 to matrix organization and mineral deposition, and TRFE to ion-binding and antimicrobial functions within the eggshell matrix; among them, OVAL is especially notable because in vitro studies indicate that it can unfold under mineralizing conditions and participate directly in early crystal-related events.", [6, 7, 8, 9, 10, 19, 21, 29]),
    (" Glycosylation is not uniformly deployed: recent comparative work on eggshell cuticle layer and mineralized-layer proteomes has shown that the same protein can adopt different glycan states across these layers, suggesting layer-specific functional roles.", [18, 20, 21, 49, 50, 52]),
    (" Yet the branched N-glycan classes carried by avian eggshell matrix glycoproteins have rarely been resolved in a cross-species framework.", [18, 20, 21]),
    (" In parallel, comparative morphometry and mechanical studies have shown that eggshell mechanics diverge systematically across bird groups.", [1, 4, 15, 16, 17]),
    (" A framework is still needed to bring these observations together and test whether glycan-state differences on key matrix proteins can help explain cross-species variation in mammillary-layer structure.", [2, 4, 20, 21]),
])

p_intro_sig = spara([
    ("Resolving that gap matters beyond descriptive avian morphology because the eggshell preserves developmental timing, matrix chemistry, microstructure, and hatching-relevant mechanics in the same biomineralized structure.", [1, 2, 4, 16, 20, 21, 38, 42]),
    (" That makes avian eggshell formation unusually suitable for cross-scale comparison: ecological setting and developmental program can be interpreted alongside matrix state and structural outcome within a single system.", [1, 2, 4, 15, 16, 20, 21, 38, 42]),
    (" It also makes the eggshell an unusually useful entry point for biomineralization research more broadly, because relationships that are often distributed across separate tissues in bone and other mineralized systems can be examined here within a single experimentally comparable structure.", [1, 4, 16, 20, 21, 38, 67, 68, 73]),
    (" Eggshell biology has often been divided between comparative studies that define phylogenetic and ecological contrasts and mechanistic studies that identify candidate regulators in the shell-gland matrix.", [1, 2, 4, 6, 7, 15, 16, 20, 21]),
    (" This system therefore permits a direct test of whether a chemically interpretable molecular layer can connect comparative phenotype to a mechanistic explanation.", [2, 16, 20, 21, 38, 42, 57, 69]),
])

# §3 — Core gap
p_intro_gap = spara([
    ("The unresolved question, therefore, is whether cross-species glycan-class divergence in avian eggshell matrix proteins aligns with a broader and structurally meaningful ordering in the eggshell.", [55, 58, 59, 60, 65]),
    (" Does it coincide with shifts in computed Ca²⁺-binding-site accessibility, mammillary density, and simulated local resistance?", [55, 58, 59, 60, 65]),
    (" This question can therefore be examined through two deliberately crossed contrasts: precocial versus altricial development, and terrestrial versus aquatic-associated habitat.", [4, 13, 27, 39]),
    (" Chicken, duck, and pigeon were selected to occupy distinct positions within that comparison space.", [4, 13, 39]),
    (" In this design, duck against chicken plus pigeon emphasizes habitat-linked contrast, pigeon against chicken plus duck emphasizes developmental contrast, and chicken against duck plus pigeon isolates the mammillary-layer phenotype most distinct in the present dataset.", [4, 13, 27, 39]),
])

# §4 — This study
p_intro4 = smixed([
        ([("This study integrates micro-CT morphometry, comparative eggshell-matrix proteomics with orthogroup and gene-family evolution analyses, intact glycopeptide mass spectrometry, Re-Glyco structural ensemble modeling, and finite-element simulation in three species \u2014 ", False, False),
            ("Gallus gallus", False, True),
            (", ", False, False),
            ("Anas platyrhynchos", False, True),
            (", and ", False, False),
            ("Columba livia", False, True),
            (" \u2014 representing, respectively, a terrestrial precocial model, an aquatic-associated precocial model, and a terrestrial altricial model \u2014 to test whether matrix-protein glycan-state divergence can connect the ordered eggshell phenotype to a more immediate biophysical layer: Ca²⁺ accessibility and local hatching resistance.", False, False)], [3, 22, 24, 25]),
        ([(" In the present data, that glycan-state ordering ultimately resolves most clearly on OVAL, where species-specific N-glycan class composition aligns with computed Ca²⁺ accessibility, mammillary density, and simulated local hatching resistance.", False, False)], [11, 12, 16]),
        ([(" These findings provide mechanistic insight into how N-glycan-state divergence in eggshell matrix proteins shapes ordered avian eggshell biomineralization and establish a glycosylation-centered comparative framework for linking matrix chemistry to structure and hatching-relevant function, thereby offering a new perspective for understanding biomineralization.", False, False)], [4, 11, 12, 16, 42]),
])

# ═══════════════════════════════════════════════════════════════════════════
# "Results" section label
# ═══════════════════════════════════════════════════════════════════════════
para("Results", bold=True, size=14, before=320, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT)
# ════════════════════════════════════════════════════════════════════════════
# § Species selection — ecological and developmental niche analysis
# ════════════════════════════════════════════════════════════════════════════
head("Three focal birds define the comparison framework")

p_ss1 = smixed([
        ([('Using 10,993 AVONET species records, we combined ecological and developmental information to place extant birds in a comparative space from which three deliberately separated model species were selected (Fig. 1A).', False, False)], [15, 22, 23, 24, 25, 41]),
        ([(' Within this comparison space, ', False, False),
            ('Gallus gallus', False, True),
            (', ', False, False),
            ('Anas platyrhynchos', False, True),
            (', and ', False, False),
            ('Columba livia', False, True),
            (' occupy representative positions for terrestrial precocial, strongly aquatic-associated precocial, and terrestrial altricial strategies, respectively, and were therefore chosen for downstream comparison.', False, False)], [15, 22, 23, 24, 25, 41]),
    ([(' This functional grouping only partly overlaps with phylogeny: chicken and duck remain closely related precocial taxa but separate along the habitat axis, whereas pigeon anchors the altricial contrast (Fig. 1B).', False, False)], [15, 23, 24, 25]),
    ([(' Accordingly, the present study focused on two deliberately separated comparison axes, precocial versus altricial and terrestrial versus strongly aquatic-associated, while avoiding intermediate forms as far as possible. Because extant birds do not provide a truly aquatic altricial model suited to this design, chicken, duck, and pigeon were selected as the model species for this study.', False, False)], [15, 23, 41]),
        ([(' Within this contrast set, the next question was which eggshell traits and which glycoprotein features scale most consistently across the three species.', False, False)], []),
])

# ════════════════════════════════════════════════════════════════════════════
head("Mammillary morphology establishes the structural ordering")

mixed([
    ("Micro-CT analysis showed that the three eggshells display clearly distinct mammillary-layer morphologies (Fig. 1C). In ", False, False),
    ("G. gallus", False, True),
    (", mammillae were smoother overall and formed rounded projections. In ", False, False),
    ("A. platyrhynchos", False, True),
    (", mammillae showed more ridges and angular turns across the inner surface. ", False, False),
    ("C. livia", False, True),
    (" was dominated by discrete triangular-conical mammillae. Three-dimensional surface reconstructions agreed with the cross-sectional views, indicating that the three eggshells differ in mammillary geometry rather than representing minor variants of a shared inner-surface template.", False, False),
])

p_s0b = mixed([
    ("Quantification further showed a stable hierarchy in mammillary knob density and in the fraction of the eggshell occupied by crystal units grown outward from each mammillary knob (Fig. 1D). Mammillary knob density was highest in ", False, False),
    ("G. gallus", False, True),
    (" (171.36 ± 5.63 per mm²), exceeding both ", False, False),
    ("A. platyrhynchos", False, True),
    (" (155.22 ± 8.63 per mm²) and ", False, False),
    ("C. livia", False, True),
    (" (158.27 ± 11.39 per mm²), while duck and pigeon remained similar to each other. Crystal-unit proportion was highest in ", False, False),
    ("C. livia", False, True),
    (" (0.5321 ± 0.0389), intermediate in ", False, False),
    ("A. platyrhynchos", False, True),
    (" (0.4413 ± 0.0249), and lowest in ", False, False),
    ("G. gallus", False, True),
    (" (0.3975 ± 0.0127). These measurements indicated that chicken established the densest early mineralization field, pigeon allocated the largest eggshell fraction to crystal units grown from individual mammillary knobs, and duck remained intermediate between those endpoints. Because eggshell matrix proteins are known to be key regulators of eggshell microstructure, we next carried out a systematic comparative proteomics analysis to investigate the origin of these interspecific differences.", False, False),
])
cite(p_s0b, [1, 2, 28, 30, 36, 38])
cite(p_s0b, [53, 54, 57])

doc.add_page_break()
add_centered_figure("Fig1.jpg", width_cm=10.1, before=0, after=20)
add_main_figure_legend(
    "Fig. 1.",
    "Comparative framework and mammillary-layer morphology of the three focal avian species.",
    [
        ("(A) Three-dimensional AVONET comparison space built from 10,993 species records, with axes summarizing aquatic association, lifestyle-habitat discordance, and developmental mode. Colors denote avian orders; gray boxes highlight the deliberately separated regions occupied by the three focal species, and open circles mark ", False, False),
        ("Gallus gallus", False, True),
        (", ", False, False),
        ("Anas platyrhynchos", False, True),
        (", and ", False, False),
        ("Columba livia", False, True),
        (". (B) Phylogenetic relationship of representative avian taxa together with heatmap tracks for aquatic association (X), developmental mode (Z), and lifestyle-habitat discordance (Y); the three focal species are highlighted within this broader comparative frame. (C) Representative micro-CT sections and three-dimensional inner-surface reconstructions of the mammillary layer. Chicken shows smoother rounded mammillae, duck more ridged and angular mammillae, and pigeon discrete triangular-conical mammillae. Scale bars, 100 μm. (D) Boxplots of mammillary density and unit volume ratio across species. Points denote individual measurements; P values from one-way ANOVA are shown above the plots, and different letters indicate Duncan's multiple range test groupings.", False, False),
    ],
    before=20,
    after=80,
)
doc.add_page_break()

# ════════════════════════════════════════════════════════════════════════════
# S_prot  Eggshell matrix proteome orthogroup analysis
# ════════════════════════════════════════════════════════════════════════════
head("Proteome background narrows toward a glycan-centered explanation")

p_sprot_bg = spara([
    ("Across the eggshell matrix proteomes of the three species, orthogroup analysis identified a large shared core together with pairwise-shared and lineage-restricted complements (Fig. S2).", [11, 20, 52, 53, 54]),
    (" At the overall level, this eggshell matrix-protein layer still preserved the comparative framework defined by phylogenetic relatedness (Fig. S3).", []),
    (" This indicated that the comparison was shaped not by wholesale replacement of the eggshell matrix-protein toolkit, but by differential deployment within a common protein repertoire.", []),
])

p_sprot_go = spara([
    ("GO enrichment and gene-family turnover further indicated stable divergence among the three lineages in immune and defense-related background (Figs. S4 and S5).", [3, 5, 14, 15, 24, 25, 26, 29, 52]),
    (" Functionally, this pattern was also biologically interpretable: in G. gallus and A. platyrhynchos, antimicrobial defense appeared to remain more strongly associated with the eggshell and its surface barrier, whereas in C. livia it appeared to shift more toward the egg-white system; the more evident immune-related expansion in duck may further relate to greater pathogen exposure in an aquatic setting.", []),
])

p_sprot_focus = spara([
    (" At the same time, the G. gallus-exclusive set was significantly enriched for protein N-linked glycosylation (BP; Fig. S4), further indicating that the differences worth pursuing across the three species were present not only in defense background but also at the level of modification on shared eggshell matrix proteins.", []),
    (" Together with prior evidence that the same eggshell proteins can assume different functions according to glycosylation state and eggshell compartment, this signal further narrowed the analysis from broad proteome background to comparative glycoproteomics, and specifically to how N-linked glycosylation states on shared key matrix proteins were reconfigured across the three species.", [8, 18, 19, 21]),
])

head("Matrix-protein glycan states identify the leading shared candidate")

p_s2a = mixed([
    ("Using intact glycopeptides, this study obtained a direct view of specific glycoforms on avian eggshell matrix proteins. That layer then allowed identification of the molecular difference that most closely tracked the ordered eggshell phenotype. The glycoprotein network in Fig. 2 first defines the overall architecture of the dataset: a three-species conserved core at the center, pairwise-shared sectors surrounding it, and lineage-restricted peripheral repertoires linked outward to seven glycan classes. Among 516 quantitatively compared nodes, only 129 belonged to the three-species core, whereas the duck-pigeon shared sector was by far the largest peripheral block and the single-species sectors were dominated by duck and then pigeon. The network therefore indicated that glycoproteomic similarity does not simply recapitulate the classical species tree, but instead combines conserved, pairwise-shared, and lineage-restricted layers in the same architecture. The glycan layer carried the same message. High Mannose and Complex-Fucosylated glycans were broadly reused across multiple protein families, indicating that they contribute to a widespread background rather than to a small number of exceptional lineage-specific proteins. By contrast, more extended sialylated classes were less globally frequent but disproportionately associated with peripheral difference nodes, making them more useful as indicators of finer candidate-protein redeployment. The main value of the network, therefore, was not to identify the most abundant glycan class globally, but to show that core conservation, peripheral redeployment, and glycan reuse coexist in the same dataset and naturally narrow the candidate space toward a smaller set of proteins suitable for stricter ortholog and structural comparison.", False, False),
])

add_centered_figure("Fig2.jpg", width_cm=14.6)
add_main_figure_legend(
    "Fig. 2.",
    "Cross-species glycoprotein network architecture.",
    [
        ("Circular network linking orthologous eggshell glycoproteins to seven glycan classes across chicken, duck, and pigeon. The innermost concentric region represents the three-species conserved glycoprotein core; surrounding sectors partition pairwise-shared and lineage-restricted repertoires; and the outer glycan-class nodes summarize connections to High Mannose, Paucimannose, Hybrid, Complex-Plain, Complex-Fucosylated, Complex-Sialylated, and Other glycans. Curved links connect protein nodes to glycan classes, and the outer callouts report the number of proteins assigned to each class. Together, the network shows that a conserved glycoprotein core is retained across species while glycan usage and peripheral redeployment remain strongly asymmetric.", False, False),
    ],
)

p_s2b = mixed([
    ("To determine whether those glycan differences reflected biologically comparable proteins rather than broad lineage replacement, we next focused on the orthologous glycoprotein subset retained after a stricter BlastP-based filter and summarized that shared candidate space in Fig. 3A. Using ", False, False),
    ("G. gallus", False, True),
    (" as the reference, non-reference candidates were retained only when the mean E-value was below 1 × 10⁻⁵ and either average sequence identity reached at least 40% for structurally concordant HSP sets or maximum identity reached at least 40% when HSP counts were discordant. This filtering restricted the downstream comparison to high-confidence orthologs with stronger functional comparability, so that glycan differences were less likely to reflect wholesale lineage replacement rather than differential deployment of biologically comparable proteins. Under that stricter mapping, OC17 was glycosylated only in chicken, consistent with its established association with early crystal mineralization and calcite habit control, and therefore more suggestive of a chicken-specific proximal mineralization program. By contrast, OC116, TRFE, and OVAL all retained glycosylation signals across the three species, making them more suitable shared anchors for cross-species comparison. Among these, OC116 remained closest to matrix organization and mineral deposition, TRFE combined ion-binding and antimicrobial functions, and OVAL showed the most consistent species-ordered glycan reconfiguration. That combination of cross-species retention plus ordered glycan-state divergence made OVAL the most informative target for the subsequent structural analysis.", False, False),
])
cite(p_s2b, [6, 7, 8, 9, 10, 19, 21, 29])

p_s2c = spara([
    ("Integrating protein abundance and glycan abundance into the same analytical frame then clarified why OVAL, rather than OC116 or TRFE, best tracked the ordered eggshell phenotype (Fig. 3B-D). At the whole-dataset level, protein-glycan coupling was weak and non-significant in chicken (Spearman rho = 0.147, P = 2.676 × 10⁻¹), but became clearly positive in duck and pigeon (rho = 0.424, P = 5.256 × 10⁻¹³; and rho = 0.430, P = 1.736 × 10⁻¹⁰, respectively), indicating that glycosylation investment scaled more tightly with protein expression in the latter two lineages.", []),
    (" Yet the highlighted eggshell-matrix proteins showed that high abundance and high glycan output were not interchangeable. OVAL and OC116 both sat within roughly the top 1% of the protein-abundance distribution in all three species, but their glycan burdens diverged sharply: chicken OVAL remained protein-rich while only mid-ranking at the glycan level, duck OVAL carried a stronger glycan signal, and pigeon OVAL combined top-tier protein abundance with one of the strongest glycan outputs; OC116 was the single most abundant protein in both chicken and pigeon, yet its glycan burden was comparatively modest in chicken and much stronger in duck and pigeon. TRFE, by contrast, remained high in both protein and glycan space across all three species, whereas OC17 appeared only in the chicken panel, consistent with lineage-restricted deployment. OVAL therefore differed from OC116 and TRFE by combining cross-species retention, abundance, ordered glycan-state variation, and direct structural interpretability. A robust cross-species candidate required both biological comparability across taxa and glycan variation not reducible to protein abundance alone, and OVAL was the only shared target that satisfied both conditions cleanly in the present dataset.", []),
    (" The pairwise enrichment plots in Fig. 3E-G sharpened the same distinction. In Gallus-versus-Anas and Gallus-versus-Columba comparisons, OVAL and especially OC116 fell far below the y = x line: chicken retained equal or higher protein abundance, but the glycan signal shifted strongly toward duck or pigeon. TRFE stayed much closer to the diagonal, indicating more coordinated protein and glycan change. In the Anas-versus-Columba comparison, OVAL and TRFE again moved broadly in parallel, whereas OC116 shifted into the glycan-enriched quadrant despite lower protein abundance in duck. The intact-glycopeptide assignments further distinguished OVAL, which alone resolved into a clean species-ordered progression from compact High-Mannose glycans in chicken to neutral complex glycans in duck and more extended Sialylated Complex/Hybrid glycans in pigeon, whereas OC116 and TRFE changed without the same monotonic ordering. Figure 3B-G therefore identified OVAL as the shared protein whose glycosylation was most consistently decoupled from bulk abundance in an ordered, phenotype-relevant manner.", [1, 4, 6, 7, 8, 18, 47, 48]),
])

p_s2d = spara([
    ("Because those OVAL glycan classes differ strongly in steric bulk and charge distribution, the comparative signal pointed to OVAL surface accessibility rather than OVAL abundance alone as the molecular variable most likely to influence eggshell mineralization output.", [1, 4, 6, 7, 8, 18, 47, 48]),
    (" When abundance alone no longer explains the pattern, the relevant question becomes how glycan state changes the chemical surface available to participate in early mineralization events. The mechanism therefore narrows from 'which protein is present' to 'which chemically relevant surface remains exposed,' a question that can be tested directly by structural ensembles and electrostatic calculations rather than inferred only from abundance matrices.", [1, 4, 6, 7, 8, 18, 42, 47, 48]),
])

add_centered_figure("Fig3.jpg", width_cm=15.5)
add_main_figure_legend(
    "Fig. 3.",
    "Ortholog screening and abundance-decoupled glycoprotein prioritization.",
    [
        ("(A) Circos-style summary of the orthologous glycoprotein subset retained after stringent BlastP filtering, highlighting shared candidate proteins across chicken, duck, and pigeon. Species are color-coded, and gray labels indicate chicken proteins without retained non-chicken orthologs under the final comparison criteria. OVAL, OC116, TRFE, and OC17 are emphasized as the key interpretable targets. (B to D) Proteotype coevolution plots comparing log2-transformed protein abundance and glycan abundance within chicken, duck, and pigeon, respectively; inset values show Spearman's ρ and two-sided P. Highlighted proteins identify cases where glycan investment diverges from protein abundance. (E to G) Pairwise two-dimensional glycan-protein enrichment plots for Gallus versus Anas, Gallus versus Columba, and Anas versus Columba. OVAL shows the most consistent species-ordered shift away from abundance matching and was therefore prioritized for structural interpretation.", False, False),
    ],
)

head("Re-Glyco links glycan-state divergence to biophysical accessibility")

p_s3a = spara([
    ("OVAL then emerged as the strongest candidate for testing whether the species-ordered glycan classes could be translated into a concrete structural mechanism. In vitro work has already shown that OVAL can bind Ca²⁺ under mineralizing conditions, undergo partial unfolding, and participate in early mineralization-related assembly, making its glycan state a biologically plausible control layer. Eighteen dominant glycosylated OVAL ensembles were therefore rebuilt together with matched deglycosylated reference structures to test whether the three species differ primarily through glycan-dependent surface behavior rather than through backbone sequence alone.", [6, 7, 11, 12, 18, 42, 43]),
    ("Panels A-C showed that glycosylation changed OVAL properties within species, whereas the deglycosylated backbones were much more similar across species. In chicken, glycosylation left hotspot count almost unchanged relative to apo OVAL, whereas in duck and pigeon it reduced the accessible hotspot pool more clearly. The same within-species contrast extended to electrostatic output: pigeon glycosylation shifted the surface toward more negative values, chicken changed little, and duck remained intermediate. Once glycans were removed, the three OVAL states no longer remained separated to the same extent in hotspot count and electrostatic output, indicating that much of the ordered divergence was introduced by glycosylation rather than by the protein scaffold alone. The comparative signal therefore remained strongest in the glycosylated state. Apo references further served as an internal control: once glycans were stripped away, much of the cross-species separation collapsed, showing that the ordered signal was not simply a by-product of distant sequence divergence carried through the structural models (Fig. S7).", [11, 12, 42, 43]),
    ("The glycan-layer geometry clarified the basis of this separation. The rebuilt pigeon glycans occupied the largest conformational space, with greater extension away from the sequon while also maintaining closer transient surface contact, whereas chicken and duck remained more compact. Geometric difference was therefore translated into surface shielding rather than glycan size alone. The pigeon state represented both a larger glycan envelope and a more persistent occupation of protein-surface territory that would otherwise remain available to acidic hotspot exposure. Chicken occupied the opposite extreme, retaining the smallest and least shielding glycan state, while duck consistently remained intermediate. The three species therefore differed not only in glycan identity, but also in how much of the acidic OVAL interface remained available to local ion approach during early mineralization (Fig. 4D-G).", [11, 12, 42, 43, 44, 45, 46]),
    ("That geometric ordering propagated directly into the accessibility readout. Interface shielding increased from chicken to duck to pigeon (Fig. 4H), while the fraction of candidate acidic residues retained as accessible Ca²⁺ hotspots declined in the opposite direction (Fig. 4J). At that stage, however, two related but non-identical summaries become useful. Panel L partitions hotspot accessibility by residue count, asking how many candidate Ca²⁺-relevant sites remain net accessible after glycan shielding. Panel M instead partitions hotspot-residue SASA, asking how much exposed surface area remains on those chemically relevant residues. Those two readouts need not rank species identically in every detail, because shielding more residues is not equivalent to removing the same amount of exposed area from each residue. That distinction explains why duck and pigeon can converge more strongly in accessible hotspot counts while still differing in how shielding is distributed across surface area. The hotspot metric used here therefore captures the exposure of surface Asp/Glu positions that satisfy a Ca²⁺-relevant accessibility definition rather than whole-protein solvent exposure, and Figure 4 links glycan geometry, surface shielding, hotspot number, and hotspot-area suppression on OVAL within the same structural framework. In practical terms, chicken retained the highest OVAL Ca²⁺ accessibility, duck was intermediate or converged downward depending on whether count or area was being summarized, and pigeon remained the most shielded state overall. That ordering helps close the mechanistic loop: higher Ca²⁺ accessibility should make chicken OVAL more permissive to the partial unfolding linked previously to early mineralization, thereby allowing faster mineralization onset and ultimately contributing to the higher mammillary-knob density seen in chicken.", [11, 12, 42, 43, 44, 45, 46, 49, 50, 51]),
])

doc.add_page_break()
add_centered_figure("Fig4.jpg", width_cm=15.2, before=0, after=20)
add_main_figure_legend(
    "Fig. 4.",
    "Re-Glyco and APBS analyses define an OVAL accessibility gradient across species.",
    [
        ("(A) Number of Ca²⁺ hotspot residues, defined as surface Asp/Glu positions with APBS potential below −5 kT/e, in glycosylated and matched deglycosylated OVAL ensembles. (B) Carboxylate surface accessibility. (C) Surface electrostatic potential distributions for glycosylated versus deglycosylated structures. (D to G) Ensemble geometric descriptors of the rebuilt glycans, including radius of gyration, end-to-end distance, glycan-protein distance, and minimum glycan-backbone distance. (H) Glycan-mediated interface shielding. (I) Mean solvent-accessible surface area (SASA) of hotspot residues. (J) Hotspot fraction among candidate acidic residues. (K) Net accessible Ca²⁺ hotspots. (L) Partition of hotspot accessibility into net accessible and glycan-shielded components. (M) Partition of hotspot-residue SASA into net accessible and glycan-shielded components. Species-specific ensemble sizes are indicated beneath the violins. Species comparisons in panels D to M used one-way ANOVA followed by Duncan's multiple range test; glycosylated-versus-apo contrasts in panels A to C were evaluated against the apo reference by one-sample t test, with significance annotations shown above the brackets. Across these metrics, chicken retained the most exposed Ca²⁺-relevant surface, pigeon showed the strongest glycan-mediated shielding, and duck remained intermediate.", False, False),
    ],
    before=20,
    after=80,
)
doc.add_page_break()

head("Local mechanics preserves the ordered biomineralization signal")

p_s4a = mixed([
    ("The glycoproteomic, structural-ensemble, and electrostatic results together indicated that glycan-dependent matrix chemistry can reshape mammillary-layer mineralization mode. The remaining question was whether those mammillary differences translated into a biologically relevant functional consequence. Because the three model species span precocial versus altricial as well as terrestrial versus semi-aquatic comparison axes, the hatching scenario in which the egg tooth locally presses the shell from the inner side was simulated next. Previous studies have effectively measured whole-eggshell strength under outside loading, but the relevant readout here was the local response of the mammillary interface during escape, and a different loading logic was therefore adopted. Figure 5A summarizes the hatching-relevant loading background, whereas Fig. 5B-D show species-specific egg-tooth geometry together with the corresponding micro-CT-derived finite-element setups. This distinction matters because the biological question here is not generalized shell strength, but whether local resistance at the mammillary contact interface remains aligned with the molecular and structural ordering recovered above. Using a conical indenter to approximate the egg tooth, impact loading was applied to circular eggshell fragments (model diameter D = 2.0 mm) at nine parameterized lateral-offset positions on a 3 × 3 grid (0.5 mm spacing), yielding n = 9 independent contact shear-stress time courses per species. To minimize the influence of sampling-model size, gross geometry, and especially eggshell thickness, both raw peak contact force (F_max) and peak contact shear stress (τ_max) were recorded. Here, τ_max is used as a metric of local hatching resistance and, because it is evaluated at the mammillary contact interface, as an operational readout of mammillary-interface resistance during hatching. Peak τ_max was extracted directly from the finite-element output at each offset position and species means ± s.d. were then calculated across the nine positions (Fig. S8A-F; eggshell thicknesses: ", False, False),
    ("G. gallus", False, True),
    (" 0.29 mm, ", False, False),
    ("A. platyrhynchos", False, True),
    (" 0.35 mm, and ", False, False),
    ("C. livia", False, True),
    (" 0.19 mm).", False, False),
])

doc.add_page_break()
add_centered_figure("Fig5.jpg", width_cm=13.8, before=0, after=20)
add_main_figure_legend(
    "Fig. 5.",
    "Hatching-relevant loading design and species-specific finite-element setup.",
    [
        ("(A) Schematic of the egg tooth pressing the eggshell from the inner side during hatching. (B to D) Species-specific egg-tooth photographs with the corresponding micro-CT-derived finite-element setups for ", False, False),
        ("Gallus gallus", False, True),
        (", ", False, False),
        ("Anas platyrhynchos", False, True),
        (", and ", False, False),
        ("Columba livia", False, True),
        (", respectively. In each species panel, the left image shows the external morphology of the egg tooth or beak tip used to motivate the impactor geometry, and the right image shows the eggshell-fragment mesh, conical impactor, and representative von Mises stress field at contact. Together, these panels define the hatching-relevant loading background and show that the simulations were built from reconstructed shell geometry rather than idealized shells.", False, False),
    ],
    before=20,
    after=80,
)
doc.add_page_break()

mixed([
    ("One-way ANOVA of F_max across the nine offset positions supported a significant three-level hierarchy (p = 1.639 × 10⁻¹³): ", False, False),
    ("G. gallus", False, True),
    (" 1.117 ± 0.110 N > ", False, False),
    ("A. platyrhynchos", False, True),
    (" 0.898 ± 0.090 N > ", False, False),
    ("C. livia", False, True),
    (" 0.485 ± 0.039 N, with all pairwise differences significant (Fig. 6A). Notably, τ_max collapsed into a two-level pattern (p = 6.644 × 10⁻¹⁰): ", False, False),
    ("G. gallus", False, True),
    (" τ_max = 551.6 ± 108.8 MPa was significantly higher than ", False, False),
    ("A. platyrhynchos", False, True),
    (" 404.0 ± 39.6 MPa and ", False, False),
    ("C. livia", False, True),
    (" 393.0 ± 35.2 MPa, whereas the latter two species did not differ significantly from each other (Fig. 6B).", False, False),
])

mixed([
    ("The divergence between F_max and τ_max rankings showed that duck's higher raw contact force was driven mainly by its greater shell thickness (0.35 mm versus 0.19 mm in pigeon), rather than by superior unit-area material resistance. By contrast, ", False, False),
    ("G. gallus", False, True),
    (" exhibited a 36-40% increase in τ_max relative to the two non-precocial species, indicating higher local hatching resistance independent of shell thickness. The τ_max grouping, with ", False, False),
    ("G. gallus", False, True),
    (" alone in the high group and ", False, False),
    ("A. platyrhynchos", False, True),
    (" together with ", False, False),
    ("C. livia", False, True),
    (" in the low group, matched exactly the DMRT grouping for mammillary density recovered by micro-CT (Fig. 1D).", False, False),
])

mixed([
    ("Whole-shell fracture force alone could make duck appear mechanically superior to chicken because of its greater shell thickness, despite the absence of the same high-density mammillary state. By focusing on local hatching resistance at the micro-CT-derived mammillary interface, τ_max removes that ambiguity and recovers the structural ordering predicted from glycoproteomics and Re-Glyco modeling.", False, False),
])

mixed([
    ("The mechanical analysis therefore asks whether the same ordering inferred from glycan class, OVAL surface accessibility, and mammillary microstructure remains visible under hatching-relevant loading. Not every coarse-grained mechanical metric reproduced that molecular signal, but the metric most directly tied to the local mammillary contact interface did. Structural information was therefore retained specifically at the level of local hatching resistance.", False, False),
])

mixed([
    ("The finite-element analysis therefore does more than add a general mechanical description: it tests whether the ordering inferred from glycoproteomics and structural modeling remains valid when the eggshell is treated as a hatching-relevant mechanical system. Preservation of the chicken-high versus duck/pigeon-lower grouping at the τ_max level shows that this ordering is indeed retained through to the functional endpoint of local hatching resistance.", False, False),
])

mixed([
    ("By the τ_max criterion, ", False, False),
    ("G. gallus", False, True),
    (" formed a distinct high-resistance group, while ", False, False),
    ("A. platyrhynchos", False, True),
    (" and ", False, False),
    ("C. livia", False, True),
    (" clustered together at lower values. That grouping reproduced the mammilla-density hierarchy from micro-CT and provided the functional endpoint of the preceding molecular-to-structural argument: the glycosylation-associated differences identified above are not only compatible with altered mammillary organization, but are propagated into a simulated difference in local hatching resistance across the three model species.", False, False),
])
add_centered_figure("Fig6.jpg", width_cm=15.5)
add_main_figure_legend(
    "Fig. 6.",
    "Force and local hatching resistance across species.",
    [
        ("(A) Mean contact-force time courses across nine impact positions for ", False, False),
        ("Gallus", False, True),
        (", ", False, False),
        ("Anas", False, True),
        (", and ", False, False),
        ("Columba", False, True),
        (", shown with shaded ±1σ envelopes, together with boxplots of peak contact force (Fmax). (B) Mean contact shear-stress time courses for the same nine positions together with boxplots of peak shear stress (τmax). Symbols on the curves mark the species mean peak value; points in the boxplots denote individual impact positions (n = 9 per species). P values from one-way ANOVA are shown above the boxplots, and different letters indicate Duncan's multiple range test groupings. Fmax preserves a three-level hierarchy, whereas τmax separates chicken from the lower-τmax duck and pigeon group, indicating that local hatching resistance at the mammillary interface most closely tracks the structural ordering inferred from morphology and OVAL accessibility.", False, False),
    ],
)

cite(p_s4a, [16, 17, 34, 35, 37, 38])

# ════════════════════════════════════════════════════════════════════════════
# Discussion
# ════════════════════════════════════════════════════════════════════════════
para("Discussion", bold=True, size=14, before=320, after=160,
    align=WD_ALIGN_PARAGRAPH.LEFT)

p_disc_mam1 = smixed([
    ([('Across chicken, duck, and pigeon, ecological divergence and developmental strategy correspond to distinct eggshell-building programs. Within that comparative frame, mammillary-layer mineralization mode, OVAL glycan class, computed Ca²⁺ accessibility, and simulated local hatching resistance converge on the same axis. ', False, False),
            ("G. gallus", False, True),
            (" defines a high-density, high-resistance state; ", False, False),
            ("A. platyrhynchos", False, True),
            (" occupies a stable intermediate state; and ", False, False),
            ("C. livia", False, True),
            (" marks a lower-density, lower-accessibility state.", False, False)], [1, 2, 4, 15, 16, 17, 20, 21, 23, 38, 39, 41, 42]),
        ([(" Mammillary-layer mineralization mode remains central because it is the earliest structural level at which matrix chemistry, crystal-unit initiation, and later mechanical behavior become joined in the mature eggshell.", False, False)], [1, 2, 20, 28, 30, 36, 38, 53, 54]),
])

p_disc_mam2 = spara([
    ("Not all molecular layers aligned equally with the ordered structural phenotype.", []),
    (" The strongest molecular signal was the signal that most consistently recovered that structural ordering across species.", []),
    (" Orthogroup turnover, gene-family change, and glycoprotein-network divergence all show that the three lineages differ historically, but those layers mainly define the evolutionary background of the comparison rather than its most proximate explanatory feature.", [1, 2, 8, 18, 21, 27]),
    (" OVAL N-glycan architecture is more informative because it is ordered across species, chemically interpretable, and positioned on a highly abundant matrix protein already implicated in mineralization.", [4, 6, 7, 18, 21, 42, 44, 45, 46]),
    (" OVAL glycan state most cleanly bridges broad proteomic divergence and the ordered structural phenotype measured here, making it the most consistent molecular variable in the present three-species framework.", [20, 21, 42, 61, 63, 66, 74, 78, 80]),
])

p_disc_other = para(
    "The non-OVAL signals also remain informative. OC116 showed substantial glycosylation divergence across the species comparisons, and that variability is biologically plausible in light of recent evidence that avian protein repertoires can vary markedly across and within species. Combined with the long-recognized proteoglycan character of OC116 and the fact that its full spatial architecture is still unresolved, the present pattern is consistent with a molecule whose function may depend on coordinated interactions across multiple domains and binding partners rather than on a single easily modeled surface. TRFE, by contrast, remained comparatively similar in glycosylation level across the three species. That stability is also interpretable: glycans can themselves operate as shielding elements in host-defense contexts, and an immune-associated matrix protein may therefore be expected to retain a relatively conserved glycan barrier even when other mineralization-linked proteins diversify more strongly. OC17 also deserves consideration. Because it was glycosylated only in chicken and has been implicated in early calcite mineralization and calcite-habit modulation, its lineage-restricted deployment could plausibly contribute to the smoother and more rounded mammillary morphology seen in chicken. At present, however, that possibility remains provisional because the dataset does not yet resolve whether the relevant effect depends primarily on OC17 glycosylation state itself, protein abundance, or local interaction with other matrix components."
)

cite(p_disc_other, [10, 19, 21, 29, 42, 44, 45, 46, 66, 81])

p_disc_oval = para(
    "Re-Glyco and APBS analyses support a concrete structural model. Compact chicken glycans leave the critical acidic OVAL surface relatively exposed, whereas the longer and more electronegative pigeon glycans reduce Ca²⁺ approach both sterically and electrostatically; duck again falls between those endpoints. Because the predicted accessibility ranking parallels the measured mammilla-density ranking, the glycan signal is unlikely to be a passive lineage marker. These data support a structural link between OVAL glycan state and mineralization phenotype."
)

cite(p_disc_oval, [4, 11, 12, 42, 44, 45, 46, 49, 50, 51, 52, 55, 65])

p_disc_axis = spara([
    ("Mammillary-layer mineralization mode therefore remains the central structural level in the interpretation.", [1, 2, 20, 28, 38]),
    (" Once early calcite crystal units are established, later eggshell regions inherit the spacing logic created in that first mineralization window.", [1, 2, 28, 30]),
    (" A dense mammillary field therefore changes more than morphology: it reorganizes matrix retention, mineral continuity, and local stress redistribution, making the mammillary layer a developmental and mechanical boundary condition for the rest of the eggshell.", [1, 2, 30, 36, 38]),
])

p_disc_regulator = spara([
    ("Duck preserves a three-state comparison rather than a simple precocial-versus-altricial contrast.", [4, 15, 23, 27, 39, 41]),
    (" If developmental mode alone dictated eggshell-building chemistry, duck should cluster with chicken throughout the molecular and mechanical analyses.", [15, 23, 27]),
    (" It does not: it retains the broad life-history condition of precocial development while shifting toward an intermediate OVAL glycan state, an intermediate accessibility profile, and an intermediate mechanical outcome.", [4, 12, 16, 17, 39, 41]),
    (" Duck therefore indicates that developmental program frames the problem but does not by itself determine the biochemical solution adopted by the eggshell-forming system.", [4, 12, 15, 23, 27, 39, 41]),
])

p_disc_discriminate = spara([
    ("Several plausible background variables can be separated from the features that repeatedly recover the ordered phenotype.", []),
    (" Eggshell thickness, body size, and broad reproductive ecology may all contribute background variation, and lineage history undoubtedly matters.", [2, 14, 16, 17, 24, 25]),
    (" But thickness-based explanations do not recover the τ_max ordering, and diffuse lineage-divergence explanations do not account for why the same ordered progression recurs in glycan class, electrostatic accessibility, and mammillary-layer mineralization mode.", [4, 16, 17, 20, 21, 38, 42]),
    (" Some variables define the design space, whereas others repeatedly recover the phenotype itself.", [1, 2, 4, 20, 21, 38, 42]),
    (" Ecology and phylogeny establish the comparison frame, whereas OVAL glycan state is the proximate feature that most consistently tracks the structural phenotype in this three-species dataset.", [1, 2, 4, 20, 21, 38, 42, 57, 70]),
])

p_disc_mech = spara([
    ("The mechanical analysis extends the same pattern to an organism-level functional context.", [16, 17, 38]),
    (" τ_max rather than raw fracture force tracks the mammillary hierarchy.", [16, 17, 34, 35, 37, 38]),
    (" Absolute failure load remains sensitive to eggshell thickness and whole-eggshell geometry, whereas τ_max provides a more direct readout of local hatching resistance at the mammillary interface under hatching-relevant loading.", [16, 17, 34, 35, 37, 38]),
    (" The convergence of duck and pigeon in τ_max despite their different overall mammillary geometries suggests that once the high-density chicken state is lost, downstream shape variation alone does not restore the same mammillary-interface resistance. This extends the molecular-to-structural signal into a functional readout rather than leaving it as a descriptive correlation.", [1, 2, 16, 17, 38]),
])

p_disc_evo = para(
    "The mechanical results also suggest a compensatory evolutionary logic. Duck lacks the chicken-like high-accessibility glycan state yet still maintains a relatively high overall force threshold because its shell remains thicker; in other words, thickness may buffer against a drop in local material resistance when glycosylation-linked mineralization no longer occupies the chicken extreme. In a broader avian evolutionary context, this pattern raises a tractable question for future sampling: whether shifts in glycosylation strategy accompanied transitions along the precocial-to-altricial spectrum, with shell thickness serving in some lineages as a compensatory route that prevents abrupt loss of shell strength. The present three-species dataset does not test that macroevolutionary proposal directly, but it does identify a specific phenotype-protein-modification-mechanics axis on which such a test can be built."
)

cite(p_disc_evo, [3, 15, 16, 17, 37, 38, 39, 41, 57])

p_disc_function = para(
    "In evolutionary terms, these findings place glycan class as a plausible intermediary between broad selective background and mineralization strategy. Eggshell diversification is therefore not reduced to a single variable; instead, broader ecological and developmental differences become legible at a chemically specific layer. A tunable post-translational state on an abundant matrix protein offers one way for eggshell systems to diversify while retaining a broadly conserved protein toolkit. Glycoprotein state can connect matrix chemistry, microstructure, and biomechanical consequence within the same comparative frame. Similar principles may extend beyond avian eggshells, because many mineralized systems rely on abundant matrix proteins whose post-translational states can shift without wholesale replacement of the underlying protein repertoire. By clarifying how chemically specific surface states bias mineral growth, this perspective may also inform how human skeletal development, regeneration, and experimentally tractable biomineralization models are interpreted. The present dataset supports a cross-scale relationship in which ecological contrast, molecular surface state, structural organization, and localized mechanics remain linked."
)

cite(p_disc_function, [4, 6, 7, 18, 20, 21, 42, 49, 50, 52, 62, 67, 68, 69, 71, 72, 73, 75, 77, 79])

p_disc_selection = para(
    "OVAL glycan state defines a chemically specific comparative layer that can be mapped onto structure and evaluated against function. In omics-rich biomineralization studies, lineage differences are often easier to detect than the molecular features that organize phenotype itself. Here, that organizing layer lies in glycan state rather than in broad proteome turnover. Similar roles in other mineralized systems could be played by sulfation, phosphorylation, proteolytic processing, or regulated cofactor binding on abundant matrix proteins, particularly where the same major matrix components are reused across divergent structural contexts."
)

cite(p_disc_selection, [20, 21, 42, 49, 50, 52, 58, 59, 60, 65, 66, 74])

p_disc_future = para(
    "Caveats merit emphasis. We analyzed dominant glycoforms rather than full in vivo heterogeneity, in part because current glycan-structure libraries remain incomplete and some experimentally relevant structures are still missing from the reference space needed for reliable ensemble rebuilding. We therefore retained the dominant forms that could be supported consistently across the three-species comparison, treated each species as mechanically uniform at the scale of the mean eggshell, and relied on incompletely constrained uterine ionic conditions in the APBS framework. These limits define the next experimental steps: defined-glycoform mineralization assays, site-directed manipulation of OVAL glycosylation together with uterine chemistry measurements, site-resolved mechanical validation, and broader phylogenetic sampling to determine whether the three-species axis reported here is recurrent or only one branch within a larger design space. Such work should clarify whether OVAL glycan state participates directly in mineralization or serves primarily as a comparative molecular indicator, and whether the same axis extends beyond the present ecological and developmental contrast set."
)

cite(p_disc_future, [4, 11, 12, 20, 21, 42, 49, 50, 51, 52, 57, 70, 76])

p_disc_close = para(
    "Taken together, these results identify a chemically specific post-translational feature that organizes an otherwise heterogeneous comparative landscape. Comparative ecology and development separate chicken, duck, and pigeon as distinct life-history states; micro-CT resolves a corresponding hierarchy in mammillary-layer organization; glycoproteomics narrows the shared candidate space to OVAL, with OC116, TRFE, and lineage-restricted OC17 providing informative contrasts; structural ensemble modeling and electrostatics show that OVAL glycan state reorders Ca²⁺-relevant accessibility from the high-accessibility chicken state through duck to the more shielded pigeon state; and finite-element analysis shows that this molecular-to-structural ordering persists in local hatching resistance. Chicken therefore represents a high-density, high-accessibility, high-resistance endpoint, duck an intermediate and partially compensated state, and pigeon a lower-accessibility, lower-resistance endpoint. Other matrix features may also contribute, but the chemically specific surface state of an abundant matrix protein remains the most experimentally tractable explanatory layer in the present dataset."
)

cite(p_disc_close, [6, 7, 18, 20, 21, 42, 44, 45, 46, 49, 50, 72, 78, 80])

p_disc_limits = p_disc_close

# ════════════════════════════════════════════════════════════════════════════
# Methods
# ════════════════════════════════════════════════════════════════════════════
para("Materials and Methods", bold=True, size=14, before=320, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT)

head("Biological materials")

p_m_bio = mixed([
    ("Six freshly laid eggs from each of three avian species were collected within "
     "24 h of oviposition. ", False, False),
    ("Gallus gallus", False, True),
    (" (domestic chicken) eggs were obtained from the Poultry Resources Conservation "
     "Farm, China Agricultural University (Beijing, China); ", False, False),
    ("Columba livia", False, True),
    (" (rock pigeon) eggs were provided by Prof. Chang Yu, College of Veterinary "
     "Medicine, China Agricultural University; and ", False, False),
    ("Anas platyrhynchos", False, True),
    (" (Mallard duck) eggs were supplied by Jinxing Duck Industry (Beijing, China). "
     "All eggs were stored at 4\u00b0C until processing.", False, False),
])

head("Eggshell matrix protein extraction")

mixed([
    ("Eggshell matrix proteins were extracted from the eggshell mammillary layer "
     "(EML) by an established EDTA demineralization protocol. Eggs were rinsed with "
     "deionised water and placed in sterile sealed bags. For ", False, False),
    ("G.\u00a0gallus", False, True),
    (" and ", False, False),
    ("A.\u00a0platyrhynchos", False, True),
    (", the eggshell cuticle layer (ECL) was removed prior to EML "
     "extraction by treatment with 15 mL of 5% EDTA (0.13 mol/L, pH 7.6) supplemented "
     "with 2-mercaptoethanol (10 mmol/L) for 30 min at 20\u00b0C, with gentle manual "
    "kneading to separate the ECL; eggshells were subsequently rinsed with deionised "
     "water. EML proteins from all three species were then solubilised under the same "
     "EDTA\u20132-mercaptoethanol conditions with the extraction duration extended to 12 h "
     "at 20\u00b0C. The resulting suspension was centrifuged at 1,000 \u00d7 g for 15 min; the "
     "pellet was resuspended and centrifuged a second time, and the pooled supernatant "
     "was stored at \u221280\u00b0C until analysis.", False, False),
])

head("Micro-CT imaging and mammillary morphometry")

p_m_ct = para(
    "Two eggshell fragments (each approximately 4\u20135 mm\u00b2) were excised from the "
    "equatorial region of each species and scanned with a Phoenix V|tome|x\u00a0M "
    "microfocus CT system (GE Sensing and Inspection Technologies GmbH, Wunstorf, "
    "Germany) at 85 kV and 160 \u03bcA with no beam filter; scan settings were held "
    "constant across all specimens. Three-dimensional reconstructions were generated "
    "in 3D Slicer by threshold-based segmentation. Acquisition noise was suppressed by a 5 \u00d7 5 \u00d7 5 "
    "median filter, followed by largest-island isolation and 9 \u00d7 9 \u00d7 9 hole-filling. "
    "Within the same region of interest, three morphometric parameters were then calculated from the labelmap. "
    "The segmented shell model was first duplicated as a single-copy volume and solid-filled with the Fill Holes operation; "
    "subtraction of the original shell model from the filled solid yielded the mammillary interspace layer, and closed voids appearing in that interspace plane were defined as mammillary knobs. "
    "Mammilla density was calculated as mammilla count divided by ROI area. "
    "Total eggshell volume in the same ROI was obtained directly from the labelmap, and mean column-unit volume was defined as total shell volume divided by mammilla count; "
    "column-unit volume fraction was then calculated as mean column-unit volume divided by the total eggshell volume of the corresponding ROI. "
    "Because the columnar units initiated by mammillae are arranged as repetitive and approximately even planar units in normal avian eggshell microstructure, these parameters were treated as local average representatives of whole-shell organization (n\u202f=\u202f2 fragments per species)."
)
cite(p_m_ct, [1, 38])

head("Shotgun proteomics of eggshell matrix proteins")

para(
    "For each species, two eggs were pooled per biological replicate and three "
    "independent replicates were prepared (n\u202f=\u202f3 per species). Proteins were "
    "extracted by resuspension in lysis buffer (1% SDS, 1% protease inhibitor "
    "cocktail), sonication on ice, and clarification by centrifugation at "
    "12,000 \u00d7 g at 4\u00b0C for 10 min; protein concentration was determined with a "
    "BCA assay kit. Proteins were precipitated with pre-cooled acetone (5 volumes, "
    "\u221220\u00b0C, 2 h), washed twice with acetone, and redissolved in 200 mM TEAB. "
    "Disulfide bonds were reduced with 5 mM dithiothreitol (56\u00b0C, 30 min) and "
    "alkylated with 11 mM iodoacetamide (room temperature, 15 min, dark). Proteins "
    "were digested overnight with sequencing-grade trypsin (enzyme:protein ratio "
    "1:50) and desalted with Strata X SPE columns."
)

mixed([
    ("Desalted peptides were dissolved in 0.1% formic acid and separated on a "
     "home-made 15-cm \u00d7 100-\u03bcm i.d. reversed-phase C18 analytical column connected "
     "to a Vanquish Neo UPLC system (Thermo Fisher Scientific) at 400 nl/min over "
     "a 22.6-min gradient (4\u201399% solvent B; 0.1% formic acid in 80% acetonitrile). "
    "Separated peptides were analyzed on an Orbitrap Astral mass spectrometer "
     "(Thermo Fisher Scientific) with a nano-electrospray ionisation source (1,900 V). "
     "Full-MS spectra were acquired in the Orbitrap at 240,000 resolution over "
     "380\u2013980 m/z; MS/MS fragments were acquired in the Astral analyser at 80,000 "
     "resolution using HCD fragmentation (NCE\u202f=\u202f25%), fixed first mass 150 m/z, "
     "AGC target 500%, and maximum injection time 3 ms. DIA data were processed with "
     "DIA-NN v1.8 against species-specific reference proteomes \u2014 ", False, False),
    ("G.\u00a0gallus", False, True),
    (" (43,711 entries), ", False, False),
    ("A.\u00a0platyrhynchos", False, True),
    (" (91,801 entries), and ", False, False),
    ("C.\u00a0livia", False, True),
    (" (17,309 entries), all downloaded August 2024 \u2014 "
     "concatenated with reverse decoy sequences. "
     "Trypsin/P cleavage was specified with up to one missed cleavage; N-terminal "
     "methionine excision and carbamidomethylation of Cys were set as fixed "
     "modifications. Protein and peptide FDR were each controlled at < 1%.", False, False),
])

head("Intact glycopeptide mass spectrometry")

para(
    "N-glycopeptides were enriched from tryptic digests by hydrophilic interaction "
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
    "glycan-site signal intensity."
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
cite(p_m_ortho, [3, 5, 14, 24, 25])

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

head("N-glycan structural ensemble modeling")

p_m_reglyco = mixed([
    ("OVAL ortholog protein structures (AlphaFold2-predicted models) were "
     "accessed through the GlycoShape platform (glycoshape.org) via UniProt "
     "accession identifiers. "
     "Experimentally detected N-glycan compositions from IGP-MS were mapped "
     "to the GlycoShape glycan library by monoisotopic mass matching "
     "(tolerance \u00b10.5\u00a0Da), using per-residue masses of 203.0794\u00a0Da (HexNAc), "
     "162.0528\u00a0Da (Hex), 291.0954\u00a0Da (NeuAc), 146.0579\u00a0Da (dHex), and "
     "132.0423\u00a0Da (Pen) with an 18.0106\u00a0Da water correction; matched entries "
     "were retrieved as GlyTouCan accession identifiers. "
     "Full conformational ensembles were then generated with the GlycoShape "
     "Re-Glyco Ensemble tool (glycoshape.org/ensemble), which restores missing "
     "glycans by aligning them to torsion angles from Privateer crystallographic "
     "standards and sampling conformations from the GlycoShape molecular-dynamics "
     "ensemble library. "
     "For each protein, a session was created via the GlycoShape API to identify "
     "available N-glycosylation sequons in the structural model; each matched "
    "glycan was then submitted as an independent modeling job and attached to "
     "the target sequon \u2014 ", False, False),
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
     "including four NeuAc positional isomers resolved from the GlycoShape library). "
     "Ensemble geometric descriptors were calculated for each model from atomic "
     "coordinates using BioPython: the radius of gyration (Rg) of all glycan heavy "
     "atoms, the end-to-end distance of the glycan chain, and the minimum distance "
     "between any glycan heavy atom and protein C\u03b1 atoms (minimum C\u03b1 contact "
     "distance). Per-structure summary statistics (mean\u00a0\u00b1\u00a0s.d.) and pairwise species "
     "comparisons (Mann\u2013Whitney\u00a0U test, two-tailed) were performed for each descriptor.", False, False),
])
cite(p_m_reglyco, [11, 49, 50, 51])
cite(p_m_reglyco, [56, 58, 59, 60, 65])

head("Electrostatic potential calculation")

p_m_apbs = para(
    "Electrostatic surface potentials were computed for each Re-Glyco ensemble "
    "model and a matched deglycosylated (apo) reference using APBS v3.4.1. Atomic "
    "partial charges and radii were assigned with PDB2PQR using the CHARMM36 force "
    "field and PROPKA protonation at pH 7.4; glycan heavy-atom partial charges were "
    "assigned from the GLYCAM06 parameter set (Kirschner et al., 2008, J. Comput. "
    "Chem. 29:622). Solvent-accessible surface areas were calculated by the "
    "Shrake\u2013Rupley algorithm; surface residues were defined by relative ASA "
    "\u2265 0.25. Ca\u00b2\u207a-binding electrostatic hotspots were defined as surface Asp or "
    "Glu residues with APBS potential < \u22125 kT/e. Ensemble-level metrics reported "
    "include hotspot count (N_hot), per-hotspot mean SASA, hotspot fraction of total "
    "surface Asp/Glu, and median surface electrostatic potential."
)
cite(p_m_apbs, [12, 42, 43])

head("Finite-element analysis")

p_m_fea = mixed([
    ("The region of interest used for downstream finite-element analysis was defined as a cylindrical volume of 1 mm radius during micro-CT reconstruction. ", False, False),
    ("Surface models derived from micro-CT were first exported as STL files and reverse-engineered in Geomagic Wrap for finite-element pre-processing by sequential de-noising (strength 2), triangle simplification to approximately 300,000 faces, mesh re-gridding at 0.01 mm, iterative defect correction to zero residual faults, and organic parametric surface fitting at minimum tolerance. The resulting eggshell surface models were then imported into LS-DYNA "
     "(Ansys) for explicit dynamic finite-element analysis (unit system: "
     "mm/kg/N/s). The eggshell was assigned elasto-plastic material properties "
     "(Young's modulus E\u202f=\u202f3.0 \u00d7 10\u00b9\u2070 Pa; yield strength \u03c3y\u202f=\u202f1.5 \u00d7 10\u2077 Pa; "
     "tangent modulus 0; maximum equivalent plastic strain at failure 0.05). "
     "The impactor, simulating the caruncle-borne egg tooth, was a frustum "
     "(base radius 0.1 mm; top radius 0.5 mm; height 0.5 mm) assigned IRON-ARMCO "
     "explicit material properties. Frictional contact between impactor and eggshell "
    "was set at \u03bc\u202f=\u202f0.2. Eggshell mesh element sizes were 0.05 mm (", False, False),
    ("G. gallus", False, True),
    ("), 0.05 mm (", False, False),
    ("A. platyrhynchos", False, True),
    ("), and 0.03 mm (", False, False),
    ("C. livia", False, True),
    ("), ensuring \u2265 6 element layers across the eggshell cross-section; the impactor "
     "was meshed at 0.1 mm. An initial velocity of 50,000 mm/s was applied to the "
     "impactor; symmetric fixed-support boundary conditions were applied to four "
     "lateral faces of each eggshell disc fragment (diameter 2.0 mm). Analyses "
     "ran for 1.0 \u00d7 10\u207b\u2074 s (time-step safety factor 0.7; automatic mass scaling; "
     "minimum time step 1 \u00d7 10\u207b\u2078 s; double-precision arithmetic; 100 equidistant "
     "output intervals). Resultant contact forces (RCFORC) were recorded at "
     "1.0 \u00d7 10\u207b\u2076 s intervals. The impactor was positioned at nine lateral-offset "
     "locations on a 3 \u00d7 3 grid (0.5 mm spacing) per species, from which peak "
     "contact force (F_max) and peak contact shear stress (\u03c4_max) were extracted "
     "per position.", False, False),
])
cite(p_m_fea, [16, 17, 38])

head("Statistical analysis")

mixed([
    ("All values are expressed as mean \u00b1 s.d. All statistical tests were two-tailed, "
     "and p < 0.05 was considered statistically significant throughout. "
     "Mammillary morphometric parameters were compared among species by one-way ANOVA "
     "followed by Duncan's multiple range test (DMRT; \u03b1\u202f=\u202f0.05) "
     "(n\u202f=\u202f2 fragments per species). Glycan ensemble geometric descriptors (Rg, "
     "end-to-end distance, minimum glycan\u2013protein contact distance) and per-ensemble "
     "hotspot SASA metrics were compared among species by one-way ANOVA followed by "
     "Duncan's multiple range test (DMRT; \u03b1\u202f=\u202f0.05). "
     "Glycosylation-induced reduction in N_hot within ", False, False),
    ("C.\u00a0livia", False, True),
    (" was assessed by one-sample t-test versus the apo reference value (t\u2081\u2083); "
     "total Asp/Glu SASA differences between glycosylated and apo structures were "
     "evaluated by one-sample t-test against the apo reference value; shifts in "
     "median surface electrostatic potential were assessed by one-sample t-test "
     "against the apo reference value. Protein\u2013glycan abundance "
     "coupling was quantified by Spearman rank correlation of log\u2082-transformed "
     "protein and glycan-site intensities. Finite-element simulation outcomes "
     "(F_max, \u03c4_max) were compared among species by one-way ANOVA with Duncan's "
     "multiple range test (DMRT; \u03b1\u202f=\u202f0.05). All statistical analyses were "
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
