"""
============================================================
 Script: groq_terms_to_pdf.py
 Autor: Leandro
 Descrição:
   - Lê JSON com termos pendentes
   - Faz requests individuais ao Groq (1 termo por vez)
   - Gera JSON estruturado com significado + exemplos
   - Gera PDF final usando ReportLab (Platypus)
============================================================

Requisitos:
- pip install requests reportlab
- groq_keys_loader.py com lista GROQ_KEYS
"""
import os
import sys
import json
import random
import requests
from itertools import cycle
from pathlib import Path
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4


# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

INPUT_JSON = Path("./terms/pending_terms.json")
OUTPUT_JSON = Path("./terms/terms_result.json")
OUTPUT_PDF = Path("./terms/terms_result.pdf")


TIMEOUT = 60

# =====================================================================================
# CONFIGURAÇÕES DO SISTEMA — MULTI GROQ KEYS (ROTATION / RANDOM)
# =====================================================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from groq_keys_loader import GROQ_KEYS

if not GROQ_KEYS or not all(isinstance(k, dict) and "key" in k for k in GROQ_KEYS):
    raise RuntimeError("❌ GROQ_KEYS inválidas ou mal carregadas")

_groq_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"


# ==========================================================
# FUNÇÕES GROQ
# ==========================================================

def groq_request(prompt: str) -> dict:
    key_info = next(_groq_key_cycle)
    api_key = key_info["key"]  # ✅ CORRETO

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an English teacher. "
                    "Return ONLY valid JSON. "
                    "Do not add explanations outside JSON."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.4
    }

    response = requests.post(
        GROQ_URL,
        headers=headers,
        json=payload,
        timeout=TIMEOUT
    )

    response.raise_for_status()
    return response.json()


def build_prompt(term: str) -> str:
    return f"""
For the English term: "{term}"

Return JSON in the following structure:

{{
  "term": "{term}",
  "meaning_pt": "significado ou tradução em português",
  "examples": [
    "example sentence 1",
    "example sentence 2"
  ]
}}
"""


# ==========================================================
# PDF
# ==========================================================

def generate_pdf(data: list, output_path: Path):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4
    )

    elements = []

    title = Paragraph(
        f"<b>English Terms Study</b><br/>Generated: {datetime.now():%Y-%m-%d %H:%M}",
        styles["Title"]
    )
    elements.append(title)
    elements.append(Spacer(1, 20))

    for item in data:
        elements.append(Paragraph(f"<b>Term:</b> {item['term']}", styles["Heading2"]))
        elements.append(Spacer(1, 6))

        elements.append(Paragraph(f"<b>Meaning (PT):</b> {item['meaning_pt']}", styles["Normal"]))
        elements.append(Spacer(1, 6))

        elements.append(Paragraph("<b>Examples:</b>", styles["Normal"]))
        for ex in item["examples"]:
            elements.append(Paragraph(f"- {ex}", styles["Normal"]))

        elements.append(Spacer(1, 20))

    doc.build(elements)


# ==========================================================
# MAIN
# ==========================================================

def main():
    if not INPUT_JSON.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {INPUT_JSON}")

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        source = json.load(f)

    pending_terms = source.get("pending", [])
    results = []

    for idx, term in enumerate(pending_terms, start=1):
        print(f"[{idx}/{len(pending_terms)}] Processing: {term}")

        prompt = build_prompt(term)
        response = groq_request(prompt)

        content = response["choices"][0]["message"]["content"]
        parsed = json.loads(content)

        results.append(parsed)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    generate_pdf(results, OUTPUT_PDF)

    print("✅ JSON gerado:", OUTPUT_JSON)
    print("📘 PDF gerado:", OUTPUT_PDF)


if __name__ == "__main__":
    main()
