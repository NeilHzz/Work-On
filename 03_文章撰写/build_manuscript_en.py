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

OUT = str(Path(__file__).with_name("manuscript0602.docx"))
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
    "OVAL glycan state tracks mammillary organisation and local hatching resistance across avian eggshells",
    bold=True, size=14, before=0, after=160, align=WD_ALIGN_PARAGRAPH.LEFT
)

# Short title (≤50 characters)
para("OVAL glycans and hatching resistance",
     bold=False, size=11, after=60, align=WD_ALIGN_PARAGRAPH.LEFT)

para(
    "[Please add full author names, affiliations, ORCID identifiers, equal-contribution notes, and corresponding-author details before submission]",
    bold=False, size=10, before=80, after=80,
    align=WD_ALIGN_PARAGRAPH.LEFT
)

para("Abstract", bold=True, size=11, before=80, after=40,
     align=WD_ALIGN_PARAGRAPH.LEFT)

para(
    "Birds hatch with a conserved egg-tooth, so unresolved differences in local shell-breaking mechanics are likely to reside in the eggshell rather than in the shell-breaking tool. "
    "We compared chicken, duck, and pigeon to test whether divergence first appears in the mammillary layer and whether glycan states on shared matrix proteins track that divergence. "
    "We integrated micro-CT morphometry, eggshell-matrix proteomics, intact glycopeptide mass spectrometry, Re-Glyco modelling, electrostatic analysis, and finite-element simulation. "
    "Mammillary organisation diverged while the matrix-protein toolkit remained broadly shared. "
    "Among the shared proteins, ovalbumin (OVAL) showed an ordered glycan-state shift from High Mannose-dominant glycans in chicken to Neutral Complex/Hybrid-dominant glycans in duck and Sialylated Complex/Hybrid-dominant glycans in pigeon. "
    "This shift aligned with progressively lower Ca²⁺-relevant surface accessibility. "
    "The same chicken-versus-duck/pigeon contrast reappeared in simulated local hatching resistance. "
    "Together, the data support OVAL glycan state as a proximate molecular layer linking a chicken-like eggshell state to mammillary organisation and local hatching mechanics.",
    bold=False, size=10, before=0, after=80, align=WD_ALIGN_PARAGRAPH.JUSTIFY
)

# Teaser (≤125 characters, one sentence for non-specialist readers)
para(
    "Teaser: Compact OVAL glycans mark the high-resistance chicken-like eggshell state.",
    bold=False, italic=True, size=10, before=80, after=160, align=WD_ALIGN_PARAGRAPH.LEFT
)

# ════════════════════════════════════════════════════════════════════════════
# Introduction
# ════════════════════════════════════════════════════════════════════════════
para("Introduction", bold=True, size=14, before=0, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT)

# §1 — Background value
p_s1a = spara([
    (" Bird hatching presents a localized mechanical problem: force must be delivered to one small shell-breaking site. In birds, that site is defined by the egg-tooth, a transient structure that presses the inner eggshell surface during escape.", [16, 86]),
    (" Comparable hatching-assist structures also occur across other egg-laying amniotes.", [82, 83, 84, 85]),
    (" Because egg-tooth function is broadly conserved, biologically meaningful hatching differences are more likely to lie in the eggshell than in the shell-breaking tool itself.", [16]),
    (" Avian eggshells vary with nesting environment, gas exchange, microbial exposure, and developmental mode.", [15, 26, 39]),
    (" Comparative analyses therefore do not recover a single architectural solution.", [40, 41]),
    (" The mammillary layer is especially relevant because it is the first mechanically consequential shell layer and the site at which calcite growth begins under eggshell-matrix control.", [1, 4, 20, 28]),
    (" Later shell layers inherit that early mineralization context.", [30, 34]),
    (" Mammillary organisation is therefore the first place where local matrix differences can scale into mature shell behaviour.", [1, 57]),
])

p_s1b = spara([
    (" The central question is therefore mechanistic: once the shell-breaking interface is held constant, which molecular regulators of the mammillary layer account for the different eggshell states recovered across species?", [1, 4, 16]),
    (" Earlier eggshell-matrix and mammillary-layer work already makes that level the most plausible control point.", [2, 28]),
])

# §2 — Prior work and its limits
p_intro2 = spara([
    (" Eggshell matrix proteins regulate mammillary-layer mineralization, crystal growth, and mature eggshell architecture.", [1, 2, 4]),
    (" OC17, OC116, TRFE, and OVAL are among the best-studied examples.", [10, 19, 21, 29]),
    (" Recent syntheses repeatedly recover an overlapping set of recurrent proteins, including OC17, OC116, ovotransferrin-related components, OVAL, ovomucoid, and ovocalyxin-family proteins.", [1, 2, 4]),
    (" Their recurrence makes them a stable anchor for shell organisation across studies.", [19, 21, 29]),
    (" These proteins therefore provide a natural comparative anchor for asking how a shared mineralization toolkit is reused in different shell contexts. The key remaining issue is not protein presence alone, but how the shared proteins are deployed.", [1, 2, 4]),
    (" Known posttranslational modifications on eggshell matrix proteins fall mainly into phosphorylation and glycosylation, and sites of both classes have already been studied extensively.", [17, 18, 21]),
    (" One major difference, however, is chemical diversity: phosphate side groups are comparatively similar, whereas glycan side chains vary widely in composition, size, and charge, with correspondingly different effects on protein biology.", [49, 50, 80]),
    (" Glycosylation studies therefore cannot stop at site occupancy alone; the specific glycan class carried at a site is itself a central variable.", [49, 50]),
    (" Earlier glycoproteomic work showed that the same eggshell-matrix proteins can occupy distinct N-glycosylation states.", [18]),
    (" Chicken-focused biochemical studies had already identified glycosylated Asn in proteins such as OC116 and defined the carbohydrate composition of OVAL-associated glycans.", [8, 21]),
    (" Parallel studies of egg white, chalaza, vitelline membrane, and incubation-stage transitions likewise indicate that glycosylation states can shift within avian egg systems.", [7, 47, 48]),
    (" Those studies were essential, but they were usually organized within one species, one shell compartment, or one site inventory at a time. They therefore established that eggshell glycosylation exists and is chemically diverse, without yet showing how matched glycan states on shared matrix proteins align with cross-species eggshell structure.", [8, 18, 21]),
    (" Many recurrent eggshell proteins and glycosites are already known.", [1, 2, 29, 66]),
    (" What remains unresolved is how those proteins are redeployed at the glycan-state level when mammillary organisation and shell-breaking mechanics diverge across species.", [18]),
    (" Avian eggshell studies have rarely resolved which specific N-glycan forms are carried by shared matrix proteins across species. The open question is whether that glycan layer explains why similar protein toolkits yield different eggshell structures.", [2, 4, 18]),
])

p_intro_sig = spara([
    (" Glycosylation alters protein stability, molecular recognition, surface exposure, and conformational state.", [61, 72, 78]),
    (" In other systems, glycans can act as dynamic shields rather than passive bulk alone.", [42, 43, 44, 63]),
    (" Zeng and colleagues further showed that the same eggshell matrix protein can occupy different N-glycosylation states across the cuticle and mineralized layer. Glycan state can therefore redistribute biological role across eggshell compartments rather than simply decorate a fixed protein scaffold.", [18]),
    (" Prior mineralization-related work suggested that OVAL can enter a Ca²⁺-responsive conformational state during early shell formation.", [4, 11, 29]),
    (" Work in other glycosylated systems further shows that glycan differences can reshape folded protein surfaces.", [42, 43, 61]),
    (" Related studies also show effects on accessible interfaces and shield-like surface behavior.", [63, 81]),
    (" We therefore asked whether cross-species glycan differences reshape the folded OVAL surface and alter the Ca²⁺-accessible interface presented at mineralization onset.", [4, 18]),
    (" If that structural difference is biologically relevant, it should remain detectable at the hatching-relevant mechanical end point. We therefore examined local resistance at the mammillary interface under egg-tooth-like loading.", [16, 37, 69]),
])

p_intro_gap = spara([
    (" We therefore anchored the comparison to the conserved egg-tooth interface. We asked whether glycan-state differences on shared matrix proteins could explain why a common shell-building toolkit yields different Ca²⁺-accessible states at mineralization onset. In that framing, the missing step is a bridge from glycan class to surface presentation on a shared matrix background.", []),
    (" OVAL provided a tractable test case. Its Ca²⁺-responsive surface behaviour was already biologically relevant in earlier mineralization work, and it remained abundant across species. Its dominant glycan classes could also be followed from glycoproteomics into structural modelling.", [4, 18, 29, 42]),
])

# §4 — This study
p_intro4 = smixed([
    ([('Here, we compared ', False, False),
      ('Gallus gallus', False, True),
      (', ', False, False),
      ('Anas platyrhynchos', False, True),
      (', and ', False, False),
      ('Columba livia', False, True),
            (' as terrestrial precocial, aquatic-associated precocial, and terrestrial altricial models, respectively.', False, False)], [3, 22, 23]),
        ([(' This design spanned crossed developmental and ecological contrasts within a common hatching framework. It avoided a simple phylogenetic or precocial-versus-altricial comparison.', False, False)], []),
    ([(' We integrated micro-CT morphometry to define mammillary organisation. We combined comparative eggshell-matrix proteomics and intact glycopeptide mass spectrometry to resolve shared matrix proteins and their glycan states. Re-Glyco structural modelling and electrostatic analysis were then used to infer protein-surface consequences, and finite-element simulation tested whether the same contrast remained detectable in local hatching resistance.', False, False)], []),
    ([(' Each level constrained the next, keeping molecular interpretation tied to shell structure rather than floating free of the material context.', False, False)], []),
    ([(' In the present dataset, that sequential comparison pointed most consistently to OVAL, whose glycan states aligned with mammillary density, Ca²⁺-relevant surface accessibility, and local hatching resistance.', False, False)], [18]),
])

# ═══════════════════════════════════════════════════════════════════════════
# "Results" section label
# ═══════════════════════════════════════════════════════════════════════════
para("Results", bold=True, size=14, before=320, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT)
# ════════════════════════════════════════════════════════════════════════════
# § Species selection — ecological and developmental niche analysis
# ════════════════════════════════════════════════════════════════════════════
head("Conserved egg-tooth function focuses the analysis on the eggshell")

p_ss1 = smixed([
    ([(' We placed extant birds into a comparative space using 10,993 AVONET species records and selected three deliberately separated model species from this comparative space (Fig. 1A).', False, False)], [16, 22, 41]),
    ([(' This broader mapping prioritized two egg-relevant axes least likely to be secondary: nesting environment and offspring developmental state. These axes span terrestrial-to-aquatic habitat use and a continuum from more precocial to more altricial young.', False, False)], [15, 22, 23]),
        ([(' Within this comparison space, ', False, False),
            ('Gallus gallus', False, True),
            (', ', False, False),
            ('Anas platyrhynchos', False, True),
            (', and ', False, False),
            ('Columba livia', False, True),
                (' were therefore chosen near contrasting regions of those ecological-developmental gradients. This reduced blurring by intermediate combinations.', False, False)], [3, 22, 23, 41]),
            ([(' This functional grouping only partly overlaps with phylogeny. Chicken and duck remain closely related precocial taxa but separate along the habitat axis, whereas pigeon anchors the altricial end of the comparison (Fig. S2).', False, False)], [3, 22, 23]),
            ([(' The comparison was therefore structured to retain shared ancestry in view while still bringing clear life-history separation into the same analytical frame.', False, False)], []),
            ([(' The focal species differed in beak-tip geometry, but the egg-tooth remained a similarly localized dorsal breaker in all three species. It therefore pointed to the same inside-out shell-breaking event during hatching (Fig. 1B).', False, False)], [16, 37, 82, 86]),
    ([(' Within this contrast set, the relevant question becomes which eggshell layer first separates the species once the hatching interface is held constant.', False, False)], []),
])

# ════════════════════════════════════════════════════════════════════════════
head("Mammillary organisation provides the first clear eggshell difference")

mixed([
    ("Viewed through that shared hatching context, the first eggshell level to separate the three species was mammillary-layer morphology (Fig. 1C). In ", False, False),
    ("G. gallus", False, True),
    (", mammillae were smoother overall and formed rounded projections. In ", False, False),
    ("A. platyrhynchos", False, True),
    (", mammillae showed more ridges and angular turns across the inner surface. ", False, False),
    ("C. livia", False, True),
    (" was dominated by discrete triangular-conical mammillae. Three-dimensional surface reconstructions agreed with the cross-sectional views, indicating that the three eggshells differ in mammillary geometry rather than representing minor variants of a shared inner-surface template.", False, False),
])

p_s0b = mixed([
    ("Quantification then separated the three species in two related but not identical ways (Fig. 1D). Mammillary knob density was highest in ", False, False),
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
    (" (0.40 ± 0.01). Quantitatively, chicken showed the densest early mineralization pattern. Pigeon devoted the largest share of shell volume to crystal units grown from individual mammillary knobs. Duck remained intermediate in crystal-unit proportion while resembling pigeon in density. The two metrics did not collapse into one monotonic axis, but both indicated that mammillary organisation had already diverged before later shell traits were considered. This layer is the earliest structural level governing eggshell mechanics and is controlled by matrix proteins. We therefore asked a narrower question: did the contrast reflect wholesale toolkit replacement or differential use of a largely shared system?", False, False),
])
cite(p_s0b, [1, 4, 28])

doc.add_page_break()
add_centered_figure("Fig1_composed.png", width_cm=10.1, before=0, after=20)
add_main_figure_legend(
    "Fig. 1.",
    "Shared hatching interface and mammillary divergence across the three model species.",
    [
        ("(A) Three-dimensional AVONET comparison space built from 10,993 species records. Axes summarize aquatic association, lifestyle-habitat discordance, and developmental mode. Colors denote avian orders, and gray boxes mark the regions occupied by the three focal species. Open circles indicate ", False, False),
        ("Gallus gallus", False, True),
        (", ", False, False),
        ("Anas platyrhynchos", False, True),
        (", and ", False, False),
        ("Columba livia", False, True),
        (". (B) Species-specific lateral head views (top row) and dorsal beak views (bottom row) show the egg-tooth-bearing beak tip in chicken, duck, and pigeon. (C) Representative micro-CT sections and three-dimensional inner-surface reconstructions of the mammillary layer. Chicken shows smoother rounded mammillae, duck more ridged and angular mammillae, and pigeon discrete triangular-conical mammillae. Scale bars, 100 μm. (D) Box plots show mammillary density and unit volume ratio across species. Points denote individual measurements. P values from one-way ANOVA are shown above the plots, and different letters indicate Tukey HSD groupings.", False, False),
    ],
    before=20,
    after=80,
)
doc.add_page_break()

# ════════════════════════════════════════════════════════════════════════════
# S_prot  Eggshell matrix proteome orthogroup analysis
# ════════════════════════════════════════════════════════════════════════════
head("Shared matrix proteins focus the comparison on glycosylation")

p_sprot_bg = spara([
    ("Orthogroup analysis resolved the three eggshell matrix proteomes into a large shared core with smaller pairwise-shared and lineage-restricted complements (Fig. S3). At the overall level, the proteome still followed broad ancestry (Fig. S4), arguing against wholesale replacement of the eggshell-matrix toolkit.", []),
])

p_sprot_go = spara([
        (" The shared core therefore became the relevant comparison frame. The next question was whether the species separated through wholesale proteome turnover or through different glycan states on shared matrix proteins.", []),
])

p_sprot_focus = spara([
    (" The G. gallus-exclusive set was simultaneously enriched for protein N-linked glycosylation (BP; Fig. S5), shifting the comparison from protein presence to chemical deployment. The retained shared core thus became the relevant molecular background. Glycosylation on shared proteins emerged as a proximate candidate layer for explaining divergence in mammillary organisation and downstream shell behaviour.", [18]),
    (" Most recurrent eggshell matrix proteins emphasized in earlier studies were recovered in the broader proteomic and glycoproteomic background here, indicating substantial agreement with prior eggshell-matrix work. The present dataset also broadened that comparative background.", []),
])

head("OVAL glycosylation provides the most interpretable cross-species contrast")

p_s2a = spara([
    ("Intact-glycopeptide profiling first showed that the three species differed in sampling depth yet still shared a stable comparison core (Fig. 2A to D). The cluster view recovered 25 clusters shared by all three species, with the largest additional pairwise overlap between duck and pigeon at 64 clusters, whereas chicken contributed little species-private cluster space (Fig. 2A).", []),
    ("The same asymmetry appeared in the catalog counts: duck yielded 321 glycoproteins, 547 glycosites, and 197 glycan compositions; pigeon yielded 192, 257, and 162; and chicken yielded 55, 88, and 105 (Fig. 2B). Shared-core Jensen-Shannon similarity nevertheless remained concentrated between 0.33 and 0.40, with the duck-pigeon pair highest (Fig. 2C). These values indicate divergence within a still comparable glycoproteomic background rather than three disconnected chemical spaces.", []),
    ("Glycan-class composition reinforced the same point at the chemical-deployment level. High-Mannose and Complex-Fucosylated glycans formed a broad cross-species background, whereas Complex-Sialylated and other more extended classes contributed more strongly to lineage separation (Fig. 2D).", []),
])

add_centered_figure("Fig2_composed.png", width_cm=14.6)
add_main_figure_legend(
    "Fig. 2.",
    "Shared-core glycoproteome structure and glycan-class deployment.",
    [
        ("(A) Species-partitioned cluster counts in the glycoproteomic dataset. (B) Numbers of detected glycoproteins, glycosites, and glycan compositions in each species. (C) Shared-core Jensen-Shannon similarity among the three species. (D) Species-level distribution of glycan-class assignments, including High Mannose, Pauci-mannose, Hybrid, Complex-Plain, Complex-Fucosylated, Complex-Sialylated, and Other glycans. (E) Ortholog-glycan chord view linking eggshell glycoproteins to dominant glycan classes across chicken, duck, and pigeon, with highlighted matrix proteins retained for downstream comparison.", False, False),
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
    "Ortholog filtering and abundance-glycan decoupling prioritize OVAL.",
    [
        ("(A to C) Proteotype coevolution plots compare log2-transformed protein abundance and glycan abundance within chicken, duck, and pigeon, respectively. Insets show Spearman's ρ and two-sided p values. Highlighted labels mark OVAL, OC116, TRFE, and OC17 where retained. (D to F) Pairwise two-dimensional glycan-protein enrichment plots compare Gallus versus Columba, Gallus versus Anas, and Anas versus Columba. The dashed diagonal marks equal protein and glycan change. Highlighted proteins identify matrix candidates whose glycan shifts depart from simple protein-abundance scaling.", False, False),
    ],
)

head("OVAL glycan state reshapes surface accessibility")

p_s3a = spara([
    ("OVAL was selected for structural analysis because it remained shared, chemically distinct, and directly comparable across species. Dominant glycosylated OVAL ensembles and matched apo references were rebuilt to test whether the three species differed mainly through glycan-dependent surface behavior rather than through backbone sequence alone.", [4, 11]),
    (" Representative rebuilt glycan conformations and species-specific surface maps showed that the dominant glycans occupied different spatial envelopes on the same folded protein scaffold (Fig. 4A and B).", []),
])

p_s3b = spara([
    (" Pigeon first separated by occupying the largest overall glycan envelope, as shown by the higher radius of gyration in Fig. 4C and the longer end-to-end distances in Fig. 4E. That expansion occurred together with closer local approaches to the backbone in Fig. 4D and a broader glycan-protein distance distribution in Fig. 4F, consistent with extended glycans that sample a larger envelope while still folding back toward the OVAL surface.", []),
    (" Chicken defined the opposite endpoint, with compact glycans and the weakest geometric intrusion into the acidic interface. Duck remained closer to chicken in radius of gyration and overall glycan-protein spacing, but it separated from both species in end-to-end span and minimum backbone approach. Fig. 4C to F thus translate glycan-class progression into a shielding geometry. Chicken sits at the compact, weakly contacting end, pigeon at the extended but surface-engaging end, and duck occupies a partially shifted but not uniformly intermediate state.", []),
])

p_s3c = spara([
    (" Fig. 4G to J resolved the same acidic interface at progressively stricter levels. Fig. 4G measures gross interface shielding, Fig. 4H asks what fraction of candidate acidic residues remained hotspots, Fig. 4I measures the surface area retained by hotspot residues, and Fig. 4J counts the subset of Ca²⁺ hotspots that remained both electrostatically favorable and physically reachable.", []),
    (" Interface shielding increased stepwise from chicken to duck to pigeon, and the same ordering was retained across hotspot surface area, hotspot fraction, and net accessible Ca²⁺ hotspots. Together, these panels show progressive masking of the shared acidic OVAL face during early mineralization.", []),
])

p_s3d = spara([
    (" Matched glycosylated-versus-apo comparisons then showed that glycan addition changed the number of Ca²⁺-relevant hotspot residues and the exposed carboxylate surface most clearly in pigeon (Fig. 4K and L; Fig. S10). Duck shifted in the same direction without a resolved structure-level significance call, and chicken could be assessed only descriptively because one glycosylated structure was available. This pattern is more consistent with a glycan-imposed shift in the acidic surface presented at mineralization onset than with a generic sequence effect alone.", []),
    (" Fig. 4K to N then collapse the same comparison to the whole-interface level. Across those panels, chicken preserved the most accessible Ca²⁺-relevant surface, pigeon shifted the largest share into a glycan-affected state, and duck trended toward the lower-accessibility side but did not separate from pigeon or apo references uniformly across metrics.", []),
    (" Chicken therefore retained the highest inferred Ca²⁺-capturing capacity and the state most compatible with earlier Ca²⁺-responsive opening of OVAL at mineralization onset. Duck and pigeon moved toward the lower-accessibility side from different structural backgrounds. The same ordering matched the phenotype sequence: chicken combined the densest mammillary field and the highest local hatching resistance, whereas duck and pigeon converged toward the lower-resistance side. Taken together, Fig. 4A to N link glycan-dependent separation, glycan geometry, interface masking, and Ca²⁺-relevant accessibility on a shared matrix protein.", []),
])

doc.add_page_break()
add_centered_figure("Fig4_composed.png", width_cm=15.2, before=0, after=20)
add_main_figure_legend(
    "Fig. 4.",
    "OVAL glycan state reorganizes interface exposure and Ca²⁺-relevant accessibility.",
    [
        ("(A) Representative rebuilt OVAL-glycan conformations on the protein surface. (B) Species-specific surface maps show glycan positions and Ca²⁺-relevant surface regions. (C to F) Ensemble geometric descriptors of the rebuilt glycans include radius of gyration, minimum glycan-backbone distance, end-to-end distance, and glycan-protein distance. (G) Glycan-mediated interface shielding. (H) Hotspot fraction among candidate acidic residues. (I) Mean solvent-accessible surface area (SASA) of hotspot residues. (J) Net accessible Ca²⁺ hotspots. (K) Ca²⁺ hotspot residue counts in glycosylated and matched apo OVAL references. (L) Carboxylate surface accessibility in glycosylated and apo references. (M) Ca²⁺ hotspot accessibility. (N) Ca²⁺ hotspot-residue SASA. Species comparisons for ensemble-derived metrics used two-sided Mann–Whitney U tests. Glycosylated-versus-apo structure-level contrasts were evaluated against matched apo references with one-sample Wilcoxon signed-rank tests when structure-level variation was present.", False, False),
    ],
    before=20,
    after=80,
)
doc.add_page_break()

head("Finite-element modelling recovers the same contrast in local hatching resistance")

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
    "Finite-element setup and local hatching resistance at the mammillary interface.",
    [
        ("(A) Species-specific dorsal beak views with dashed boxes marking the egg-tooth position. The panel is paired with micro-CT-derived finite-element setups and summary box plots of peak contact force (F_max) and peak shear stress (τ_max). Species are ", False, False),
        ("Gallus gallus", False, True),
        (", ", False, False),
        ("Anas platyrhynchos", False, True),
        (", and ", False, False),
        ("Columba livia", False, True),
        (". In each species set, the left image shows the dorsal beak view used to localize the egg-tooth. The right image shows the eggshell-fragment mesh, conical impactor, and representative finite-element model output at contact. (B) Mean contact-force time courses across nine impact positions with shaded ±1σ envelopes. (C) Mean contact shear-stress time courses for the same nine positions with shaded ±1σ envelopes. Points in the box plots denote individual impact positions (n = 9 per species). P values from one-way ANOVA are shown above the box plots. Different letters indicate Tukey HSD groupings. The simulations were built from reconstructed shell geometry rather than idealized shells.", False, False),
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
        ([('Mammillary organisation diverged while the eggshell-matrix toolkit remained broadly shared across the three species. ', False, False),
            ('Within that shared background, OVAL glycan state provided the most consistent link between molecular variation, surface accessibility, and local hatching resistance in this dataset.', False, False)], [1, 16, 18]),
])

p_disc_regulator = spara([
    ("The three-species design matters because egg traits are shaped by continuous ecological and developmental gradients rather than by a single binary label.", [15, 39]),
    (" Nesting environment tracks a terrestrial-to-aquatic axis, and offspring condition spans a continuum from more precocial to more altricial young. Neither axis is well represented by a simple yes-or-no partition.", [3, 23]),
    (" Duck is particularly informative in that design. It retains a broadly precocial developmental condition while shifting toward an intermediate OVAL glycan state and accessibility profile. Its τ_max outcome converges with pigeon rather than with chicken. The three-species comparison therefore samples deliberately separated regions of a continuous ecological-developmental space while keeping the hatching interface itself comparable.", [3, 15, 22, 23]),
])

p_disc_axis = spara([
    ("Mammillary-layer mineralization mode remains the central structural level in the interpretation.", [1, 28]),
    (" Once early calcite crystal units are established, later eggshell regions inherit the spacing logic created in that first mineralization window. A dense mammillary field can therefore change matrix retention, mineral continuity, local stress redistribution, and morphology.", [1, 30, 36]),
    (" That emphasis is consistent with earlier eggshell studies that place the mammillary layer at the intersection of crystal nucleation and matrix control. The present comparison extends that line of work by linking the layer to a cross-species glycan-state readout rather than to shell-quality descriptors alone.", [1, 28, 31, 32]),
    (" Recent poultry omics studies increasingly tie age, shell-gland transcription, extracellular-vesicle cargo, and other whole-shell quality traits to eggshell phenotype. However, those descriptors usually remain broader than the proximate material layer isolated here.", [33, 52, 57, 70]),
    (" For that reason, mammillary organisation is not merely another shell trait, but the earliest material context in which matrix chemistry can plausibly bias later mechanical outcome.", [1, 2]),
    (" That structural position is why the mammillary layer remains the first place where a cross-species difference can be read as potentially consequential rather than merely descriptive.", [1, 28]),
])

p_disc_mam2 = spara([
    (" Among the molecular layers examined here, OVAL N-glycan architecture most closely tracked the cross-species structural differences.", []),
    (" Orthogroup turnover, gene-family change, and glycoprotein-network divergence still matter, but they mainly define comparative background rather than the nearest explanation. OVAL glycan state is especially informative because it is shared across species, chemically interpretable, and located on an abundant matrix protein already implicated in mineralization.", [4, 18, 27]),
    (" Earlier work had already kept OVAL in view as an abundant eggshell glycoprotein and mineralization candidate. Prior glycoproteomic studies also showed that eggshell-matrix proteins can occupy different N-glycosylation states. The advance here is not simply that additional glycopeptides were detected. Rather, the ortholog-resolved cross-species comparison identifies which glycan states align most consistently with phenotype and carries those assignments into structural and mechanical interpretation.", [4, 18]),
    (" Earlier chicken studies established a glycosite foundation for OVAL and identified glycosylated Asn in OC116. The present dataset resolved dominant glycan classes on the corresponding OVAL ortholog sequons carried into structural modelling (G. gallus N293; A. platyrhynchos and C. livia N97). Relative to earlier site-detection studies, the present comparison extends breadth across species and into glycan-class interpretation rather than merely lengthening a within-species site inventory.", [8, 18, 21]),
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
    ("Re-Glyco and APBS analyses provide the structural bridge in this argument.", []),
    (" Compact chicken glycans left the critical acidic OVAL surface relatively exposed. Longer, more electronegative pigeon glycans reduced Ca²⁺ approach both sterically and electrostatically. Duck again fell between those endpoints.", []),
    (" Earlier in vitro and structural work had already suggested that OVAL conformation and electrostatics matter during mineralization, but matched glycoform-resolved surface ensembles had not been compared across bird species.", [4, 11]),
    (" Glycan-state variation is therefore resolved here as a physically interpretable surface difference. Although this result does not establish direct causality, it supports a restrained inference. Different glycan states on the same matrix protein can alter the chemical surface presented to the mineralizing environment and may contribute to the structural divergence observed here.", [42, 61]),
])

p_disc_mech = spara([
    ("The mechanical comparison was designed around the inside-out loading event of hatching rather than conventional outside compression or whole-shell breaking tests.", [16, 37, 69]),
    (" That distinction matters because eggshell thickness strongly influences absolute failure load. By contrast, τ_max is less confounded by thickness and more directly reflects load transfer through the mammillary interface itself.", [16, 34, 69]),
    (" The present analysis therefore complements recent finite-element and eggshell-strength studies. It asks whether the inner mammillary interface preserves the same cross-species contrast already inferred from matrix state and morphology.", [16, 34, 35, 69]),
    (" Duck makes that separation especially clear because its thicker shell elevated F_max but did not recreate the high-τ_max state observed in chicken.", [16, 37, 69]),
])

p_disc_evo = para(
    "A second interpretive issue is that the mammillary layer can be partly resorbed during late incubation and hatching. That possibility does not erase the relevance of the present comparison because the quantified descriptors used here were mammillary density and crystal-unit organisation. Those features remain embedded in the shell even when part of the innermost material has been absorbed. The same consideration guided the mechanical readout. We emphasized the second characteristic peak rather than the first because the earliest force excursion is dominated more strongly by initial morphology-dependent contact, whereas the later peak more faithfully reflects stress transmission through the shell wall as a whole."
)

p_disc_discriminate = spara([
    ("These considerations help separate thickness buffering and developmental background from the material pathway emphasized here.", []),
    (" Eggshell thickness, body size, and broad reproductive ecology all contribute background variation, and lineage history undoubtedly matters.", [3, 14]),
    (" But thickness-based explanations do not account for the τ_max differences. Diffuse lineage-divergence explanations also do not explain why the same contrast recurs in glycan class, electrostatic accessibility, mammillary-layer organisation, and hatching-relevant mechanics.", [16, 37]),
    (" What recurs across the dataset is the alignment between glycan state, surface shielding, mammillary organisation, and τ_max under inside-out loading.", []),
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
    "In summary, this study connected mammillary organisation, glycoprotein state, surface accessibility, and local hatching mechanics across three avian eggshells. Chicken defined the high-resistance end of that axis, combining dense mammillary organisation, compact OVAL glycans, greater Ca²⁺-relevant surface exposure, and the highest local resistance at the mammillary interface. As comparable glycoform assignments become available, the same strategy can be extended to other abundant eggshell matrix proteins. Taken together, the morphometric, glycoproteomic, structural, and mechanical evidence supports OVAL glycan state as a consistently aligned molecular layer linking the chicken-like eggshell state to mammillary organisation and local hatching mechanics."
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
    "Because the columnar units initiated by mammillae are arranged as repetitive and approximately even planar units in normal avian eggshell microstructure, these parameters were treated as local average representatives of whole-shell organisation (n\u202f=\u202f9 subfragments per species from one scanned fragment). The same segmentation and post-processing workflow was applied to all scans so that species contrasts reflected morphology rather than reconstruction settings."
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
     "followed by Duncan's multiple range test (DMRT; \u03b1\u202f=\u202f0.05) "
     "(n\u202f=\u202f9 subfragments per species). The same assumption checks supported one-way ANOVA with Duncan's multiple range test for finite-element outcomes (F_max and \u03c4_max). In contrast, glycan ensemble geometric descriptors (Rg, end-to-end distance, minimum glycan\u2013protein contact distance) and hotspot-derived ensemble metrics did not satisfy normality and/or homoscedasticity across species, so pairwise species contrasts for these variables were evaluated with two-sided Mann\u2013Whitney U tests. "
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
