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
# CONFIGURAÇÕES DO SISTEMA
# ================================================================================

# Variáveis configuráveis pelo usuário (PROMPTS)
# ------------------------------------------------
# Estas variáveis podem ser alteradas para mudar completamente a estrutura
# do estudo gerado pelo Groq sem precisar alterar o resto do script.
# python doc.py
# ------------------------------------------------

SYSTEM_PROMPT = """
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
"""

# Prompt de usuário poderá ser modificado em caso de necessidade
USER_PROMPT_TEMPLATE = """
Here is a list of vocabulary entries. Generate a bilingual English learning guide:

{json_content}
"""


# ================================================================================
# CONFIGURAÇÃO GROQ
# ================================================================================
GROQ_API_KEY = r"C:\dev\scripts\ScriptsUteis\Python\secret_tokens_keys\groq_api_key.txt"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

INPUT_JSON_PATH = "./TranscriptResults.json"
OUTPUT_DIR = "./EnglishReview"
TEMP_DIR = "./.temp"


# ================================================================================
# LIMPEZA DE ARTEFATOS
# ================================================================================
def clean_llm_text(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"\|\|+", "", text)
    text = text.replace("  ", " ")
    return text.strip()


# ================================================================================
# CHAMAR GROQ
# ================================================================================
def call_groq(json_content: str) -> str:
    prompt = USER_PROMPT_TEMPLATE.format(json_content=json_content)

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
    }

    response = requests.post(GROQ_URL, headers=headers, json=body)

    if response.status_code != 200:
        raise Exception(f"Erro Groq: {response.status_code} - {response.text}")

    result = response.json()["choices"][0]["message"]["content"]
    return clean_llm_text(result)


# ================================================================================
# ESTILOS DO PDF (PROFISSIONAIS)
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
# CRIAR PDF
# ================================================================================
def generate_pdf(output_path: str, structured_text: str):
    styles = build_styles()
    story = []

    story.append(Paragraph("English Study Guide – Bilingual Edition", styles["TitleCustom"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 24))

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
# DIVIDIR JSON GRANDE EM PARTES DE 10 ITENS
# ================================================================================
def split_json_into_parts(full_list):
    os.makedirs(TEMP_DIR, exist_ok=True)

    parts = []
    part_number = 1

    for i in range(0, len(full_list), 10):
        chunk = full_list[i:i + 10]
        part_path = os.path.join(TEMP_DIR, f"part_{part_number}.json")

        with open(part_path, "w", encoding="utf-8") as f:
            json.dump(chunk, f, indent=2, ensure_ascii=False)

        parts.append(part_path)
        part_number += 1

    return parts


# ================================================================================
# MAIN
# ================================================================================
def main():
    if not os.path.exists(INPUT_JSON_PATH):
        print("Arquivo TranscriptResults.json não encontrado.")
        return

    with open(INPUT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Divide caso seja array grande
    parts = split_json_into_parts(data)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")

    # Processa cada parte
    for idx, part_path in enumerate(parts, start=1):
        with open(part_path, "r", encoding="utf-8") as f:
            part_json = json.load(f)

        print(f"Processando parte {idx}/{len(parts)}...")

        groq_text = call_groq(json.dumps(part_json, indent=2, ensure_ascii=False))

        pdf_name = f"{timestamp}_part{idx}.pdf"
        pdf_path = os.path.join(OUTPUT_DIR, pdf_name)

        print(f"Gerando PDF {pdf_name}...")
        generate_pdf(pdf_path, groq_text)

    # Remove diretório temporário
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

    # ================================
    # Renomear e mover TranscriptResults.json
    # ================================
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
    json_new_name = f"{timestamp}_TranscriptResults.json"
    json_new_path = os.path.join(OUTPUT_DIR, json_new_name)

    shutil.move(INPUT_JSON_PATH, json_new_path)

    print(f"Arquivo original movido para: {json_new_name}")
    print("Todos os PDFs foram gerados com sucesso!")


if __name__ == "__main__":
    main()
