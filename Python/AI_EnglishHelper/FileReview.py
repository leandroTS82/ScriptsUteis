import os
import re
import json
import requests
import datetime
import shutil

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ================================================================================
# CONFIGURAÇÃO GROQ
# ================================================================================
GROQ_API_KEY = "***"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

INPUT_JSON_PATH = "./TranscriptResults.json"
OUTPUT_DIR = "./EnglishReview"

# ================================================================================
# PROMPT PROFISSIONAL — OBRIGA GROQ A PRODUZIR APOSTILA PRONTA
# ================================================================================
GROQ_SYSTEM_PROMPT = """
You are an expert English teacher.

You MUST return a structured bilingual study guide with the following clear sections:

## Vocabulary List
For each vocabulary item:
- English term
- Portuguese definition
- English explanation in simple form
- Example in English
- Translation of example into Portuguese

## Grammar & Usage
Explain how expressions are used, common mistakes, when to use them.
Include EN → PT versions.

## Patterns & Collocations
Provide common combinations, small phrases, and usage patterns (EN + PT).

## Reading Practice
A short paragraph in English using several words.
Then a full Portuguese translation.

## Study Tips
Simple practical advice for learning the terms.

RULES:
- MUST use section headers starting with “## ” exactly.
- MUST NOT use markdown bold (**), italics (*), or pipes (|).
- MUST NOT return tables; only clean paragraphs and lists.
- MUST NOT break the structure.
"""


# ================================================================================
# LIMPEZA DE ARTEFATOS DE LLM
# ================================================================================
def clean_llm_text(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"\|\|+", "", text)
    text = re.sub(r"\s+\n", "\n", text)
    return text.strip()


# ================================================================================
# CHAMAR GROQ
# ================================================================================
def call_groq(prompt_content: str) -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": GROQ_SYSTEM_PROMPT},
            {"role": "user", "content": prompt_content}
        ],
        "temperature": 0.2,
    }

    response = requests.post(GROQ_URL, headers=headers, json=body)

    if response.status_code != 200:
        raise Exception(f"Erro Groq: {response.status_code} - {response.text}")

    result = response.json()["choices"][0]["message"]["content"]
    return clean_llm_text(result)


# ================================================================================
# ESTILOS DO PDF
# ================================================================================
def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="TitleCustom",
        fontSize=26,
        leading=30,
        alignment=1,
        textColor=colors.HexColor("#1B4F72"),
        spaceAfter=28
    ))

    styles.add(ParagraphStyle(
        name="SectionCustom",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#154360"),
        spaceBefore=20,
        spaceAfter=12
    ))

    styles.add(ParagraphStyle(
        name="BodyCustom",
        parent=styles["Normal"],
        fontSize=12,
        leading=18,
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        name="PortugueseCustom",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#7E5109"),
        spaceAfter=10
    ))

    return styles


# ================================================================================
# GERAR PDF FINAL
# ================================================================================
def generate_pdf(output_path: str, structured_text: str):
    styles = build_styles()
    story = []

    # CAPA
    story.append(Paragraph("English Study Guide – Bilingual Edition", styles["TitleCustom"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 24))

    # SEPARA SEÇÕES
    sections = re.split(r"(?=## )", structured_text)

    for sec in sections:
        sec = sec.strip()
        if not sec.startswith("##"):
            continue

        title_line, *content = sec.split("\n", 1)
        section_title = clean_llm_text(title_line.replace("##", "").strip())
        story.append(Paragraph(section_title, styles["SectionCustom"]))

        if content:
            paragraphs = content[0].split("\n")

            for p in paragraphs:
                p = clean_llm_text(p)
                if not p:
                    continue

                # linha em português detectada automaticamente
                if p.lower().startswith("pt:"):
                    story.append(Paragraph(p[3:].strip(), styles["PortugueseCustom"]))
                else:
                    story.append(Paragraph(p, styles["BodyCustom"]))

        story.append(PageBreak())

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=50,
        rightMargin=50,
        topMargin=60,
        bottomMargin=50
    )

    doc.build(story)


# ================================================================================
# MAIN
# ================================================================================
def main():
    if not os.path.exists(INPUT_JSON_PATH):
        print("Arquivo TranscriptResults.json não encontrado.")
        return

    with open(INPUT_JSON_PATH, "r", encoding="utf-8") as f:
        data_json = json.load(f)

    print("Chamando Groq para gerar conteúdo...")
    groq_text = call_groq("Here is the vocabulary list:\n\n" + json.dumps(data_json, indent=2, ensure_ascii=False))

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
    pdf_path = os.path.join(OUTPUT_DIR, f"{timestamp}_EnglishReview.pdf")

    print("Gerando PDF final...")
    generate_pdf(pdf_path, groq_text)

    shutil.move(INPUT_JSON_PATH, os.path.join(OUTPUT_DIR, "TranscriptResults.json"))
    print("PDF criado com sucesso:", pdf_path)


if __name__ == "__main__":
    main()
