import os
import sys
import json
import re
import datetime
import requests
from itertools import cycle
from collections import defaultdict

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


# =============================================================================
# GROQ CONFIG
# =============================================================================

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

GROQ_KEYS_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\FilesHelper\secret_tokens_keys\GroqKeys.json"

GROQ_KEYS_FALLBACK = [
    {"name": "lts@gmail.com", "key": "gsk_r***"},
    {"name": "ltsCV@gmail", "key": "gsk_4***"},
    {"name": "butterfly", "key": "gsk_n***"},
    {"name": "??", "key": "gsk_P***"},
    {"name": "MelLuz201811@gmail.com", "key": "gsk_***i"}
]


# =============================================================================
# GEMINI CONFIG (IMAGES)
# =============================================================================

GEMINI_KEY_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\FilesHelper\secret_tokens_keys\google-gemini-key.txt"

GEMINI_IMAGE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"


# =============================================================================
# LOADERS
# =============================================================================

def load_groq_keys():
    if os.path.exists(GROQ_KEYS_PATH):
        try:
            return json.load(open(GROQ_KEYS_PATH, encoding="utf-8"))
        except:
            pass
    return GROQ_KEYS_FALLBACK


def load_gemini_key():
    if not os.path.exists(GEMINI_KEY_PATH):
        raise RuntimeError("Gemini key não encontrada")
    return open(GEMINI_KEY_PATH, encoding="utf-8").read().strip()


GROQ_KEYS = load_groq_keys()
KEY_CYCLE = cycle(GROQ_KEYS)
GEMINI_KEY = load_gemini_key()


# =============================================================================
# API HELPERS
# =============================================================================

def groq_call(system, user):
    key = next(KEY_CYCLE)["key"]
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "temperature": 0.2
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=40)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def generate_gemini_image(theme, output_path):
    prompt = (
        f"Educational illustration for English learners. "
        f"Topic: {theme}. Clean, simple, neutral style, no text."
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    r = requests.post(
        f"{GEMINI_IMAGE_URL}?key={GEMINI_KEY}",
        json=payload,
        timeout=60
    )
    r.raise_for_status()

    data = r.json()
    img_base64 = data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]

    import base64
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(img_base64))


# =============================================================================
# CONFIG
# =============================================================================

INPUT_JSON_DIR = r"C:\dev\scripts\ScriptsUteis\Python\extract_reading_practice\pdf_json_dump"
OUTPUT_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\FinalStudyBooklets_groq"

AUTHOR = "Leandro teixeira da silva"
PROMPTS = json.load(open("./build_study_booklets_groq_prompts.json", encoding="utf-8"))

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =============================================================================
# STYLES
# =============================================================================

def styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle(name="BookTitle", fontSize=28, alignment=1, spaceAfter=24))
    s.add(ParagraphStyle(name="Section", fontSize=20, spaceBefore=18, spaceAfter=12))
    s.add(ParagraphStyle(name="Body", fontSize=12, leading=18, spaceAfter=12))
    return s


# =============================================================================
# PDF GENERATION
# =============================================================================

def generate_booklet(theme, intro, level, blocks):
    s = styles()
    story = []

    date = datetime.datetime.now().strftime("%Y%m%d")
    base_name = f"{date}_{theme.replace(' ', '_')}_study_booklet"
    pdf_path = os.path.join(OUTPUT_DIR, f"{base_name}.pdf")
    img_path = os.path.join(OUTPUT_DIR, f"{base_name}.png")

    generate_gemini_image(theme, img_path)

    story.append(Paragraph(theme.upper(), s["BookTitle"]))
    story.append(Paragraph(f"Level: {level}", s["Body"]))
    story.append(Paragraph(f"Author: {AUTHOR}", s["Body"]))
    story.append(Image(img_path, width=400, height=250))
    story.append(PageBreak())

    story.append(Paragraph("Introduction", s["Section"]))
    story.append(Paragraph(intro, s["Body"]))
    story.append(PageBreak())

    story.append(Paragraph("Reading Content", s["Section"]))

    for block in blocks:
        paragraphs = [p for p in block.split("\n\n") if p.strip()]
        group = [Paragraph(p, s["Body"]) for p in paragraphs]
        story.append(KeepTogether(group))
        story.append(Spacer(1, 16))

    SimpleDocTemplate(pdf_path, pagesize=letter).build(story)
    print(f"✔ Apostila gerada: {os.path.basename(pdf_path)}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    term = sys.argv[1].lower() if len(sys.argv) > 1 else input("Digite o termo: ").lower()

    clusters = defaultdict(list)
    titles = defaultdict(set)

    for file in os.listdir(INPUT_JSON_DIR):
        if not file.endswith(".json"):
            continue

        data = json.load(open(os.path.join(INPUT_JSON_DIR, file), encoding="utf-8"))
        full_text = "\n\n".join(p["text"] for p in data["pages"])
        title = data["pages"][0]["text"].split("\n")[0]

        root = re.findall(r"[a-z]+", title.lower())[0]

        clusters[root].append(full_text)
        titles[root].add(title)

    matched = {k: v for k, v in clusters.items() if term in " ".join(v).lower()}

    if not matched:
        print(f'\nNenhum conteúdo encontrado para: "{term}"\n')
        print("Sugestões disponíveis:\n")

        for k, t in titles.items():
            if term in k:
                print(f"• {k}")
        return

    for raw_theme, blocks in matched.items():
        canonical = groq_call(
            PROMPTS["canonical_theme"]["system"],
            PROMPTS["canonical_theme"]["user"].replace("{{theme}}", raw_theme)
        )

        intro = groq_call(
            PROMPTS["generate_intro"]["system"],
            PROMPTS["generate_intro"]["user"].replace("{{theme}}", canonical)
        )

        level = groq_call(
            PROMPTS["estimate_level"]["system"],
            PROMPTS["estimate_level"]["user"].replace("{{theme}}", canonical)
        )

        generate_booklet(canonical, intro, level, blocks)

    print("Processo finalizado com sucesso.")


if __name__ == "__main__":
    main()
