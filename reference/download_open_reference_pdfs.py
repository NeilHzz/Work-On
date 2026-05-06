from __future__ import annotations

import csv
import json
import re
import time
import urllib.parse
import urllib.request
import urllib.error
from difflib import SequenceMatcher
from pathlib import Path
import runpy


WORKSPACE = Path(__file__).resolve().parent.parent
REFERENCE_DIR = WORKSPACE / "reference"
REFS_PATH = WORKSPACE / "03_文章撰写" / "shared_references.py"
MANIFEST_PATH = REFERENCE_DIR / "manifest.csv"
SUMMARY_PATH = REFERENCE_DIR / "summary.txt"


def build_opener() -> urllib.request.OpenerDirector:
    opener = urllib.request.build_opener()
    opener.addheaders = [
        ("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ReferenceDownloader/2.0"),
        ("Accept", "application/json,application/pdf,text/html;q=0.9,*/*;q=0.8"),
    ]
    return opener


OPENER = build_opener()


def fetch_json(url: str) -> dict:
    delay = 2.0
    for attempt in range(4):
        try:
            with OPENER.open(url, timeout=30) as response:
                return json.loads(response.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < 3:
                time.sleep(delay)
                delay *= 2
                continue
            raise


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def safe_name(text: str, limit: int = 100) -> str:
    text = re.sub(r'[\\/:*?"<>|]+', "_", text)
    text = re.sub(r"\s+", " ", text).strip().replace(" ", "_")
    return text[:limit] or "untitled"


def get_year(ref: str) -> str:
    match = re.search(r"\((\d{4})\)\.?$", ref)
    return match.group(1) if match else "0000"


def get_index(ref: str) -> str:
    match = re.match(r"^(\d+)\.", ref)
    return match.group(1).zfill(3) if match else "000"


def citation_text(ref: str) -> str:
    return re.sub(r"^\d+\.\s*", "", ref).strip()


def choose_crossref_item(ref: str, items: list[dict]) -> dict | None:
    ref_norm = normalize(citation_text(ref))
    year = get_year(ref)
    best_item = None
    best_score = -1.0

    for item in items:
        title = " ".join(item.get("title") or [])
        title_norm = normalize(title)
        score = 0.0

        if title_norm and title_norm in ref_norm:
            score += 12.0

        score += 4.0 * SequenceMatcher(None, title_norm[:140], ref_norm[:260]).ratio()

        date_parts = item.get("issued", {}).get("date-parts", [[None]])
        pub_year = str(date_parts[0][0]) if date_parts and date_parts[0] else ""
        if pub_year == year:
            score += 2.0

        container = " ".join(item.get("container-title") or [])
        if container and normalize(container) in ref_norm:
            score += 1.0

        authors = item.get("author") or []
        if authors:
            surname = normalize(authors[0].get("family") or "")
            if surname and surname in ref_norm:
                score += 0.5

        if score > best_score:
            best_score = score
            best_item = item

    return best_item if best_score >= 5.0 else None


def crossref_match(ref: str) -> dict | None:
    query = urllib.parse.quote(citation_text(ref))
    url = f"https://api.crossref.org/works?query.bibliographic={query}&rows=5"
    items = fetch_json(url).get("message", {}).get("items", [])
    return choose_crossref_item(ref, items)


def openalex_by_doi(doi: str) -> dict | None:
    url = "https://api.openalex.org/works/https://doi.org/" + urllib.parse.quote(doi, safe="")
    try:
        return fetch_json(url)
    except Exception:
        return None


def candidate_pdf_urls(crossref_item: dict, openalex_item: dict | None) -> list[str]:
    urls: list[str] = []
    doi = crossref_item.get("DOI") or ""
    crossref_url = crossref_item.get("URL") or ""

    for link in crossref_item.get("link") or []:
        if not isinstance(link, dict):
            continue
        url = link.get("URL")
        if not isinstance(url, str):
            continue
        if link.get("content-type") == "application/pdf" or url.lower().endswith(".pdf"):
            urls.append(url)

    if openalex_item:
        open_access = openalex_item.get("open_access") or {}
        oa_url = open_access.get("oa_url")
        if isinstance(oa_url, str) and oa_url.lower().endswith(".pdf"):
            urls.append(oa_url)

        for loc in [
            openalex_item.get("best_oa_location"),
            openalex_item.get("primary_location"),
            *(openalex_item.get("locations") or []),
        ]:
            if not isinstance(loc, dict):
                continue
            for key in ("pdf_url", "landing_page_url"):
                url = loc.get(key)
                if isinstance(url, str) and ".pdf" in url.lower():
                    urls.append(url)

    if doi.startswith("10.1038/") and isinstance(crossref_url, str) and "/articles/" in crossref_url:
        article_path = crossref_url.split("/articles/", 1)[1].strip("/")
        if article_path:
            urls.append(f"https://www.nature.com/articles/{article_path}.pdf?download=1")
            urls.append(f"https://www.nature.com/articles/{article_path}.pdf")

    deduped: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if url and url not in seen:
            seen.add(url)
            deduped.append(url)
    return deduped


def download_pdf(url: str, target: Path) -> tuple[bool, str]:
    delay = 2.0
    last_error = ""
    try:
        for attempt in range(4):
            try:
                request = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0",
                        "Accept": "application/pdf,*/*;q=0.8",
                    },
                )
                with OPENER.open(request, timeout=45) as response:
                    data = response.read()
                    content_type = (response.headers.get("Content-Type") or "").lower()
                if b"%PDF" not in data[:1024] and "application/pdf" not in content_type:
                    return False, f"non-pdf response ({content_type or 'unknown'})"
                target.write_bytes(data)
                return True, "downloaded"
            except urllib.error.HTTPError as exc:
                last_error = str(exc)
                if exc.code == 429 and attempt < 3:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise
        return False, last_error or "download failed"
    except Exception as exc:
        return False, str(exc)


def main() -> None:
    refs = runpy.run_path(str(REFS_PATH))["REFS"]

    for path in REFERENCE_DIR.glob("*"):
        if path.is_file() and path.name != Path(__file__).name:
            path.unlink()

    rows: list[dict[str, str]] = []
    matched = 0
    downloaded = 0

    for ref in refs:
        ref_index = get_index(ref)
        year = get_year(ref)
        status = "not-found"
        note = ""
        matched_title = ""
        doi = ""
        crossref_url = ""
        pdf_url = ""
        filename = ""

        try:
            item = crossref_match(ref)
            if item is None:
                note = "No confident Crossref match"
            else:
                matched += 1
                matched_title = " ".join(item.get("title") or [])
                doi = item.get("DOI") or ""
                crossref_url = item.get("URL") or ""
                openalex_item = openalex_by_doi(doi) if doi else None
                urls = candidate_pdf_urls(item, openalex_item)

                if not urls:
                    status = "matched-no-open-pdf"
                    note = "Matched DOI but no direct open PDF URL found"
                else:
                    short_title = safe_name(matched_title or f"ref_{ref_index}")
                    filename = f"{ref_index}_{year}_{short_title}.pdf"
                    target = REFERENCE_DIR / filename
                    for url in urls:
                        ok, message = download_pdf(url, target)
                        pdf_url = url
                        if ok:
                            status = "downloaded"
                            note = message
                            downloaded += 1
                            break
                        note = message
                    if status != "downloaded":
                        status = "matched-no-open-pdf"
                        filename = ""
                        if target.exists():
                            target.unlink(missing_ok=True)
        except Exception as exc:
            status = "error"
            note = str(exc)

        rows.append(
            {
                "index": ref_index,
                "status": status,
                "year": year,
                "matched_title": matched_title,
                "doi": doi,
                "crossref_url": crossref_url,
                "pdf_url": pdf_url,
                "filename": filename,
                "note": note,
                "reference": ref,
            }
        )
        time.sleep(0.1)

    with MANIFEST_PATH.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "index",
                "status",
                "year",
                "matched_title",
                "doi",
                "crossref_url",
                "pdf_url",
                "filename",
                "note",
                "reference",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    summary_lines = [
        f"Total references: {len(refs)}",
        f"Crossref matched: {matched}",
        f"PDF downloaded: {downloaded}",
        f"Not downloaded: {len(refs) - downloaded}",
        "",
        "Only openly reachable PDFs were downloaded. No paywalls were bypassed.",
    ]
    SUMMARY_PATH.write_text("\n".join(summary_lines), encoding="utf-8")
    print("\n".join(summary_lines))
    print(f"Manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()