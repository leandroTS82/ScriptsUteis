import os
import json
import re
import math
import hashlib
from typing import Optional, List, Tuple

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
# CONFIGURAÇÕES DE ENTRADA
# =============================================================================

INPUT_JSON_PATH = (
    r"C:\dev\scripts\ScriptsUteis\Python\Gemini\NewHistory\history\stories.json"
)

IMAGES_DIR = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Images"
)

OUTPUT_PDF_DIR = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\EnglishReview\stories_compilation"
)

CONTROL_JSON_PATH = os.path.join(OUTPUT_PDF_DIR, "processed_stories.json")

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# FLAGS DE COMPORTAMENTO
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

ENABLE_PRE_CLEAN_DUPLICATES = True   # <<< ATIVA / DESATIVA LIMPEZA (1), (2), etc.

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# PARÂMETROS DE PAGINAÇÃO
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

STORIES_PER_PAGE = 2
MAX_PAGES_PER_FILE = 50

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

os.makedirs(OUTPUT_PDF_DIR, exist_ok=True)


# =============================================================================
# NORMALIZAÇÃO
# =============================================================================

def normalize_title(title: str) -> str:
    t = title.strip().lower()
    t = re.sub(r"^\.?trashed\s+", "", t)
    t = re.sub(r"\(\d+\)$", "", t)
    t = re.sub(r"\s+\d+$", "", t)
    return t.strip()


def normalize_title_to_image_name(title: str) -> str:
    t = normalize_title(title)
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", "_", t)
    return f"{t}.png"


def generate_story_hash(title: str, text: str) -> str:
    base = normalize_title(title) + "||" + text.strip().lower()
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


# =============================================================================
# LIMPEZA PRÉVIA DE DUPLICADOS (1), (2)...
# =============================================================================

def pre_clean_stories(stories: List[dict]) -> List[dict]:
    """
    Remove histórias duplicadas com sufixo numérico (1), (2), etc.
    Mantém apenas a primeira ocorrência do título base.
    """
    seen = {}
    cleaned = []

    for story in stories:
        title = story.get("title", "")
        key = normalize_title(title)

        if key in seen:
            continue

        seen[key] = True
        cleaned.append(story)

    removed = len(stories) - len(cleaned)
    print(f"[CLEAN] Histórias removidas por sufixo numérico: {removed}")

    return cleaned


# =============================================================================
# RESOLUÇÃO DE IMAGEM
# =============================================================================

def find_image_for_title(title: str, images_dir: str) -> Optional[str]:
    normalized = normalize_title_to_image_name(title)

    exact = os.path.join(images_dir, normalized)
    if os.path.exists(exact):
        return exact

    if normalized.startswith("trashed_"):
        alt = normalized.replace("trashed_", "", 1)
        alt_path = os.path.join(images_dir, alt)
        if os.path.exists(alt_path):
            return alt_path
    else:
        alt = normalized

    base = alt.replace(".png", "")
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
        fontSize=18,
        leading=22,
        spaceAfter=8,
        textColor=colors.HexColor("#154360")
    ))

    styles.add(ParagraphStyle(
        name="StoryText",
        fontSize=11,
        leading=16,
        spaceAfter=10
    ))

    return styles


# =============================================================================
# RENDERIZAÇÃO
# =============================================================================

def render_story(flow, styles, title, text, image_path):
    flow.append(Paragraph(title, styles["StoryTitle"]))
    flow.append(Spacer(1, 6))

    img = Image(image_path, width=360, height=360, kind="proportional")
    flow.append(img)
    flow.append(Spacer(1, 8))

    flow.append(Paragraph(text, styles["StoryText"]))
    flow.append(Spacer(1, 12))


# =============================================================================
# CONTROLE DE PROCESSAMENTO
# =============================================================================

def load_processed_hashes() -> set:
    if not os.path.exists(CONTROL_JSON_PATH):
        return set()

    with open(CONTROL_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return set(data.get("processed_hashes", []))


def save_processed_hashes(hashes: set):
    with open(CONTROL_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {"processed_hashes": sorted(hashes)},
            f,
            indent=2,
            ensure_ascii=False
        )


# =============================================================================
# GERAÇÃO DE PDFs
# =============================================================================

def generate_pdfs(stories: List[dict]):
    styles = build_styles()
    processed_hashes = load_processed_hashes()
    new_hashes = set()

    valid_stories: List[Tuple[str, str, str]] = []

    for story in stories:
        title = story.get("title", "").strip()
        text = story.get("text", "").strip()

        if not title or not text:
            continue

        story_hash = generate_story_hash(title, text)
        if story_hash in processed_hashes:
            continue

        image_path = find_image_for_title(title, IMAGES_DIR)
        if not image_path:
            print(f"[WARN] Imagem não encontrada: {title}")
            continue

        valid_stories.append((title, text, image_path))
        new_hashes.add(story_hash)

    if not valid_stories:
        print("Nenhuma história nova para processar.")
        return

    stories_per_file = STORIES_PER_PAGE * MAX_PAGES_PER_FILE
    total_files = math.ceil(len(valid_stories) / stories_per_file)

    print(f"\nHistórias novas: {len(valid_stories)}")
    print(f"Arquivos a gerar: {total_files}\n")

    for file_index in range(total_files):
        start = file_index * stories_per_file
        end = start + stories_per_file
        batch = valid_stories[start:end]

        pdf_name = f"stories_compilation_part_{file_index + 1:02d}.pdf"
        pdf_path = os.path.join(OUTPUT_PDF_DIR, pdf_name)

        flow = []

        for i in range(0, len(batch), STORIES_PER_PAGE):
            page_stories = batch[i:i + STORIES_PER_PAGE]

            for title, text, image_path in page_stories:
                render_story(flow, styles, title, text, image_path)

            # PageBreak SOMENTE se ainda houver histórias depois
            if i + STORIES_PER_PAGE < len(batch):
                flow.append(PageBreak())

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=50,
            bottomMargin=40
        )

        doc.build(flow)
        print(f"[OK] PDF gerado: {pdf_name}")

        save_processed_hashes(processed_hashes.union(new_hashes))


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

    print(f"Histórias totais no JSON (original): {len(stories)}")

    if ENABLE_PRE_CLEAN_DUPLICATES:
        stories = pre_clean_stories(stories)

    print(f"Histórias após limpeza: {len(stories)}")
    print("Processando histórias novas...\n")

    generate_pdfs(stories)

    print("\nProcesso concluído com sucesso.")


if __name__ == "__main__":
    main()
