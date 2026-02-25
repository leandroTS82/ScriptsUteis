"""
python extract_pdf_to_json.py

- Percorre PDFs em um diretório
- Extrai TODO o texto de cada página
- Gera 1 JSON estruturado por PDF em ./pdf_json_dump

pip install pymupdf
"""

import os
import json
import fitz  # PyMuPDF
from pathlib import Path

# =========================================================
# CONFIGURAÇÃO (mantendo seu path)
# =========================================================

PDF_ROOT_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\EnglishReview"
OUTPUT_DIR = "./pdf_json_dump"

# =========================================================
# EXTRAÇÃO
# =========================================================

def extract_pdf_to_json(pdf_path: str, output_json_path: str):
    doc = fitz.open(pdf_path)

    pages = []

    for page_index, page in enumerate(doc, start=1):
        text = page.get_text("text")

        pages.append({
            "page": page_index,
            "text": text.strip()
        })

    payload = {
        "file": Path(pdf_path).name,
        "pages": pages
    }

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

# =========================================================
# MAIN
# =========================================================

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for file in os.listdir(PDF_ROOT_PATH):
        if not file.lower().endswith(".pdf"):
            continue

        pdf_path = os.path.join(PDF_ROOT_PATH, file)
        json_name = Path(file).stem + ".json"
        json_path = os.path.join(OUTPUT_DIR, json_name)

        print(f"📄 Extraindo: {file}")

        try:
            extract_pdf_to_json(pdf_path, json_path)
            print(f"✅ JSON gerado: {json_path}")
        except Exception as e:
            print(f"❌ Erro ao extrair {file}: {e}")

    print("\n📁 Dump JSON completo finalizado.")

# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()
