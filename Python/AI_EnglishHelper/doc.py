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
# LISTA DE CATEGORIAS — EMBUTIDA NO PROMPT
# =====================================================================================

CATEGORY_DATA = {
  "Grammar": {
    "name": "Gramática Essencial do Inglês",
    "description": "Domine a gramática inglesa com explicações simples, exemplos claros e dicas práticas para acelerar sua fluência no dia a dia."
  },
  "PhrasalVerbs": {
    "name": "Phrasal Verbs no Dia a Dia",
    "description": "Aprenda phrasal verbs usados por nativos em conversas reais, séries e trabalho — explicado de forma leve e fácil."
  },
  "DailyRoutine": {
    "name": "Inglês para a Rotina Diária",
    "description": "Fale sobre sua rotina em inglês com naturalidade! Vocabulário prático, expressões reais e exemplos do cotidiano."
  },
  "WeatherNature": {
    "name": "Inglês para Falar do Clima e da Natureza",
    "description": "Descubra como descrever clima, tempo e natureza como um nativo — perfeito para conversas, viagens e exames."
  },
  "HomeFurniture": {
    "name": "Vocabulário de Casa e Móveis em Inglês",
    "description": "Aprenda o vocabulário essencial de casa, móveis e objetos do lar para viver ou viajar para países de língua inglesa."
  },
  "HealthMedicine": {
    "name": "Inglês para Saúde: Sintomas, Remédios e Emergências",
    "description": "Fale com confiança sobre saúde, sintomas e emergências — vocabulário fundamental para consultas e viagens."
  },
  "BodyParts": {
    "name": "Partes do Corpo em Inglês — Vocabulário Fácil",
    "description": "Aprenda as partes do corpo em inglês com explicações claras e frases práticas para usar no dia a dia."
  },
  "AccidentsInjuries": {
    "name": "Inglês para Acidentes e Primeiros Socorros",
    "description": "Saiba como descrever acidentes, dores e emergências — inglês útil para situações reais e inesperadas."
  },
  "FoodCooking": {
    "name": "Inglês para Comida, Cozinha e Restaurante",
    "description": "Domine o inglês para cozinha, receitas e restaurantes — ideal para viagens, intercâmbio e amantes da gastronomia."
  },
  "Shopping": {
    "name": "Inglês para Compras: Frases e Vocabulário",
    "description": "Aprenda frases essenciais para comprar roupas, eletrônicos e produtos no exterior com segurança e naturalidade."
  },
  "Transportation": {
    "name": "Inglês para Transporte e Viagens Urbanas",
    "description": "Comunique-se com facilidade em ônibus, metrô, taxi e aeroportos — frases úteis e vocabulário real."
  },
  "EmotionsFeelings": {
    "name": "Como Expressar Emoções em Inglês",
    "description": "Descubra como expressar emoções, sentimentos e sensações com naturalidade — essencial para conversas profundas."
  },
  "BusinessWork": {
    "name": "Inglês para Trabalho e Negócios",
    "description": "Aprenda o inglês profissional usado em reuniões, e-mails, entrevistas e ambiente corporativo global."
  },
  "Hobbies": {
    "name": "Inglês para Hobbies e Tempo Livre",
    "description": "Fale sobre seus hobbies, esportes e atividades favoritas em inglês com fluidez e naturalidade."
  },
  "Travel": {
    "name": "Inglês para Viagem — Frases Essenciais",
    "description": "Frases essenciais para aeroportos, hotéis, restaurantes e turismo — perfeito para qualquer viagem internacional."
  },
  "ExpressionsIdioms": {
    "name": "Expressões e Idioms Essenciais do Inglês",
    "description": "Aprenda expressões idiomáticas que nativos usam o tempo todo — aumente sua naturalidade e fluência rapidamente."
  },
  "GeneralVocabulary": {
    "name": "Vocabulário Geral de Inglês — Palavras do Dia",
    "description": "Amplie seu vocabulário com palavras úteis e fáceis de memorizar, explicadas com exemplos práticos."
  },
  "HouseItems": {
    "name": "Inglês para Itens da Casa — Vocabulário Prático",
    "description": "Aprenda nomes de utensílios domésticos, eletrodomésticos, objetos e cômodos para falar como um nativo."
  },
  "JobInterview": {
    "name": "Inglês para Entrevista de Emprego — Respostas Prontas",
    "description": "Aprenda como responder perguntas de entrevista em inglês, frases-chave, vocabulário profissional e exemplos reais."
  }
}

CATEGORY_JSON = json.dumps(CATEGORY_DATA, indent=2, ensure_ascii=False)


# =====================================================================================
# SYSTEM PROMPT – EXPLÍCITO SOBRE SEÇÕES E CATEGORIAS
# =====================================================================================

SYSTEM_PROMPT = f"""
You are an English teacher and instructional designer.

TASK:
Transform the user vocabulary list into a structured CALLAN-STYLE JSON module.
Return ONLY JSON. Do NOT output explanations or markdown.

===============================================================================
CATEGORIES AVAILABLE FOR CLASSIFICATION
===============================================================================

{CATEGORY_JSON}

CATEGORY RULES:
- Analyze all "palavra_chave".
- Choose 1–3 best matching categories.
- Return:
   "category_keys": ["BusinessWork", "GeneralVocabulary"],
   "category_names": ["Inglês para Trabalho e Negócios", "Vocabulário Geral de Inglês — Palavras do Dia"].
- First category = primary.

===============================================================================
FILENAME RULES
===============================================================================

- Derive from terms and/or categories.
- Use 1–4 key words (nouns/verbs).
- Only lowercase, underscore.
- Max 45 characters.
- DO NOT use generic names like "vocabulary_module", "training_file", etc.

===============================================================================
SECTION STRUCTURE (MANDATORY)
===============================================================================

You MUST return exactly 5 sections in this order:

1) Vocabulary
2) Grammar & Usage
3) Patterns & Collocations
4) Reading Practice
5) Study Tips

The JSON MUST follow this structure:

{{
  "filename": "",
  "category_keys": [],
  "category_names": [],
  "cover": {{
    "title": "",
    "subtitle": "",
    "author": "Leandro teixeira da silva",
    "edition": ""
  }},
  "sections": [
    {{
      "title": "Vocabulary",
      "entries": [
        {{
          "term": "",
          "content": [
            {{ "type": "definition_pt", "text": "" }},
            {{ "type": "explanation_en", "text": "" }},
            {{ "type": "collocations", "items": ["", ""] }},
            {{
              "type": "examples",
              "items": [
                {{ "level": "", "en": "", "pt": "" }}
              ]
            }}
          ]
        }}
      ]
    }},
    {{
      "title": "Grammar & Usage",
      "content": [
        {{ "type": "rule", "text": "" }},
        {{ "type": "examples", "items": [ {{ "en": "", "pt": "" }} ] }}
      ]
    }},
    {{
      "title": "Patterns & Collocations",
      "content": [
        {{ "type": "list", "title": "", "items": ["", ""] }}
      ]
    }},
    {{
      "title": "Reading Practice",
      "content": [
        {{ "type": "reading_en", "text": "" }},
        {{ "type": "reading_pt", "text": "" }}
      ]
    }},
    {{
      "title": "Study Tips",
      "tips": ["", ""]
    }}
  ]
}}

RULES:
- All vocabulary explanations MUST be clear and simple.
- Examples MUST have EN + PT when possible.
- Keep CALLAN style: short, clear, progressive.
"""

USER_PROMPT_TEMPLATE = """
Here is the raw vocabulary list. Transform it into the structured CALLAN JSON:

{json_content}
"""


# =====================================================================================
# CHAMADA AO GROQ – PARSER ROBUSTO
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

    # Tentativa direta
    try:
        return json.loads(json_str)
    except Exception:
        pass

    # Extração do primeiro { ... }
    try:
        cleaned = json_str[json_str.index("{"):json_str.rindex("}") + 1]
        return json.loads(cleaned)
    except Exception:
        pass

    raise Exception("Groq returned invalid JSON. See last_groq_raw.txt.")


# =====================================================================================
# NORMALIZAÇÃO DE SEÇÕES (CASO O GROQ AINDA FUJA DO FORMATO)
# =====================================================================================

def normalize_sections(structured: dict) -> dict:
    if "sections" not in structured or not isinstance(structured["sections"], list):
        structured["sections"] = []

    # Seções conhecidas que podem vir soltas
    known = {
        "Vocabulary",
        "Grammar & Usage",
        "Patterns & Collocations",
        "Reading Practice",
        "Study Tips",
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
            "entries": obj.get("entries", []),
            "content": obj.get("content", []),
            "tips": obj.get("tips", [])
        })

    # Garante que as seções estejam na ordem esperada se existirem
    order = ["Vocabulary", "Grammar & Usage", "Patterns & Collocations", "Reading Practice", "Study Tips"]
    sections_by_title = {s["title"]: s for s in structured["sections"] if "title" in s}
    ordered_sections = []

    for t in order:
        if t in sections_by_title:
            ordered_sections.append(sections_by_title[t])

    # Se algo sobrar com título diferente, mantém no final
    for s in structured["sections"]:
        if s.get("title") not in order:
            ordered_sections.append(s)

    if ordered_sections:
        structured["sections"] = ordered_sections

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
        spaceAfter=10,
        textColor=colors.HexColor("#1F618D")
    ))

    styles.add(ParagraphStyle(
        name="CategoryTag",
        fontSize=12,
        leading=14,
        alignment=1,
        spaceAfter=6,
        textColor=colors.HexColor("#145A32")
    ))

    styles.add(ParagraphStyle(
        name="Body",
        fontSize=12,
        leading=18,
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        name="SectionTitle",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#154360"),
        spaceBefore=20,
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        name="TermTitle",
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#0E6251"),
        spaceBefore=10,
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        name="DefinitionPT",
        fontSize=12,
        leading=18,
        textColor=colors.HexColor("#7E5109"),
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        name="ExplanationEN",
        fontSize=12,
        leading=18,
        textColor=colors.HexColor("#1A5276"),
        spaceAfter=8
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
        textColor=colors.HexColor("#117A65"),
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        name="ReadingEN",
        fontSize=12,
        leading=18,
        textColor=colors.HexColor("#0E6655"),
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        name="ReadingPT",
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#7D6608"),
        spaceAfter=10
    ))

    return styles


# =====================================================================================
# RENDERIZAÇÃO DO PDF
# =====================================================================================

def generate_pdf_from_json(output_path: str, data: dict):
    styles = build_styles()
    story = []

    category_names = data.get("category_names", [])
    main_cat = category_names[0] if category_names else "General Module"
    extra_cats = ", ".join(category_names[1:]) if len(category_names) > 1 else None

    cover = data["cover"]

    # CAPA
    story.append(Paragraph(cover["title"], styles["CoverTitle"]))
    story.append(Paragraph(cover["subtitle"], styles["CoverSubtitle"]))
    story.append(Paragraph(f"Category: {main_cat}", styles["CategoryTag"]))
    if extra_cats:
        story.append(Paragraph(f"Secondary: {extra_cats}", styles["CategoryTag"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Author: {cover['author']}", styles["Body"]))
    if cover.get("edition"):
        story.append(Paragraph(f"Edition: {cover['edition']}", styles["Body"]))
    story.append(PageBreak())

    # SUMÁRIO
    story.append(Paragraph("Table of Contents", styles["SectionTitle"]))
    toc_rows = [[sec.get("title", "")] for sec in data["sections"]]
    toc_table = Table(toc_rows, colWidths=[450])
    toc_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("FONTSIZE", (0,0), (-1,-1), 12),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(toc_table)
    story.append(PageBreak())

    # SEÇÕES
    for sec in data["sections"]:
        title = sec.get("title", "")
        story.append(Paragraph(title, styles["SectionTitle"]))

        # VOCABULARY
        if title.lower().startswith("vocabulary") and "entries" in sec:
            for entry in sec["entries"]:
                story.append(Paragraph(entry.get("term", ""), styles["TermTitle"]))
                for item in entry.get("content", []):
                    t = item.get("type")
                    if t == "definition_pt":
                        story.append(Paragraph(item.get("text", ""), styles["DefinitionPT"]))
                    elif t == "explanation_en":
                        story.append(Paragraph(item.get("text", ""), styles["ExplanationEN"]))
                    elif t == "collocations":
                        for col in item.get("items", []):
                            story.append(Paragraph(f"- {col}", styles["ListItem"]))
                    elif t == "examples":
                        for ex in item.get("items", []):
                            story.append(Paragraph(
                                f"{ex.get('level','')} — {ex.get('en','')} / {ex.get('pt','')}",
                                styles["ExampleItem"]
                            ))

        # OUTRAS SEÇÕES (Grammar, Patterns, Reading)
        if "content" in sec:
            for item in sec["content"]:
                t = item.get("type")
                if t == "rule":
                    story.append(Paragraph(item.get("text", ""), styles["ExplanationEN"]))
                elif t == "examples":
                    for ex in item.get("items", []):
                        story.append(Paragraph(
                            f"{ex.get('en','')} / {ex.get('pt','')}",
                            styles["ExampleItem"]
                        ))
                elif t == "list":
                    story.append(Paragraph(item.get("title", ""), styles["TermTitle"]))
                    for x in item.get("items", []):
                        story.append(Paragraph(f"- {x}", styles["ListItem"]))
                elif t == "reading_en":
                    story.append(Paragraph(item.get("text", ""), styles["ReadingEN"]))
                elif t == "reading_pt":
                    story.append(Paragraph(item.get("text", ""), styles["ReadingPT"]))
                # fallback genérico se vier algo diferente
                elif "text" in item:
                    story.append(Paragraph(item.get("text", ""), styles["Body"]))

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

    with open(INPUT_JSON_PATH, "r", encoding="utf-8") as f:
        raw_json = json.load(f)

    print("Calling Groq…")
    structured = call_groq_structured(json.dumps(raw_json, ensure_ascii=False))
    structured = normalize_sections(structured)

    filename = structured.get("filename", "module")
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
    pdf_path = os.path.join(PDF_OUTPUT_DIR, f"{timestamp}_{filename}.pdf")

    print(f"Generating PDF: {pdf_path}")
    generate_pdf_from_json(pdf_path, structured)

    dest_json = os.path.join(JSON_OUTPUT_DIR, f"{timestamp}_TranscriptResults.json")
    shutil.move(INPUT_JSON_PATH, dest_json)

    print("Process completed successfully.")


if __name__ == "__main__":
    main()
