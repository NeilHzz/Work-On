from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests
from docx import Document


BASE = Path.cwd()
WORK_DIR = next(BASE.glob("03_*"))
DOCX = WORK_DIR / "manuscript260608.docx"
OUT_JSON = WORK_DIR / "manuscript260608_doi_matches.json"


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_coverage(title: str, ref: str) -> float:
    title_tokens = set(normalize(title).split())
    ref_tokens = set(normalize(ref).split())
    if not title_tokens:
        return 0.0
    return len(title_tokens & ref_tokens) / len(title_tokens)


def parse_references() -> list[dict]:
    doc = Document(str(DOCX))
    in_refs = False
    refs = []
    for idx, paragraph in enumerate(doc.paragraphs):
        text = paragraph.text.strip()
        if text == "References":
            in_refs = True
            continue
        if not in_refs or not text:
            continue
        match = re.match(r"^(\d+)\.\s+(.+)$", text)
        if match:
            refs.append({"number": int(match.group(1)), "paragraph": idx, "text": text})
    return refs


def crossref_lookup(ref_text: str) -> dict | None:
    response = requests.get(
        "https://api.crossref.org/works",
        params={"query.bibliographic": ref_text, "rows": 3},
        headers={"User-Agent": "Codex DOI checker (mailto:unknown@example.com)"},
        timeout=30,
    )
    response.raise_for_status()
    items = response.json()["message"]["items"]
    best = None
    for item in items:
        title = (item.get("title") or [""])[0]
        doi = item.get("DOI")
        if not title or not doi:
            continue
        year_parts = item.get("published-print", item.get("published-online", item.get("issued", {}))).get("date-parts", [])
        year = year_parts[0][0] if year_parts and year_parts[0] else None
        coverage = token_coverage(title, ref_text)
        ref_year_match = re.search(r"\((\d{4})\)\.?$", ref_text)
        expected_year = int(ref_year_match.group(1)) if ref_year_match else None
        year_ok = expected_year is None or year is None or expected_year == year
        score = coverage + (0.15 if year_ok else -0.25)
        candidate = {
            "doi": doi.lower(),
            "title": title,
            "year": year,
            "coverage": round(coverage, 3),
            "year_ok": year_ok,
            "score": round(score, 3),
            "container": (item.get("container-title") or [""])[0],
        }
        if best is None or candidate["score"] > best["score"]:
            best = candidate
    return best


def main() -> None:
    refs = parse_references()
    results = []
    for ref in refs:
        try:
            match = crossref_lookup(ref["text"])
        except Exception as exc:
            match = {"error": str(exc)}
        accepted = bool(match and not match.get("error") and match["coverage"] >= 0.82 and match["year_ok"])
        results.append({**ref, "match": match, "accepted": accepted})
        print(ref["number"], "accepted" if accepted else "review", match)
        time.sleep(0.12)
    OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT_JSON)


if __name__ == "__main__":
    main()
