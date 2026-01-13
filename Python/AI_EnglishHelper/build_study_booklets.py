import os
import json
import re
import datetime
from collections import defaultdict

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


# =============================================================================
# CONFIG
# =============================================================================

INPUT_JSON_DIR = r"C:\dev\scripts\ScriptsUteis\Python\extract_reading_practice\pdf_json_dump"
OUTPUT_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\FinalStudyBooklets"

AUTHOR = "Leandro teixeira da silva"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =============================================================================
# NORMALIZAÇÃO E INTELIGÊNCIA TEMÁTICA
# =============================================================================

STOPWORDS = {
    "the", "and", "of", "to", "for", "in", "on", "with",
    "english", "expressions", "vocabulary", "grammar",
    "essential", "general", "study", "practice"
}

ROOT_MAP = {
    "even though": "even",
    "even if": "even",
    "even with": "even",
    "not even": "even",
    "despite": "even",
    "in spite of": "even"
}


def normalize_theme(text: str) -> str:
    t = text.lower()
    for k, v in ROOT_MAP.items():
        if k in t:
            return v

    words = re.findall(r"[a-z]+", t)
    words = [w for w in words if w not in STOPWORDS]

    return words[0] if words else "general"


def extract_signals(pages):
    full_text = "\n".join(p["text"] for p in pages)
    title = pages[0]["text"].split("\n")[0]

    vocab_matches = re.findall(
        r"\n([a-z][a-z\s]{2,})\n",
        full_text.lower()
    )

    return {
        "title": title,
        "root": normalize_theme(title),
        "vocab": set(vocab_matches),
        "full_text": full_text
    }


# =============================================================================
# SEPARAÇÃO DE SEÇÕES
# =============================================================================

SECTION_MARKERS = {
    "vocabulary": "Vocabulary",
    "grammar": "Grammar & Usage",
    "patterns": "Patterns & Collocations",
    "reading": "Reading Practice",
    "study": "Study Tips"
}


def split_sections(text):
    sections = {k: "" for k in SECTION_MARKERS}
    current = None

    for line in text.splitlines():
        line_strip = line.strip()

        for key, marker in SECTION_MARKERS.items():
            if line_strip.startswith(marker):
                current = key
                break
        else:
            if current:
                sections[current] += line + "\n"

    return sections


# =============================================================================
# PDF STYLES (NOMES ÚNICOS — SEM CONFLITO)
# =============================================================================

def styles():
    s = getSampleStyleSheet()

    s.add(ParagraphStyle(
        name="BookTitle",
        fontSize=26,
        alignment=1,
        textColor=colors.HexColor("#0B3C5D"),
        spaceAfter=20
    ))

    s.add(ParagraphStyle(
        name="BookSubtitle",
        fontSize=15,
        alignment=1,
        spaceAfter=10,
        textColor=colors.HexColor("#1F618D")
    ))

    s.add(ParagraphStyle(
        name="BookSection",
        fontSize=20,
        textColor=colors.HexColor("#154360"),
        spaceBefore=18,
        spaceAfter=10
    ))

    s.add(ParagraphStyle(
        name="BookBody",
        fontSize=12,
        leading=18,
        spaceAfter=8
    ))

    s.add(ParagraphStyle(
        name="BookBullet",
        fontSize=12,
        leading=16,
        leftIndent=16,
        spaceAfter=4
    ))

    return s


# =============================================================================
# PDF GERADOR (APOSTILA)
# =============================================================================

def generate_booklet(theme, items):
    s = styles()
    story = []

    date = datetime.datetime.now().strftime("%Y%m%d")
    filename = f"{date}_{theme}_study_booklet.pdf"
    path = os.path.join(OUTPUT_DIR, filename)

    # ---------------- CAPA ----------------
    story.append(Paragraph(theme.upper(), s["BookTitle"]))
    story.append(Paragraph("English Study Booklet", s["BookSubtitle"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Author: {AUTHOR}", s["BookBody"]))
    story.append(Paragraph(f"Generated on: {date}", s["BookBody"]))
    story.append(PageBreak())

    aggregated = defaultdict(list)

    for item in items:
        for k, v in item["sections"].items():
            if v:
                aggregated[k].append(v.strip())

    # ---------------- INTRO ----------------
    story.append(Paragraph("Introduction", s["BookSection"]))
    story.append(Paragraph(
        f"This booklet consolidates essential concepts related to '{theme}', "
        "bringing vocabulary, grammar, patterns, and reading practice into a single, structured study material.",
        s["BookBody"]
    ))
    story.append(PageBreak())

    # ---------------- SEÇÕES ----------------
    for sec, title in [
        ("vocabulary", "Vocabulary Core"),
        ("grammar", "Grammar & Usage"),
        ("patterns", "Patterns & Collocations"),
        ("reading", "Reading Practice"),
        ("study", "Study Guide")
    ]:
        if aggregated.get(sec):
            story.append(Paragraph(title, s["BookSection"]))
            seen = set()

            for block in aggregated[sec]:
                for line in block.splitlines():
                    l = line.strip()

                    if not l or l in seen:
                        continue

                    seen.add(l)

                    if l.startswith("-") or l.startswith("•"):
                        story.append(Paragraph(l, s["BookBullet"]))
                    else:
                        story.append(Paragraph(l, s["BookBody"]))

            story.append(PageBreak())

    # ---------------- BUILD ----------------
    doc = SimpleDocTemplate(
        path,
        pagesize=letter,
        leftMargin=50,
        rightMargin=50,
        topMargin=60,
        bottomMargin=50
    )

    doc.build(story)
    print(f"✔ Apostila gerada: {filename}")


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def main():
    temp_clusters = defaultdict(list)

    for file in os.listdir(INPUT_JSON_DIR):
        if not file.endswith(".json"):
            continue

        with open(os.path.join(INPUT_JSON_DIR, file), encoding="utf-8") as f:
            data = json.load(f)

        signals = extract_signals(data["pages"])
        sections = split_sections(signals["full_text"])

        temp_clusters[signals["root"]].append({
            "file": data["file"],
            "sections": sections,
            "signals": signals
        })

    for theme, items in temp_clusters.items():
        generate_booklet(theme, items)

    print("Processo finalizado com sucesso.")


if __name__ == "__main__":
    main()
