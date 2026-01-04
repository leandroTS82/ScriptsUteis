import os
import json
import re
from typing import Optional

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

INPUT_JSON_PATH = (
    r"C:\dev\scripts\ScriptsUteis\Python\Gemini\NewHistory\history\stories.json"
)

IMAGES_DIR = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS"
    r"\LTS SP Site - VideosGeradosPorScript\Images"
)

OUTPUT_PDF_PATH = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS"
    r"\LTS SP Site - Documentos de estudo de inglês\EnglishReview\stories_compilation.pdf"
)

os.makedirs(os.path.dirname(OUTPUT_PDF_PATH), exist_ok=True)


# =============================================================================
# NORMALIZAÇÃO DE TÍTULO → NOME DE IMAGEM
# =============================================================================

def normalize_title_to_image_name(title: str) -> str:
    """
    ".Trashed 1769699729 202512151927 Affordable Expensive Vocab"
    → "trashed_1769699729_202512151927_affordable_expensive_vocab.png"
    """
    t = title.strip()

    # remove ponto inicial
    t = t.lstrip(".")

    # lowercase
    t = t.lower()

    # remove caracteres especiais
    t = re.sub(r"[^\w\s]", "", t)

    # normaliza espaços
    t = re.sub(r"\s+", "_", t)

    return f"{t}.png"


# =============================================================================
# RESOLUÇÃO ROBUSTA DE IMAGEM
# =============================================================================

def find_image_for_title(title: str, images_dir: str) -> Optional[str]:
    """
    Estratégia:
    1) Match exato
    2) Match sem 'trashed_'
    3) Match por tokens relevantes
    """

    normalized = normalize_title_to_image_name(title)

    # 1️⃣ Match exato
    exact_path = os.path.join(images_dir, normalized)
    if os.path.exists(exact_path):
        return exact_path

    # 2️⃣ Remove prefixo 'trashed_'
    if normalized.startswith("trashed_"):
        alt_name = normalized.replace("trashed_", "", 1)
        alt_path = os.path.join(images_dir, alt_name)
        if os.path.exists(alt_path):
            return alt_path
    else:
        alt_name = normalized

    # 3️⃣ Match por tokens significativos
    base = alt_name.replace(".png", "")
    tokens = [
        t for t in base.split("_")
        if len(t) > 3 and not t.isdigit()
    ]

    for file in os.listdir(images_dir):
        fname = file.lower()

        if not fname.endswith(".png"):
            continue

        if all(token in fname for token in tokens):
            return os.path.join(images_dir, file)

    return None


# =============================================================================
# ESTILOS DO PDF
# =============================================================================

def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="StoryTitle",
        fontSize=20,
        leading=24,
        spaceAfter=12,
        textColor=colors.HexColor("#154360")
    ))

    styles.add(ParagraphStyle(
        name="StoryText",
        fontSize=12,
        leading=18,
        spaceAfter=12
    ))

    return styles


# =============================================================================
# GERAÇÃO DO PDF
# =============================================================================

def generate_pdf(stories: list):
    styles = build_styles()
    flow = []

    missing_images = []

    for idx, story in enumerate(stories, start=1):
        title = story.get("title", "").strip()
        text = story.get("text", "").strip()

        if not title or not text:
            print(f"[WARN] História inválida (sem title ou text) — índice {idx}")
            continue

        image_path = find_image_for_title(title, IMAGES_DIR)

        if not image_path:
            print(f"[WARN] Imagem não encontrada, pulando história: {title}")
            missing_images.append(title)
            continue

        # TÍTULO
        flow.append(Paragraph(title, styles["StoryTitle"]))
        flow.append(Spacer(1, 10))

        # IMAGEM
        img = Image(image_path, width=400, height=400, kind="proportional")
        flow.append(img)
        flow.append(Spacer(1, 14))

        # TEXTO
        flow.append(Paragraph(text, styles["StoryText"]))

        flow.append(PageBreak())

    if not flow:
        raise RuntimeError("Nenhuma história válida foi renderizada no PDF.")

    doc = SimpleDocTemplate(
        OUTPUT_PDF_PATH,
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=60,
        bottomMargin=50
    )

    doc.build(flow)

    print("\n==================== RESUMO ====================")
    print(f"Total de histórias processadas: {len(stories)}")
    print(f"Histórias sem imagem: {len(missing_images)}")

    if missing_images:
        print("\nLista de histórias sem imagem:")
        for t in missing_images:
            print(f" - {t}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    if not os.path.exists(INPUT_JSON_PATH):
        raise FileNotFoundError(f"JSON não encontrado: {INPUT_JSON_PATH}")

    with open(INPUT_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    stories = data.get("stories", [])

    if not stories:
        raise ValueError("Nenhuma história encontrada no JSON.")

    print(f"Histórias encontradas: {len(stories)}")
    print("Validando imagens e gerando PDF...\n")

    generate_pdf(stories)

    print("\nPDF gerado com sucesso:")
    print(OUTPUT_PDF_PATH)


if __name__ == "__main__":
    main()
