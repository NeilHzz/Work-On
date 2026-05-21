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

OUT = str(Path(__file__).with_name("manuscript260520.docx"))
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
    "Glycan states of eggshell matrix proteins link mammillary organization to local hatching resistance across birds",
    bold=True, size=14, before=0, after=160, align=WD_ALIGN_PARAGRAPH.LEFT
)

# Short title (≤50 characters)
para("Matrix protein glycans and hatching resistance",
     bold=False, size=11, after=60, align=WD_ALIGN_PARAGRAPH.LEFT)

para(
    "[Please add full author names, affiliations, ORCID identifiers, equal-contribution notes, and corresponding-author details before submission]",
    bold=False, size=10, before=80, after=80,
    align=WD_ALIGN_PARAGRAPH.LEFT
)

para("Abstract", bold=True, size=11, before=80, after=40,
     align=WD_ALIGN_PARAGRAPH.LEFT)

para(
    "Birds hatch with a conserved egg-tooth, placing unresolved mechanical differences in the eggshell rather than the shell-breaking tool. "
    "We compared chicken, duck, and pigeon to test whether the first clear divergence appeared in the mammillary layer and whether glycan states on shared matrix proteins tracked that divergence. "
    "Micro-CT morphometry, eggshell-matrix proteomics, intact glycopeptide mass spectrometry, Re-Glyco modeling, electrostatic analysis, and finite-element simulation showed that mammillary organization diverged while the matrix-protein toolkit remained largely shared. "
    "Among shared proteins, ovalbumin (OVAL) showed an ordered glycan-state shift from High-Mannose-dominant chicken to Neutral Complex/Hybrid-dominant duck and Sialylated Complex/Hybrid-dominant pigeon. "
    "This shift aligned with progressively lower Ca²⁺-relevant surface accessibility and with the same chicken-versus-duck/pigeon contrast in simulated local hatching resistance. "
    "These results identified OVAL glycan state as the most informative molecular layer linking a chicken-like eggshell state to mammillary organization and local hatching mechanics.",
    bold=False, size=10, before=0, after=80, align=WD_ALIGN_PARAGRAPH.JUSTIFY
)

# Teaser (≤125 characters, one sentence for non-specialist readers)
para(
    "Teaser: Compact OVAL glycans align with a chicken-like eggshell state and higher simulated local hatching resistance.",
    bold=False, italic=True, size=10, before=80, after=160, align=WD_ALIGN_PARAGRAPH.LEFT
)

# ════════════════════════════════════════════════════════════════════════════
# Introduction
# ════════════════════════════════════════════════════════════════════════════
para("Introduction", bold=True, size=14, before=0, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT)

# §1 — Background value
p_s1a = spara([
    (" Bird hatching presents a localized mechanical problem: force must be delivered to one small shell-breaking site. In birds, that site is defined by the egg-tooth, a transient structure that presses the inner eggshell surface during escape. Comparable hatching-assist structures also occur across other egg-laying amniotes.", [16, 82, 83, 84, 85, 86]),
    (" Because egg-tooth function is broadly conserved, biologically meaningful hatching differences are more likely to lie in the eggshell than in the shell-breaking tool itself. Avian eggshells vary with nesting environment, gas exchange, microbial exposure, and developmental mode rather than following a single architectural solution.", [15, 26, 39, 40, 41]),
    (" The mammillary layer is especially relevant because it is the first mechanically consequential shell layer and the site at which calcite growth begins under eggshell-matrix control. Later shell layers inherit that early mineralization context. Mammillary organization is therefore the first place where local matrix differences can scale into mature shell behavior.", [1, 4, 20, 28, 30, 34, 57]),
])

p_s1b = spara([
    (" The central question is therefore mechanistic: once the shell-breaking interface is held constant, which molecular regulators of the mammillary layer account for the different eggshell states recovered across species?", [1, 2, 4, 16, 28]),
])

# §2 — Prior work and its limits
p_intro2 = spara([
    (" Eggshell matrix proteins regulate mammillary-layer mineralization, crystal growth, and mature eggshell architecture, with OC17, OC116, TRFE, and OVAL among the best-studied examples.", [1, 2, 4, 10, 19, 21, 29]),
    (" Recent eggshell-matrix syntheses repeatedly return to a partly overlapping set of key proteins, especially OC17, OC116, ovotransferrin-related components, OVAL, ovomucoid, and ovocalyxin-family proteins, because these molecules are recovered consistently enough to anchor discussion of shell organization across studies.", [1, 2, 4, 19, 21, 29]),
    (" Because these proteins recur across avian eggshell studies, they provide a natural comparative anchor for asking how a shared mineralization toolkit is reused in different shell contexts. The key remaining issue is not protein presence alone, but how those shared proteins are deployed.", [1, 2, 4]),
    (" Earlier eggshell glycoproteomic work showed that the same eggshell-matrix proteins can occupy distinct N-glycosylation states, and chicken-focused biochemical studies had already identified glycosylated Asn in proteins such as OC116 while defining the carbohydrate composition of OVAL-associated glycans. Parallel studies of egg white, chalaza, vitelline membrane, and incubation-stage transitions likewise indicate that glycosylation states can shift within avian egg systems.", [7, 8, 18, 21, 47, 48]),
    (" Those studies were essential, but they were usually organized within one species, one shell compartment, or one site inventory at a time. They therefore established that eggshell glycosylation exists and is chemically diverse, without yet showing how matched glycan states on shared matrix proteins align with cross-species eggshell structure.", [8, 18, 21]),
    (" The recurring eggshell proteins and many recoverable glycosites are already known. What remains unresolved is how those recurrent proteins are redeployed at the glycan-state level when mammillary organization and shell-breaking mechanics diverge across species.", [1, 2, 18, 29, 66]),
    (" Avian eggshell studies have rarely resolved which specific N-glycan forms are carried by shared matrix proteins across species. The unresolved layer is whether glycosylation on shared matrix proteins can explain why similar protein toolkits yield different eggshell structures.", [2, 4, 18]),
])

p_intro_sig = spara([
    (" Glycosylation alters protein stability, molecular recognition, surface exposure, and conformational state, and glycans in other systems can act as dynamic shields rather than passive bulk alone.", [42, 43, 61, 63, 72, 78]),
    (" Zeng and colleagues further showed that the same eggshell matrix protein can occupy different N-glycosylation states across the cuticle and mineralized layer, indicating that glycan state can redistribute biological role across eggshell compartments rather than simply decorate a fixed protein scaffold.", [18]),
    (" Prior mineralization-related work also suggested that OVAL can enter a Ca²⁺-responsive conformational state during early shell formation. We therefore asked whether cross-species glycan differences reshape the folded OVAL surface and alter the Ca²⁺-accessible interface presented at mineralization onset.", [4, 11, 29, 42, 43, 61, 63, 81]),
    (" If that structural difference is biologically relevant, then it should remain detectable at the hatching-relevant mechanical end point as local resistance at the mammillary interface under egg-tooth-like loading.", [16, 37, 69]),
])

p_intro_gap = spara([
    (" We therefore anchored the comparison to a conserved egg-tooth interface and tested whether glycan-state differences on shared matrix proteins could explain why a common shell-building toolkit yields different Ca²⁺-accessible states at the onset of mineralization. In that framing, the key missing step is not another protein list, but a bridge from glycan class to surface presentation on a shared matrix background.", []),
    (" OVAL provided a tractable test case: its Ca²⁺-responsive surface behavior had already been made biologically relevant in earlier mineralization work, it remained abundant across species, and its dominant glycan classes could be followed from glycoproteomics into structural modeling.", [4, 18, 29, 42]),
])

# §4 — This study
p_intro4 = smixed([
    ([('Here, we compared ', False, False),
      ('Gallus gallus', False, True),
      (', ', False, False),
      ('Anas platyrhynchos', False, True),
      (', and ', False, False),
      ('Columba livia', False, True),
      (' as terrestrial precocial, aquatic-associated precocial, and terrestrial altricial models, respectively, thereby spanning crossed developmental and ecological contrasts within a common hatching framework.', False, False)], [3, 22, 23]),
        ([(' This design prevented the comparison from collapsing into either a simple phylogenetic pairing or a single precocial-versus-altricial contrast.', False, False)], []),
    ([(' We integrated micro-CT morphometry to define mammillary organization; comparative eggshell-matrix proteomics and intact glycopeptide mass spectrometry to resolve shared matrix proteins and their glycan states; Re-Glyco structural modeling and electrostatic analysis to infer protein-surface consequences; and finite-element simulation to test whether the same cross-species contrast remained detectable in local hatching resistance.', False, False)], []),
    ([(' Each level constrained the next, keeping molecular interpretation tied to shell structure rather than floating free of the material context.', False, False)], []),
    ([(' In the present dataset, that sequential comparison converged most clearly on OVAL, whose glycan states aligned with mammillary density, Ca²⁺-relevant surface accessibility, and local hatching resistance.', False, False)], [18]),
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
    ([(' This broader mapping was used to prioritize the two egg-relevant axes least likely to be secondary: nesting environment, which covaries strongly with terrestrial-to-aquatic habitat use, and offspring developmental state, which spans a continuum from more precocial to more altricial young.', False, False)], [15, 22, 23]),
        ([(' Within this comparison space, ', False, False),
            ('Gallus gallus', False, True),
            (', ', False, False),
            ('Anas platyrhynchos', False, True),
            (', and ', False, False),
            ('Columba livia', False, True),
                (' were therefore chosen as deliberately separated species near contrasting regions of those continuous ecological-developmental gradients, so that downstream comparison would be less blurred by intermediate combinations.', False, False)], [3, 22, 23, 41]),
            ([(' This functional grouping only partly overlaps with phylogeny: chicken and duck remain closely related precocial taxa but separate along the habitat axis, whereas pigeon anchors the altricial end of the comparison (Fig. S2).', False, False)], [3, 22, 23]),
            ([(' The comparison was therefore structured to retain shared ancestry in view while still bringing clear life-history separation into the same analytical frame.', False, False)], []),
            ([(' The focal species differed in beak-tip geometry, but the egg-tooth itself remained a similarly localized dorsal breaker in all three species and pointed to the same inside-out shell-breaking event during hatching (Fig. 1B).', False, False)], [16, 37, 82, 86]),
    ([(' Within this contrast set, the relevant question becomes which eggshell layer first separates the species once the hatching interface is held constant.', False, False)], []),
])

# ════════════════════════════════════════════════════════════════════════════
head("Mammillary organization provides the first clear eggshell difference")

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
    (" (0.5321 ± 0.0389), intermediate in ", False, False),
    ("A. platyrhynchos", False, True),
    (" (0.4413 ± 0.0249), and lowest in ", False, False),
    ("G. gallus", False, True),
    (" (0.3975 ± 0.0127). Quantitatively, chicken showed the densest early mineralization pattern, pigeon devoted the largest share of shell volume to crystal units grown from individual mammillary knobs, and duck remained intermediate in crystal-unit proportion while resembling pigeon in density. The two metrics therefore did not collapse into one simple monotonic axis, but they agreed that mammillary organization had already diverged in measurable ways before later shell traits were considered. Because mammillary organization is the earliest structural layer governing eggshell mechanics and is controlled by eggshell matrix proteins, we next asked whether this cross-species morphology reflected wholesale toolkit replacement or differential use of a largely shared system.", False, False),
])
cite(p_s0b, [1, 4, 28])

doc.add_page_break()
add_centered_figure("Fig1.jpg", width_cm=10.1, before=0, after=20)
add_main_figure_legend(
    "Fig. 1.",
    "Shared hatching interface and mammillary divergence across the three model species.",
    [
        ("(A) Three-dimensional AVONET comparison space built from 10,993 species records; axes summarize aquatic association, lifestyle-habitat discordance, and developmental mode. Colors denote avian orders, gray boxes mark the regions occupied by the three focal species, and open circles indicate ", False, False),
        ("Gallus gallus", False, True),
        (", ", False, False),
        ("Anas platyrhynchos", False, True),
        (", and ", False, False),
        ("Columba livia", False, True),
        (". (B) Species-specific lateral head views (top row) and dorsal beak views (bottom row) showing the egg-tooth-bearing beak tip in chicken, duck, and pigeon. (C) Representative micro-CT sections and three-dimensional inner-surface reconstructions of the mammillary layer; chicken shows smoother rounded mammillae, duck more ridged and angular mammillae, and pigeon discrete triangular-conical mammillae. Scale bars, 100 μm. (D) Box plots of mammillary density and unit volume ratio across species. Points denote individual measurements; p values from one-way ANOVA are shown above the plots, and different letters indicate Duncan's multiple range test groupings.", False, False),
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
    (" GO enrichment and gene-family turnover further pointed to lineage-specific immune and defense background (Figs. S5 and S6), but those signals described comparative context more than the layer most directly tied to mammillary organization. Those lineage-biased signals remained relevant as evolutionary backdrop, but they did not by themselves identify the proximate layer connecting a shared matrix repertoire to mammillary-layer divergence and, later, hatching-relevant mechanics across species.", []),
])

p_sprot_focus = spara([
    (" The G. gallus-exclusive set was simultaneously enriched for protein N-linked glycosylation (BP; Fig. S5), shifting the comparison from protein presence to chemical deployment. The retained shared core thus became the relevant molecular background, and glycosylation on shared proteins emerged as the most proximate candidate layer for explaining divergence in mammillary organization and downstream shell behavior.", [18]),
    (" Most recurrent eggshell matrix proteins emphasized in earlier studies were recovered in the broader proteomic and glycoproteomic background here, indicating substantial agreement with prior eggshell-matrix work. The present dataset also broadened that comparative background.", []),
])

head("OVAL glycosylation provides the most interpretable cross-species contrast")

p_s2a = mixed([
    ("Intact glycopeptides gave a direct cross-species view of specific glycoforms on avian eggshell matrix proteins. Fig. 2 resolved a conserved three-species core together with pairwise-shared and lineage-restricted sectors. The innermost rings correspond to the three-species shared proteins, the surrounding sectors capture pairwise-shared and lineage-restricted repertoires, and the outer nodes summarize the dominant glycan classes represented in the network. Gray links connect proteins to their observed glycan classes, and darker outer glycan nodes indicate classes linked to larger numbers of proteins. High-Mannose and Fucosylated Complex/Hybrid glycans formed a broad background across many protein families, whereas more extended Sialylated Complex/Hybrid glycans concentrated in the peripheral difference nodes. This asymmetry highlighted shared glycoproteins with strongly divergent states and narrowed the candidate space for ortholog and structural analysis.", False, False),
])

add_centered_figure("Fig2.jpg", width_cm=14.6)
add_main_figure_legend(
    "Fig. 2.",
    "Network view of shared and lineage-biased eggshell glycoproteins.",
    [
        ("Circular network linking orthologous eggshell glycoproteins to the dominant glycan classes across chicken, duck, and pigeon. The innermost concentric region marks the three-species conserved glycoprotein core; surrounding sectors mark pairwise-shared and lineage-restricted repertoires; and the outer glycan-class nodes summarize the manuscript-standard glycan classes, including High-Mannose, Paucimannose/Truncated, Neutral Complex/Hybrid, Fucosylated Complex/Hybrid, Sialylated Complex/Hybrid, and Other glycans. Curved links connect protein nodes to glycan classes, and the outer callouts report the number of proteins assigned to each class.", False, False),
    ],
)

p_s2b = mixed([
    ("A stricter BlastP-based filter retained an orthologous glycoprotein subset suitable for structural comparison and summarized that shared candidate space in Fig. 3A. Using ", False, False),
    ("G. gallus", False, True),
    (" as the reference, non-reference candidates were retained only when the mean E-value was below 1 × 10⁻⁵ and sequence identity met the final comparability thresholds. This filter restricted the downstream comparison to high-confidence orthologs. Under that stricter mapping, OC17 was glycosylated only in chicken, whereas OC116, TRFE, and OVAL all retained glycosylation signals across the three species and served as shared anchors. Among them, OVAL showed the clearest cross-species glycan differences and became the main target for subsequent structural analysis.", False, False),
])
p_s2c = spara([
    ("Integrated protein and glycan abundance profiles further identified OVAL as the shared protein most closely aligned with the cross-species eggshell differences (Fig. 3B to D). Across the full dataset, protein-glycan coupling was weak in chicken but consistently positive in duck and pigeon, indicating lineage differences in how glycosylation scaled with protein output.", []),
    (" Among the highlighted eggshell-matrix proteins, OVAL remained abundant in all three species but differed sharply in glycan burden: relatively modest in chicken, stronger in duck, and strongest in pigeon. OC116 and TRFE remained informative shared proteins, but neither separated bulk protein abundance from glycan output as consistently as OVAL.", []),
    (" Pairwise enrichment plots then showed why OVAL remained the clearest discriminator (Fig. 3E to G). In the Gallus-versus-Anas and Gallus-versus-Columba planes, OVAL fell on the glycan-skewed side of the comparison, indicating that its glycan shift outpaced or even opposed the corresponding protein-abundance shift rather than merely mirroring it. In the Anas-versus-Columba plane, OVAL again remained displaced from simple protein-glycan equivalence, preserving the same ordering beyond the chicken comparison. Intact-glycopeptide assignments therefore placed OVAL along a coherent cross-species progression from compact High-Mannose glycans in chicken to Neutral Complex/Hybrid glycans in duck and more extended Sialylated Complex/Hybrid glycans in pigeon. Together, Fig. 3B to G identified OVAL as the shared protein whose glycosylation changed in the most phenotype-relevant manner.", []),
])

p_s2d = spara([
    ("Because those OVAL glycan classes differ strongly in size and charge distribution, the most informative comparative variable was OVAL surface accessibility rather than OVAL abundance alone.", []),
    (" The relevant feature was how much of the acidic OVAL interface remained chemically reachable once decorated by different glycans. Ortholog control, abundance decoupling, and glycan-class progression together left OVAL as the only shared candidate that remained simultaneously comparable, chemically specific, and structurally actionable.", []),
])

add_centered_figure("Fig3.jpg", width_cm=15.5)
add_main_figure_legend(
    "Fig. 3.",
    "Ortholog filtering and abundance-glycan decoupling prioritize OVAL.",
    [
        ("(A) Circos-style summary of the orthologous glycoprotein subset retained after stringent BlastP filtering, highlighting shared candidate proteins across chicken, duck, and pigeon. Species are color-coded, gray labels indicate chicken proteins without retained non-chicken orthologs under the final comparison criteria, and highlighted labels mark OVAL, OC116, TRFE, and OC17. (B to D) Proteotype coevolution plots comparing log2-transformed protein abundance and glycan abundance within chicken, duck, and pigeon, respectively; inset values show Spearman's ρ and two-sided p values. (E to G) Pairwise two-dimensional glycan-protein enrichment plots for Gallus versus Anas, Gallus versus Columba, and Anas versus Columba.", False, False),
    ],
)

head("OVAL glycan state reshapes surface accessibility")

p_s3a = spara([
    ("OVAL was selected for structural analysis because it remained shared, chemically distinct, and directly comparable across species. Dominant glycosylated OVAL ensembles and matched deglycosylated references were rebuilt to test whether the three species differed mainly through glycan-dependent surface behavior rather than through backbone sequence alone.", [4, 11]),
    (" In Fig. 4A, glycosylated ensembles departed from their matched apo references in the number of Ca²⁺-relevant acidic hotspots, and the same displacement reappeared in the physically exposed carboxylate surface measured in Fig. 4B and in the whole-surface electrostatic maps in Fig. 4C. Removing glycans collapsed much of that separation and brought the three backbones closer together. The initial structural difference therefore reflected a glycan-imposed shift in the exposed acidic surface presented at mineralization onset rather than a generic sequence effect (Fig. 4A to C; Fig. S7).", []),
])

p_s3b = spara([
    (" Pigeon first separated by occupying the largest overall glycan envelope, as shown by the higher radius of gyration in Fig. 4D and the longer end-to-end distances in Fig. 4E. That expansion, however, did not lift the glycans away from the protein.", []),
    (" Instead, the same pigeon ensembles remained at similar or closer glycan-protein separations in Fig. 4F and reached smaller minimum backbone distances in Fig. 4G, consistent with extended glycans that also fold back toward the surface. Chicken defined the opposite endpoint: compact glycans in Fig. 4D and Fig. 4E, weaker surface contact in Fig. 4F and Fig. 4G, and therefore the least geometrically intrusive glycan layer. Duck again lay between those limits. Fig. 4D to G therefore convert glycan-class progression into a shielding geometry, from compact and weakly contacting chicken glycans to extended but surface-hugging pigeon glycans, with duck occupying the intermediate state.", []),
])

p_s3c = spara([
    (" Fig. 4H to K resolved the same acidic interface at progressively stricter levels. Fig. 4H measures gross shielding, Fig. 4I the hotspot surface area that remains solvent exposed, Fig. 4J the hotspot fraction among candidate acidic residues, and Fig. 4K the subset of hotspots that remains both electrostatically favorable and physically reachable to Ca²⁺.", []),
    (" Interface shielding increased stepwise from chicken to duck to pigeon, and the same ordering was retained across hotspot surface area, hotspot fraction, and net accessible Ca²⁺ hotspots. Together, these panels show progressive masking of the shared acidic OVAL face during early mineralization.", []),
])

p_s3d = spara([
    (" Fig. 4L and Fig. 4M then collapse the same contrast to the whole-interface level by partitioning hotspot counts and hotspot-residue surface area into exposed and shielded fractions. Chicken retained the largest exposed share in both panels, pigeon shifted the largest share into the shielded compartment, and duck again remained intermediate.", []),
    (" Chicken therefore retained the strongest inferred Ca²⁺-capturing capacity and the state most compatible with earlier Ca²⁺-responsive opening of OVAL at mineralization onset; pigeon defined the weakest and latest-starting limit, and duck remained intermediate. The same ordering matched the phenotype sequence: chicken combined the densest mammillary field and the highest local hatching resistance, whereas duck and pigeon converged toward the lower-resistance side from different structural backgrounds. Fig. 4A to M thus links glycan-dependent separation, glycan geometry, interface masking, and Ca²⁺-relevant accessibility on a shared matrix protein.", []),
])

doc.add_page_break()
add_centered_figure("Fig4.jpg", width_cm=15.2, before=0, after=20)
add_main_figure_legend(
    "Fig. 4.",
    "OVAL glycan state reorganizes interface exposure and Ca²⁺-relevant accessibility.",
    [
        ("(A) Number of Ca²⁺ hotspot residues, defined as surface Asp/Glu positions with APBS potential below −5 kT/e, in glycosylated and matched deglycosylated OVAL ensembles. (B) Carboxylate surface accessibility. (C) Surface electrostatic potential distributions for glycosylated versus deglycosylated structures. (D to G) Ensemble geometric descriptors of the rebuilt glycans, including radius of gyration, end-to-end distance, glycan-protein distance, and minimum glycan-backbone distance. (H) Glycan-mediated interface shielding. (I) Mean solvent-accessible surface area (SASA) of hotspot residues. (J) Hotspot fraction among candidate acidic residues. (K) Net accessible Ca²⁺ hotspots. (L) Partition of hotspot accessibility into net accessible and glycan-shielded components. (M) Partition of hotspot-residue SASA into net accessible and glycan-shielded components. Species-specific ensemble sizes are indicated beneath the violins. Species comparisons in Fig. 4D to M used one-way ANOVA followed by Duncan's multiple range test; glycosylated-versus-apo contrasts in Fig. 4A to C were evaluated against matched apo references by one-sample t test, with significance annotations shown above the brackets.", False, False),
    ],
    before=20,
    after=80,
)
doc.add_page_break()

head("Finite-element modeling recovers the same contrast in local hatching resistance")

p_s4a = mixed([
    ("Finite-element testing translated the shared egg-tooth interface into an explicit inside-out loading design. Fig. 5A summarizes the loading background of hatching. Fig. 5B to D pair species-specific dorsal beak views with the corresponding micro-CT-derived finite-element setups built from the beak-tip geometry summarized in Fig. 1B. Because the meshes preserved species-specific shell geometry, the analysis remained anchored to the same mammillary context identified morphologically. Impact loading was sampled on circular eggshell fragments (model diameter D = 2.0 mm) at nine parameterized lateral-offset positions on a 3 × 3 grid (0.5 mm spacing), yielding n = 9 independent contact shear-stress time courses per species. Both raw peak contact force (F_max) and peak contact shear stress (τ_max) were recorded to reduce the influence of model size, gross geometry, and especially eggshell thickness. Peak τ_max was used as the direct readout of local hatching resistance at the mammillary contact interface, and species means ± s.d. were calculated across the nine positions (Fig. S8A to F; eggshell thicknesses: ", False, False),
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
    "Finite-element setup for hatching-relevant loading at the mammillary interface.",
    [
        ("(A) Schematic of the egg-tooth pressing the eggshell from the inner side during hatching. (B to D) Species-specific dorsal beak views with dashed boxes marking the egg-tooth position, paired with the corresponding micro-CT-derived finite-element setups for ", False, False),
        ("Gallus gallus", False, True),
        (", ", False, False),
        ("Anas platyrhynchos", False, True),
        (", and ", False, False),
        ("Columba livia", False, True),
        (", respectively. In each species panel, the left image shows the dorsal beak view used to localize the egg-tooth, and the right image shows the eggshell-fragment mesh, conical impactor, and representative finite-element model output at contact. The simulations were built from reconstructed shell geometry rather than idealized shells.", False, False),
    ],
    before=20,
    after=80,
)
doc.add_page_break()

mixed([
    ("Peak F_max differed significantly among species (p = 1.639 × 10⁻¹³). ", False, False),
    ("G. gallus", False, True),
    (" reached 1.117 ± 0.110 N, ", False, False),
    ("A. platyrhynchos", False, True),
    (" reached 0.898 ± 0.090 N, and ", False, False),
    ("C. livia", False, True),
    (" reached 0.485 ± 0.039 N, with all pairwise differences significant (Fig. 6A). By contrast, τ_max resolved a two-level pattern (p = 6.644 × 10⁻¹⁰). ", False, False),
    ("G. gallus", False, True),
    (" reached 551.6 ± 108.8 MPa and was significantly higher than ", False, False),
    ("A. platyrhynchos", False, True),
    (" at 404.0 ± 39.6 MPa and ", False, False),
    ("C. livia", False, True),
    (" at 393.0 ± 35.2 MPa, whereas the latter two species did not differ significantly from each other (Fig. 6B).", False, False),
])

mixed([
    ("The difference between F_max and τ_max showed that duck's higher raw contact force was driven mainly by its greater shell thickness (0.35 mm versus 0.19 mm in pigeon), rather than by superior unit-area material resistance. By contrast, ", False, False),
    ("G. gallus", False, True),
    (" exhibited a 36-40% increase in τ_max relative to the two other species, indicating higher local hatching resistance independent of shell thickness. This high-versus-low grouping, with ", False, False),
    ("G. gallus", False, True),
    (" alone in the high group and ", False, False),
    ("A. platyrhynchos", False, True),
    (" together with ", False, False),
    ("C. livia", False, True),
    (" in the low group, matched the grouping recovered for mammillary density by Duncan's multiple range test (Fig. 1D). The mechanics therefore retained the contrast already recovered from mammillary organization and OVAL accessibility.", False, False),
])

mixed([
    ("Whole-shell fracture force alone could make duck appear mechanically superior to chicken because of its greater shell thickness, despite the absence of the same high-density mammillary state. By focusing instead on local hatching resistance at the micro-CT-derived mammillary interface, τ_max removes that ambiguity and shows that the high-density chicken state remains distinct, whereas duck and pigeon converge at lower resistance. This functional readout preserved the same asymmetry already visible in earlier sections and linked glycosylation-associated differences to local shell-breaking mechanics across the three model species.", False, False),
])
add_centered_figure("Fig6.jpg", width_cm=15.5)
add_main_figure_legend(
    "Fig. 6.",
    "Local hatching resistance differs across the three model species.",
    [
        ("(A) Mean contact-force time courses across nine impact positions for ", False, False),
        ("Gallus gallus", False, True),
        (", ", False, False),
        ("Anas platyrhynchos", False, True),
        (", and ", False, False),
        ("Columba livia", False, True),
        (", shown with shaded ±1σ envelopes, together with box plots of peak contact force (F_max). (B) Mean contact shear-stress time courses for the same nine positions together with box plots of peak shear stress (τ_max). Symbols on the curves mark species mean peak values, points in the box plots denote individual impact positions (n = 9 per species), p values from one-way ANOVA are shown above the box plots, and different letters indicate Duncan's multiple range test groupings. F_max differs across all three species, whereas τ_max separates chicken from the lower-τ_max duck and pigeon group.", False, False),
    ],
)

cite(p_s4a, [16, 37, 69])

# ════════════════════════════════════════════════════════════════════════════
# Discussion
# ════════════════════════════════════════════════════════════════════════════
para("Discussion", bold=True, size=14, before=320, after=160,
    align=WD_ALIGN_PARAGRAPH.LEFT)

p_disc_mam1 = smixed([
    ([('Mammillary organization diverged while the eggshell-matrix toolkit remained broadly shared across the three species. ', False, False),
            ('Within that shared background, OVAL glycan state provided the clearest correspondence between molecular variation, surface accessibility, and local hatching resistance recovered in this dataset.', False, False)], [1, 16, 18]),
])

p_disc_regulator = spara([
    ("The three-species design matters because egg traits are shaped by continuous ecological and developmental gradients rather than by a single binary label.", [15, 39]),
    (" Nesting environment tracks a terrestrial-to-aquatic axis, offspring condition spans a continuum from more precocial to more altricial young, and neither axis is well represented by a simple yes-or-no partition.", [3, 23]),
    (" Duck is particularly informative in that design because it retains a broadly precocial developmental condition while shifting toward an intermediate OVAL glycan state and accessibility profile, with a τ_max outcome that converges with pigeon rather than with chicken. The three-species comparison thus samples deliberately separated regions of a continuous ecological-developmental space while keeping the hatching interface itself comparable.", [3, 15, 22, 23]),
])

p_disc_axis = spara([
    ("Mammillary-layer mineralization mode remains the central structural level in the interpretation.", [1, 28]),
    (" Once early calcite crystal units are established, later eggshell regions inherit the spacing logic created in that first mineralization window, so a dense mammillary field changes matrix retention, mineral continuity, and local stress redistribution as well as morphology.", [1, 30, 36]),
    (" That emphasis is consistent with earlier eggshell studies that place the mammillary layer at the intersection of crystal nucleation and matrix control, but the present comparison goes further by linking that layer to a specific cross-species glycan-state readout rather than to shell-quality descriptors alone.", [1, 28, 31, 32]),
    (" Recent poultry omics studies increasingly tie age, shell-gland transcription, extracellular-vesicle cargo, and other whole-shell quality traits to eggshell phenotype, but those descriptors usually remain broader than the proximate material layer isolated here.", [33, 52, 57, 70]),
    (" For that reason, mammillary organization is not merely another shell trait, but the earliest material context in which matrix chemistry can plausibly bias later mechanical outcome.", [1, 2]),
    (" That structural position is why the mammillary layer remains the first place where a cross-species difference can be read as potentially consequential rather than merely descriptive.", [1, 28]),
])

p_disc_mam2 = spara([
    ("Among the molecular layers examined here, OVAL N-glycan architecture most closely tracked the cross-species structural differences.", []),
    (" Orthogroup turnover, gene-family change, and glycoprotein-network divergence still matter, but they mainly define comparative background rather than the nearest explanation. OVAL glycan state is more informative because it is shared across species, chemically interpretable, and located on an abundant matrix protein already implicated in mineralization.", [4, 18, 27]),
    (" Earlier work had already kept OVAL in view as an abundant eggshell glycoprotein and mineralization candidate, and prior glycoproteomic studies showed that eggshell-matrix proteins can occupy different N-glycosylation states. The advance here is therefore not simply that additional glycopeptides were detected, but that an ortholog-resolved cross-species comparison identified which glycan states aligned most clearly with phenotype and carried those assignments into structural and mechanical interpretation.", [4, 18]),
    (" Earlier chicken studies established a glycosite foundation for OVAL and identified glycosylated Asn in OC116, whereas the present dataset resolved dominant glycan classes on the corresponding OVAL ortholog sequons carried into structural modeling (G. gallus N293; A. platyrhynchos and C. livia N97). Relative to earlier site-detection studies, the present comparison extends breadth across species and into glycan-class interpretation rather than merely lengthening a within-species site inventory. OVAL is therefore useful not because it is unique, but because it remains comparable across species while retaining interpretable chemical divergence at the level of specific glycan classes.", [8, 18, 21]),
])

p_disc_other = spara([
    ("The non-OVAL signals still matter. OC116 and TRFE remained informative shared proteins, whereas OC17 appeared glycosylated only in chicken and may therefore represent a more lineage-restricted mineralization program.", []),
    (" Earlier eggshell studies had already assigned functional importance to OC17, OC116, and ovotransferrin-related matrix components, and the present dataset does not overturn that view. Instead, these proteins define the biological backdrop more consistently than they define the sharpest cross-species discriminator.", [10, 19, 29]),
    (" For OC116 in particular, earlier biochemical work had already established glycosylated Asn in chicken eggshell matrix, and more recent avian palaeoproteomic work showed that OC116 is among the most sequence-variable avian eggshell proteins, with substantial intraspecies variability rather than a uniformly stable species marker. That broader context fits our comparison: retained glycosylation keeps OC116 biologically relevant, but it does not recover as stable a structure-linked contrast as OVAL.", [21, 66]),
    (" The same point also clarifies how the present study relates to earlier eggshell glycoproteomics. Those studies were essential for showing that eggshell matrix proteins can be glycosylated and that site-level inventories are experimentally accessible. Our contribution is the next comparative step: shared orthologs, dominant glycan classes, and the consequence of those classes for surface presentation across species.", [18, 21]),
    (" The shared toolkit therefore remains multicomponent, even though OVAL provides the most experimentally tractable entry point.", []),
])

p_disc_oval = spara([
    ("Re-Glyco and APBS analyses provide the structural bridge in this argument.", []),
    (" Compact chicken glycans left the critical acidic OVAL surface relatively exposed, whereas longer, more electronegative pigeon glycans reduced Ca²⁺ approach both sterically and electrostatically; duck again fell between those endpoints.", []),
    (" Earlier in vitro and structural work had already suggested that OVAL conformation and electrostatics matter during mineralization, but matched glycoform-resolved surface ensembles had not been compared across bird species.", [4, 11]),
    (" Glycan-state variation is therefore resolved here as a physically interpretable surface difference. Although this result does not establish direct causality, it supports a restrained inference that different glycan states on the same matrix protein can alter the chemical surface presented to the mineralizing environment and thereby contribute to the structural divergence observed here.", [42, 61]),
])

p_disc_mech = spara([
    ("The mechanical comparison was designed around the inside-out loading event of hatching rather than conventional outside compression or whole-shell breaking tests.", [16, 37, 69]),
    (" That distinction matters because eggshell thickness strongly influences absolute failure load, whereas τ_max is less confounded by thickness and more directly reflects load transfer through the mammillary interface itself.", [16, 34, 69]),
    (" The present analysis therefore complements recent finite-element and eggshell-strength studies by asking whether the inner mammillary interface preserves the same cross-species contrast already inferred from matrix state and morphology.", [16, 34, 35, 69]),
    (" Duck makes that separation especially clear because its thicker shell elevated F_max but did not recreate the high-τ_max state observed in chicken.", [16, 37, 69]),
])

p_disc_evo = para(
    "A second interpretive issue is that the mammillary layer can be partly resorbed during late incubation and hatching. That possibility does not erase the relevance of the present comparison because the quantified descriptors used here were mammillary density and crystal-unit organization, which remain embedded in the shell even when part of the innermost material has been absorbed. The same consideration guided the mechanical readout. We emphasized the second characteristic peak rather than the first because the earliest force excursion is dominated more strongly by initial morphology-dependent contact, whereas the later peak more faithfully reflects stress transmission through the shell wall as a whole."
)

p_disc_discriminate = spara([
    ("These considerations help separate thickness buffering and developmental background from the material pathway emphasized here.", []),
    (" Eggshell thickness, body size, and broad reproductive ecology all contribute background variation, and lineage history undoubtedly matters.", [3, 14]),
    (" But thickness-based explanations do not account for the τ_max differences, and diffuse lineage-divergence explanations do not explain why the same contrast recurs in glycan class, electrostatic accessibility, mammillary-layer organization, and hatching-relevant mechanics.", [16, 37]),
    (" What recurs across the dataset is the alignment between glycan state, surface shielding, mammillary organization, and τ_max under inside-out loading.", []),
    (" Ecology and phylogeny establish the design space, whereas matrix-protein glycan state remains the most proximate chemically readable layer recovered here.", [4, 18]),
])

p_disc_function = para(
    "The discussion therefore converges on the chicken eggshell state. Across the present comparison, chicken combined the densest mammillary field, the least shielded Ca²⁺-relevant OVAL surface, and the highest local hatching resistance under inside-out loading. This convergence identifies the chicken-like state as the structural-functional target in the dataset and supports the broader point that chemically specific states on reused matrix proteins can organize mineralized phenotypes more clearly than proteome turnover alone."
)
cite(p_disc_function, [67, 73, 74])

p_disc_selection = para(
    "Duck and pigeon remain essential because they define the bounds of the chicken state across both shell structure and ecological-developmental position. Duck shows that a more aquatic niche and broadly precocial developmental condition can coexist with greater shell thickness, intermediate OVAL accessibility, and low τ_max without recreating the same mammillary-interface resistance. Pigeon shows that a more terrestrial and more altricial position can still converge with duck at low τ_max, but from a thinner shell and a different mammillary background. Together, these contrasts make chicken the clearest reference state for linking glycan-dependent matrix behavior to eggshell performance across the ecological and developmental space sampled here. OVAL glycan state is the most explicit molecular layer through which that high-resistance state becomes mechanistically interpretable."
)

p_disc_biomineral = para(
    "That same analytical sequence should travel beyond avian eggshell. Many biomineralization systems depend on organic matrices that modulate ion access, surface exposure, and mineral nucleation through chemically specific interfacial states rather than through bulk composition alone. In that broader frame, the present workflow offers a way to move from glycoproteomic state to surface presentation and then to mesoscale function, which is also the scale-bridging problem faced in other mineralized tissues and biomimetic materials. The same logic may be relevant even in regenerative contexts, where eggshell-derived materials and eggshell membrane proteins have already been explored for tissue engineering and bone repair, including improved osteoproductivity of injectable grafts. The study therefore also provides a template for asking how chemically specific matrix states organize biomineral behavior across biological and biomedical settings."
)
cite(p_disc_biomineral, [64, 67, 68, 73])

p_disc_future = para(
    "The present scope remains bounded. We analyzed dominant glycoforms rather than the full in vivo range of glycan heterogeneity, treated each species as mechanically uniform at the scale of the mean eggshell, and relied on incompletely constrained uterine ionic conditions in the APBS framework. The next decisive tests are defined-glycoform mineralization assays, direct manipulation of OVAL glycosylation in chicken, and site-resolved validation of the same inside-out mechanical contrast. Those experiments should determine whether the OVAL glycan state identified here directly participates in shell mineralization or mainly marks the chicken-like high-resistance state with unusual fidelity."
)

p_disc_close = para(
    "In summary, the present study establishes a continuous comparison from mammillary organization to glycoprotein state, structure, and local hatching mechanics in three avian eggshells. Chicken emerged as the target state, combining dense mammillary organization, compact OVAL glycosylation, greater Ca²⁺-relevant surface exposure, and the highest local resistance at the mammillary interface during hatching. This strategy can be extended to other abundant eggshell matrix proteins as their modification states become resolvable with similar confidence. Together, the morphometric, glycoproteomic, structural, and mechanical analyses identify OVAL glycan state as the most informative molecular layer linking the chicken-like eggshell state to mammillary organization and local hatching mechanics."
)

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
        "All eggs were stored at 4\u00b0C until processing. Fresh collection and matched cold storage were used to minimize post-oviposition variation before comparative analysis.", False, False),
])

head("Eggshell matrix protein extraction")

mixed([
    ("Eggshell matrix proteins were extracted from the eggshell mammillary layer "
     "(EML) by an established EDTA demineralization protocol. Eggs were rinsed with "
    "deionized water and placed in sterile sealed bags. For ", False, False),
    ("G.\u00a0gallus", False, True),
    (" and ", False, False),
    ("A.\u00a0platyrhynchos", False, True),
    (", the eggshell cuticle layer (ECL) was removed prior to EML "
     "extraction by treatment with 15 mL of 5% EDTA (0.13 mol/L, pH 7.6) supplemented "
     "with 2-mercaptoethanol (10 mmol/L) for 30 min at 20\u00b0C, with gentle manual "
    "kneading to separate the ECL; eggshells were subsequently rinsed with deionized "
     "water. EML proteins from all three species were then solubilized under the same "
     "EDTA\u20132-mercaptoethanol conditions with the extraction duration extended to 12 h "
     "at 20\u00b0C. The resulting suspension was centrifuged at 1,000 \u00d7 g for 15 min; the "
     "pellet was resuspended and centrifuged a second time, and the pooled supernatant "
        "was stored at \u221280\u00b0C until analysis. Species were processed in parallel under the same extraction chemistry so that downstream differences were less likely to reflect handling drift.", False, False),
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
    "Mammillary density was calculated as mammilla count divided by ROI area. "
    "Total eggshell volume in the same ROI was obtained directly from the labelmap, and mean column-unit volume was defined as total shell volume divided by mammilla count; "
    "column-unit volume fraction was then calculated as mean column-unit volume divided by the total eggshell volume of the corresponding ROI. "
    "Because the columnar units initiated by mammillae are arranged as repetitive and approximately even planar units in normal avian eggshell microstructure, these parameters were treated as local average representatives of whole-shell organization (n\u202f=\u202f2 fragments per species). The same segmentation and post-processing workflow was applied to all scans so that species contrasts reflected morphology rather than reconstruction settings."
)
cite(p_m_ct, [1, 30])

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
    "were pooled at the two-egg level to reduce idiosyncratic egg-to-egg variation while preserving the dominant species-level signal. They "
    "were digested overnight with sequencing-grade trypsin (enzyme:protein ratio "
    "1:50) and desalted with Strata X SPE columns."
)

mixed([
    ("Desalted peptides were dissolved in 0.1% formic acid and separated on a "
     "home-made 15-cm \u00d7 100-\u03bcm i.d. reversed-phase C18 analytical column connected "
     "to a Vanquish Neo UPLC system (Thermo Fisher Scientific) at 400 nl/min over "
     "a 22.6-min gradient (4\u201399% solvent B; 0.1% formic acid in 80% acetonitrile). "
    "Separated peptides were analyzed on an Orbitrap Astral mass spectrometer "
    "(Thermo Fisher Scientific) with a nano-electrospray ionization source (1,900 V). "
     "Full-MS spectra were acquired in the Orbitrap at 240,000 resolution over "
    "380\u2013980 m/z; MS/MS fragments were acquired in the Astral analyzer at 80,000 "
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
     "Using species-matched reference databases reduced the risk that peptide assignments would be biased toward the best-annotated proteome. "
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
    "For Fig. 3B to D, protein-level and glycan-site quantification tables were "
    "loaded separately for each species from the Protein_quant and Site_quant sheets. "
    "When the Number Comparable field was present, protein entries with values < 2 "
    "and glycan-site entries with values < 1 were excluded. Mean protein intensity "
    "was calculated across all species-matched intensity columns for each accession, "
    "and mean glycan intensity was calculated for each quantified glycosylation site "
    "across the corresponding site-intensity columns. Only positive-intensity entries "
    "were retained. Glycan-site rows were then inner-joined to protein rows by protein "
    "accession so that each point represented one quantified glycosylated sequon with "
    "a matched protein-abundance measurement. Protein and glycan intensities were "
    "log2-transformed, and within-species protein-glycan coupling was summarized by "
    "Spearman rank correlation with two-sided p values. OVAL, OC116, TRFE, and OC17 "
    "were highlighted by the strict ortholog assignments used in Fig. 3A, and labels "
    "were annotated with the corresponding glycosylated Asn position.")

para(
    "For Fig. 3E to G, pairwise glycan-protein enrichment plots were built from "
    "ortholog-mapped protein and glycan abundance differences between species. Protein "
    "abundance for each accession was defined as the mean of nonzero replicate "
    "intensities after excluding proteins with Number Comparable < 2 when available. "
    "Glycan abundance was defined at the protein level as the sum of mean nonzero site "
    "intensities across all quantified glycosylation sites assigned to that accession. "
    "Gallus-versus-Anas and Gallus-versus-Columba comparison spaces were built from "
    "blastp outfmt 6 mappings, retaining the best hit per query when the mean E value "
    "was <= 1 x 10^-5 and the average sequence identity was >= 0.40; when query and "
    "subject had different numbers of non-overlapping HSPs, the maximum identity "
    "threshold >= 0.40 was applied instead. The Anas-versus-Columba plane was bridged "
    "through shared Gallus orthologs that passed the same filter in both datasets. For "
    "each retained ortholog pair, the x coordinate was calculated as log2(I_ref) - "
    "log2(I_comp) and the y coordinate as log2(G_ref) - log2(G_comp), where I and G "
    "denote protein and glycan abundance, respectively. The y = x diagonal therefore "
    "marked matched protein-glycan change, whereas displacement toward the glycan-rich "
    "side identified proteins whose glycan shift exceeded the corresponding change in "
    "bulk protein abundance.")

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
    "model and a matched deglycosylated (apo) reference using APBS v3.4.1. Atomic "
    "partial charges and radii were assigned with PDB2PQR using the CHARMM36 force "
    "field and PROPKA protonation at pH 7.4; glycan heavy-atom partial charges were "
    "assigned from the GLYCAM06 parameter set. "
    "Chem. 29:622). Solvent-accessible surface areas were calculated by the "
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
    ("Surface models derived from micro-CT were first exported as STL files and reverse-engineered in Geomagic Wrap for finite-element pre-processing by sequential de-noising (strength 2), triangle simplification to approximately 300,000 faces, mesh re-gridding at 0.01 mm, iterative defect correction to zero residual faults, and organic parametric surface fitting at minimum tolerance. The resulting eggshell surface models were then imported into LS-DYNA "
     "(Ansys) for explicit dynamic finite-element analysis (unit system: "
     "mm/kg/N/s). The eggshell was assigned elasto-plastic material properties "
     "(Young's modulus E\u202f=\u202f3.0 \u00d7 10\u00b9\u2070 Pa; yield strength \u03c3y\u202f=\u202f1.5 \u00d7 10\u2077 Pa; "
     "tangent modulus 0; maximum equivalent plastic strain at failure 0.05). "
    "The impactor, simulating the egg-tooth, was a frustum "
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
     "per position. Sampling nine offsets allowed local positional heterogeneity to be measured without changing fragment size or loading geometry between species.", False, False),
])
cite(p_m_fea, [16, 37, 69])

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
    (" was assessed by one-sample t test versus the apo reference value (t\u2081\u2083); "
     "total Asp/Glu SASA differences between glycosylated and apo structures were "
     "evaluated by one-sample t test against the apo reference value; shifts in "
     "median surface electrostatic potential were assessed by one-sample t test "
    "against the apo reference value. Finite-element simulation outcomes "
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
