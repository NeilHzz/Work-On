import fitz  # PyMuPDF
import sys

pdf_path = "Proteotype coevolution and quantitative diversity across 11 mammalian species - Ba 等 - 2022 .pdf"
output_path = "extracted_paper.txt"

try:
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Successfully extracted text to {output_path}")
except Exception as e:
    print(f"Error: {e}")
