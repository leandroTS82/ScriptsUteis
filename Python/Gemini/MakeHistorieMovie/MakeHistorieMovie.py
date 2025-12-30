import os
import sys
import json
import shutil

from utils.story_image_generator import generate_story_image_or_gif
from utils.story_audio_generator import generate_story_audio
from utils.story_video_builder import build_story_video
from utils.story_theme_extractor import extract_story_theme

# python MakeHistorieMovie.py                                         
# -------------------------------------------------------
# FLAGS
# -------------------------------------------------------
ONLY_IMAGE = "--onlyImage" in sys.argv
ONLY_AUDIO = "--onlyAudio" in sys.argv

if ONLY_IMAGE and ONLY_AUDIO:
    print("❌ Use apenas uma flag: --onlyImage OU --onlyAudio")
    exit(1)

# -------------------------------------------------------
# Caminho do JSON
# -------------------------------------------------------
stories_file = r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeHistorieMovie\history\stories.json"

if not os.path.exists(stories_file):
    print(f"❌ Arquivo não encontrado: {stories_file}")
    exit(1)

print("📘 Lendo arquivo JSON de histórias...")

with open(stories_file, "r", encoding="utf-8") as f:
    data = json.load(f)

stories = data.get("stories", [])

if not stories:
    print("❌ Nenhuma história encontrada no JSON.")
    exit(1)


# -------------------------------------------------------
# Pastas obrigatórias
# -------------------------------------------------------
os.makedirs("outputs/images", exist_ok=True)
os.makedirs("outputs/gifs", exist_ok=True)
os.makedirs("outputs/audio", exist_ok=True)
os.makedirs("outputs/videos", exist_ok=True)

AUDIO_DEST = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Audios para estudar inglês\Histories"
VIDEO_DEST = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Histories\20251229"

os.makedirs(AUDIO_DEST, exist_ok=True)
os.makedirs(VIDEO_DEST, exist_ok=True)

print(f"📌 {len(stories)} histórias encontradas.\n")


# -------------------------------------------------------
# PROCESSAMENTO
# -------------------------------------------------------
for index, story_obj in enumerate(stories, start=1):

    story_text = story_obj.get("text", "").strip()
    provided_title = story_obj.get("title", "").strip()

    if not story_text:
        print(f"⚠ História {index} está vazia — ignorando.")
        continue

    print(f"\n================ HISTÓRIA {index} ==================")

    # Nome do arquivo seguro baseado no título
    safe_name = extract_story_theme(provided_title or story_text)
    print(f"🧠 Nome seguro do arquivo: {safe_name}")

    # Título final
    final_title = provided_title if provided_title else safe_name.replace("_", " ").title()

    # -------------------------------------------------------
    # SOMENTE IMAGEM
    # -------------------------------------------------------
    if ONLY_IMAGE:
        print("🖼 ONLY IMAGE MODE")
        generate_story_image_or_gif(story_text, safe_name, final_title)
        continue

    # -------------------------------------------------------
    # SOMENTE ÁUDIO
    # -------------------------------------------------------
    if ONLY_AUDIO:
        print("🎤 ONLY AUDIO MODE")
        audio_path = f"outputs/audio/{safe_name}.wav"
        generate_story_audio(story_text, audio_path)
        shutil.copy(audio_path, AUDIO_DEST)
        continue

    # -------------------------------------------------------
    # MODE COMPLETO
    # -------------------------------------------------------
    print("🎬 MODO COMPLETO: IMAGE + AUDIO + VIDEO")

    # 1) Imagem
    media_path = generate_story_image_or_gif(story_text, safe_name, final_title)

    # 2) Áudio
    audio_path = f"outputs/audio/{safe_name}.wav"
    generate_story_audio(story_text, audio_path)

    # 3) Vídeo
    video_path = f"outputs/videos/{safe_name}.mp4"
    build_story_video(
        story_text=story_text,
        media_path=media_path,
        audio_path=audio_path,
        output_path=video_path
    )

    # Mover os arquivos para as pastas finais
    shutil.copy(audio_path, AUDIO_DEST)
    shutil.copy(video_path, VIDEO_DEST)

    print(f"✔ Conteúdo final gerado:\n   - Áudio → {AUDIO_DEST}\n   - Vídeo → {VIDEO_DEST}")

print("\n🎉 Todas as histórias foram processadas com sucesso!")
