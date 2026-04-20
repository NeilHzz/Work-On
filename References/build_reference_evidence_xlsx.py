from __future__ import annotations

import ast
import html
import json
import re
import time
from pathlib import Path
from typing import Any

import requests
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font


ROOT = Path(__file__).resolve().parent
SCRIPT_PATH = ROOT / "build_manuscript_en.py"
OUTPUT_XLSX = ROOT / "manuscript_reference_evidence.xlsx"
OUTPUT_JSON = ROOT / "manuscript_reference_evidence.json"

CROSSREF_URL = "https://api.crossref.org/works"
EUROPEPMC_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
USER_AGENT = "GitHubCopilot/1.0 (mailto:research@example.com)"


def clean_text(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def first_sentence(text: str) -> str:
    clean = clean_text(text)
    if not clean:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", clean)
    for part in parts:
        part = part.strip()
        if len(part) >= 40:
            return part
    return clean


def call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def extract_para_text(call: ast.Call) -> str:
    if not call.args:
        return ""
    first = call.args[0]
    func = call_name(call.func)
    if func == "para":
        try:
            value = ast.literal_eval(first)
        except Exception:
            return ""
        return clean_text(str(value))
    if func == "mixed":
        try:
            parts = ast.literal_eval(first)
        except Exception:
            return ""
        chunks = []
        for part in parts:
            if isinstance(part, (list, tuple)) and part:
                chunks.append(str(part[0]))
        return clean_text("".join(chunks))
    return ""


def parse_script(script_path: Path) -> tuple[list[str], dict[int, str]]:
    source = script_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    refs: list[str] = []
    paragraph_by_var: dict[str, str] = {}
    first_claim_by_ref: dict[int, str] = {}

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_refs":
                    refs = ast.literal_eval(node.value)
                if isinstance(target, ast.Name) and isinstance(node.value, ast.Call):
                    func = call_name(node.value.func)
                    if func in {"para", "mixed"}:
                        text = extract_para_text(node.value)
                        if text:
                            paragraph_by_var[target.id] = text

        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            func = call_name(node.value.func)
            if func != "cite" or len(node.value.args) < 2:
                continue
            para_arg = node.value.args[0]
            nums_arg = node.value.args[1]
            para_text = ""
            if isinstance(para_arg, ast.Name):
                para_text = paragraph_by_var.get(para_arg.id, "")
            elif isinstance(para_arg, ast.Call):
                para_text = extract_para_text(para_arg)

            try:
                nums = ast.literal_eval(nums_arg)
            except Exception:
                nums = []

            for num in nums:
                if isinstance(num, int) and num not in first_claim_by_ref and para_text:
                    first_claim_by_ref[num] = para_text

    return refs, first_claim_by_ref


def crossref_lookup(citation: str) -> dict[str, Any]:
    response = requests.get(
        CROSSREF_URL,
        params={"query.bibliographic": citation, "rows": 1},
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    items = response.json().get("message", {}).get("items", [])
    return items[0] if items else {}


def europepmc_lookup(doi: str | None, title: str | None) -> dict[str, Any]:
    queries = []
    if doi:
        queries.append(f'DOI:"{doi}"')
    if title:
        queries.append(f'TITLE:"{title}"')

    for query in queries:
        response = requests.get(
            EUROPEPMC_URL,
            params={"query": query, "format": "json", "pageSize": 1, "resultType": "core"},
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        response.raise_for_status()
        results = response.json().get("resultList", {}).get("result", [])
        if results:
            return results[0]
    return {}


def extract_doi(item: dict[str, Any]) -> str:
    return str(item.get("DOI") or item.get("doi") or "").strip()


def extract_title(item: dict[str, Any]) -> str:
    title = item.get("title") or ""
    if isinstance(title, list):
        return clean_text(title[0]) if title else ""
    return clean_text(str(title))


def extract_abstract(item: dict[str, Any]) -> str:
    return clean_text(str(item.get("abstract") or item.get("abstractText") or ""))


def build_rows() -> list[dict[str, str]]:
    refs, claim_map = parse_script(SCRIPT_PATH)
    rows: list[dict[str, str]] = []

    for index, citation in enumerate(refs, start=1):
        print(f"Resolving ref {index}/52")
        crossref_item: dict[str, Any] = {}
        europepmc_item: dict[str, Any] = {}
        doi = ""
        paper_title = ""
        abstract_text = ""
        source = ""

        try:
            crossref_item = crossref_lookup(citation)
        except Exception:
            crossref_item = {}

        doi = extract_doi(crossref_item)
        paper_title = extract_title(crossref_item)

        try:
            europepmc_item = europepmc_lookup(doi or None, paper_title or None)
        except Exception:
            europepmc_item = {}

        if europepmc_item:
            doi = doi or extract_doi(europepmc_item)
            paper_title = paper_title or clean_text(str(europepmc_item.get("title") or ""))
            abstract_text = extract_abstract(europepmc_item)
            source = "Europe PMC abstract"

        if not abstract_text and crossref_item:
            abstract_text = extract_abstract(crossref_item)
            if abstract_text:
                source = "Crossref abstract"

        support_sentence = first_sentence(abstract_text)
        if not support_sentence:
            support_sentence = paper_title or citation
            source = source or "Title fallback"

        rows.append(
            {
                "ref_no": str(index),
                "manuscript_sentence": claim_map.get(index, ""),
                "full_citation": citation,
                "paper_title": paper_title,
                "doi": doi,
                "supporting_sentence": support_sentence,
                "evidence_source": source,
            }
        )
        time.sleep(0.2)

    return rows


def write_outputs(rows: list[dict[str, str]]) -> None:
    OUTPUT_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Reference Evidence"

    headers = [
        "Ref No",
        "Manuscript Sentence",
        "Full Citation",
        "Paper Title",
        "DOI",
        "Supporting Sentence From Paper",
        "Evidence Source",
    ]
    sheet.append(headers)

    for row in rows:
        sheet.append(
            [
                row["ref_no"],
                row["manuscript_sentence"],
                row["full_citation"],
                row["paper_title"],
                row["doi"],
                row["supporting_sentence"],
                row["evidence_source"],
            ]
        )

    for cell in sheet[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center")

    widths = {
        "A": 10,
        "B": 55,
        "C": 90,
        "D": 55,
        "E": 34,
        "F": 80,
        "G": 20,
    }
    for column, width in widths.items():
        sheet.column_dimensions[column].width = width

    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    sheet.freeze_panes = "A2"
    workbook.save(OUTPUT_XLSX)


def main() -> None:
    rows = build_rows()
    write_outputs(rows)
    print(f"[OK] {OUTPUT_XLSX}")
    print(f"[OK] {OUTPUT_JSON}")
    print(f"rows={len(rows)}")


if __name__ == "__main__":
    main()