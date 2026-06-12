"""
Strict Chinese translation generator.
Produces a sentence-aligned Chinese manuscript from the latest English manuscript.
"""

from pathlib import Path
import json
import re
import time
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from deep_translator import GoogleTranslator

EN_DOC = Path(__file__).with_name("0_Manuscript") / "manuscript260608v4.docx"
OUT_DOC = Path(__file__).with_name("0_Manuscript_CN") / "manuscript260608v4_cn.docx"
CACHE_FILE = Path(__file__).with_name(".translation_cache_cn.json")

translator = GoogleTranslator(source="en", target="zh-CN")
try:
    _cache: dict[str, str] = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
except (FileNotFoundError, json.JSONDecodeError):
    _cache = {}

# Locked terminology keeps sentence-level translation stable across reruns.
TERM_LOCKS: list[tuple[str, str]] = [
    ("Cross-species OVAL glycan states reveal a matrix mechanism for avian shell-breaking mechanics", "跨物种OVAL糖链状态揭示鸟类破壳力学的基质机制"),
    ("Eggshell matrix proteins are key regulators of eggshell structural formation, and existing studies have generated rich posttranslational-modification site maps, leaving the side-chain properties of glycosylation modifications as an important layer for further investigation.", "蛋壳基质蛋白是蛋壳结构形成的关键调控因子，已有研究已经建立了丰富的翻译后修饰位点图谱，而糖基化修饰侧链性质仍是有待进一步解析的重要层面。"),
    ("Ca²⁺accessibility-mammillary-mechanics axis", "Ca²⁺可及性-乳突层-力学轴"),
    ("Ca²⁺accessibility", "Ca²⁺可及性"),
    ("Ca²⁺access", "Ca²⁺可及性"),
    ("Ca²⁺accessible matrix-protein surfaces", "Ca²⁺可及的基质蛋白表面"),
    ("rapid vertebrate mineralization process", "快速的脊椎动物矿化过程"),
    ("rapid mineralization process", "快速矿化过程"),
    ("organic matrix-protein system", "有机基质蛋白系统"),
    ("calcium delivery", "钙供应"),
    ("matrix-guided calcite nucleation", "基质引导的方解石成核"),
    ("spacing and continuity", "间距和连续性"),
    ("later shell units", "后续蛋壳结构单元"),
    ("glycan-modulated OVAL unfolding", "糖链调控的OVAL解折叠"),
    ("OVAL unfolding", "OVAL解折叠"),
    ("matrix-bound nucleation-site exposure", "基质结合成核位点暴露"),
    ("nucleation-site exposure", "成核位点暴露"),
    ("nucleation-site presentation", "成核位点呈现"),
    ("mammillary-layer formation", "乳突层形成"),
    ("mature mammillary density", "成熟乳突层密度"),
    ("local shell-breaking structural strength", "局部破壳结构强度"),
    ("Sun et al.", "Sun等"),
    ("matrix behaviour", "基质行为"),
    ("matrix behavior", "基质行为"),
    ("ovalbumin (OVAL)", "卵清蛋白（OVAL）"),
    ("ovalbumin", "卵清蛋白"),
    ("OVAL", "卵清蛋白（OVAL）"),
    ("OVAL glycan states", "OVAL糖链状态"),
    ("OVAL glycan state", "OVAL糖链状态"),
    ("OC116", "OC116"),
    ("TRFE", "TRFE"),
    ("OC17", "OC17"),
    ("Re-Glyco", "Re-Glyco"),
    ("GlycoShape", "GlycoShape"),
    ("GlyTouCan", "GlyTouCan"),
    ("AlphaFold2", "AlphaFold2"),
    ("APBS", "APBS"),
    ("PDB2PQR", "PDB2PQR"),
    ("MSFragger", "MSFragger"),
    ("DIA-NN", "DIA-NN"),
    ("OrthoFinder", "OrthoFinder"),
    ("OrthoVenn3", "OrthoVenn3"),
    ("CAFE5", "CAFE5"),
    ("Gallus gallus", "Gallus gallus"),
    ("Anas platyrhynchos", "Anas platyrhynchos"),
    ("Columba livia", "Columba livia"),
    ("G. gallus", "G. gallus"),
    ("A. platyrhynchos", "A. platyrhynchos"),
    ("C. livia", "C. livia"),
    ("chicken", "鸡"),
    ("duck", "鸭"),
    ("pigeon", "鸽"),
    ("mammillary-layer", "乳突层"),
    ("mammillary layer", "乳突层"),
    ("mammillary", "乳突层"),
    ("matrix-protein", "基质蛋白"),
    ("matrix protein", "基质蛋白"),
    ("glycoprotein", "糖蛋白"),
    ("glycopeptides", "糖肽"),
    ("glycopeptide", "糖肽"),
    ("glycan-state", "糖链状态"),
    ("glycan states", "糖链状态"),
    ("glycan state", "糖链状态"),
    ("N-glycan", "N-糖链"),
    ("glycans", "糖链"),
    ("glycan", "糖链"),
    ("glycosylation", "糖基化"),
    ("inside-out loading", "由内向外加载"),
    ("inside-out", "由内向外"),
    ("egg-tooth", "卵齿"),
    ("Local finite-element loading connects egg-tooth contact geometry to species-specific shell resistance", "局部有限元加载将卵齿接触几何与物种特异性蛋壳阻力联系起来"),
    ("finite-element", "有限元"),
    ("micro-CT", "显微CT"),
    ("shell resistance", "蛋壳阻力"),
    ("interface resistance", "界面阻力"),
    ("local resistance", "局部阻力"),
    ("egg shell", "蛋壳"),
    ("eggshell", "蛋壳"),
    ("radius of gyration", "回转半径"),
    ("hatching resistance", "孵化阻力"),
    ("hatching-favourable", "有利于破壳"),
    ("hatching-relevant", "破壳相关"),
    ("hatching-favourable eggshell mechanics", "有利于破壳的蛋壳力学"),
    ("hatching-relevant shell mechanics", "破壳相关蛋壳力学"),
    ("shell-breaking mechanics", "破壳力学"),
    ("local hatching mechanics", "局部破壳力学"),
    ("shell mechanics", "蛋壳力学"),
    ("local stress response", "局部应力响应"),
    ("mammillary-interface mechanism", "乳突层界面机制"),
    ("hotspots", "热点"),
    ("hotspot", "热点"),
    ("Ca²⁺relevant", "Ca²⁺相关"),
    ("Ca²⁺responsive", "Ca²⁺响应性"),
    ("Ca²⁺", "Ca²⁺"),
    ("Ca2+", "Ca²⁺"),
]

ABBREVIATIONS: tuple[str, ...] = (
    "Fig.",
    "Figs.",
    "Table.",
    "Eq.",
    "Dr.",
    "Prof.",
    "G.",
    "A.",
    "C.",
    "s.d.",
    "e.g.",
    "i.e.",
    "vs.",
 )


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
            _save_cache()
            return out
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(0.8 * (i + 1))

    # Fallback: keep original if remote translation fails.
    print(f"[WARN] translation failed, keep original: {text[:80]} :: {last_err}")
    _cache[text] = text
    _save_cache()
    return text


def _save_cache() -> None:
    CACHE_FILE.write_text(
        json.dumps(_cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _term_token(index: int) -> str:
    return f"ZXQTERM{index:03d}X"


def _lock_terms_for_translation(text: str) -> tuple[str, dict[str, str]]:
    protected = text
    token_to_cn: dict[str, str] = {}
    ordered_terms = sorted(TERM_LOCKS, key=lambda item: len(item[0]), reverse=True)
    for index, (src_term, cn_term) in enumerate(ordered_terms):
        token = _term_token(index)
        token_to_cn[token] = cn_term
        protected = re.sub(re.escape(src_term), token, protected, flags=re.IGNORECASE)
    return protected, token_to_cn


def _restore_locked_terms(text: str, token_to_cn: dict[str, str]) -> str:
    out = text
    for token, cn_term in token_to_cn.items():
        out = re.sub(re.escape(token), cn_term, out, flags=re.IGNORECASE)
    return out


def _normalize_locked_terms(text: str) -> str:
    out = text
    for src_term, cn_term in TERM_LOCKS:
        out = re.sub(re.escape(src_term), cn_term, out, flags=re.IGNORECASE)
    return out


def _group_translation_texts(texts: list[str], max_count: int, max_chars: int = 4500) -> list[list[str]]:
    groups: list[list[str]] = []
    current: list[str] = []
    current_chars = 0
    for text in texts:
        next_chars = current_chars + len(text) + 20
        if current and (len(current) >= max_count or next_chars > max_chars):
            groups.append(current)
            current = []
            current_chars = 0
        current.append(text)
        current_chars += len(text) + 20
    if current:
        groups.append(current)
    return groups


def _translate_joined_sentences(texts: list[str]) -> list[str]:
    delimiter = "ZXQSENTSEP000X"
    joined = f"\n{delimiter}\n".join(texts)
    translated = translator.translate(joined)
    if not translated:
        raise RuntimeError("empty translation")
    parts = [part.strip() for part in translated.split(delimiter)]
    if len(parts) != len(texts):
        raise RuntimeError("joined sentence split mismatch")
    return parts


def _translate_batch(texts: list[str], batch_size: int = 8) -> list[str]:
    out: list[str] = []
    for i in range(0, len(texts), batch_size):
        chunk = texts[i : i + batch_size]
        cached = [_cache.get(text) for text in chunk]
        if all(item is not None for item in cached):
            out.extend(item or source for item, source in zip(cached, chunk))
            print(f"[cn] translated/cached sentences: {min(i + batch_size, len(texts))}/{len(texts)}", flush=True)
            continue

        missing_positions = [index for index, item in enumerate(cached) if item is None]
        missing_texts = [chunk[index] for index in missing_positions]
        for group in _group_translation_texts(missing_texts, max_count=batch_size):
            try:
                translated = _translate_joined_sentences(group)
                for source, target in zip(group, translated):
                    _cache[source] = target or source
            except Exception:
                for source in group:
                    _translate_text(source)

        _save_cache()
        out.extend(_cache.get(text, text) for text in chunk)
        print(f"[cn] translated/cached sentences: {min(i + batch_size, len(texts))}/{len(texts)}", flush=True)
    return out


def _protect_abbreviations(text: str) -> tuple[str, dict[str, str]]:
    protected = text
    token_to_abbr: dict[str, str] = {}
    for index, abbr in enumerate(ABBREVIATIONS):
        token = f"ZXQABBR{index:03d}X"
        token_to_abbr[token] = abbr
        protected = protected.replace(abbr, token)
    return protected, token_to_abbr


def _restore_abbreviations(text: str, token_to_abbr: dict[str, str]) -> str:
    restored = text
    for token, abbr in token_to_abbr.items():
        restored = restored.replace(token, abbr)
    return restored


def _split_sentences(text: str) -> list[str]:
    s = text.strip()
    if not s:
        return []

    protected, token_to_abbr = _protect_abbreviations(s)
    raw_sentences = re.split(r"(?<=[.!?])\s+", protected)
    sentences = []
    for sentence in raw_sentences:
        restored = _restore_abbreviations(sentence.strip(), token_to_abbr)
        if restored:
            sentences.append(restored)
    return sentences or [s]


def _translate_long_text(text: str) -> str:
    locked_text, token_to_cn = _lock_terms_for_translation(text)
    sentences = _split_sentences(locked_text)
    translated_chunks = _translate_batch(sentences, batch_size=20)
    aligned_sentences = []
    for source, translated in zip(sentences, translated_chunks):
        out = translated.strip() if translated and translated.strip() else source
        aligned_sentences.append(out)
    joined = " ".join(aligned_sentences)
    normalized = _normalize_locked_terms(joined)
    return _restore_locked_terms(normalized, token_to_cn)


def _restore_translated_sentences(
    source_sentences: list[str],
    translated_sentences: list[str],
    token_to_cn: dict[str, str],
) -> str:
    aligned_sentences = []
    for source, translated in zip(source_sentences, translated_sentences):
        out = translated.strip() if translated and translated.strip() else source
        aligned_sentences.append(out)
    joined = " ".join(aligned_sentences)
    normalized = _normalize_locked_terms(joined)
    return _restore_locked_terms(normalized, token_to_cn)


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
    targets = []
    for p in paragraphs:
        src = "".join(r.text for r in p.runs) if p.runs else p.text
        if _should_translate(src):
            targets.append((p, src))

    if not targets:
        return 0

    prepared = []
    all_sentences = []
    for p, src in targets:
        locked_text, token_to_cn = _lock_terms_for_translation(src)
        sentences = _split_sentences(locked_text)
        start = len(all_sentences)
        all_sentences.extend(sentences)
        prepared.append((p, sentences, token_to_cn, start, len(sentences)))

    translated_sentences = _translate_batch(all_sentences, batch_size=8)

    for p, sentences, token_to_cn, start, count in prepared:
        chunk = translated_sentences[start : start + count]
        dst = _restore_translated_sentences(sentences, chunk, token_to_cn)
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
