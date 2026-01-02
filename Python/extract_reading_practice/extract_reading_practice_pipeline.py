"""
python extract_reading_practice_pipeline.py

PIPELINE:
1) PDF -> JSON estruturado (por página)
2) JSON -> Reading Practice (texto completo EN + PT)
3) Gera JSON final consolidado

pip install pymupdf
"""

import os
import json
import re
import fitz  # PyMuPDF
from pathlib import Path

# =========================================================
# CONFIGURAÇÃO
# =========================================================

PDF_ROOT_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\EnglishReview"

PDF_JSON_DIR = "./pdf_json_dump"
OUTPUT_DIR = "./extractedFromPdf"
OUTPUT_FILE = "reading_practice_stories.json"

# =========================================================
# UTILITÁRIOS
# =========================================================

def clean_title(filename: str) -> str:
    """
    Remove prefixo yyyyMMddHHmm_ e normaliza título
    """
    name = Path(filename).stem
    name = re.sub(r"^\d{12}_", "", name)
    name = name.replace("_", " ").replace("-", " ")
    return name.title()


# =========================================================
# ETAPA 1 — PDF -> JSON
# =========================================================

def extract_pdf_to_json(pdf_path: str, output_json_path: str):
    doc = fitz.open(pdf_path)
    pages = []

    for idx, page in enumerate(doc, start=1):
        pages.append({
            "page": idx,
            "text": page.get_text("text").strip()
        })

    payload = {
        "file": Path(pdf_path).name,
        "pages": pages
    }

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


# =========================================================
# ETAPA 2 — JSON -> Reading Practice (COMPLETO)
# =========================================================

def extract_reading_practice_from_json(json_path: str) -> str | None:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for page in data.get("pages", []):
        text = page.get("text", "")
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        if not lines:
            continue

        # Página correta
        if "reading practice" not in lines[0].lower():
            continue

        # Tudo após o título
        content = " ".join(lines[1:]).strip()
        return content if content else None

    return None


# =========================================================
# MAIN PIPELINE
# =========================================================

def main():
    os.makedirs(PDF_JSON_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    stories = []

    pdf_files = [f for f in os.listdir(PDF_ROOT_PATH) if f.lower().endswith(".pdf")]

    print(f"🔍 PDFs encontrados: {len(pdf_files)}\n")

    # -----------------------------
    # PDF -> JSON
    # -----------------------------
    for pdf in pdf_files:
        pdf_path = os.path.join(PDF_ROOT_PATH, pdf)
        json_path = os.path.join(PDF_JSON_DIR, Path(pdf).stem + ".json")

        print(f"📄 [PDF → JSON] {pdf}")
        extract_pdf_to_json(pdf_path, json_path)

    print("\n✅ Conversão PDF → JSON finalizada.\n")

    # -----------------------------
    # JSON -> Reading Practice
    # -----------------------------
    for json_file in os.listdir(PDF_JSON_DIR):
        if not json_file.lower().endswith(".json"):
            continue

        json_path = os.path.join(PDF_JSON_DIR, json_file)
        title = clean_title(json_file)

        print(f"📘 [Reading Practice] {title}")

        reading_text = extract_reading_practice_from_json(json_path)

        if not reading_text:
            print("   ⚠ Reading Practice não encontrada.")
            continue

        stories.append({
            "title": title,
            "text": reading_text
        })

        print("   ✅ Extraída (texto completo).")

    # -----------------------------
    # JSON FINAL
    # -----------------------------
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"stories": stories}, f, ensure_ascii=False, indent=2)

    print("\n📦 JSON FINAL GERADO:")
    print(f"📍 {output_path}")
    print(f"📚 Total de stories: {len(stories)}")


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()
