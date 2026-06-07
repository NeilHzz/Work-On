from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from docx import Document


BASE = Path.cwd()
WORK_DIR = next(BASE.glob("03_*"))
DOCX = WORK_DIR / "manuscript260608.docx"
REPORT = WORK_DIR / "manuscript260608_citation_check.md"
JSON_OUT = WORK_DIR / "manuscript260608_citation_check.json"


REFERENCE_HEADING = "References"


def normalize_dash(text: str) -> str:
    return text.replace("–", "-").replace("—", "-").replace("−", "-")


def split_doc(docx_path: Path) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    doc = Document(str(docx_path))
    paragraphs = [(i, p.text.strip()) for i, p in enumerate(doc.paragraphs) if p.text.strip()]
    ref_idx = next((i for i, text in paragraphs if text == REFERENCE_HEADING), None)
    if ref_idx is None:
        return paragraphs, []
    body = [(i, text) for i, text in paragraphs if i < ref_idx]
    refs = [(i, text) for i, text in paragraphs if i > ref_idx]
    return body, refs


def expand_numbers(token: str) -> list[int]:
    token = normalize_dash(token).strip()
    if "-" in token:
        left, right = [part.strip() for part in token.split("-", 1)]
        if left.isdigit() and right.isdigit():
            a, b = int(left), int(right)
            if a <= b:
                return list(range(a, b + 1))
    if token.isdigit():
        return [int(token)]
    return []


def extract_citations(body: list[tuple[int, str]]) -> list[dict]:
    citations = []
    citation_pattern = re.compile(r"\((\d+(?:\s*[-–]\s*\d+)?(?:\s*,\s*\d+(?:\s*[-–]\s*\d+)?)*)\)")
    for para_idx, text in body:
        for match in citation_pattern.finditer(text):
            raw = match.group(1)
            numbers = []
            for part in raw.split(","):
                numbers.extend(expand_numbers(part))
            citations.append(
                {
                    "paragraph": para_idx,
                    "raw": f"({raw})",
                    "numbers": numbers,
                    "context": text[max(0, match.start() - 90) : min(len(text), match.end() + 90)],
                }
            )
    return citations


def extract_references(refs: list[tuple[int, str]]) -> dict[int, dict]:
    parsed = {}
    pattern = re.compile(r"^(\d+)\.\s+(.+)$")
    for para_idx, text in refs:
        match = pattern.match(text)
        if match:
            number = int(match.group(1))
            parsed[number] = {"paragraph": para_idx, "text": match.group(2)}
    return parsed


def first_citation_order(citations: list[dict]) -> list[int]:
    seen = set()
    order = []
    for citation in citations:
        for number in citation["numbers"]:
            if number not in seen:
                seen.add(number)
                order.append(number)
    return order


def reference_format_issues(references: dict[int, dict]) -> list[dict]:
    issues = []
    for number, ref in references.items():
        text = ref["text"]
        if " et al" in text or "et al." in text:
            issues.append({"ref": number, "issue": "uses et al.; Science style requires complete author lists"})
        if re.search(r"\bdoi:|https?://doi\.org/", text, re.I):
            has_doi = True
        else:
            has_doi = False
        if not has_doi:
            issues.append({"ref": number, "issue": "DOI missing; Science Advances asks for DOI when available"})
        if not re.search(r"\(\d{4}\)\.?$", text):
            issues.append({"ref": number, "issue": "does not end with publication year in parentheses"})
        if re.search(r"\b\d{4};", text):
            issues.append({"ref": number, "issue": "appears to use semicolon-year style rather than Science citation style"})
        if re.search(r"^\[[0-9]+\]", text):
            issues.append({"ref": number, "issue": "reference list number uses square brackets; current manuscript does not, keep style consistent"})
    return issues


def detect_style(body: list[tuple[int, str]], references: dict[int, dict]) -> dict:
    body_text = "\n".join(text for _, text in body)
    parenthetical = len(re.findall(r"\(\d+(?:\s*[-–]\s*\d+)?(?:\s*,\s*\d+(?:\s*[-–]\s*\d+)?)*\)", body_text))
    square = len(re.findall(r"\[\d+(?:\s*[-–]\s*\d+)?(?:\s*,\s*\d+(?:\s*[-–]\s*\d+)?)*\]", body_text))
    ref_dot = sum(1 for n, ref in references.items() if re.match(r"^\d+\.", f"{n}. {ref['text']}"))
    return {
        "in_text_parentheses_count": parenthetical,
        "in_text_square_bracket_count": square,
        "reference_dot_numbering_count": ref_dot,
    }


def main() -> None:
    body, ref_paras = split_doc(DOCX)
    citations = extract_citations(body)
    references = extract_references(ref_paras)
    cited_numbers = [n for citation in citations for n in citation["numbers"]]
    cited_set = set(cited_numbers)
    ref_set = set(references)
    order = first_citation_order(citations)

    max_ref = max(ref_set) if ref_set else 0
    expected_ref_set = set(range(1, max_ref + 1))
    missing_reference_numbers = sorted(cited_set - ref_set)
    uncited_reference_numbers = sorted(ref_set - cited_set)
    numbering_gaps = sorted(expected_ref_set - ref_set)
    first_order_violations = [
        {"position": i + 1, "first_seen": number, "expected": i + 1}
        for i, number in enumerate(order)
        if number != i + 1
    ]
    format_issues = reference_format_issues(references)
    citation_counter = Counter(cited_numbers)
    style = detect_style(body, references)

    status = "PASS" if not missing_reference_numbers and not uncited_reference_numbers and not numbering_gaps and not first_order_violations else "FAIL"

    data = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "document": str(DOCX),
        "total_in_text_citation_groups": len(citations),
        "unique_cited_references": len(cited_set),
        "reference_entries": len(ref_set),
        "overall_status": status,
        "missing_reference_numbers": missing_reference_numbers,
        "uncited_reference_numbers": uncited_reference_numbers,
        "numbering_gaps": numbering_gaps,
        "first_citation_order_violations": first_order_violations,
        "reference_format_issues": format_issues,
        "style": style,
        "citation_frequency": dict(sorted(citation_counter.items())),
    }
    JSON_OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    first_order_note = "PASS" if not first_order_violations else "FAIL"
    crossref_note = "PASS" if not missing_reference_numbers and not uncited_reference_numbers and not numbering_gaps else "FAIL"
    doi_missing = sum(1 for item in format_issues if "DOI missing" in item["issue"])
    report = [
        "# manuscript260608 Citation Check",
        "",
        f"Generated: {data['generated_at']}",
        f"Document: `{DOCX.name}`",
        "Target: Science Advances",
        "",
        "## Summary",
        "",
        f"- Overall status: **{status}**",
        f"- In-text citation groups: {len(citations)}",
        f"- Unique cited references: {len(cited_set)}",
        f"- Reference entries: {len(ref_set)}",
        f"- Citation/reference cross-match: **{crossref_note}**",
        f"- First-citation numbering order: **{first_order_note}**",
        f"- Reference entries missing DOI field: {doi_missing}",
        "",
        "## Science Advances Checks Applied",
        "",
        "- References should be numbered by first citation order.",
        "- Every in-text citation should have a matching reference entry, and every reference entry should be cited.",
        "- The journal style is numeric; Science-family style commonly uses numbered references and complete bibliographic data.",
        "- DOI should be included when available.",
        "- Complete author lists are preferred; avoid `et al.` in the reference list.",
        "",
        "## Findings",
        "",
    ]

    if missing_reference_numbers:
        report.append(f"- Missing reference entries for cited numbers: {missing_reference_numbers}")
    if uncited_reference_numbers:
        report.append(f"- Reference entries not cited in main text/figure legends/methods: {uncited_reference_numbers}")
    if numbering_gaps:
        report.append(f"- Reference list numbering gaps: {numbering_gaps}")
    if first_order_violations:
        report.append("- First citation order violations:")
        for item in first_order_violations[:25]:
            report.append(f"  - First-seen position {item['position']}: cited ref {item['first_seen']} but expected {item['expected']}")
        if len(first_order_violations) > 25:
            report.append(f"  - ... {len(first_order_violations) - 25} more")
    if not (missing_reference_numbers or uncited_reference_numbers or numbering_gaps or first_order_violations):
        report.append("- No citation/reference matching or first-citation-order errors found.")

    report.extend(
        [
            "",
            "## Format Issues",
            "",
            f"- DOI missing in {doi_missing} of {len(ref_set)} reference entries. This is the main Science Advances compliance gap.",
            f"- In-text citation style detected: {style['in_text_parentheses_count']} parenthetical numeric groups, {style['in_text_square_bracket_count']} square-bracket numeric groups.",
            "- Current reference list uses `1. Author...` numbering. Keep this only if you are following Science-family parenthetical-number style; convert consistently if the submission system/template requires square brackets.",
        ]
    )

    non_doi_issues = [item for item in format_issues if "DOI missing" not in item["issue"]]
    if non_doi_issues:
        report.append("")
        report.append("### Non-DOI Format Flags")
        for item in non_doi_issues[:40]:
            report.append(f"- Ref. {item['ref']}: {item['issue']}")
        if len(non_doi_issues) > 40:
            report.append(f"- ... {len(non_doi_issues) - 40} more")

    report.extend(
        [
            "",
            "## Recommended Fixes",
            "",
            "1. Add DOI values to references where available.",
            "2. Confirm whether final submission should use Science-family parenthetical numbers `(1, 2)` or square-bracket numbers `[1, 2]`; do not mix styles.",
            "3. If using Science-family final style, keep reference numbering in first-citation order and retain complete author lists.",
            "4. Re-run this check after DOI insertion or any reference-manager export.",
        ]
    )

    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(REPORT)
    print(JSON_OUT)
    print(status)


if __name__ == "__main__":
    main()
