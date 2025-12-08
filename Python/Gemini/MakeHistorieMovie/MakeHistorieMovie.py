import os
import sys
import json
from utils.story_image_generator import generate_story_image_or_gif
from utils.story_audio_generator import generate_story_audio
from utils.story_video_builder import build_story_video
from utils.story_theme_extractor import extract_story_theme

# -------------------------------------------------------
# FLAGS DE EXECUÇÃO
# python MakeHistorieMovie.py --onlyImage
# python MakeHistorieMovie.py --onlyAudio
# python MakeHistorieMovie.py
# -------------------------------------------------------
ONLY_IMAGE = "--onlyImage" in sys.argv
ONLY_AUDIO = "--onlyAudio" in sys.argv

if ONLY_IMAGE and ONLY_AUDIO:
    print("❌ Use apenas uma flag: --onlyImage OU --onlyAudio")
    exit(1)

# -------------------------------------------------------
# Caminho do JSON com múltiplas histórias
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

# Criar pastas
os.makedirs("outputs/images", exist_ok=True)
os.makedirs("outputs/gifs", exist_ok=True)
os.makedirs("outputs/audio", exist_ok=True)
os.makedirs("outputs/videos", exist_ok=True)

print(f"📌 {len(stories)} histórias encontradas.\n")

# -------------------------------------------------------
# Processar cada história
# -------------------------------------------------------

for index, story_obj in enumerate(stories, start=1):

    story_text = story_obj.get("text", "").strip()
    if not story_text:
        print(f"⚠ História #{index} está vazia — ignorando.")
        continue

    print(f"\n================ HISTÓRIA {index} ==================")

    # 1) Gerar nome seguro do arquivo baseado no contexto
    safe_name = extract_story_theme(story_text)
    print(f"🧠 Nome do arquivo baseado no contexto: {safe_name}")

    # ---------------------------------------------------
    # SOMENTE IMAGEM
    # ---------------------------------------------------
    if ONLY_IMAGE:
        print("🖼 Modo ONLY IMAGE ativado")
        generate_story_image_or_gif(story_text, safe_name)
        continue

    # ---------------------------------------------------
    # SOMENTE ÁUDIO
    # ---------------------------------------------------
    if ONLY_AUDIO:
        print("🎤 Modo ONLY AUDIO ativado")
        audio_path = f"outputs/audio/{safe_name}.wav"
        generate_story_audio(story_text, audio_path)
        continue

    # ---------------------------------------------------
    # MODO COMPLETO (imagem + áudio + vídeo)
    # ---------------------------------------------------
    print("🎬 Modo padrão: Gerando IMAGEM + ÁUDIO + VÍDEO")

    # 1) Gerar imagem
    media_path = generate_story_image_or_gif(story_text, safe_name)

    # 2) Gerar áudio
    audio_path = f"outputs/audio/{safe_name}.wav"
    generate_story_audio(story_text, audio_path)

    # 3) Gerar vídeo final
    video_path = f"outputs/videos/{safe_name}.mp4"
    build_story_video(
        story_text=story_text,
        media_path=media_path,
        audio_path=audio_path,
        output_path=video_path
    )

    print(f"✔ Vídeo final gerado: {video_path}")

print("\n🎉 Todas as histórias foram processadas!")
