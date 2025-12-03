import os
import sys
import json
import re
import unicodedata

from generate_script import generate_lesson_json
from generate_audio_text import build_tts_text
from generate_audio import generate_audio
from generate_image import generate_image
from generate_video import build_video


# ------------------------------------------------------
#  Sanitização do nome da word/frase
# ------------------------------------------------------
def sanitize_filename(text):
    # remover acentos
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode()

    # lower
    text = text.lower().strip()

    # retirar caracteres especiais indesejados
    text = re.sub(r"[^a-z0-9\s_-]", "", text)

    # trocar espaços por _
    text = re.sub(r"\s+", "_", text)

    # remover múltiplos _ consecutivos
    text = re.sub(r"_+", "_", text)

    return text.strip("_")  # remover underscores no início/fim


# ------------------------------------------------------
# SCRIPT PRINCIPAL
# ------------------------------------------------------
if len(sys.argv) < 2:
    print("Uso: python main.py palavra_ou_frase")
    exit(1)

RAW_WORD = sys.argv[1].strip()
SAFE_NAME = sanitize_filename(RAW_WORD)

if not SAFE_NAME:
    print("Erro: palavra inválida após sanitização.")
    exit(1)

print(f"📌 Gerando vídeo para: {RAW_WORD}")
print(f"➡ Nome seguro do arquivo: {SAFE_NAME}")

os.makedirs("outputs/audio", exist_ok=True)
os.makedirs("outputs/images", exist_ok=True)
os.makedirs("outputs/videos", exist_ok=True)

# ----------------------------------------------------
# 1) JSON Gerado
# ----------------------------------------------------
lesson = generate_lesson_json(RAW_WORD)

# Atualizar nome_arquivos dentro do JSON → MUITO IMPORTANTE
lesson["nome_arquivos"] = SAFE_NAME

json_path = f"outputs/videos/{SAFE_NAME}.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(lesson, f, ensure_ascii=False, indent=2)

print(f"✔ JSON salvo em: {json_path}")

# ----------------------------------------------------
# 2) Texto para o TTS
# ----------------------------------------------------
tts_text = build_tts_text(lesson)

# ----------------------------------------------------
# 3) Imagem
# ----------------------------------------------------
img_path = f"outputs/images/{SAFE_NAME}.png"
generate_image(RAW_WORD, img_path, mode="landscape")

# ----------------------------------------------------
# 4) Áudio
# ----------------------------------------------------
audio_path = f"outputs/audio/{SAFE_NAME}.wav"
generate_audio(tts_text, audio_path, voice="Fenrir")

# ----------------------------------------------------
# 5) Vídeo final
# ----------------------------------------------------
video_path = f"outputs/videos/{SAFE_NAME}.mp4"
build_video(SAFE_NAME, "outputs/images", "outputs/audio", video_path)

print("🎉 VÍDEO FINAL GERADO:")
print(video_path)
print(f"📁 JSON correspondente: {json_path}")
