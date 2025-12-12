import os
import re
import json
import requests
import datetime
import shutil

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


# =====================================================================================
# CONFIGURAÇÕES DO SISTEMA
# =====================================================================================

# GROQ_API_KEY = "C:\\dev\\scripts\\ScriptsUteis\\Python\\secret_tokens_keys\\groq_api_key.txt"
GROQ_API_KEY = "***"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

INPUT_JSON_PATH = "./TranscriptResults.json"
JSON_OUTPUT_DIR = "./json"
PDF_OUTPUT_DIR = "./EnglishReview"

os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)


# =====================================================================================
# PROMPTS – Groq gera JSON final no estilo CALLAN
# =====================================================================================

SYSTEM_PROMPT = """
You are an English teacher and instructional designer.

TASK:
Transform the user vocabulary list into a structured JSON formatted as a CALLAN-STYLE
training module.

RETURN ONLY VALID JSON.

STRUCTURE:
{
  "filename": "safe_filename_lowercase_no_spaces",
  "cover": {
    "title": "",
    "subtitle": "",
    "author": "",
    "edition": ""
  },
  "sections": [
    {
      "title": "",
      "entries": [
        {
          "term": "",
          "content": [
            { "type": "definition_pt", "text": "" },
            { "type": "explanation_en", "text": "" },
            { "type": "collocations", "items": ["", ""] },
            {
              "type": "examples",
              "items": [
                { "level": "", "en": "", "pt": "" }
              ]
            }
          ]
        }
      ]
    },
    {
      "title": "Grammar & Usage",
      "content": [
        { "type": "rule", "text": "" },
        { "type": "examples", "items": [ { "en": "", "pt": "" } ] }
      ]
    },
    {
      "title": "Patterns & Collocations",
      "content": [
        { "type": "list", "title": "", "items": ["", ""] }
      ]
    },
    {
      "title": "Reading Practice",
      "content": [
        { "type": "reading_en", "text": "" },
        { "type": "reading_pt", "text": "" }
      ]
    },
    {
      "title": "Study Tips",
      "tips": ["", ""]
    }
  ]
}

RULES:
- JSON must be valid.
- filename must contain only lowercase letters, numbers, and underscores.
- Keep CALLAN style: short, clear, progressive, easy to read.
- All example phrases must be improved, simplified, and friendly for learners.
- Return English and Portuguese versions of examples where appropriate.
"""

USER_PROMPT_TEMPLATE = """
Here is the raw vocabulary list. Transform it into the structured CALLAN JSON:

{json_content}
"""


# =====================================================================================
# CHAMADA GROQ
# =====================================================================================

def call_groq_structured(content: str) -> dict:
    prompt = USER_PROMPT_TEMPLATE.format(json_content=content)

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT + 
                "\n\nIMPORTANT:\nReturn ONLY JSON. No markdown. No explanations."
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    response = requests.post(GROQ_URL, headers=headers, json=body)

    if response.status_code != 200:
        raise Exception(f"Groq error {response.status_code}: {response.text}")

    json_str = response.json()["choices"][0]["message"]["content"].strip()

    # SALVA RETORNO BRUTO PARA DEBUG
    with open("last_groq_raw.txt", "w", encoding="utf-8") as f:
        f.write(json_str)

    # ============================================================
    # 1. Verificação inicial — retorno vazio
    # ============================================================
    if not json_str:
        raise Exception("Groq returned an empty response. Check last_groq_raw.txt.")

    # ============================================================
    # 2. Se já inicia com '{', tenta fazer loads direto
    # ============================================================
    if json_str.startswith("{"):
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass  # Vamos tentar limpeza mais abaixo

    # ============================================================
    # 3. LIMPEZA AUTOMÁTICA: extrair apenas o trecho JSON
    # ============================================================
    try:
        start = json_str.index("{")
        end = json_str.rindex("}") + 1
        cleaned = json_str[start:end]

        return json.loads(cleaned)

    except Exception:
        pass

    # ============================================================
    # 4. ÚLTIMA TENTATIVA: corrigir aspas quebradas
    # ============================================================
    try:
        fixed = json_str.replace("\n", " ").replace("\r", " ")
        fixed = re.sub(r"([a-zA-Z0-9_]+):", r'"\1":', fixed)
        return json.loads(fixed)
    except Exception:
        pass

    # ============================================================
    # 5. TUDO FALHOU → Exibir erro com retorno bruto
    # ============================================================
    raise Exception(
        "Groq did not return valid JSON. See last_groq_raw.txt for debugging.\n"
        f"Raw response:\n{json_str}"
    )



# =====================================================================================
# ESTILOS DO REPORTLAB – CALLAN STYLE
# =====================================================================================

def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="CoverTitle",
        fontSize=28,
        leading=34,
        alignment=1,
        spaceAfter=20,
        textColor=colors.HexColor("#0B3C5D")
    ))

    styles.add(ParagraphStyle(
        name="CoverSubtitle",
        fontSize=16,
        leading=20,
        alignment=1,
        spaceAfter=20,
        textColor=colors.HexColor("#1F618D")
    ))

    styles.add(ParagraphStyle(
        name="SectionTitle",
        fontSize=20,
        leading=26,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor("#154360")
    ))

    styles.add(ParagraphStyle(
        name="TermTitle",
        fontSize=16,
        leading=22,
        spaceBefore=12,
        spaceAfter=6,
        textColor=colors.HexColor("#0E6251")
    ))

    styles.add(ParagraphStyle(
        name="Body",
        fontSize=12,
        leading=18,
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        name="DefinitionPT",
        fontSize=12,
        leading=18,
        textColor=colors.HexColor("#7E5109"),
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        name="ExplanationEN",
        fontSize=12,
        leading=18,
        textColor=colors.HexColor("#1A5276"),
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        name="ListItem",
        fontSize=12,
        leading=16,
        leftIndent=15,
        bulletIndent=10,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        name="ExampleItem",
        fontSize=12,
        leading=16,
        leftIndent=20,
        spaceAfter=6,
        textColor=colors.HexColor("#117A65")
    ))

    styles.add(ParagraphStyle(
        name="ReadingEN",
        fontSize=12,
        leading=18,
        spaceAfter=6,
        textColor=colors.HexColor("#0E6655")
    ))

    styles.add(ParagraphStyle(
        name="ReadingPT",
        fontSize=11,
        leading=16,
        spaceAfter=10,
        textColor=colors.HexColor("#7D6608")
    ))

    return styles


# =====================================================================================
# RENDER PDF – CALLAN STYLE
# =====================================================================================

def generate_pdf_from_json(output_path: str, data: dict):
    styles = build_styles()
    story = []

    # COVER
    cover = data["cover"]
    story.append(Paragraph(cover["title"], styles["CoverTitle"]))
    story.append(Paragraph(cover["subtitle"], styles["CoverSubtitle"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Author: {cover['author']}", styles["Body"]))
    story.append(Paragraph(f"Edition: {cover['edition']}", styles["Body"]))
    story.append(PageBreak())

    # TABLE OF CONTENTS
    story.append(Paragraph("Table of Contents", styles["SectionTitle"]))
    toc_rows = [[sec["title"]] for sec in data["sections"]]

    toc_table = Table(toc_rows, [450])
    toc_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.black),
        ("FONTSIZE", (0,0), (-1,-1), 12),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6)
    ]))

    story.append(toc_table)
    story.append(PageBreak())

    # SECTIONS
    for sec in data["sections"]:
        story.append(Paragraph(sec["title"], styles["SectionTitle"]))

        # Vocabulary List sections
        if "entries" in sec:
            for entry in sec["entries"]:
                story.append(Paragraph(entry["term"], styles["TermTitle"]))

                for item in entry["content"]:
                    t = item["type"]

                    if t == "definition_pt":
                        story.append(Paragraph(item["text"], styles["DefinitionPT"]))

                    elif t == "explanation_en":
                        story.append(Paragraph(item["text"], styles["ExplanationEN"]))

                    elif t == "collocations":
                        for col in item["items"]:
                            story.append(Paragraph(f"- {col}", styles["ListItem"]))

                    elif t == "examples":
                        for ex in item["items"]:
                            story.append(Paragraph(
                                f"{ex['level']} — {ex['en']} / {ex['pt']}",
                                styles["ExampleItem"]
                            ))

        # Standard content sections
        if "content" in sec:
            for item in sec["content"]:
                t = item["type"]

                if t == "rule":
                    story.append(Paragraph(item["text"], styles["Body"]))

                elif t == "examples":
                    for ex in item["items"]:
                        story.append(Paragraph(
                            f"{ex['en']} / {ex['pt']}",
                            styles["ExampleItem"]
                        ))

                elif t == "list":
                    story.append(Paragraph(item["title"], styles["TermTitle"]))
                    for x in item["items"]:
                        story.append(Paragraph(f"- {x}", styles["ListItem"]))

                elif t == "reading_en":
                    story.append(Paragraph(item["text"], styles["ReadingEN"]))

                elif t == "reading_pt":
                    story.append(Paragraph(item["text"], styles["ReadingPT"]))

        if "tips" in sec:
            for tip in sec["tips"]:
                story.append(Paragraph(f"• {tip}", styles["ListItem"]))

        story.append(PageBreak())

    # BUILD PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=50,
        rightMargin=50,
        topMargin=60,
        bottomMargin=50
    )

    doc.build(story)


# =====================================================================================
# MAIN PIPELINE
# =====================================================================================

def main():
    if not os.path.exists(INPUT_JSON_PATH):
        print("TranscriptResults.json not found.")
        return

    raw_json = json.load(open(INPUT_JSON_PATH, "r", encoding="utf-8"))

    print("Calling Groq…")
    structured = call_groq_structured(json.dumps(raw_json, ensure_ascii=False))

    filename = structured["filename"]
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
    pdf_path = os.path.join(PDF_OUTPUT_DIR, f"{timestamp}_{filename}.pdf")

    print(f"Generating PDF: {pdf_path}")
    generate_pdf_from_json(pdf_path, structured)

    dest_json = os.path.join(JSON_OUTPUT_DIR, f"{timestamp}_TranscriptResults.json")
    shutil.move(INPUT_JSON_PATH, dest_json)

    print("Process completed successfully.")


if __name__ == "__main__":
    main()
