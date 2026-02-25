"""
SCRIPT ISOLADO — GERA JSONs DO YOUTUBE FALTANTES

O que faz:
- Lê history_state.json
- Identifica histórias marcadas como processadas (true)
- Verifica se o vídeo existe
- Verifica se o JSON do YouTube existe
- Se não existir, gera o JSON automaticamente

⚠ NÃO gera áudio, imagem ou vídeo
⚠ NÃO altera history_state.json
"""

import json
import os
import sys
from utils.slugify import slugify
from utils.prompt_manager import PromptManager
from utils.youtube_json_generator import generate_youtube_json


# ==================================================
# PATHS FIXOS
# ==================================================

BASE_VIDEO_PATH = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Histories\NewHistory"
)

SUBTITLES_PATH = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Histories\NewHistory\subtitles"
)

HISTORY_STATE_PATH = "history/history_state.json"
STORIES_PATH = "history/stories.json"


# ==================================================
# INIT
# ==================================================

print("🔍 Verificando JSONs do YouTube ausentes...\n")

prompts = PromptManager()

if not os.path.exists(HISTORY_STATE_PATH):
    print("❌ history_state.json não encontrado.")
    sys.exit(1)

if not os.path.exists(STORIES_PATH):
    print("❌ stories.json não encontrado.")
    sys.exit(1)

state = json.load(open(HISTORY_STATE_PATH, encoding="utf-8"))
stories = json.load(open(STORIES_PATH, encoding="utf-8"))["stories"]

# Indexação rápida por slug
stories_by_slug = {
    slugify(story["title"]): story
    for story in stories
}

generated = 0
skipped = 0


# ==================================================
# PROCESSAMENTO
# ==================================================

for slug, processed in state.items():

    if not processed:
        continue

    video_path = f"{BASE_VIDEO_PATH}\\{slug}.mp4"
    json_path = f"{BASE_VIDEO_PATH}\\{slug}.json"
    srt_path = f"{SUBTITLES_PATH}\\{slug}.en.srt"

    if not os.path.exists(video_path):
        print(f"⏭ Vídeo não encontrado: {slug}")
        skipped += 1
        continue

    if os.path.exists(json_path):
        print(f"✅ JSON já existe: {slug}")
        skipped += 1
        continue

    story = stories_by_slug.get(slug)

    if not story:
        print(f"⚠ História não encontrada em stories.json: {slug}")
        skipped += 1
        continue

    print(f"🛠 Gerando JSON YouTube: {slug}")

    try:
        generate_youtube_json(
            output_path=video_path,
            title=story["title"],
            description=prompts.youtube_description(
                story["title"],
                story["text"]
            ),
            tags=prompts.youtube_tags(story["text"]),
            playlist=prompts.youtube_playlist()
        )

        generated += 1

    except Exception as e:
        print(f"❌ Erro ao gerar JSON para {slug}")
        print(str(e))
        skipped += 1


# ==================================================
# FINAL
# ==================================================

print("\n RESUMO FINAL")
print(f"✔ JSONs criados: {generated}")
print(f"⏭ Ignorados / existentes / erro: {skipped}")
print("\n  Script finalizado.")
