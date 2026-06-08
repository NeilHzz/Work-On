"""
Generate a Science Advances cover letter for the current manuscript.
"""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

OUT = Path(__file__).with_name("0_Cover letter") / "cover_letter260606.docx"
FONT = "Times New Roman"


def set_font(run, size=11, bold=False):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    r_pr = run._r.get_or_add_rPr()
    r_fonts = OxmlElement("w:rFonts")
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        r_fonts.set(qn(attr), FONT)
    r_pr.insert(0, r_fonts)


def spacing(paragraph, before=0, after=120, line=16):
    p_pr = paragraph._p.get_or_add_pPr()
    element = OxmlElement("w:spacing")
    element.set(qn("w:before"), str(before))
    element.set(qn("w:after"), str(after))
    element.set(qn("w:line"), str(line * 20))
    element.set(qn("w:lineRule"), "auto")
    p_pr.append(element)


def para(doc, text="", bold=False, align=WD_ALIGN_PARAGRAPH.LEFT, after=120):
    paragraph = doc.add_paragraph()
    paragraph.alignment = align
    spacing(paragraph, after=after)
    run = paragraph.add_run(text)
    set_font(run, bold=bold)
    return paragraph


doc = Document()
section = doc.sections[0]
section.left_margin = section.right_margin = section.top_margin = section.bottom_margin = Cm(2.54)

para(doc, "[Date]")
para(doc, "Science Advances Editorial Office")
para(doc, "Dear Editors,")

para(
    doc,
    'We are pleased to submit our manuscript entitled "OVAL glycan states link eggshell matrix chemistry to avian shell-breaking mechanics" for consideration as a Research Article in Science Advances.',
)

para(
    doc,
    "Avian eggshells are built rapidly by matrix-guided mineralization, yet they must also permit controlled local fracture during hatching. A central unresolved question is how conserved matrix proteins are chemically tuned to produce species-specific mammillary architectures and hatching-relevant mechanics within a shared shell-building program.",
)

para(
    doc,
    "Here, we compare chicken, duck, and pigeon using micro-CT morphometry, eggshell-matrix proteomics, intact glycopeptide mass spectrometry, Re-Glyco structural modeling, electrostatic analysis, and finite-element simulation. Species divergence emerged first in the mammillary layer, whereas the matrix-protein toolkit remained largely shared. Within this shared background, OVAL glycan states shifted from High-Mannose-dominant glycans in chicken to Neutral Complex/Hybrid-dominant glycans in duck and Sialylated Complex/Hybrid-dominant glycans in pigeon.",
)

para(
    doc,
    "This glycan-state progression supports a model in which compact chicken OVAL glycans preserve greater Ca2+-accessible surface, promote earlier or more efficient nucleation-site exposure, and contribute to a denser mammillary field. Consistent with this model, chicken showed the highest mammillary density (171.36 +/- 5.63 per mm2), compared with duck (155.22 +/- 8.63 per mm2) and pigeon (158.27 +/- 11.39 per mm2).",
)

para(
    doc,
    "The inside-out finite-element analysis further separated shell thickness from local hatching-relevant response. Duck had a thicker shell than pigeon (0.35 versus 0.19 mm) and a higher peak contact force (0.90 +/- 0.09 versus 0.49 +/- 0.04 N), but its peak contact shear stress grouped with pigeon rather than chicken. Chicken reached the highest local stress response (551.60 +/- 108.80 MPa), whereas duck and pigeon reached 404.00 +/- 39.60 MPa and 393.00 +/- 35.20 MPa, respectively.",
)

para(
    doc,
    "We believe the study is well suited to Science Advances because it addresses a general problem in biomineralization: how posttranslational states of conserved matrix proteins organize material phenotypes across molecular, mesoscale, and mechanical levels. Rather than describing species differences in eggshell structure, the manuscript provides a testable cross-scale framework linking matrix glycosylation to mineral nucleation, mammillary architecture, and localized fracture behavior.",
)

para(
    doc,
    "All authors have approved the manuscript and its submission. The work is original and is not under consideration elsewhere. Conflicts of interest, funding information, and data and code availability statements are provided in the manuscript.",
)

para(doc, "Sincerely,")
para(doc, "[Corresponding author name]")
para(doc, "[Affiliation]")
para(doc, "[Email]")

doc.save(OUT)
print(f"[OK] {OUT}")
