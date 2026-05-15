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

OUT = str(Path(__file__).with_name("manuscript260515.docx"))
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
    "Eggshell glycan states link avian biomineralization to local hatching resistance",
    bold=True, size=14, before=0, after=160, align=WD_ALIGN_PARAGRAPH.LEFT
)

# Short title (≤50 characters)
para("Eggshell glycans and hatching resistance",
     bold=False, size=11, after=60, align=WD_ALIGN_PARAGRAPH.LEFT)

para("Abstract", bold=True, size=11, before=80, after=40,
     align=WD_ALIGN_PARAGRAPH.LEFT)

para(
    "Birds hatch with a broadly conserved egg tooth, shifting the unresolved source of mechanical differences to the eggshell. "
    "We therefore asked whether those differences first arise in the mammillary layer, where matrix proteins regulate early mineralization. "
    "Across chicken, duck, and pigeon, micro-CT morphometry, eggshell-matrix proteomics, intact glycopeptide mass spectrometry, Re-Glyco structural modeling, electrostatic analysis, and finite-element simulation showed that mammillary organization provided the first clear eggshell difference while the overall matrix-protein toolkit remained largely shared. "
    "That combination narrowed the explanatory problem from protein turnover to how common matrix components are chemically redeployed across species. "
    "Among shared proteins, ovalbumin (OVAL) showed the clearest glycan shift, from high-mannose in chicken to neutral complex-hybrid in duck and sialylated complex-hybrid in pigeon. "
    "Structural modeling linked those states to lower Ca²⁺-relevant surface accessibility from chicken to pigeon, and finite-element analysis recovered the same cross-species contrast in local hatching resistance at the mammillary interface. "
    "These results support matrix-protein glycan state as a chemically interpretable layer linking shared eggshell biology to mammillary organization and local hatching performance.",
    bold=False, size=10, before=0, after=80, align=WD_ALIGN_PARAGRAPH.JUSTIFY
)

# Teaser (≤125 characters, one sentence for non-specialist readers)
para(
    "Teaser: Eggshell glycan states track how birds differ in local hatching resistance.",
    bold=False, italic=True, size=10, before=80, after=160, align=WD_ALIGN_PARAGRAPH.LEFT
)

# ════════════════════════════════════════════════════════════════════════════
# Introduction
# ════════════════════════════════════════════════════════════════════════════
para("Introduction", bold=True, size=14, before=0, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT)

# §1 — Background value
p_s1a = spara([
    (" Bird hatching begins with a simple mechanical problem: the embryo must focus force on one small shell-breaking site.", [16, 17, 38, 82, 86]),
    (" In birds, that site is defined by the egg tooth, a transient structure that presses the inner eggshell surface during escape.", [16, 17, 38, 82, 86]),
    (" If egg-tooth function is broadly conserved across species, then meaningful hatching differences are more likely to lie in the eggshell than in the shell-breaking tool itself.", [16, 17, 38, 82, 86]),
    (" That shift in emphasis is biologically plausible because avian eggshells already vary with incubation environment and life-history strategy rather than presenting one uniform solution across birds.", [15, 39, 87, 88]),
    (" Nesting habitat can alter the balance among water loss, gas exchange, and microbial exposure, so terrestrial and aquatic-associated birds need not build identical shell barriers or pore systems.", [39, 87, 88]),
    (" Developmental mode adds a second axis: precocial and altricial birds differ in offspring independence and parental buffering, and comparative work has linked that contrast to differences in cuticle deployment and eggshell antibacterial performance.", [15, 26]),
    (" The mammillary layer is the strongest place to start because it is the first eggshell layer to shape mechanics, and its mammillary knobs mark where calcite growth begins under the control of eggshell matrix proteins.", [1, 4, 28, 38]),
    (" The eggshell therefore lets us read matrix chemistry, microstructure, and hatching-relevant mechanics within one structure.", [1, 4, 16, 20, 21, 38, 42]),
    (" Because later shell layers inherit that early mineralization context, mammillary organization is also the point at which local matrix differences are most likely to scale into mature shell behavior.", [1, 4, 28, 38, 42]),
])

p_s1b = spara([
    (" That makes mammillary organization the first phenotype to examine, because it is the earliest eggshell layer where structural differences can plausibly become mechanical differences.", [1, 4, 16, 28, 38]),
    (" Once attention moves from the conserved hatching tool to this mechanically important eggshell layer, the next question is which molecular regulators organize that layer and how they differ across species.", [1, 2, 4, 20, 21, 28, 38]),
    (" The comparison therefore becomes mechanistic rather than descriptive: once the interface is fixed, the key issue is how a shared shell-building system is tuned differently across species.", [1, 2, 4, 20, 21, 28, 38]),
])

# §2 — Prior work and its limits
p_intro2 = spara([
    (" Eggshell matrix proteins are already known to regulate mammillary-layer mineralization, crystal growth, and mature eggshell architecture. Well-studied examples include ovocleidin-17 (OC17), a calcite-associated eggshell protein; ovocleidin-116 (OC116), a glycosylated eggshell-matrix proteoglycan; ovotransferrin (TRFE), a recurrent iron-binding matrix glycoprotein; and ovalbumin (OVAL), an abundant glycoprotein that has also remained a functional candidate in in vitro mineralization-related work.", [1, 2, 4, 6, 7, 8, 9, 10, 19, 20, 21, 29]),
    (" Because these proteins recur across avian eggshell studies, they offer a natural comparative anchor for asking how a shared mineralization toolkit is reused in different shell contexts.", [1, 2, 4, 20, 21]),
    (" But these proteins do not act only through abundance. As highlighted by Zeng et al., the same eggshell-matrix proteins can appear in distinct N-glycosylation states, implying that differences in glycosylation extent can change biological function without wholesale protein replacement.", [18, 20, 21, 49, 50, 52]),
    (" Avian eggshell studies, however, have rarely resolved which specific N-glycan forms are carried by shared matrix proteins across species.", [18, 20, 21]),
    (" That absence is limiting because comparative eggshell work has often had to infer mechanism from protein identity or abundance without directly observing the glycan forms carried by those same shared proteins.", [18, 20, 21]),
    (" The missing layer is therefore not whether matrix proteins matter, but whether glycosylation on shared matrix proteins can explain why similar protein toolkits yield different eggshell structures.", [2, 4, 18, 20, 21]),
])

p_intro_sig = spara([
    (" That gap matters because glycosylation can influence several protein properties, including stability, intermolecular recognition, surface exposure, and conformational control; among them, folding state is especially important here.", [11, 12, 18, 42, 43, 49, 50, 51]),
    (" Prior in vitro mineralization work on OVAL is therefore highly relevant: once enough Ca²⁺ is loaded onto the protein, OVAL begins to unfold, and mineralization starts as that unfolding proceeds.", [6, 7, 11, 12, 18, 42, 43]),
    (" That logic is why we sought to connect glycan-state detection to Ca²⁺-relevant accessibility: if glycan differences reshape how the same shared matrix protein holds or leaves its folded state, then structural modeling should reveal corresponding differences in the Ca²⁺-accessible surface presented at the onset of mineralization.", [11, 12, 18, 42, 43, 49, 50, 51]),
    (" If that structural difference matters biologically, then it should still be visible at the hatching-relevant mechanical end point: local resistance at the mammillary interface under egg-tooth-like loading.", [16, 17, 34, 35, 37, 38]),
])

# §3 — Core gap
p_intro_gap = spara([
    (" We therefore framed the core question more narrowly: once the comparison is anchored to a conserved egg-tooth interface, can glycan-state differences on shared matrix proteins help explain why the same shell-building toolkit presents different Ca²⁺-accessible states when mineralization begins?", [11, 12, 18, 42, 43, 49, 50, 51]),
    (" OVAL provided the clearest test case because prior in vitro work had already shown a specific mechanistic sequence, Ca²⁺ loading, then unfolding, then mineralization onset, making it reasonable to ask whether glycan state helps set that calcium-accessible conformational context.", [6, 7, 11, 12, 18, 42, 43]),
    (" This framing let the manuscript follow one clear chain from conserved hatching tool to eggshell structure, matrix regulation, glycosylation, Ca²⁺-accessible surface state, structural inference, and finite-element validation.", [4, 11, 12, 16, 42, 57, 69]),
    (" The aim was not to force all three species into one overly simple ranking, but to ask whether one conserved interface could still reveal a coherent path from shell structure to molecular state and local function.", [4, 11, 12, 16, 42, 57, 69]),
])

# §4 — This study
p_intro4 = smixed([
    ([("In this study, we compared ", False, False),
            ("Gallus gallus", False, True),
            (", ", False, False),
            ("Anas platyrhynchos", False, True),
            (", and ", False, False),
            ("Columba livia", False, True),
            (" as terrestrial precocial, aquatic-associated precocial, and terrestrial altricial models, respectively, thereby spanning crossed developmental and ecological contrasts within a common hatching framework.", False, False)], [3, 22, 24, 25, 82, 83]),
    ([(" This design prevented the comparison from collapsing into either a simple phylogenetic pairing or a single precocial-versus-altricial contrast.", False, False)], [3, 22, 24, 25, 82, 83]),
    ([(" We integrated micro-CT morphometry to define mammillary organization, comparative eggshell-matrix proteomics and intact glycopeptide mass spectrometry to resolve shared matrix proteins and their glycan states, Re-Glyco structural modeling and electrostatic analysis to infer protein-surface consequences, and finite-element simulation to test whether the same cross-species contrast remained detectable in local hatching resistance.", False, False)], [3, 22, 24, 25]),
    ([(" Each level was therefore used to constrain the next, so that molecular interpretation remained tied to shell structure rather than floating free of the material context.", False, False)], [3, 22, 24, 25, 42]),
        ([(" In the present dataset, that chain was clearest for OVAL, whose glycan states aligned with mammillary density, Ca²⁺-relevant surface accessibility, and local hatching resistance.", False, False)], [11, 12, 16]),
    ([(" OVAL was therefore not introduced as a preferred candidate in advance; it emerged as the shared protein on which the full comparison became most legible.", False, False)], [11, 12, 16, 18, 42]),
        ([(" The resulting Introduction therefore leads into the Results with the same causal sequence used by the manuscript as a whole: conserved egg-tooth function, eggshell focus, mammillary organization, matrix proteins, glycosylation, structural inference, and finite-element validation.", False, False)], [4, 11, 12, 16, 42]),
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
        ([(' Because the shell-breaking tool appeared functionally conserved, the next source of hatching-related difference had to be sought in the eggshell. We then placed extant birds into a comparative space using 10,993 AVONET species records and selected three deliberately separated model species from it (Fig. 1A).', False, False)], [15, 16, 22, 23, 24, 25, 41]),
        ([(' That broader mapping mattered because it showed that the three focal taxa were not arbitrary case studies, but deliberately spaced points in avian ecological-developmental space.', False, False)], [15, 16, 22, 23, 24, 25, 41]),
        ([(' Within this comparison space, ', False, False),
            ('Gallus gallus', False, True),
            (', ', False, False),
            ('Anas platyrhynchos', False, True),
            (', and ', False, False),
            ('Columba livia', False, True),
            (' occupy representative positions for terrestrial precocial, aquatic-associated precocial, and terrestrial altricial strategies, respectively, and were therefore chosen for downstream comparison.', False, False)], [15, 22, 23, 24, 25, 41]),
    ([(' This functional grouping only partly overlaps with phylogeny: chicken and duck remain closely related precocial taxa but separate along the habitat axis, whereas pigeon anchors the altricial end of the comparison (Fig. S2).', False, False)], [15, 23, 24, 25]),
    ([(' The comparison was therefore structured to retain shared ancestry in view while still forcing clear life-history separation into the same analytical frame.', False, False)], [15, 23, 24, 25, 41]),
    ([(' The focal species differed in beak-tip geometry, but the egg tooth itself remained a similarly localized dorsal breaker in all three species and pointed to the same inside-out shell-breaking event during hatching (Fig. 1B).', False, False)], [16, 17, 22, 38, 82, 86]),
    ([(' Within this contrast set, the comparison therefore moves from egg-tooth conservation to eggshell divergence: once the interface is held constant, the relevant question becomes which eggshell layer first separates the species.', False, False)], []),
])

# ════════════════════════════════════════════════════════════════════════════
head("Mammillary organization marks the first eggshell difference")

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
    (" (0.3975 ± 0.0127). Quantitatively, chicken showed the densest early mineralization pattern, pigeon devoted the largest share of shell volume to crystal units grown from individual mammillary knobs, and duck remained intermediate in crystal-unit proportion while resembling pigeon in density. The two metrics therefore did not collapse into one simple monotonic ranking, but they agreed that mammillary organization had already diverged in measurable ways before later shell traits were considered. Because mammillary organization is the earliest structural layer governing eggshell mechanics and is controlled by eggshell matrix proteins, the next question was whether this cross-species morphology reflected wholesale toolkit replacement or different use of a largely shared system.", False, False),
])
cite(p_s0b, [1, 2, 28, 30, 36, 38, 53, 54, 57])

doc.add_page_break()
add_centered_figure("Fig1.jpg", width_cm=10.1, before=0, after=20)
add_main_figure_legend(
    "Fig. 1.",
    "Comparative space, egg-tooth morphology, and mammillary-layer phenotype after defining a shared hatching interface.",
    [
        ("(A) Three-dimensional AVONET comparison space built from 10,993 species records, with axes summarizing aquatic association, lifestyle-habitat discordance, and developmental mode. After the common egg-tooth interface is established in the main text, this panel locates the broader comparison space from which the three focal species were selected. Colors denote avian orders; gray boxes highlight the deliberately separated regions occupied by the three focal species, and open circles mark ", False, False),
        ("Gallus gallus", False, True),
        (", ", False, False),
        ("Anas platyrhynchos", False, True),
        (", and ", False, False),
        ("Columba livia", False, True),
        (". (B) Species-specific lateral head views (top row) and dorsal beak views (bottom row) showing the egg-tooth-bearing beak tip in chicken, duck, and pigeon. Although the beak-tip geometry differs among species, all three present a localized hatching interface positioned to transmit embryonic force from the inside of the shell. (C) Representative micro-CT sections and three-dimensional inner-surface reconstructions of the mammillary layer. Chicken shows smoother rounded mammillae, duck more ridged and angular mammillae, and pigeon discrete triangular-conical mammillae. Scale bars, 100 μm. (D) Boxplots of mammillary density and unit volume ratio across species. Points denote individual measurements; P values from one-way ANOVA are shown above the plots, and different letters indicate Duncan's multiple range test groupings.", False, False),
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
    ("Orthogroup analysis identified a large shared core together with pairwise-shared and lineage-restricted complements in the eggshell matrix proteomes of the three species (Fig. S3). This pattern indicates that the observed eggshell differences did not arise from wholesale replacement of the matrix-protein toolkit.", [11, 20, 52, 53, 54]),
    (" At the overall level, the proteome still followed the broad frame set by shared ancestry (Fig. S4). The main question therefore shifted from which proteins were present to how a shared set of proteins was being used.", []),
    (" The retained shared core was therefore the main molecular background against which any candidate mechanistic difference had to be judged, not a residual category to be ignored.", [11, 20, 52, 53, 54]),
])

p_sprot_go = spara([
    ("GO enrichment and gene-family turnover further indicated lineage-specific immune and defense background (Figs. S5 and S6), but those signals mainly described the comparative backdrop rather than the feature most directly tied to mammillary organization.", [3, 5, 14, 15, 24, 25, 26, 29, 52]),
    (" They therefore remained relevant as evolutionary context, yet they did not by themselves identify the most proximate layer linking eggshell structure to hatching-relevant mechanics.", [3, 5, 14, 15, 24, 25, 26, 29, 52]),
])

p_sprot_focus = spara([
    (" At the same time, the G. gallus-exclusive set was significantly enriched for protein N-linked glycosylation (BP; Fig. S5), indicating that the most informative differences lay not only in proteome background but also in post-translational state.", []),
    (" Because glycosylation can change what the same matrix protein does, this result narrowed the analysis from broad proteome background to comparative glycoproteomics and, specifically, to how N-linked glycosylation on shared proteins differed across the three species.", [8, 18, 19, 21]),
    (" In other words, the comparison no longer asked only which matrix proteins were present, but which chemical states on those proteins were preferentially deployed in each lineage.", [8, 18, 19, 21]),
])

head("OVAL glycosylation marks the clearest cross-species difference")

p_s2a = mixed([
    ("Having established that the observed eggshell differences did not reflect wholesale replacement of the eggshell-matrix toolkit, we next asked which shared glycoprotein differences tracked that phenotype most closely. Intact glycopeptides gave a direct cross-species view of specific glycoforms on avian eggshell matrix proteins. The glycoprotein network in Fig. 2 showed a conserved three-species core together with pairwise-shared and lineage-restricted sectors. High-Mannose and Complex-Fucosylated glycans formed a broad background across many protein families, whereas more extended sialylated classes were concentrated in the peripheral difference nodes. That network-level asymmetry mattered because it pointed away from species-exclusive proteins and toward shared glycoproteins whose states could still diverge strongly. The comparison therefore narrowed from many glycoprotein differences to a smaller group of shared candidates suitable for ortholog and structural analysis.", False, False),
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
    (" as the reference, non-reference candidates were retained only when the mean E-value was below 1 × 10⁻⁵ and sequence identity met the final comparability thresholds. This filtering restricted the downstream comparison to high-confidence orthologs. The restriction was important because the structural interpretation below required comparing like with like rather than merely different members of a broad protein family. Under that stricter mapping, OC17 was glycosylated only in chicken, whereas OC116, TRFE, and OVAL all retained glycosylation signals across the three species and therefore served as shared anchors. Among them, OVAL showed the clearest cross-species glycan differences and became the priority target for subsequent structural analysis.", False, False),
])
cite(p_s2b, [6, 7, 8, 9, 10, 19, 21, 29])

p_s2c = spara([
    ("Integrating protein abundance and glycan abundance into the same analytical frame then clarified why OVAL, rather than OC116 or TRFE, best tracked the cross-species eggshell differences (Fig. 3B-D). Across the full dataset, protein-glycan coupling was weak in chicken but consistently positive in duck and pigeon. The three lineages therefore differed not only in glycan identity, but also in how glycosylation scaled with protein output.", []),
    (" Yet the highlighted eggshell-matrix proteins showed that high abundance and high glycan output were not the same thing. OVAL remained abundant in all three species, but its glycan burden changed sharply across them: relatively modest in chicken, stronger in duck, and strongest in pigeon. OVAL therefore stayed cross-species comparable while also escaping simple abundance matching.", []),
    (" By comparison, OC116 and TRFE remained informative shared proteins but did not separate bulk protein abundance from glycan output as consistently as OVAL did in the same analytical space.", [1, 4, 6, 7, 8, 18, 47, 48]),
    (" The pairwise enrichment plots in Fig. 3E-G sharpened the same point. Intact-glycopeptide assignments identified OVAL as the clearest cross-species contrast, from compact high-mannose glycans in chicken to neutral complex-hybrid glycans in duck and more extended sialylated complex-hybrid glycans in pigeon. Figure 3B-G therefore identified OVAL as the shared protein whose glycosylation changed in the clearest phenotype-relevant way.", [1, 4, 6, 7, 8, 18, 47, 48]),
])

p_s2d = spara([
    ("Because those OVAL glycan classes differ strongly in size and charge distribution, the comparison pointed to OVAL surface accessibility rather than OVAL abundance alone as the molecular variable most likely to matter for eggshell mineralization.", [1, 4, 6, 7, 8, 18, 47, 48]),
    (" The key issue was therefore how glycan state changed the exposed, chemically active OVAL surface during early mineralization, a feature that could be tested directly by structural ensembles and electrostatic calculations rather than inferred only from abundance matrices.", [1, 4, 6, 7, 8, 18, 42, 47, 48]),
    (" The relevant variable was not simply how much OVAL was present, but how much of its acidic interface remained chemically reachable once decorated by different glycans.", [1, 4, 6, 7, 8, 18, 42, 47, 48]),
    (" Taken together, ortholog control, abundance decoupling, and glycan-class progression made OVAL the only shared candidate that remained simultaneously comparable, chemically specific, and structurally actionable.", [1, 4, 6, 7, 8, 18, 42, 47, 48]),
])

add_centered_figure("Fig3.jpg", width_cm=15.5)
add_main_figure_legend(
    "Fig. 3.",
    "Ortholog screening and abundance-decoupled glycoprotein prioritization.",
    [
        ("(A) Circos-style summary of the orthologous glycoprotein subset retained after stringent BlastP filtering, highlighting shared candidate proteins across chicken, duck, and pigeon. Species are color-coded, and gray labels indicate chicken proteins without retained non-chicken orthologs under the final comparison criteria. OVAL, OC116, TRFE, and OC17 are emphasized as the key interpretable targets. (B to D) Proteotype coevolution plots comparing log2-transformed protein abundance and glycan abundance within chicken, duck, and pigeon, respectively; inset values show Spearman's ρ and two-sided P. Highlighted proteins identify cases where glycan investment diverges from protein abundance. (E to G) Pairwise two-dimensional glycan-protein enrichment plots for Gallus versus Anas, Gallus versus Columba, and Anas versus Columba. OVAL shows the clearest shift away from abundance matching across species and was therefore prioritized for structural interpretation.", False, False),
    ],
)

head("OVAL glycan state reshapes surface accessibility")

p_s3a = spara([
    ("OVAL was then examined as the strongest shared candidate for a structural mechanism. In vitro work has already shown that OVAL can participate in early mineralization-related events, so glycan state provided a biologically plausible control layer. We therefore rebuilt dominant glycosylated OVAL ensembles together with matched deglycosylated references to test whether the three species differed mainly through glycan-dependent surface behavior rather than through backbone sequence alone.", [6, 7, 11, 12, 18, 42, 43]),
    (" The rebuilt comparison covered the dominant detected glycan classes in all three species, so species-specific glycan geometry could be evaluated within the same structural frame rather than as isolated models.", [11, 12, 18, 42, 43]),
    (" Panels A-C address the first and most basic question: what changes in the protein when glycans are present versus absent? In panel A, a Ca²⁺ hotspot denotes an acidic Asp/Glu surface position with sufficiently negative electrostatic potential to favor local calcium approach. Panel B then measures how much of that carboxylate-bearing surface remains physically exposed, and panel C visualizes the same shift as a whole-surface electrostatic map. Across all three species, glycosylation displaced these readouts away from the matched deglycosylated references, whereas the deglycosylated backbones themselves clustered much more closely across species. Once glycans were removed, much of the cross-species separation collapsed, indicating that most of that divergence was introduced by glycosylation rather than by the protein scaffold alone (Fig. S7).", [6, 7, 11, 12, 18, 42, 43]),
])

p_s3b = spara([
    (" Panels D-G then explain where that separation came from by describing the glycans themselves rather than the protein-wide readout. Radius of gyration reports how broadly a glycan occupies space, end-to-end distance reports how extended the chain becomes, glycan-protein distance reports how far the glycan projects from the protein surface, and minimum glycan-backbone distance reports how tightly it folds back to contact the protein.", [11, 12, 42, 43, 44, 45, 46]),
    (" Read together, these metrics showed that pigeon glycans occupied the largest conformational space yet also approached the protein surface most closely, consistent with long but surface-hugging glycans. Chicken glycans remained the most compact and least contacting, whereas duck remained intermediate. The three species therefore differed not only in glycan class, but also in the spatial manner by which the glycan layer sat over the OVAL surface (Fig. 4D-G).", [11, 12, 42, 43, 44, 45, 46]),
])

p_s3c = spara([
    (" Panels H-K move one step further, from glycan geometry to glycan-protein interaction and its consequence for Ca²⁺ accessibility. Interface shielding in panel H quantifies how much of the relevant acidic OVAL surface is masked by glycans. Panel I reports the solvent-accessible surface area of hotspot residues, that is, how much of those acidic sites remains open to solvent and therefore potentially to ions. Panel J records what fraction of candidate acidic residues still remains in the hotspot category, and panel K counts how many Ca²⁺-relevant hotspots remain both electrostatically favorable and physically reachable.", [11, 12, 42, 43, 44, 45, 46, 49, 50, 51]),
    (" Across these four readouts, shielding increased from chicken to duck to pigeon, whereas exposed hotspot area, hotspot fraction, and net accessible hotspot number declined in the opposite direction. At this stage the interpretation became specific: the species were not separated simply by carrying different glycans, but by how strongly those glycans covered the shared acidic OVAL interface that could otherwise engage local calcium during early mineralization (Fig. 4H-K).", [11, 12, 42, 43, 44, 45, 46, 49, 50, 51]),
])

p_s3d = spara([
    (" Panels L and M summarize that result at the whole-interface level by partitioning each hotspot readout into an exposed component and a glycan-shielded component. Panel L performs this bookkeeping for hotspot counts, whereas panel M does so for hotspot-residue surface area, allowing the reader to see not only how much potentially Ca²⁺-relevant surface exists, but how much of it remains usable after glycan masking.", [11, 12, 42, 43, 44, 45, 46, 49, 50, 51]),
    (" Chicken retained the largest exposed fraction, pigeon shifted the largest fraction into the shielded compartment, and duck again remained intermediate. The three dominant OVAL glycoforms therefore converged on one ordered physical consequence: high-mannose chicken OVAL left the acidic interface most open, neutral complex-hybrid duck OVAL partly covered it, and sialylated complex-hybrid pigeon OVAL produced the most extensive shielding. Taken together, the reglycosylation and electrostatic analyses resolved the cross-species contrast into a stepwise physical interpretation, from glycan composition, to glycan geometry, to interface masking, to Ca²⁺-relevant accessibility on a shared matrix protein (Fig. 4L-M).", [11, 12, 42, 43, 44, 45, 46, 49, 50, 51]),
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

head("Finite-element modeling links the same contrast to local hatching resistance")

p_s4a = mixed([
    ("The common egg-tooth interface introduced at the start of the Results section was then turned into an explicit loading design for finite-element testing. Figure 5A summarizes that hatching-relevant loading background, whereas Fig. 5B-D pair species-specific dorsal beak views, with dashed boxes marking the egg-tooth position, and the corresponding micro-CT-derived finite-element setups built from the beak-tip geometry summarized in Fig. 1B. Because the meshes preserved species-specific shell geometry derived from micro-CT, the mechanical test remained anchored to the same mammillary context identified morphologically rather than substituting an idealized shell wall. Previous studies have often measured whole-eggshell strength under outside loading, but our question here was narrower: did the same cross-species contrast remain visible at the mammillary interface during hatching? In that sense, the finite-element analysis served as a scale-bridging test of whether the contrast inferred from OVAL accessibility and mammillary organization remained detectable at the mechanical interface experienced during shell breaking. Using a conical indenter to approximate the egg tooth, impact loading was applied to circular eggshell fragments (model diameter D = 2.0 mm) at nine parameterized lateral-offset positions on a 3 × 3 grid (0.5 mm spacing), yielding n = 9 independent contact shear-stress time courses per species. To reduce the influence of model size, gross geometry, and especially eggshell thickness, both raw peak contact force (F_max) and peak contact shear stress (τ_max) were recorded. Here, τ_max was treated as the direct readout of local hatching resistance at the mammillary contact interface because raw force thresholds alone could be elevated by thickness without preserving the same local interface behavior. Peak τ_max was extracted directly from the finite-element output at each offset position and species means ± s.d. were then calculated across the nine positions (Fig. S8A-F; eggshell thicknesses: ", False, False),
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
    "Hatching-relevant loading design and species-specific finite-element setup constrained by egg-tooth geometry.",
    [
        ("(A) Schematic of the egg tooth pressing the eggshell from the inner side during hatching. (B to D) Species-specific dorsal beak views with dashed boxes marking the egg-tooth position, paired with the corresponding micro-CT-derived finite-element setups for ", False, False),
        ("Gallus gallus", False, True),
        (", ", False, False),
        ("Anas platyrhynchos", False, True),
        (", and ", False, False),
        ("Columba livia", False, True),
        (", respectively. In each species panel, the left image shows the dorsal beak view used to localize the egg tooth, and the right image shows the eggshell-fragment mesh, conical impactor, and representative finite-element model output at contact. Together, these panels define the hatching-relevant loading background and show that the simulations were built from reconstructed shell geometry rather than idealized shells.", False, False),
    ],
    before=20,
    after=80,
)
doc.add_page_break()

mixed([
    ("With the loading framework defined, one-way ANOVA of F_max across the nine offset positions supported a significant species effect (p = 1.639 × 10⁻¹³): ", False, False),
    ("G. gallus", False, True),
    (" 1.117 ± 0.110 N > ", False, False),
    ("A. platyrhynchos", False, True),
    (" 0.898 ± 0.090 N > ", False, False),
    ("C. livia", False, True),
    (" 0.485 ± 0.039 N, with all pairwise differences significant (Fig. 6A). By contrast, τ_max collapsed into a two-level pattern (p = 6.644 × 10⁻¹⁰): ", False, False),
    ("G. gallus", False, True),
    (" τ_max = 551.6 ± 108.8 MPa was significantly higher than ", False, False),
    ("A. platyrhynchos", False, True),
    (" 404.0 ± 39.6 MPa and ", False, False),
    ("C. livia", False, True),
    (" 393.0 ± 35.2 MPa, whereas the latter two species did not differ significantly from each other (Fig. 6B).", False, False),
])

mixed([
    ("The difference between F_max and τ_max showed that duck's higher raw contact force was driven mainly by its greater shell thickness (0.35 mm versus 0.19 mm in pigeon), rather than by superior unit-area material resistance. By contrast, ", False, False),
    ("G. gallus", False, True),
    (" exhibited a 36-40% increase in τ_max relative to the two other species, indicating higher local hatching resistance independent of shell thickness. The τ_max grouping, with ", False, False),
    ("G. gallus", False, True),
    (" alone in the high group and ", False, False),
    ("A. platyrhynchos", False, True),
    (" together with ", False, False),
    ("C. livia", False, True),
    (" in the low group, matched exactly the DMRT grouping for mammillary density recovered by micro-CT (Fig. 1D). In that sense, the mechanics did not create a new pattern; they retained the contrast already recovered from mammillary organization and OVAL accessibility.", False, False),
])

mixed([
    ("Whole-shell fracture force alone could make duck appear mechanically superior to chicken because of its greater shell thickness, despite the absence of the same high-density mammillary state. By focusing instead on local hatching resistance at the micro-CT-derived mammillary interface, τ_max removes that ambiguity and shows that the high-density chicken state remains functionally distinct, whereas duck and pigeon converge at lower resistance. The functional readout therefore preserved the same asymmetry already visible in earlier sections: chicken occupied the high-resistance end, whereas duck and pigeon converged on the lower-resistance side. The finite-element analysis therefore extends the molecular-to-structural argument to a functional endpoint: the glycosylation-associated differences identified above are not only compatible with altered mammillary organization, but are also mirrored by a simulated difference in local hatching resistance across the three model species.", False, False),
])
add_centered_figure("Fig6.jpg", width_cm=15.5)
add_main_figure_legend(
    "Fig. 6.",
    "Force and local hatching resistance across species.",
    [
        ("(A) Mean contact-force time courses across nine impact positions for ", False, False),
        ("Gallus gallus", False, True),
        (", ", False, False),
        ("Anas platyrhynchos", False, True),
        (", and ", False, False),
        ("Columba livia", False, True),
        (", shown with shaded ±1σ envelopes, together with boxplots of peak contact force (Fmax). (B) Mean contact shear-stress time courses for the same nine positions together with boxplots of peak shear stress (τmax). Symbols on the curves mark the species mean peak value; points in the boxplots denote individual impact positions (n = 9 per species). P values from one-way ANOVA are shown above the boxplots, and different letters indicate Duncan's multiple range test groupings. Fmax differs across all three species, whereas τmax separates chicken from the lower-τmax duck and pigeon group, indicating that local hatching resistance at the mammillary interface most closely tracks the structural differences inferred from morphology and OVAL accessibility.", False, False),
    ],
)

cite(p_s4a, [16, 17, 34, 35, 37, 38])

# ════════════════════════════════════════════════════════════════════════════
# Discussion
# ════════════════════════════════════════════════════════════════════════════
para("Discussion", bold=True, size=14, before=320, after=160,
    align=WD_ALIGN_PARAGRAPH.LEFT)

p_disc_mam1 = smixed([
    ([('Taken together, the results define a consistent comparative sequence. Because egg-tooth function remained conserved across the three birds, the most informative differences had to be sought in the eggshell. The first mechanically relevant difference appeared in the mammillary layer, and the shared matrix toolkit then focused the comparison on glycosylation rather than wholesale protein replacement. ', False, False),
            ('Within that chain, OVAL glycan state provided the clearest link from molecular variation to surface accessibility and local hatching resistance.', False, False)], [1, 2, 4, 15, 16, 17, 20, 21, 22, 23, 38, 39, 41, 42, 82, 86]),
    ([(' The mammillary layer remains central because it is the earliest level at which matrix chemistry, crystal initiation, and eggshell mechanics meet in the same material context. That sequence matters because the analysis does not begin from a favored molecule; it narrows to one through successive structural levels.', False, False)], [1, 2, 20, 28, 30, 36, 38, 53, 54]),
])

p_disc_mam2 = spara([
    ("Among the molecular layers examined here, OVAL N-glycan architecture most closely tracked the cross-species structural differences.", []),
    (" Orthogroup turnover, gene-family change, and glycoprotein-network divergence still matter, but they mainly define comparative background rather than the nearest explanation.", [1, 2, 8, 18, 21, 27]),
    (" OVAL glycan state was especially informative because it is shared across species, chemically interpretable, and located on an abundant matrix protein already implicated in mineralization.", [4, 6, 7, 18, 21, 42, 44, 45, 46]),
    (" That combination makes OVAL useful not because it is unique, but because it remains comparable across species while still carrying interpretable chemical divergence.", [4, 6, 7, 18, 21, 42, 44, 45, 46]),
    (" It also remains interpretable at the level of specific glycan classes rather than only as a generic increase or decrease in modification load.", [4, 6, 7, 18, 21, 42, 44, 45, 46]),
])

p_disc_other = para(
    "The non-OVAL signals still matter. OC116 and TRFE remained informative shared proteins, whereas OC17 appeared glycosylated only in chicken and may therefore represent a more lineage-restricted mineralization program. The shared toolkit therefore remains multicomponent even if one component offers the most experimentally tractable explanatory handle. These findings do not imply that one protein explains the entire eggshell; rather, OVAL provides a particularly clear path from matrix modification to structure and function in the present dataset."
)

cite(p_disc_other, [10, 19, 21, 29, 42, 44, 45, 46, 66, 81])

p_disc_oval = para(
    "Re-Glyco and APBS analyses provide the structural bridge in this argument. Compact chicken glycans left the critical acidic OVAL surface relatively exposed, whereas the longer and more electronegative pigeon glycans reduced Ca²⁺ approach both sterically and electrostatically; duck again fell between those endpoints. That bridge matters because it turns glycan-state variation from a catalogued compositional difference into a physically interpretable surface difference. This result does not by itself prove a direct causal mechanism for mineralization, but it indicates how different glycan states on the same matrix protein can change the chemical surface presented to the mineralizing environment."
)

cite(p_disc_oval, [4, 11, 12, 42, 44, 45, 46, 49, 50, 51, 52, 55, 65])

p_disc_axis = spara([
    ("Mammillary-layer mineralization mode remains the central structural level in the interpretation.", [1, 2, 20, 28, 38]),
    (" Once early calcite crystal units are established, later eggshell regions inherit the spacing logic created in that first mineralization window, so a dense mammillary field changes matrix retention, mineral continuity, and local stress redistribution as well as morphology.", [1, 2, 28, 30, 36, 38]),
    (" For that reason, mammillary organization is not merely another shell trait, but the earliest material context in which matrix chemistry can plausibly bias later mechanical outcome.", [1, 2, 20, 28, 30, 36, 38]),
])

p_disc_regulator = spara([
    ("Duck prevents the comparison from collapsing into a simple precocial-versus-altricial contrast.", [4, 15, 23, 27, 39, 41]),
    (" If developmental mode alone dictated eggshell-building chemistry, duck should cluster with chicken throughout the molecular and mechanical analyses.", [15, 23, 27]),
    (" It does not: duck retains the broad life-history condition of precocial development while shifting toward an intermediate OVAL glycan state and accessibility profile, with a τ_max outcome that converges with pigeon rather than with chicken.", [4, 12, 16, 17, 39, 41]),
    (" Duck therefore shows that developmental category alone is insufficient to predict the molecular state ultimately associated with local shell performance.", [4, 12, 15, 23, 27, 39, 41]),
    (" Duck therefore reinforces the main argument that a shared hatching problem can be solved through different matrix-state configurations.", [4, 12, 15, 23, 27, 39, 41]),
])

p_disc_discriminate = spara([
    ("Several plausible background variables can be separated from the features that repeatedly recover the same cross-species pattern.", []),
    (" Eggshell thickness, body size, and broad reproductive ecology may all contribute background variation, and lineage history undoubtedly matters.", [2, 14, 16, 17, 24, 25]),
    (" But thickness-based explanations do not account for the τ_max differences, and diffuse lineage-divergence explanations do not explain why the same contrast recurs in glycan class, electrostatic accessibility, and mammillary-layer organization.", [4, 16, 17, 20, 21, 38, 42]),
    (" What recurs across the dataset is therefore not a generic species ranking, but a repeated alignment between glycan state, surface shielding, mammillary organization, and τ_max grouping.", [4, 16, 17, 20, 21, 38, 42]),
    (" Ecology and phylogeny establish the design space, whereas matrix-protein glycan state offers a proximate chemically readable layer in this three-species dataset.", [1, 2, 4, 20, 21, 38, 42, 57, 70]),
])

p_disc_mech = spara([
    ("The mechanical analysis extends the same pattern to an organism-level functional context.", [16, 17, 38]),
    (" τ_max rather than raw fracture force best captures the mammillary-level mechanical difference.", [16, 17, 34, 35, 37, 38]),
    (" Absolute failure load remains sensitive to eggshell thickness and whole-eggshell geometry, whereas τ_max provides a more direct readout of local hatching resistance at the mammillary interface under hatching-relevant loading. Duck and pigeon converged in τ_max despite their different overall mammillary geometries, suggesting that once the chicken-like high-density state is absent, downstream shape variation alone does not restore the same mammillary-interface resistance.", [1, 2, 16, 17, 34, 35, 37, 38]),
    (" That is precisely why τ_max, rather than whole-shell force alone, is the more informative functional companion to the molecular and morphological results.", [16, 17, 34, 35, 37, 38]),
])

p_disc_evo = para(
    "Duck sharpens the interpretation because it separates developmental mode from the rest of the chain. It did not remain chicken-like across the molecular, structural, and mechanical analyses, showing that a shared hatching problem can be resolved through different matrix-state configurations. In practical terms, duck indicates that thickness can buffer whole-shell loading more readily than it can recreate the same local interface resistance. Shell thickness may buffer whole-shell loading, but it did not erase the local τ_max differences recovered at the mammillary interface."
)

cite(p_disc_evo, [3, 15, 16, 17, 37, 38, 39, 41, 57])

p_disc_function = para(
    "The broader implication is methodological as much as biological. In this dataset, a chemically specific post-translational state on a shared matrix protein helped fill the missing layer between eggshell structure and local function. This type of intermediate layer is especially valuable in biomineralization systems, where broad proteome turnover is often easier to detect than the specific chemical states that bias crystal growth. Similar logic may extend beyond avian eggshells, because many mineralized systems rely on abundant matrix proteins whose post-translational states can shift without wholesale replacement of the underlying protein repertoire. That does not reduce eggshell diversification to a single molecule, but it does show how a conserved protein toolkit can generate different structural outcomes through glycan-state redeployment."
)

cite(p_disc_function, [4, 6, 7, 18, 20, 21, 42, 49, 50, 52, 62, 67, 68, 69, 71, 72, 73, 75, 77, 79])

p_disc_selection = para(
    "OVAL glycan state therefore serves here as a chemically specific comparative layer that can be mapped onto structure and evaluated against function. In omics-rich biomineralization studies, lineage differences are often easier to detect than the molecular features that most consistently organize phenotype itself. In this eggshell system, that layer appears to lie in glycan state rather than in broad proteome turnover. The same comparative logic could in principle be extended to other abundant matrix proteins if their modification states can be resolved with similar confidence. In other mineralized systems, analogous layers may instead be carried by sulfation, phosphorylation, proteolytic processing, or regulated cofactor binding on reused matrix proteins."
)

cite(p_disc_selection, [20, 21, 42, 49, 50, 52, 58, 59, 60, 65, 66, 74])

p_disc_future = para(
    "Caveats define the present scope. We analyzed dominant glycoforms rather than the full in vivo range of glycan heterogeneity because current glycan-structure libraries remain incomplete. That means the present structural ensembles are best read as well-supported dominant states rather than exhaustive representations of in vivo glycan diversity. We also treated each species as mechanically uniform at the scale of the mean eggshell and relied on incompletely constrained uterine ionic conditions in the APBS framework. The most useful next tests are defined-glycoform mineralization assays, site-directed manipulation of OVAL glycosylation coupled with uterine chemistry measurements, site-resolved mechanical validation, and broader phylogenetic sampling. It will be equally important to test whether the same glycan-state axis remains stable across more taxa, or whether different avian lineages solve the same shell-building problem through distinct molecular routes. These experiments should clarify whether OVAL glycan state participates directly in mineralization or mainly serves as a comparative molecular indicator."
)

cite(p_disc_future, [4, 11, 12, 20, 21, 42, 49, 50, 51, 52, 57, 70, 76])

p_disc_close = para(
    "Within those limits, the present three-species comparison still supports one continuous interpretation. Conserved egg-tooth function shifts the analysis to the eggshell, the first clear difference appears in the mammillary layer, and the shared matrix toolkit focuses attention on glycosylation rather than wholesale protein replacement. Within that chain, OVAL glycan state provides the clearest structurally interpretable link between mammillary organization and local hatching resistance. The main claim is therefore deliberately limited: matrix-protein glycan state is not the only explanatory layer, but it is one that remains legible from chemistry to local mechanical consequence in the present dataset. Matrix-protein glycan state is therefore best viewed here as a chemically interpretable comparative layer, not as the sole determinant of eggshell performance."
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
        "All eggs were stored at 4\u00b0C until processing. Fresh collection and matched cold storage were used to minimize post-oviposition variation before comparative analysis.", False, False),
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
    " were pooled at the two-egg level to reduce idiosyncratic egg-to-egg variation while preserving the dominant species-level signal. "
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
     "including four NeuAc positional isomers resolved from the GlycoShape library). Using the same random seed and ensemble size for every submitted glycan maintained matched sampling depth across species. "
     "Ensemble geometric descriptors were calculated for each model from atomic "
     "coordinates using BioPython: the radius of gyration (Rg) of all glycan heavy "
     "atoms, the end-to-end distance of the glycan chain, and the minimum distance "
     "between any glycan heavy atom and protein C\u03b1 atoms (minimum C\u03b1 contact "
     "distance). Per-structure summary statistics (mean\u00a0\u00b1\u00a0s.d.) and pairwise species "
     "comparisons (Mann\u2013Whitney\u00a0U test, two-tailed) were performed for each descriptor.", False, False),
])
cite(p_m_reglyco, [11, 49, 50, 51, 56, 58, 59, 60, 65])

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
    "The impactor, simulating the egg tooth, was a frustum "
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
