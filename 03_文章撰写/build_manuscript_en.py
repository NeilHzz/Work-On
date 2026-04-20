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

OUT = str(Path(__file__).with_name("manuscript260420v1.docx"))

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

# ════════════════════════════════════════════════════════════════════════════
# Science Advances 必需元素：Title / Short title / Authors / Teaser
# ════════════════════════════════════════════════════════════════════════════

# Title (≤135 characters)
para(
    "Glycosylation states link ecological and evolutionary variation to avian eggshell structure",
    bold=True, size=14, before=0, after=160, align=WD_ALIGN_PARAGRAPH.LEFT
)

# Short title (≤50 characters)
para("Glycosylation links eggshell structure",
     bold=False, size=11, after=60, align=WD_ALIGN_PARAGRAPH.LEFT)

# Authors & Affiliations (placeholder)
para(
    "[Insert full author names, affiliations, ORCID IDs, equal-contribution notes, and corresponding author information before submission.]",
    bold=False, size=10, before=80, after=80, align=WD_ALIGN_PARAGRAPH.LEFT
)

para("Abstract", bold=True, size=11, before=80, after=40,
     align=WD_ALIGN_PARAGRAPH.LEFT)

para(
    "A mechanistic explanation for cross-species divergence in avian eggshell structure remains lacking. "
    "Here, we integrated micro-CT morphometry, eggshell-matrix proteomics, glycopeptide mass spectrometry, structural ensemble "
    "modeling, and finite-element simulation in three species—chicken, duck, and pigeon—chosen to span major developmental "
    "and ecological contrasts. We present the first comparative description of branched N-glycan classes in avian eggshell "
    "glycoproteins, showing that ovalbumin (OVAL) carries a species-ordered series: high-mannose in Gallus gallus, neutral "
    "complex/hybrid in Anas platyrhynchos, and sialylated complex/hybrid in "
    "Columba livia. The same ordering was recapitulated in computed Ca²⁺-accessible surface exposure, quantified mammillary-layer "
    "mineralization mode, and simulated local shear resistance. Taken together, these aligned shifts place glycan-state variation within a "
    "cross-scale framework linking ecological and evolutionary divergence to avian eggshell structure and mechanics. Within that framework, "
    "OVAL provides the most consistently ordered molecular readout in the present comparison and helps connect matrix chemistry to structural "
    "and mechanical divergence across species.",
    bold=False, size=10, before=0, after=80, align=WD_ALIGN_PARAGRAPH.JUSTIFY
)

# Teaser (≤125 characters, one sentence for non-specialist readers)
para(
    "Teaser: Glycosylation states track ecological and evolutionary divergence in avian eggshell structure and mechanics.",
    bold=False, italic=True, size=10, before=80, after=160, align=WD_ALIGN_PARAGRAPH.LEFT
)

# ════════════════════════════════════════════════════════════════════════════
# Introduction
# ════════════════════════════════════════════════════════════════════════════
para("Introduction", bold=True, size=14, before=0, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT)

# §1 — Background value
p_s1a = spara([
    (" Precocial lineages generally require eggshells that support relatively independent hatchlings and prolonged pre-hatch loading, whereas altricial lineages often develop in more protected nest contexts.", [15, 16, 23, 26]),
    (" Aquatic or semi-aquatic versus terrestrial egg-laying environments add a second ecological contrast, altering the conditions under which eggshell architecture evolves.", [15, 23, 40, 41]),
    (" Although the eggshell also mediates gas exchange, antimicrobial defense, and embryonic calcium supply, its resistance to fracture depends to a large extent on mammillary features and on how mineral is organized around the mammillae.", [1, 4, 38]),
    (" The mammillary layer is therefore not merely the innermost eggshell layer; it is the structural origin of whole-eggshell mechanics.", [1, 28, 38]),
])

p_s1b = spara([
    (" Mammillary knobs, positioned by eggshell matrix proteins within the mammillary layer, determine where calcite growth is initiated and therefore what kind of microstructural organization the mature eggshell can form.", [1, 4, 28]),
    (" Because that layer is where matrix-regulated nucleation is first translated into crystal-unit patterning, it provides the most direct structural readout of how developmental program and habitat-linked selection are written into the eggshell.", [1, 2, 4, 28, 38]),
    (" These life-history and habitat differences make mammillary-layer mineralization mode an obvious comparative phenotype, yet they still do not explain why interspecific differences in mammillary-layer morphology are so pronounced.", [1, 16, 41]),
])

# §2 — Prior work and its limits
p_intro2 = spara([
    ("Work over the past two decades has identified uterine matrix proteins as major regulators of mammillary-layer mineralization, crystal growth orientation, and eggshell architecture, with ovocleidin-17 (OC17), ovocleidin-116 (OC116), ovotransferrin (TRFE), and ovalbumin (OVAL) among the best-characterized examples.", [1, 2, 4, 6, 7, 8, 9, 10, 19, 20, 21, 29]),
    (" OC17 has been linked to early crystal mineralization and calcite habit control, OC116 to matrix organization and mineral deposition, and TRFE to ion-binding and antimicrobial functions within the eggshell matrix; among them, OVAL is especially notable because in vitro studies indicate that it can unfold under mineralizing conditions and participate directly in early crystal-related events.", [6, 7, 8, 9, 10, 19, 21, 29]),
    (" Glycosylation is not uniformly deployed: recent comparative work on eggshell cuticle layer and mineralized-layer proteomes has shown that the same protein can adopt different glycan states across these layers, suggesting layer-specific functional roles.", [18, 20, 21, 49, 50, 52]),
    (" Yet the branched N-glycan classes carried by avian eggshell matrix glycoproteins have rarely been resolved in a cross-species framework.", [18, 20, 21]),
    (" In parallel, comparative morphometry and simulation studies have shown that eggshell mechanics diverge systematically across bird groups.", [1, 4, 15, 16, 17]),
    (" What is missing is a framework that brings these observations together and asks whether glycan-state differences on key matrix proteins can help explain cross-species variation in mammillary-layer structure.", [2, 4, 20, 21]),
])

p_intro_sig = spara([
    ("Resolving that gap matters beyond descriptive avian morphology because the eggshell preserves developmental timing, matrix chemistry, microstructure, and hatching-relevant mechanics in the same biomineralized structure.", [1, 2, 4, 16, 20, 21, 38, 42]),
    (" That makes avian eggshell formation unusually suitable for cross-scale comparison: ecological setting and developmental program can be read against matrix state and structural consequence within a single object.", [1, 2, 4, 15, 16, 20, 21, 38, 42]),
    (" It also makes the eggshell an unusually useful entry point for biomineralization research more broadly, because relationships that are often distributed across separate tissues in bone and other mineralized systems can be interrogated here within one experimentally comparable structure.", [1, 4, 16, 20, 21, 38, 67, 68, 73]),
    (" Eggshell biology has often been divided between comparative studies that define phylogenetic and ecological contrasts and mechanistic studies that identify candidate regulators in the shell-gland matrix.", [1, 2, 4, 6, 7, 15, 16, 20, 21]),
    (" The opportunity here is to test whether one chemically interpretable molecular layer can connect comparative phenotype to mechanism-ready explanation.", [2, 16, 20, 21, 38, 42, 57, 69]),
])

# §3 — Core gap
p_intro_gap = spara([
    ("The unresolved question, therefore, is whether avian OVAL glycan-class divergence aligns with a broader and structurally meaningful ordering in the eggshell.", [55, 58, 59, 60, 65]),
    (" Does it coincide with shifts in computed Ca²⁺-binding-site accessibility, mammillary density, and simulated local resistance?", [55, 58, 59, 60, 65]),
    (" The analysis is therefore organized around two deliberately crossed contrasts: precocial versus altricial development, and terrestrial versus aquatic-linked life setting.", [4, 13, 27, 39]),
    (" Chicken, duck, and pigeon were selected to occupy separated positions within that comparison space.", [4, 13, 39]),
    (" In this design, duck against chicken plus pigeon emphasizes habitat-linked contrast, pigeon against chicken plus duck emphasizes developmental contrast, and chicken against duck plus pigeon isolates the mammillary-layer phenotype most distinct in the present dataset.", [4, 13, 27, 39]),
])

# §4 — This study
p_intro4 = smixed([
        ([("Here, we build that cross-scale framework by integrating micro-CT morphometry, comparative eggshell matrix proteomics with gene-family evolution analysis, intact glycopeptide mass spectrometry, Re-Glyco structural ensemble modelling, and finite-element simulation in three species \u2014 ", False, False),
            ("Gallus gallus", False, True),
            (", ", False, False),
            ("Anas platyrhynchos", False, True),
            (", and ", False, False),
            ("Columba livia", False, True),
            (" \u2014 representing, respectively, a terrestrial precocial model, an aquatic-linked precocial model, and a terrestrial altricial model.", False, False)], [3, 22, 24, 25]),
        ([(" Moving from whole-eggshell morphology through proteome-wide orthogroup comparison and atomic-level electrostatic modeling to tissue-scale contact-stress simulation, we ask whether species-specific N-glycan class composition on OVAL tracks a gradient in computed Ca²⁺ accessibility, mammillary density, and simulated shear resistance.", False, False)], [11, 12, 16]),
        ([(" Species-specific OVAL N-glycan class composition tracked the same gradient in Ca²⁺ accessibility, mammillary density, and simulated shear resistance.", False, False)], []),
        ([(" This framework provides the first comparative branched-glycan view of avian eggshell matrix glycoproteins and identifies OVAL glycan state as the molecular feature most closely aligned with mammillary-layer divergence in this three-species comparison. It therefore links comparative phenotype with a structurally explicit and experimentally testable explanation. More broadly, it places biomineralization into a connected analytical sequence spanning phenotype, matrix protein, post-translational modification, mineralized product, and functional validation.", False, False)], [4, 11, 12, 16, 42, 57, 66, 67, 68, 73, 74]),
])

# ═══════════════════════════════════════════════════════════════════════════
# "Results" section label
# ═══════════════════════════════════════════════════════════════════════════
para("Results", bold=True, size=14, before=320, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT)
# ════════════════════════════════════════════════════════════════════════════
# § Species selection — ecological and developmental niche analysis
# ════════════════════════════════════════════════════════════════════════════
head("Three avian orders span the comparison axis")

p_ss1 = smixed([
        ([('Using 10,993 AVONET species records, we combined ecological and developmental information to place extant birds in a comparative space from which three deliberately separated model species were selected (Fig. 1A).', False, False)], [15, 22, 23, 24, 25, 41]),
        ([(' Within this comparison space, ', False, False),
            ('Gallus gallus', False, True),
            (', ', False, False),
            ('Anas platyrhynchos', False, True),
            (', and ', False, False),
            ('Columba livia', False, True),
            (' occupy representative positions for terrestrial precocial, strongly aquatic-associated precocial, and terrestrial altricial strategies, respectively, and were therefore chosen for downstream comparison.', False, False)], [15, 22, 23, 24, 25, 41]),
        ([(' This functional grouping only partly overlaps with phylogeny: chicken and duck remain closely related precocial taxa but separate along the habitat axis, whereas pigeon anchors the altricial contrast (Fig. 1B). We therefore used these three species to define the comparison space for all downstream analyses.', False, False)], [15, 23, 24, 25, 41]),
        ([(' Having established this contrast set, we next asked which eggshell traits and which glycoprotein features scale most consistently across the three species.', False, False)], []),
])

# ════════════════════════════════════════════════════════════════════════════
head("Mammillary architecture differs systematically across species")

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
    (" (0.3975 ± 0.0127). These measurements indicated that chicken established the densest early mineralization field, pigeon allocated the largest eggshell fraction to crystal units grown from individual mammillary knobs, and duck remained intermediate between those endpoints. To investigate the origin of these interspecific differences, we next carried out a systematic comparative proteomics analysis.", False, False),
])
cite(p_s0b, [1, 2, 28, 30, 36, 38])
cite(p_s0b, [53, 54, 57])

# ════════════════════════════════════════════════════════════════════════════
# S_prot  Eggshell matrix proteome orthogroup analysis
# ════════════════════════════════════════════════════════════════════════════
head("Orthogroup analysis reveals a conserved core and lineage-restricted repertoires")

p_sprot_a = mixed([
    ("Having established the mammillary hierarchy, we next asked whether the eggshell matrix proteome was similarly stratified. It was, but first as an evolutionary architecture composed of a conserved core plus lineage-restricted peripheral repertoires, rather than as a single ordered eggshell module. Eggshell matrix orthogroup analysis showed a large shared core, with lineage-restricted independently expressed proteins most pronounced in pigeon. OrthoFinder identified 2620, 2921, and "
     "3219 protein orthogroups in ", False, False),
    ("G. gallus", False, True),
    (", ", False, False),
    ("A. platyrhynchos", False, True),
    (", and ", False, False),
    ("C. livia", False, True),
    (" respectively (Supplementary Fig. 1A). Of these, 1997 orthogroups were conserved "
     "across all three species, constituting the core eggshell matrix "
     "proteome independent of developmental strategy or nesting ecology. "
     "Pairwise-only orthogroups numbered 180 (", False, False),
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
    ("). Species-exclusive orthogroups were most numerous in ", False, False),
    ("C. livia", False, True),
    (" (72), followed by ", False, False),
    ("A. platyrhynchos", False, True),
    (" (28) and ", False, False),
    ("G. gallus", False, True),
    (" (9), indicating that the pigeon eggshell harbors the broadest "
     "lineage-restricted protein complement. This asymmetry was informative because it showed that the three eggshell systems were not separated only by a few candidate proteins; they differed at the level of overall matrix repertoire composition as well. A phylogeny reconstructed from these eggshell matrix proteins alone also cleanly separated the three model species: ", False, False),
    ("G. gallus", False, True),
    (" and ", False, False),
    ("A. platyrhynchos", False, True),
    (" formed the sister pair, whereas ", False, False),
    ("C. livia", False, True),
    (" branched separately, indicating that the matrix-protein repertoire itself is sufficient to discriminate the three comparison lineages (Supplementary Fig. 1B).", False, False),
])
cite(p_sprot_a, [2, 29, 31, 32, 33])
cite(p_sprot_a, [66, 74])

p_sprot_pair = mixed([
    ("Functionally, the pairwise-shared orthogroup sets did not sort simply by phylogenetic distance; instead, they captured overlapping background differences in developmental strategy, mineralization deployment, and eggshell-surface defense (Figs. 2b\u2013d). The ", False, False),
    ("A. platyrhynchos", False, True),
    ("–", False, False),
    ("C. livia", False, True),
    (" set—proteins shared between duck and pigeon but absent in chicken—was "
     "the most significantly enriched for calcium ion binding and metal ion "
    "binding (MF; both p < 10⁻²⁵), alongside the Wnt signaling pathway and "
    "signal transduction (BP; Supplementary Fig. 1C). In the present three-species framework, these enrichments are better treated as comparative background than as direct molecular readouts of any single calcium-acquisition mode. The ", False, False),
    ("G. gallus", False, True),
    ("–", False, False),
    ("A. platyrhynchos", False, True),
    (" set—shared by the two precocial Galloanserae but absent in "
     "the altricial pigeon—was enriched for adaptive immune response "
    "and spermatogenesis (BP; Supplementary Fig. 1B), suggesting that the two precocial species retain a larger immune-defense burden at the eggshell/outer-membrane interface; in pigeon, by contrast, antimicrobial deployment is likely shifted more strongly toward egg-white proteins. The ", False, False),
    ("G. gallus", False, True),
    ("–", False, False),
    ("C. livia", False, True),
    (" set—proteins shared by chicken and pigeon but absent in duck—"
     "was most strongly enriched for protein transport and intracellular "
     "protein transport (BP) and integral component of membrane (CC; "
    "Supplementary Fig. 1D), suggesting partially shared organizational demands in oviductal secretion and intracellular trafficking. Taken together, these enrichment results provide comparative context, but they do not by themselves identify the specific molecular layer responsible for the structural phenotype.", False, False),
])
cite(p_sprot_pair, [15, 26, 29])

p_sprot_species = mixed([
    ("Species-exclusive proteins further sharpened this contrast and highlighted glycan-processing capacity as a distinctive chicken feature (Supplementary Fig. 1F). The nine ", False, False),
    ("G. gallus", False, True),
    ("-exclusive orthogroups were prominently enriched for protein "
     "N-linked glycosylation (BP)\u2014identifying glycan-processing capacity as a particularly informative chicken-associated feature in the present comparison. In contrast, ", False, False),
    ("A. platyrhynchos", False, True),
    ("-exclusive proteins (n\u202f=\u202f28) were dominated by regulation of immune "
     "response (the largest GO bubble in the dataset; p\u202f<\u202f10\u207b\u00b3\u2075) and B cell activation, alongside response to iron ion, consistent with the pathogen exposure and mineral-metabolic demands of a semi-aquatic lineage. The largest species-specific complement belonged to ", False, False),
    ("C. livia", False, True),
    ("-exclusive proteins (n\u202f=\u202f72), which were enriched for nervous system development, ubiquitin-dependent protein catabolism, and proteolysis, making the lineage-restricted independently expressed protein reservoir most conspicuous in pigeon. This ranking also echoed the earlier mammillary-layer phenotype: chicken, at the high-density end, uniquely enriched N-linked glycosylation, whereas pigeon, at the low-density end, retained the broadest lineage-restricted peripheral repertoire. Together with evidence that glycosylation can deploy the same eggshell protein differently across cuticle and mineralized-layer compartments, the emergence of N-linked glycosylation as a ", False, False),
    ("Gallus", False, True),
    ("-exclusive enrichment term motivated a detailed comparative "
     "glycoproteomics investigation of the three species.", False, False),
])
cite(p_sprot_species, [18, 20, 21, 26])

# ════════════════════════════════════════════════════════════════════════════
# S1  Phylogenomics & gene-family evolution
# ════════════════════════════════════════════════════════════════════════════
p_s1a = mixed([
    ("Extending the comparison from orthogroup composition to gene-family turnover made the same point more strongly: the three eggshell-forming systems are evolutionarily distinct, but genome-wide divergence remains too broad to explain the ordered eggshell phenotype on its own. CAFE5 recovered the expected Galloanserae relationship while showing net contraction in chicken, an intermediate pattern in duck, and net expansion in pigeon (Supplementary Fig. 1G,H). In chicken, the most prominent contractions affected immunoglobulin production, outer dynein arm assembly, and immune response, whereas the strongest expansions involved immune response, cell adhesion, and Wnt signaling. This combination is consistent with a lineage in which some ancestral immune investment in the eggshell matrix may have been partly redistributed toward outer antimicrobial barriers, while adhesion- and Wnt-related modules remain relevant to dense mammillary-layer mineralization interfaces. Duck showed a more intermediate turnover profile: expansions were led by immunoglobulin production, mitotic cell cycle, and outer dynein arm assembly, whereas contractions centered on motor activity, proteolysis, and receptor tyrosine kinase signaling, a pattern compatible with a semi-aquatic lineage under both higher pathogen exposure and sustained epithelial turnover. In pigeon, the dominant expansions involved mitotic cell cycle, motor activity, and proteolysis, whereas the main contractions affected immunoglobulin production, outer dynein arm assembly, and immune response, suggesting a distinct outgroup strategy in which more antimicrobial burden is shifted toward egg-white proteins while eggshell-associated repertoires are deployed more strongly toward altricial developmental remodeling. These contrasts establish asymmetric lineage history, but they also reinforce the interpretive logic of the study: the ordered signal must be resolved at a more proximate layer than background genomic divergence alone.", False, False),
])
cite(p_s1a, [3, 5, 14, 15, 24, 25, 26, 29, 52])

head("OVAL-linked glycoproteome features track the species axis")

p_s2a = mixed([
    ("We therefore turned to intact glycopeptides to ask which molecular layer most closely tracked the ordered eggshell phenotype. The glycoprotein network in Fig. 2 first defines the overall architecture of the dataset: a three-species conserved core at the center, pairwise-shared sectors surrounding it, and lineage-restricted peripheral repertoires linked outward to seven glycan classes. Among 516 quantitatively compared nodes, only 129 belonged to the three-species core, whereas the duck-pigeon shared sector was by far the largest peripheral block and the single-species sectors were dominated by duck and then pigeon. The network therefore indicated that glycoproteomic similarity does not simply recapitulate the classical species tree, but instead combines conserved, pairwise-shared, and lineage-restricted layers in the same architecture. The glycan layer carried the same message. High Mannose and Complex-Fucosylated glycans were broadly reused across multiple protein families, indicating that they contribute to a widespread background rather than to a small number of exceptional lineage-specific proteins. By contrast, more extended sialylated classes were less globally frequent but disproportionately associated with peripheral difference nodes, making them more useful as indicators of finer candidate-protein redeployment. The main value of the network, therefore, was not to identify the most abundant glycan class globally, but to show that core conservation, peripheral redeployment, and glycan reuse coexist in the same dataset and naturally narrow the candidate space toward a smaller set of proteins suitable for stricter ortholog and structural comparison.", False, False),
])

p_s2b = mixed([
    ("To determine whether those glycan differences reflected biologically comparable proteins rather than broad lineage replacement, we next applied a stricter BlastP-based ortholog screen to the key targets (Fig. 3A). Using ", False, False),
    ("G. gallus", False, True),
    (" as the reference, non-reference candidates were retained only when the mean E-value was below 1 × 10⁻⁵ and either average sequence identity reached at least 40% for structurally concordant HSP sets or maximum identity reached at least 40% when HSP counts were discordant. This step was intended to keep the downstream comparison focused on high-confidence orthologs with greater functional comparability. That filter is important for interpretation, because without it the glycan signal could be explained by wholesale lineage replacement rather than by differential deployment of biologically comparable proteins. Under that stricter mapping, OC17 was glycosylated only in chicken, consistent with its established association with early crystal mineralization and calcite habit control, and therefore more suggestive of a chicken-specific proximal mineralization program. By contrast, OC116, TRFE, and OVAL all retained glycosylation signals across the three species, making them more suitable shared anchors for cross-species comparison. Among these, OC116 remained closest to matrix organization and mineral deposition, TRFE combined ion-binding and antimicrobial functions, and OVAL showed the clearest species-ordered glycan reconfiguration. That combination of cross-species retention plus ordered glycan-state divergence is precisely why the subsequent structural analysis focused on OVAL.", False, False),
])
cite(p_s2b, [6, 7, 8, 9, 10, 19, 21, 29])

p_s2c = spara([
    ("Integrating protein abundance and glycan abundance into the same analytical frame then clarified why OVAL, rather than OC116 or TRFE, best tracked the ordered eggshell phenotype (Fig. 3B-D). At the whole-dataset level, protein-glycan coupling was weak and non-significant in chicken (Spearman rho = 0.15, P = 2.68e-01), but became clearly positive in duck and pigeon (rho = 0.42 and 0.47; both P ≈ 2 × 10⁻⁹), indicating that glycosylation investment scaled more tightly with protein expression in the latter two lineages.", []),
    (" Yet the highlighted eggshell-matrix proteins showed that high abundance and high glycan output were not interchangeable. OVAL and OC116 both sat within roughly the top 1% of the protein-abundance distribution in all three species, but their glycan burdens diverged sharply: chicken OVAL remained protein-rich while only mid-ranking at the glycan level, duck OVAL carried a stronger glycan signal, and pigeon OVAL combined top-tier protein abundance with one of the strongest glycan outputs; OC116 was the single most abundant protein in both chicken and pigeon, yet its glycan burden was comparatively modest in chicken and much stronger in duck and pigeon. TRFE, by contrast, remained high in both protein and glycan space across all three species, whereas OC17 appeared only in the chicken panel, consistent with lineage-restricted deployment. OVAL therefore differed from OC116 and TRFE by combining cross-species retention, abundance, ordered glycan-state variation, and direct structural interpretability. A robust cross-species candidate required both biological comparability across taxa and glycan variation not reducible to protein abundance alone, and OVAL was the only shared target that satisfied both conditions cleanly in the present dataset.", []),
    (" The pairwise enrichment plots in Fig. 3E-G sharpened the same distinction. In Gallus-versus-Anas and Gallus-versus-Columba comparisons, OVAL and especially OC116 fell far below the y = x line: chicken retained equal or higher protein abundance, but the glycan signal shifted strongly toward duck or pigeon. TRFE stayed much closer to the diagonal, indicating more coordinated protein and glycan change. In the Anas-versus-Columba comparison, OVAL and TRFE again moved broadly in parallel, whereas OC116 shifted into the glycan-enriched quadrant despite lower protein abundance in duck. The glycan-class profiles in Supplementary Fig. 2 further distinguished OVAL, which alone resolved into a clean species-ordered progression from compact High-Mannose glycans in chicken to neutral complex glycans in duck and more extended Sialylated Complex/Hybrid glycans in pigeon, whereas OC116 and TRFE changed without the same monotonic ordering. Figure 3B-G together with Supplementary Fig. 2 therefore identified OVAL as the shared protein whose glycosylation was most clearly decoupled from bulk abundance in an ordered, phenotype-relevant manner.", [1, 4, 6, 7, 8, 18, 47, 48]),
])

p_s2d = spara([
    ("Because those OVAL glycan classes differ strongly in steric bulk and charge distribution, the comparative signal pointed to OVAL surface accessibility rather than OVAL abundance alone as the molecular variable most likely to influence eggshell mineralization output.", [1, 4, 6, 7, 8, 18, 47, 48]),
    (" Once abundance is no longer treated as the sole explanatory variable, the relevant question becomes how glycan state changes the chemical surface available to participate in early mineralization events. The mechanism therefore narrows from 'which protein is present' to 'which chemically relevant surface remains exposed,' a question that can be tested directly by structural ensembles and electrostatic calculations rather than inferred only from abundance matrices.", [1, 4, 6, 7, 8, 18, 42, 47, 48]),
])

head("Re-Glyco and APBS analyses reveal an OVAL accessibility gradient")

p_s3a = spara([
    ("Having identified OVAL as the strongest candidate, we next asked whether the species-ordered glycan classes could be translated into a concrete structural mechanism. In vitro work has already shown that OVAL can bind Ca²⁺ under mineralizing conditions, undergo partial unfolding, and participate in early mineralization-related assembly, making its glycan state a biologically plausible control layer. We therefore rebuilt 18 dominant glycosylated OVAL ensembles together with matched deglycosylated reference structures to test whether the three species differ primarily through glycan-dependent surface behavior rather than through backbone sequence alone.", [6, 7, 11, 12, 18, 42, 43]),
    ("Panels A-C showed that glycosylation changed OVAL properties within species, whereas the deglycosylated backbones were much more similar across species. In chicken, glycosylation left hotspot count almost unchanged relative to apo OVAL, whereas in duck and pigeon it reduced the accessible hotspot pool more clearly. The same within-species contrast extended to electrostatic output: pigeon glycosylation shifted the surface toward more negative values, chicken changed little, and duck remained intermediate. Once glycans were removed, the three OVAL states no longer remained separated to the same extent in hotspot count and electrostatic output, indicating that much of the ordered divergence was introduced by glycosylation rather than by the protein scaffold alone. The comparative signal therefore remained strongest in the glycosylated state. Apo references further served as an internal control: once glycans were stripped away, much of the cross-species separation compressed, showing that the ordered signal was not simply a by-product of distant sequence divergence carried through the structural models (Supplementary Fig. 3).", [11, 12, 42, 43]),
    ("The glycan-layer geometry clarified the basis of this separation. The rebuilt pigeon glycans occupied the largest conformational space, with greater extension away from the sequon while also maintaining closer transient surface contact, whereas chicken and duck remained more compact. Geometric difference was therefore translated into surface shielding rather than glycan size alone. The pigeon state represented both a larger glycan envelope and a more persistent occupation of protein-surface territory that would otherwise remain available to acidic hotspot exposure. Chicken occupied the opposite extreme, retaining the smallest and least shielding glycan state, while duck consistently remained intermediate. The three species therefore differed not only in glycan identity, but also in how much of the acidic OVAL interface remained available to local ion approach during early mineralization (Fig. 4D-G).", [11, 12, 42, 43, 44, 45, 46]),
    ("That geometric ordering propagated directly into the accessibility readout. Interface shielding increased from chicken to duck to pigeon (Fig. 4H), while the fraction of candidate acidic residues retained as accessible Ca²⁺ hotspots declined in the opposite direction (Fig. 4J). At that stage, however, two related but non-identical summaries become useful. Panel L partitions hotspot accessibility by residue count, asking how many candidate Ca²⁺-relevant sites remain net accessible after glycan shielding. Panel M instead partitions hotspot-residue SASA, asking how much exposed surface area remains on those chemically relevant residues. Those two readouts need not rank species identically in every detail, because shielding more residues is not equivalent to removing the same amount of exposed area from each residue. That distinction explains why duck and pigeon can converge more strongly in accessible hotspot counts while still differing in how shielding is distributed across surface area. The hotspot metric used here therefore captures the exposure of surface Asp/Glu positions that satisfy a Ca²⁺-relevant accessibility definition rather than whole-protein solvent exposure, and Figure 4 links glycan geometry, surface shielding, hotspot number, and hotspot-area suppression on OVAL within the same structural framework. In practical terms, chicken retained the highest OVAL Ca²⁺ accessibility, duck was intermediate or converged downward depending on whether count or area was being summarized, and pigeon remained the most shielded state overall. That ordering helps close the mechanistic loop: higher Ca²⁺ accessibility should make chicken OVAL more permissive to the partial unfolding linked previously to early mineralization, thereby allowing faster mineralization onset and ultimately contributing to the higher mammillary-knob density seen in chicken.", [11, 12, 42, 43, 44, 45, 46, 49, 50, 51]),
])

head("Mechanical simulation recovers the mammillary hierarchy")

p_s4a = mixed([
    ("Having argued from glycoproteomics, structural ensembles, and electrostatics that glycan-dependent matrix chemistry can reshape mammillary-layer mineralization mode, we next asked whether those mammillary differences translated into a biologically relevant functional consequence. We therefore simulated inside-out local failure by applying a conical indenter to the inner surface of micro-CT-derived eggshell fragments, a loading regime designed to approximate embryo-driven escape rather than conventional outside-in eggshell breaking. The hatching-relevant loading geometry and species-specific egg-tooth context are summarized in Fig. 5A,B, and the finite-element meshes were built directly from micro-CT reconstructions rather than idealized eggshell geometries (Fig. 5C). This distinction in loading logic matters because the relevant biological problem here is not generalized shell strength, but whether local resistance at the mammillary interface remains aligned with the molecular and structural ordering recovered in the preceding analyses.", False, False),
])

mixed([
    ("We recorded both peak contact force (F_max) and peak contact shear stress (tau_max), because F_max remained strongly influenced by eggshell thickness and gross geometry, whereas tau_max more directly estimated local resistance at the contact interface itself. By these two criteria, the species were not ranked identically. F_max retained a three-level hierarchy (", False, False),
    ("G. gallus", False, True),
    (" 1.117 ± 0.110 N > ", False, False),
    ("A. platyrhynchos", False, True),
    (" 0.898 ± 0.090 N > ", False, False),
    ("C. livia", False, True),
    (" 0.485 ± 0.039 N; Fig. 6A), but tau_max collapsed the result into a two-level pattern in which duck and pigeon converged while chicken remained distinct (Fig. 6B). This divergence showed that duck's higher raw force requirement was driven largely by thickness rather than by superior unit-area resistance at the mammillary interface.", False, False),
])

mixed([
    ("That distinction is central to the logic of the study. If the three eggshells were discussed only in terms of global breaking force, duck could appear mechanically superior to chicken despite lacking the same mammillary density state. Tau_max resolves that ambiguity by focusing on the local contact response preserved in the micro-CT-derived mammillary interface. In that more localized readout, the structural ordering predicted from glycoproteomics and Re-Glyco modeling becomes visible again.", False, False),
])

mixed([
    ("The mechanical analysis addresses whether the same ordering inferred from glycan class, OVAL surface accessibility, and mammillary microstructure remains visible in a hatching-relevant loading problem. Not every gross force metric reproduced the molecular signal, but the metric most directly tied to the local mammillary interface did. This selective convergence identifies the mechanical level at which the structural information is retained.", False, False),
])

mixed([
    ("The finite-element analysis therefore tests whether the ordering inferred from glycoproteomics and structural modeling remains visible when the eggshell is treated as a hatching-relevant mechanical system. Preservation of the chicken-high versus duck/pigeon-lower grouping at the tau_max level shows that this ordering is retained.", False, False),
])

mixed([
    ("By the tau_max criterion, ", False, False),
    ("G. gallus", False, True),
    (" formed a distinct high-resistance group, while ", False, False),
    ("A. platyrhynchos", False, True),
    (" and ", False, False),
    ("C. livia", False, True),
    (" clustered together at lower values. That grouping reproduced the mammilla-density hierarchy from micro-CT and provided the functional endpoint of the preceding molecular-to-structural argument: the glycosylation-associated differences identified above are not only compatible with altered mammillary organization, but are propagated into a simulated hatching-relevant mechanical consequence across the three model species.", False, False),
])
cite(p_s4a, [16, 17, 34, 35, 37, 38])

# ════════════════════════════════════════════════════════════════════════════
# Discussion
# ════════════════════════════════════════════════════════════════════════════
para("Discussion", bold=True, size=14, before=320, after=160,
    align=WD_ALIGN_PARAGRAPH.LEFT)

p_disc_mam1 = smixed([
    ([('Ecological and developmental contrasts in birds map onto distinct mineralization strategies. Within that frame, mammillary-layer mineralization mode, OVAL glycan class, computed Ca²⁺ accessibility, and simulated local resistance all converge on the same comparative axis. ', False, False),
            ("G. gallus", False, True),
            (" defines a high-density, high-resistance state; ", False, False),
            ("A. platyrhynchos", False, True),
            (" occupies a reproducible intermediate state; and ", False, False),
            ("C. livia", False, True),
            (" marks a lower-density, lower-accessibility state.", False, False)], [1, 2, 4, 15, 16, 17, 20, 21, 23, 38, 39, 41, 42]),
        ([(" Mammillary-layer mineralization mode is therefore the phenotype most in need of explanation, because it is the earliest structural level at which matrix chemistry, crystal-unit initiation, and later mechanical behavior become joined in the mature eggshell.", False, False)], [1, 2, 20, 28, 30, 36, 38, 53, 54]),
])

p_disc_mam2 = spara([
    (" The molecular results converge on a narrower explanatory layer than orthogroup turnover, gene-family change, or glycoprotein-network structure alone.", []),
    (" Orthogroup turnover, gene-family change, and glycoprotein-network divergence all show that the three lineages differ historically, but those layers mainly define the evolutionary background of the comparison rather than the most proximate explanatory feature.", [1, 2, 8, 18, 21, 27]),
    (" OVAL N-glycan architecture is more informative because it is ordered across species, chemically interpretable, and positioned on a highly abundant matrix protein already implicated in mineralization.", [4, 6, 7, 18, 21, 42, 44, 45, 46]),
    (" OVAL glycan state most cleanly bridges broad proteomic divergence and the ordered structural phenotype measured here, making it the clearest molecular variable in the present three-species framework.", [20, 21, 42, 61, 63, 66, 74, 78, 80]),
])

p_disc_other = para(
    "The non-OVAL signals also remain informative. OC116 showed substantial glycosylation divergence across the species comparisons, and that variability is biologically plausible in light of recent evidence that avian protein repertoires can vary markedly across and within species. Combined with the long-recognized proteoglycan character of OC116 and the fact that its full spatial architecture is still unresolved, the present pattern is consistent with a molecule whose function may depend on coordinated interactions across multiple domains and binding partners rather than on a single easily modeled surface. TRFE, by contrast, remained comparatively similar in glycosylation level across the three species. That stability is also interpretable: glycans can themselves operate as shielding elements in host-defense contexts, and an immune-associated matrix protein may therefore be expected to retain a relatively conserved glycan barrier even when other mineralization-linked proteins diversify more strongly."
)

cite(p_disc_other, [19, 21, 29, 42, 44, 45, 46, 66, 81])

p_disc_oval = para(
    "The Re-Glyco and APBS analyses turn that claim into a concrete working model. Compact chicken glycans leave the critical acidic OVAL surface relatively exposed, whereas the longer and more electronegative pigeon glycans reduce Ca²⁺ approach both sterically and electrostatically; duck again falls between those endpoints. Because the predicted accessibility ranking parallels the measured mammilla-density ranking, the glycan signal is unlikely to be a passive lineage marker. These data support a comparative structural model linking OVAL glycan state to mineralization phenotype."
)

cite(p_disc_oval, [4, 11, 12, 42, 44, 45, 46, 49, 50, 51, 52, 55, 65])

p_disc_axis = spara([
    ("Mammillary-layer mineralization mode therefore remains central to the interpretation.", [1, 2, 20, 28, 38]),
    (" Once early calcite crystal units are established, later eggshell regions inherit the spacing logic created in that first mineralization window.", [1, 2, 28, 30]),
    (" A dense mammillary field therefore changes more than morphology: it reorganizes matrix retention, mineral continuity, and local stress redistribution, making the mammillary layer a developmental and mechanical boundary condition for the rest of the eggshell.", [1, 2, 30, 36, 38]),
])

p_disc_regulator = spara([
    ("Duck is particularly informative in this framework because it preserves a three-state comparison rather than a simple precocial-versus-altricial contrast.", [4, 15, 23, 27, 39, 41]),
    (" If developmental mode alone dictated eggshell-building chemistry, duck should cluster with chicken throughout the molecular and mechanical analyses.", [15, 23, 27]),
    (" It does not: it retains the broad life-history condition of precocial development while shifting toward an intermediate OVAL glycan state, an intermediate accessibility profile, and an intermediate mechanical outcome.", [4, 12, 16, 17, 39, 41]),
    (" Duck therefore acts as the key comparative anchor, showing that developmental program frames the problem but does not by itself determine the biochemical solution adopted by the eggshell-forming system.", [4, 12, 15, 23, 27, 39, 41]),
])

p_disc_discriminate = spara([
    ("This comparative structure distinguishes among competing interpretations.", []),
    (" Eggshell thickness, body size, and broad reproductive ecology may all contribute background variation, and lineage history undoubtedly matters.", [2, 14, 16, 17, 24, 25]),
    (" But thickness-based explanations do not recover the τ_max ordering, and diffuse lineage-divergence explanations do not account for why the same ordered progression recurs in glycan class, electrostatic accessibility, and mammillary-layer mineralization mode.", [4, 16, 17, 20, 21, 38, 42]),
    (" Within this framework, background variables can be ranked: some define the design space, whereas others repeatedly recover the phenotype itself.", [1, 2, 4, 20, 21, 38, 42]),
    (" A cautious synthesis therefore follows: ecology and phylogeny establish the comparison frame, whereas OVAL glycan state is the proximate feature that most consistently tracks the structural phenotype in this three-species dataset.", [1, 2, 4, 20, 21, 38, 42, 57, 70]),
])

p_disc_mech = spara([
    ("The mechanical analysis gives the framework organism-level relevance.", [16, 17, 38]),
    (" τ_max rather than raw fracture force tracks the mammillary hierarchy.", [16, 17, 34, 35, 37, 38]),
    (" Absolute failure load remains sensitive to eggshell thickness and whole-eggshell geometry, whereas τ_max more directly isolates localized resistance under hatching-relevant shear at the contact site.", [16, 17, 34, 35, 37, 38]),
    (" The convergence of duck and pigeon in τ_max despite their different gross mammillary geometries suggests that once the high-density chicken state is lost, downstream shape variation alone does not restore the same local resistance. This extends the molecular-to-structural signal into a functional readout rather than leaving it as a descriptive correlation.", [1, 2, 16, 17, 38]),
])

p_disc_evo = para(
    "The mechanical results suggest a compensatory evolutionary logic as well. Duck lacks the chicken-like high-accessibility glycan state yet preserves a relatively high gross force threshold because shell thickness remains greater; in other words, thickness may buffer against a drop in local material resistance when glycosylation-linked mineralization no longer occupies the chicken extreme. Read cautiously against broader avian evolutionary history, this raises a tractable question for future sampling: whether changes in glycosylation strategy accompanied transitions along the precocial-to-altricial spectrum, with shell thickness acting in some lineages as a compensatory route that prevents abrupt loss of shell strength. The present three-species dataset cannot test that macroevolutionary proposal directly, but it identifies a specific phenotype-protein-modification-mechanics axis on which such a test can now be built."
)

cite(p_disc_evo, [3, 15, 16, 17, 37, 38, 39, 41, 57])

p_disc_function = para(
    "In evolutionary terms, these findings place glycan class as a plausible intermediary between broad selective background and mineralization strategy. This does not reduce eggshell diversification to a single variable; rather, it identifies a chemically specific layer at which broader ecological and developmental differences become structurally legible. A tunable post-translational state on an abundant matrix protein offers one way for eggshell systems to diversify while retaining a broadly conserved protein toolkit. Glycoprotein state can therefore connect matrix chemistry, microstructure, and biomechanical consequence within the same comparative frame. The same logic may extend beyond avian eggshells, because many mineralized systems rely on abundant matrix proteins whose post-translational states can shift without wholesale replacement of the underlying protein repertoire. That broader framing may also carry translational value: by clarifying how chemically specific surface states bias mineral growth, this kind of framework could inform how we think about human skeletal development, regeneration, and the choice of experimentally tractable biomineralization models relevant to calcified tissues. The present dataset therefore supports a cross-scale interpretation in which ecological contrast, molecular surface state, structural organization, and localized mechanics remain analytically connected."
)

cite(p_disc_function, [4, 6, 7, 18, 20, 21, 42, 49, 50, 52, 62, 67, 68, 69, 71, 72, 73, 75, 77, 79])

p_disc_selection = para(
    "This bridge also has methodological value for comparative biomineralization research. Omics-rich studies can readily show that lineages differ, yet they less often identify which molecular differences are most useful for organizing phenotype. Here, OVAL glycan state reduces that interpretive breadth to a smaller, chemically meaningful layer that can be mapped onto structure and considered against function. That logic is likely to be portable. In other mineralized systems, analogous roles might be played by sulfation, phosphorylation, proteolytic processing, or regulated cofactor binding on abundant matrix proteins, particularly where the same major matrix components are reused across divergent structural contexts."
)

cite(p_disc_selection, [20, 21, 42, 49, 50, 52, 58, 59, 60, 65, 66, 74])

p_disc_future = para(
    "Caveats merit emphasis. We analyzed dominant glycoforms rather than full in vivo heterogeneity, in part because current glycan-structure libraries remain incomplete and some experimentally relevant structures are still missing from the reference space needed for reliable ensemble rebuilding. We therefore retained the dominant forms that could be supported consistently across the three-species comparison, treated each species as mechanically uniform at the scale of the mean eggshell, and relied on incompletely constrained uterine ionic conditions in the APBS framework. These limits define the next experimental steps: defined-glycoform mineralization assays, site-directed manipulation of OVAL glycosylation together with uterine chemistry measurements, site-resolved mechanical validation, and broader phylogenetic sampling to determine whether the three-species axis reported here is recurrent or only one branch within a larger design space. Such work should clarify whether OVAL glycan state participates directly in mineralization or serves primarily as a comparative molecular indicator, and whether the same axis extends beyond the present ecological and developmental contrast set."
)

cite(p_disc_future, [4, 11, 12, 20, 21, 42, 49, 50, 51, 52, 57, 70, 76])

p_disc_close = para(
    "Taken together, these results show how a chemically specific post-translational feature can help organize an otherwise heterogeneous comparative landscape into a coherent explanatory framework. Across the present dataset, the argument was built stepwise: comparative ecology and development first separated chicken, duck, and pigeon as distinct life-history states; micro-CT then resolved a corresponding hierarchy in mammillary-layer organization; glycoproteomics narrowed the shared candidate space to OVAL, with OC116 and TRFE providing informative contrasts; structural ensemble modeling and electrostatics showed that OVAL glycan state reordered Ca²⁺-relevant accessibility from the high-accessibility chicken state through duck to the more shielded pigeon state; and finite-element analysis finally showed that this molecular-to-structural ordering persisted in a hatching-relevant mechanical readout. In that combined sense, chicken represents a high-density, high-accessibility, high-resistance endpoint, duck an intermediate and partially compensated state, and pigeon a lower-accessibility, lower-resistance endpoint. This interpretation reduces a broad comparative problem to a smaller and experimentally tractable layer of explanation without implying that other matrix features are unimportant, and it identifies the chemically specific surface state of an abundant matrix protein as the most informative level for future intervention."
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

para(
    "Two eggshell fragments (each approximately 4\u20135 mm\u00b2) were excised from the "
    "equatorial region of each species and scanned with a Phoenix V|tome|x\u00a0M "
    "microfocus CT system (GE Sensing and Inspection Technologies GmbH, Wunstorf, "
    "Germany) at 85 kV and 160 \u03bcA with no beam filter; scan settings were held "
    "constant across all specimens. Three-dimensional reconstructions were generated "
    "in 3D Slicer by threshold-based segmentation restricted to a cylindrical region "
    "of interest of 1 mm radius. Acquisition noise was suppressed by a 5 \u00d7 5 \u00d7 5 "
    "median filter, followed by largest-island isolation and 9 \u00d7 9 \u00d7 9 hole-filling. "
    "Surface models were exported as STL files and reverse-engineered in Geomagic "
    "Wrap by sequential de-noising (strength 2), triangle simplification to "
    "approximately 300,000 faces, mesh re-gridding at 0.01 mm, iterative defect "
    "correction to zero residual faults, and organic parametric surface fitting at "
    "minimum tolerance. Three morphometric parameters were quantified per specimen: "
    "mammilla density (count per mm\u00b2), column unit volume (mm\u00b3), and unit volume "
    "ratio (organic matrix core volume relative to total column volume; "
    "n\u202f=\u202f2 fragments per species)."
)

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
    ("Eggshell surface models derived from micro-CT were imported into LS-DYNA "
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

# ─────────────────────────────────────────────────────────────────────────
# Acknowledgments
# ─────────────────────────────────────────────────────────────────────────
para("Acknowledgments", bold=True, size=14, before=320, after=160,
     align=WD_ALIGN_PARAGRAPH.LEFT)

para(
    "Funding: [Insert all funding sources; if none, replace with 'The authors acknowledge that they received no funding in support for this research.']. "
    "Author contributions: [Insert each author's contributions using author initials and CRediT-style roles]. "
    "Competing interests: The authors declare that they have no competing interests. "
    "Data and materials availability: All data needed to evaluate the conclusions in the paper are "
    "present in the paper and/or the Supplementary Materials. "
    "Raw mass spectrometry data and proteomics search results have been deposited in a "
    "public repository [accession number to be inserted before submission].",
    bold=False, size=11, before=0, after=120
)

doc.save(OUT)
print(f"[OK]  {OUT}")
