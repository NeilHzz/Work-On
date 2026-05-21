import os, re, json, zipfile, xml.etree.ElementTree as ET, urllib.request, urllib.parse, time
workspace = r'e:\Data\Desktop\Work On'
docx_path = os.path.join(workspace, 'eggshell_matrix_ptm_direct_related_refs.docx')
with zipfile.ZipFile(docx_path) as z:
    xml_bytes = z.read('word/document.xml')
root = ET.fromstring(xml_bytes)
text = ''.join(t.text or '' for t in root.iter() if t.tag.endswith('}t'))
pat = re.compile(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', re.I)
dois = []
seen = set()
for m in pat.finditer(text):
    doi = re.sub(r'\s+', '', m.group(0).rstrip('.,;:)]>}').strip())
    if doi.lower() not in seen:
        seen.add(doi.lower())
        dois.append(doi)

def get_json(url):
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))

def inverted_to_text(inv):
    if not inv:
        return None
    arr = []
    for word, poss in inv.items():
        for pos in poss:
            arr.append((pos, word))
    arr.sort()
    return ' '.join(word for pos, word in arr)

def fetch_pubmed_abstract(pmid):
    if not pmid:
        return None
    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?' + urllib.parse.urlencode({'db':'pubmed','id':str(pmid),'retmode':'xml'})
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        root = ET.fromstring(r.read())
    parts = []
    for node in root.findall('.//Abstract/AbstractText'):
        label = node.attrib.get('Label') or node.attrib.get('NlmCategory') or ''
        txt = ''.join(node.itertext()).strip()
        if txt:
            parts.append(((label + ': ') if label and label != 'UNASSIGNED' else '') + txt)
    return '\n'.join(parts) if parts else None

results = []
for doi in dois:
    rec = {'doi':doi,'title':None,'year':None,'journal':None,'pmid':None,'abstract':None}
    try:
        url = 'https://api.openalex.org/works/' + urllib.parse.quote('https://doi.org/' + doi, safe='')
        data = get_json(url)
        rec['title'] = data.get('title')
        rec['year'] = data.get('publication_year')
        src = ((data.get('primary_location') or {}).get('source') or {})
        rec['journal'] = src.get('display_name')
        if not rec['journal']:
            for loc in data.get('locations') or []:
                s = (loc.get('source') or {}) if isinstance(loc, dict) else {}
                if s.get('display_name'):
                    rec['journal'] = s['display_name']
                    break
        pmid = (data.get('ids') or {}).get('pmid')
        if pmid:
            rec['pmid'] = re.sub(r'^https?://pubmed\.ncbi\.nlm\.nih\.gov/', '', pmid).strip('/ ')
        rec['abstract'] = inverted_to_text(data.get('abstract_inverted_index'))
        if not rec['abstract'] and rec['pmid']:
            try:
                rec['abstract'] = fetch_pubmed_abstract(rec['pmid'])
            except Exception:
                pass
    except Exception as e:
        rec['title'] = 'OpenAlex lookup failed: ' + str(e)
    results.append(rec)
    time.sleep(0.11)
open('openalex_pubmed_output.json','w',encoding='utf-8').write(json.dumps(results, ensure_ascii=False, separators=(',',':')))
print(len(dois))
