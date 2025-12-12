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

GROQ_API_KEY = "***"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

INPUT_JSON_PATH = "./TranscriptResults.json"
JSON_OUTPUT_DIR = "./json"
PDF_OUTPUT_DIR = "./EnglishReview"

os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)


# =====================================================================================
# SYSTEM PROMPT – CALLAN + NOVAS REGRAS DE FILENAME + REGRAS DE ESTRUTURA
# =====================================================================================

SYSTEM_PROMPT = """
You are an English teacher and instructional designer.

TASK:
Transform the user vocabulary list into a structured CALLAN-STYLE JSON module.
Return ONLY JSON. Do NOT output explanations or markdown.

=====================================================================================
FILENAME RULES
=====================================================================================

1. If the input contains ONLY ONE “palavra_chave”, the filename MUST be a normalized
version of that term:
- remove articles and stopwords (the, a, an, in, on, when, I, etc.)
- extract only key nouns and/or verbs
- convert to lowercase
- replace spaces with underscores
- keep only a–z, 0–9 and underscore
Example:
  "The statuses were adjusted" -> "statuses_adjusted"

2. If the input contains TWO OR MORE terms:
   - extract the essential nouns/verbs from each “palavra_chave”
   - choose 2–4 important category words (status, enum, database, step, error, fix…)
   - compress them into a short filename
   - MUST be human-readable and informative
   - MUST NOT exceed 45 characters

3. NEVER generate generic filenames like:
   "vocabulary_module"
   "training_file"
   "lesson"
   "module_file"

4. ALWAYS produce lowercase, underscore-separated safe identifiers.

=====================================================================================
STRUCTURE RULES
=====================================================================================

ALL sections MUST be inside the array "sections": [].
NEVER output sections at top-level.

WRONG:
"Reading Practice": { ... }

RIGHT:
{
  "title": "Reading Practice",
  "content": [ ... ]
}

If the content is examples, grammar, tips, etc., ALWAYS follow the structure:

{
  "title": "",
  "entries": [ ... ],   <-- Vocabulary
  "content": [ ... ],   <-- Grammar, patterns, reading
  "tips": [ ... ]       <-- Study tips
}

=====================================================================================
OUTPUT STRUCTURE
=====================================================================================

{
  "filename": "generated_filename_here",
  "cover": {
    "title": "",
    "subtitle": "",
    "author": "Leandro teixeira da silva",
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
"""

USER_PROMPT_TEMPLATE = """
Here is the raw vocabulary list. Transform it into the structured CALLAN JSON:

{json_content}
"""


# =====================================================================================
# PARSER ROBUSTO + FALLBACK
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
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    response = requests.post(GROQ_URL, headers=headers, json=body)

    if response.status_code != 200:
        raise Exception(f"Groq error {response.status_code}: {response.text}")

    json_str = response.json()["choices"][0]["message"]["content"].strip()

    with open("last_groq_raw.txt", "w", encoding="utf-8") as f:
        f.write(json_str)

    if not json_str:
        raise Exception("Groq returned empty output.")

    # Tentativa direta
    if json_str.startswith("{"):
        try:
            return json.loads(json_str)
        except:
            pass

    # Extração entre { e }
    try:
        start = json_str.index("{")
        end = json_str.rindex("}") + 1
        cleaned = json_str[start:end]
        return json.loads(cleaned)
    except:
        pass

    # Última tentativa
    try:
        fixed = re.sub(r"([a-zA-Z0-9_]+):", r'"\1":', json_str)
        return json.loads(fixed)
    except:
        raise Exception(
            "Groq returned invalid JSON. Inspect last_groq_raw.txt.\n"
            f"Raw content:\n{json_str}"
        )


# =====================================================================================
# NORMALIZAÇÃO DE SEÇÕES — CORRIGE ERROS DO GROQ
# =====================================================================================

def normalize_sections(structured: dict) -> dict:
    if "sections" not in structured or not isinstance(structured["sections"], list):
        structured["sections"] = []

    known = {
        "Reading Practice",
        "Study Tips",
        "Patterns & Collocations",
        "Grammar & Usage",
        "Vocabulary",
        "Vocabulary List"
    }

    extras = []

    for key in list(structured.keys()):
        if key in known and key != "sections":
            extras.append((key, structured[key]))
            del structured[key]

    for title, obj in extras:
        structured["sections"].append({
            "title": title,
            "content": obj.get("content", []),
            "entries": obj.get("entries", []),
            "tips": obj.get("tips", [])
        })

    return structured


# =====================================================================================
# ESTILOS VISUAIS – CALLAN STYLE
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
# RENDERIZAÇÃO DO PDF
# =====================================================================================

def generate_pdf_from_json(output_path: str, data: dict):
    styles = build_styles()
    story = []

    # CAPA
    cover = data["cover"]
    story.append(Paragraph(cover["title"], styles["CoverTitle"]))
    story.append(Paragraph(cover["subtitle"], styles["CoverSubtitle"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Author: {cover['author']}", styles["Body"]))
    story.append(Paragraph(f"Edition: {cover['edition']}", styles["Body"]))
    story.append(PageBreak())

    # SUMÁRIO
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

    # SEÇÕES
    for sec in data["sections"]:
        story.append(Paragraph(sec["title"], styles["SectionTitle"]))

        # VOCABULARY
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

        # OUTRAS SEÇÕES
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

        # STUDY TIPS
        if "tips" in sec:
            for tip in sec["tips"]:
                story.append(Paragraph(f"• {tip}", styles["ListItem"]))

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
    structured = normalize_sections(structured)

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
