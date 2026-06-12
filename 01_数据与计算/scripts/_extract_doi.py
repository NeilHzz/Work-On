from docx import Document
import re

doc = Document('eggshell_matrix_ptm_direct_related_refs.docx')
pat = re.compile(r'DOI:\s*(10\.\d{4,9}/\S+)', re.IGNORECASE)
results = []
for p in doc.paragraphs:
    for m in pat.finditer(p.text):
        results.append(m.group(1).rstrip('.,;)]'))
for doi in results:
    print(doi)
print('Total count: {}'.format(len(results)))
