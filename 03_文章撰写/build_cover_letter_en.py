"""
Generate a Science Advances cover letter for the current manuscript.
"""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

OUT = Path(__file__).with_name("cover_letter260606.docx")
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
    'We are pleased to submit our manuscript entitled "Cross-species OVAL glycan states reveal a matrix mechanism for avian shell-breaking mechanics" for consideration as a Research Article in Science Advances.',
)

para(
    doc,
    "Avian eggshell formation is a rapid mineralization process in which matrix proteins must coordinate calcium access, nucleation, crystal growth, and shell architecture within a compressed uterine time window. The mammillary layer is the first structural layer established during this process and a key determinant of later shell organization, yet it remains unclear how conserved matrix proteins generate distinct mammillary states and local hatching mechanics across species.",
)

para(
    doc,
    "Here, we address this gap by integrating micro-CT morphometry, eggshell-matrix proteomics, intact glycopeptide mass spectrometry, Re-Glyco structural modeling, electrostatic analysis, and finite-element simulation across chicken, duck, and pigeon. Our results identify OVAL glycan state as a chemically interpretable axis that links Ca2+-relevant surface accessibility, glycan-modulated OVAL unfolding and nucleation-site exposure, mammillary-layer organization, and local shell-breaking mechanics under an inside-out hatching interface.",
)

para(
    doc,
    "The study is well suited to Science Advances because it connects molecular glycoform variation to a mesoscale biomineral structure and to a biologically relevant mechanical endpoint. Rather than treating eggshell differences as descriptive species traits, the manuscript provides a cross-scale framework for testing how posttranslational states on shared matrix proteins can organize mineralized phenotypes.",
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
