import os
import sys
import json

from generate_script import generate_lesson_json
from generate_audio import generate_audio
from generate_image import generate_image
from generate_video import build_video

if len(sys.argv) < 2:
    print("Uso: python main.py palavra")
    exit(1)

WORD = sys.argv[1].strip().lower()

print(f"📌 Gerando vídeo para: {WORD}")

os.makedirs("outputs/audio", exist_ok=True)
os.makedirs("outputs/images", exist_ok=True)
os.makedirs("outputs/videos", exist_ok=True)

# ---- 1) JSON ----
lesson = generate_lesson_json(WORD)

# Caminho final do JSON (mesmo da saída do vídeo)
json_path = f"outputs/videos/{WORD}.json"

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(lesson, f, ensure_ascii=False, indent=2)

print(f"✔ JSON salvo em: {json_path}")

# ---- 2) Imagem ----
img_path = f"outputs/images/{WORD}.png"
generate_image(WORD, img_path, mode="landscape")

# ---- 3) TEXTO DO ÁUDIO (incluindo introdução) ----
parts = []

# introdução
parts.append(lesson["introducao"])

# WORD_BANK completo
for group in lesson["WORD_BANK"]:
    for item in group:
        parts.append(item["text"])

# texto final para TTS
text = ". ".join(parts)

audio_path = f"outputs/audio/{WORD}.wav"
generate_audio(text, audio_path, voice="Fenrir")

# ---- 4) Vídeo ----
video_path = f"outputs/videos/{WORD}.mp4"
build_video(WORD, "outputs/images", "outputs/audio", video_path)

print("🎉 VÍDEO FINAL GERADO:")
print(video_path)
print(f"📁 JSON correspondente: {json_path}")
