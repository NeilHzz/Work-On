"""
Strict Chinese translation generator.
Produces a sentence-aligned Chinese manuscript from the latest English manuscript.
"""

from pathlib import Path
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
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
            with ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(translator.translate, text)
                out = fut.result(timeout=25)
            if not out:
                out = text
            _cache[text] = out
            return out
        except FutureTimeoutError:
            last_err = RuntimeError("translation timeout")
            time.sleep(0.8 * (i + 1))
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(0.8 * (i + 1))

    # Fallback: keep original if remote translation fails.
    print(f"[WARN] translation failed, keep original: {text[:80]} :: {last_err}")
    _cache[text] = text
    return text


def _translate_batch(texts: list[str], batch_size: int = 12) -> list[str]:
    # Use per-item translation with timeout protection to avoid batch-level hangs.
    out: list[str] = []
    for i in range(0, len(texts), batch_size):
        chunk = texts[i : i + batch_size]
        out.extend(_translate_text(t) for t in chunk)
    return out


def _split_for_translation(text: str) -> list[str]:
    # Prefer sentence chunks; fallback to punctuation-based chunking for long blocks.
    s = text.strip()
    if len(s) <= 260:
        return [s]

    parts = re.split(r"(?<=[.!?])\s+", s)
    chunks: list[str] = []
    buf = ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if len(p) > 260:
            sub_parts = re.split(r"(?<=[,;:])\s+", p)
        else:
            sub_parts = [p]
        for sp in sub_parts:
            sp = sp.strip()
            if not sp:
                continue
            if len(buf) + len(sp) + 1 <= 260:
                buf = (buf + " " + sp).strip()
            else:
                if buf:
                    chunks.append(buf)
                buf = sp
    if buf:
        chunks.append(buf)
    return chunks if chunks else [s]


def _translate_long_text(text: str) -> str:
    chunks = _split_for_translation(text)
    translated_chunks = _translate_batch(chunks, batch_size=8)
    return " ".join(t.strip() for t in translated_chunks if t and t.strip())


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


def _translate_paragraphs(paragraphs, label: str = "paragraphs") -> int:
    changed = 0
    targets = []
    for p in paragraphs:
        src = "".join(r.text for r in p.runs) if p.runs else p.text
        if _should_translate(src):
            targets.append((p, src))

    if not targets:
        return 0

    total = len(targets)
    for idx, (p, src) in enumerate(targets, 1):
        dst = _translate_long_text(src)
        _replace_paragraph_text_keep_format(p, dst)
        changed += 1
        if idx % 10 == 0 or idx == total:
            print(f"[PROGRESS] {label}: {idx}/{total}", flush=True)
    return changed


def main() -> None:
    if not EN_DOC.exists():
        raise FileNotFoundError(f"English manuscript not found: {EN_DOC}")

    doc = Document(str(EN_DOC))
    changed = 0

    changed += _translate_paragraphs(doc.paragraphs, label="body")

    for t_idx, table in enumerate(doc.tables, 1):
        for row in table.rows:
            for cell in row.cells:
                changed += _translate_paragraphs(cell.paragraphs, label=f"table-{t_idx}")

    for s_idx, sec in enumerate(doc.sections, 1):
        changed += _translate_paragraphs(sec.header.paragraphs, label=f"header-{s_idx}")
        changed += _translate_paragraphs(sec.footer.paragraphs, label=f"footer-{s_idx}")

    _set_cn_fonts(doc)
    doc.save(str(OUT_DOC))
    print(f"[OK] translated paragraphs: {changed}")
    print(f"[OK] {OUT_DOC}")


if __name__ == "__main__":
    main()
