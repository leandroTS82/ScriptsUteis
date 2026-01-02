"""
python extract_reading_practice_from_json.py

- Percorre JSONs gerados a partir dos PDFs
- Extrai Reading Practice do campo pages[].text
- Gera JSON consolidado em ./extractedFromPdf/reading_practice_stories.json
"""

import os
import json
import re
from pathlib import Path

# =========================================================
# CONFIGURAÇÃO
# =========================================================

PDF_JSON_DIR = "./pdf_json_dump"
OUTPUT_DIR = "./extractedFromPdf"
OUTPUT_FILE = "reading_practice_stories.json"

# =========================================================
# EXTRAÇÃO
# =========================================================

def extract_reading_practice_from_page_text(text: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if not lines:
        return None

    # Primeira linha deve ser "Reading Practice"
    if "reading practice" not in lines[0].lower():
        return None

    collected = []

    for line in lines[1:]:
        # ignora tradução em português
        if re.search(r"[áéíóúãõç]", line.lower()):
            continue

        collected.append(line)

    if not collected:
        return None

    return " ".join(collected).strip()


# =========================================================
# MAIN
# =========================================================

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    stories = []

    for file in os.listdir(PDF_JSON_DIR):
        if not file.lower().endswith(".json"):
            continue

        json_path = os.path.join(PDF_JSON_DIR, file)
        print(f"📄 Processando JSON: {file}")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        pages = data.get("pages", [])

        reading_text = None

        for page in pages:
            text = page.get("text", "")
            reading_text = extract_reading_practice_from_page_text(text)
            if reading_text:
                break

        if not reading_text:
            print("⚠ Reading Practice não encontrada.")
            continue

        title = Path(file).stem.replace("_", " ").replace("-", " ").title()

        stories.append({
            "title": title,
            "text": reading_text
        })

        print("✅ Reading Practice extraída.")

    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {"stories": stories},
            f,
            ensure_ascii=False,
            indent=2
        )

    print(f"\n📦 JSON final gerado em: {output_path}")
    print(f"📚 Total de histórias extraídas: {len(stories)}")


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()
