import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from docx import Document


DOC_PATH = Path(r"e:\Data\Desktop\Work On\eggshell_matrix_ptm_direct_related_refs.docx")
OUTPUT_PATH = Path(r"e:\Data\Desktop\Work On\eggshell_matrix_ptm_abstracts.json")


def http_get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def http_get_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def reconstruct_abstract(inverted_index: dict | None) -> str | None:
    if not inverted_index:
        return None
    positions: list[tuple[int, str]] = []
    for token, indexes in inverted_index.items():
        for index in indexes:
            positions.append((index, token))
    if not positions:
        return None
    positions.sort(key=lambda item: item[0])
    return " ".join(token for _, token in positions)


def normalize_whitespace(text: str | None) -> str | None:
    if not text:
        return None
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def extract_dois(document_path: Path) -> list[str]:
    document = Document(str(document_path))
    dois: list[str] = []
    seen: set[str] = set()
    for paragraph in document.paragraphs:
        if "DOI:" not in paragraph.text:
            continue
        doi = paragraph.text.split("DOI:", 1)[1].strip()
        if doi and doi not in seen:
            dois.append(doi)
            seen.add(doi)
    return dois


def extract_pmid(result: dict) -> str | None:
    ids = result.get("ids") or {}
    pmid_url = ids.get("pmid")
    if pmid_url:
        return pmid_url.rstrip("/").rsplit("/", 1)[-1]

    for location in result.get("locations") or []:
        landing_page_url = location.get("landing_page_url") or ""
        if "pubmed.ncbi.nlm.nih.gov" in landing_page_url:
            return landing_page_url.rstrip("/").rsplit("/", 1)[-1]
    return None


def fetch_pubmed_abstract(pmid: str) -> str | None:
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
        + urllib.parse.urlencode(
            {
                "db": "pubmed",
                "id": pmid,
                "retmode": "xml",
            }
        )
    )
    try:
        xml_text = http_get_text(url)
    except Exception:
        return None

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None

    abstract_parts: list[str] = []
    for abstract_text in root.findall(".//Abstract/AbstractText"):
        label = abstract_text.attrib.get("Label")
        section_text = "".join(abstract_text.itertext()).strip()
        if not section_text:
            continue
        if label:
            abstract_parts.append(f"{label}: {section_text}")
        else:
            abstract_parts.append(section_text)

    if not abstract_parts:
        return None
    return normalize_whitespace(" ".join(abstract_parts))


def fetch_openalex_record(doi: str) -> dict:
    url = "https://api.openalex.org/works?filter=" + urllib.parse.quote(f"doi:{doi}")
    payload = http_get_json(url)
    results = payload.get("results") or []
    return results[0] if results else {}


def build_record(doi: str) -> dict:
    result = fetch_openalex_record(doi)
    title = normalize_whitespace(result.get("title") or result.get("display_name"))
    primary_location = result.get("primary_location") or {}
    source = primary_location.get("source") or {}
    abstract = normalize_whitespace(reconstruct_abstract(result.get("abstract_inverted_index")))
    pmid = extract_pmid(result)
    if not abstract and pmid:
        abstract = fetch_pubmed_abstract(pmid)

    authors = []
    for authorship in result.get("authorships") or []:
        author = authorship.get("author") or {}
        display_name = normalize_whitespace(author.get("display_name"))
        if display_name:
            authors.append(display_name)

    return {
        "doi": doi,
        "title": title,
        "year": result.get("publication_year"),
        "journal": normalize_whitespace(source.get("display_name")),
        "pmid": pmid,
        "authors": authors,
        "abstract": abstract,
    }


def main() -> None:
    dois = extract_dois(DOC_PATH)
    records = []
    for index, doi in enumerate(dois, start=1):
        print(f"[{index}/{len(dois)}] {doi}", flush=True)
        try:
            record = build_record(doi)
        except Exception as exc:
            record = {
                "doi": doi,
                "title": None,
                "year": None,
                "journal": None,
                "pmid": None,
                "authors": [],
                "abstract": None,
                "error": f"{type(exc).__name__}: {exc}",
            }
        records.append(record)
        OUTPUT_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(records)} records to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()