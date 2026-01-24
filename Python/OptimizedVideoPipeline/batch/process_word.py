import os
import sys
import json
import re
import unicodedata

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from engine.text.groq_text_generator import generate_text
from engine.audio.gemini_audio_generator import generate_audio
from engine.image.gemini_image_generator import generate_image
from engine.image.fixed_image_provider import get_fixed_image
from engine.video.moviepy_builder import build_video

def safe_name(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9_-]", "_", text)
    return text.lower()

if len(sys.argv) < 2:
    print("Uso: python process_word.py <palavra>")
    sys.exit(1)

word = sys.argv[1]
safe = safe_name(word)

pipeline_cfg = json.load(open("settings/pipeline.json", encoding="utf-8"))

lesson = generate_text(word)

with open(f"media/videos/{safe}.json", "w", encoding="utf-8") as f:
    json.dump(lesson, f, ensure_ascii=False, indent=2)

audio_path = generate_audio(lesson, safe)

if pipeline_cfg["enable_image_ai"]:
    image_path = generate_image(safe)
else:
    image_path = get_fixed_image()

build_video(safe, image_path, audio_path)

print(f"✅ Vídeo gerado: media/videos/{safe}.mp4")
