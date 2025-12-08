import os
import sys
from utils.story_image_generator import generate_story_image_or_gif
from utils.story_audio_generator import generate_story_audio
from utils.story_video_builder import build_story_video
from utils.story_theme_extractor import extract_story_theme

# -------------------------------------------
# Caminho fixo (pode modificar se desejar)
# -------------------------------------------
story_file = r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeHistorieMovie\history\my_story.txt"

if not os.path.exists(story_file):
    print(f"❌ Arquivo não encontrado: {story_file}")
    exit(1)

print("📘 Lendo arquivo de história...")
with open(story_file, "r", encoding="utf-8") as f:
    story_text = f.read().strip()

if not story_text:
    print("❌ Arquivo está vazio!")
    exit(1)

# ---------------------------------------------------
# 1) Extração automática do nome (tema do vídeo)
# ---------------------------------------------------
print("🧠 Extraindo tema da história...")
safe_name = extract_story_theme(story_text)
print(f"📌 Nome do arquivo baseado no contexto: {safe_name}")

# Ensure directories
os.makedirs("outputs/images", exist_ok=True)
os.makedirs("outputs/gifs", exist_ok=True)
os.makedirs("outputs/audio", exist_ok=True)
os.makedirs("outputs/videos", exist_ok=True)

# -------------------------------------------
# 2) GERAR IMAGEM OU GIF (Priorizar Groq)
# -------------------------------------------
media_path = generate_story_image_or_gif(story_text, safe_name)

# -------------------------------------------
# 3) GERAR ÁUDIO
# -------------------------------------------
audio_path = f"outputs/audio/{safe_name}.wav"
generate_story_audio(story_text, audio_path)

# -------------------------------------------
# 4) GERAR VÍDEO FINAL
# -------------------------------------------
video_path = f"outputs/videos/{safe_name}.mp4"
build_story_video(
    story_text=story_text,
    media_path=media_path,
    audio_path=audio_path,
    output_path=video_path
)

print("🎉 VÍDEO FINAL GERADO:")
print(video_path)
