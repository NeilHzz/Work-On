"""
Strict Chinese translation generator.
Produces a sentence-aligned Chinese manuscript from the latest English manuscript.
"""

from pathlib import Path
import re
import time
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from deep_translator import GoogleTranslator

EN_DOC = Path(__file__).with_name("manuscript260602v2.docx")
OUT_DOC = Path(__file__).with_name("manuscript260602v2_cn.docx")

translator = GoogleTranslator(source="en", target="zh-CN")
_cache: dict[str, str] = {}


def _has_english_letters(text: str) -> bool:
    return bool(re.search(r"[A-Za-z]", text))


def _should_translate(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    if not _has_english_letters(t):
        return False
    if re.fullmatch(r"[\d\s.,;:()\[\]{}\-+/×=]+", t):
        return False
    return True


def _translate_text(text: str, retries: int = 3) -> str:
    if text in _cache:
        return _cache[text]

    last_err = None
    for i in range(retries):
        try:
            out = translator.translate(text)
            if not out:
                out = text
            _cache[text] = out
            return out
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(0.8 * (i + 1))

    # Fallback: keep original if remote translation fails.
    print(f"[WARN] translation failed, keep original: {text[:80]} :: {last_err}")
    _cache[text] = text
    return text


def _replace_paragraph_text_keep_format(p, new_text: str) -> None:
    if p.runs:
        p.runs[0].text = new_text
        for r in p.runs[1:]:
            r.text = ""
    else:
        p.add_run(new_text)


def _set_cn_fonts(doc: Document) -> None:
    # Ensure East Asian fonts render consistently in translated output.
    for para in doc.paragraphs:
        for run in para.runs:
            run.font.name = "Times New Roman"
            rPr = run._r.get_or_add_rPr()
            rFonts = rPr.find(qn("w:rFonts"))
            if rFonts is None:
                rFonts = OxmlElement("w:rFonts")
                rPr.insert(0, rFonts)
            rFonts.set(qn("w:ascii"), "Times New Roman")
            rFonts.set(qn("w:hAnsi"), "Times New Roman")
            rFonts.set(qn("w:cs"), "Times New Roman")
            rFonts.set(qn("w:eastAsia"), "SimSun")


def _translate_paragraphs(paragraphs) -> int:
    changed = 0
    for p in paragraphs:
        src = "".join(r.text for r in p.runs) if p.runs else p.text
        if not _should_translate(src):
            continue
        dst = _translate_text(src)
        _replace_paragraph_text_keep_format(p, dst)
        changed += 1
    return changed


def main() -> None:
    if not EN_DOC.exists():
        raise FileNotFoundError(f"English manuscript not found: {EN_DOC}")

    doc = Document(str(EN_DOC))
    changed = 0

    changed += _translate_paragraphs(doc.paragraphs)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                changed += _translate_paragraphs(cell.paragraphs)

    for sec in doc.sections:
        changed += _translate_paragraphs(sec.header.paragraphs)
        changed += _translate_paragraphs(sec.footer.paragraphs)

    _set_cn_fonts(doc)
    doc.save(str(OUT_DOC))
    print(f"[OK] translated paragraphs: {changed}")
    print(f"[OK] {OUT_DOC}")


if __name__ == "__main__":
    main()
