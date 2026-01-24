import os
import sys
import json
import re
import unicodedata

# ============================================================
# GARANTIR ROOT NO PATH
# ============================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from engine.project_root import get_project_root
from engine.text.groq_text_generator import generate_text
from engine.audio.gemini_audio_generator import generate_audio
from engine.image.gemini_image_generator import generate_image
from engine.image.fixed_image_provider import get_fixed_image
from engine.video.moviepy_builder import build_video

# ============================================================
# ROOT
# ============================================================

ROOT = get_project_root()

# ============================================================
# HELPERS
# ============================================================

def safe_name(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9_-]", "_", text)
    return text.lower().strip("_")

# ============================================================
# MAIN
# ============================================================

if len(sys.argv) < 2:
    print("Uso: python process_word.py <palavra>")
    sys.exit(1)

word = sys.argv[1]
safe = safe_name(word)

# ✔ AGORA USANDO ROOT (CORRETO)
pipeline_cfg = json.load(
    open(ROOT / "settings" / "pipeline.json", encoding="utf-8")
)

print(f"🧠 Gerando conteúdo para: {word}")
lesson = generate_text(word)

# Salvar JSON da aula
json_output = ROOT / "media" / "videos" / f"{safe}.json"
with open(json_output, "w", encoding="utf-8") as f:
    json.dump(lesson, f, ensure_ascii=False, indent=2)

print("🎤 Gerando áudio...")
audio_path = generate_audio(lesson, safe)

print("🖼️ Gerando imagem...")
if pipeline_cfg.get("enable_image_ai", True):
    image_path = generate_image(safe)
else:
    image_path = get_fixed_image()

print("🎬 Montando vídeo...")
build_video(safe, image_path, audio_path)

print(f"\n✅ VÍDEO GERADO COM SUCESSO:")
print(f"   📄 JSON : {json_output}")
print(f"   🎧 Áudio: {audio_path}")
print(f"   🖼️ Img  : {image_path}")
print(f"   🎥 MP4  : {ROOT / 'media' / 'videos' / f'{safe}.mp4'}")
