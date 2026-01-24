import json
import io
from pathlib import Path
from PIL import Image
from google import genai
from google.genai import types
from engine.project_root import get_project_root

# ============================================================
# ROOT
# ============================================================

ROOT = get_project_root()

# ============================================================
# CONFIG
# ============================================================

cfg = json.load(
    open(ROOT / "settings" / "gemini_image.json", encoding="utf-8")
)

API_KEY_PATH = Path(cfg["api_key_path"])

if not API_KEY_PATH.exists():
    raise FileNotFoundError(f"Gemini API key não encontrada: {API_KEY_PATH}")

API_KEY = API_KEY_PATH.read_text(encoding="utf-8").strip()

client = genai.Client(api_key=API_KEY)

# ============================================================
# MAIN
# ============================================================

def generate_image(word: str) -> str:
    prompt = json.load(
        open(ROOT / "prompts" / "gemini" / "image_prompt.json", encoding="utf-8")
    )["template"].replace("{{word}}", word)

    response = client.models.generate_content(
        model=cfg["model"],
        contents=prompt,
        config=types.GenerateContentConfig(
            image_config=types.ImageConfig(
                aspect_ratio=cfg.get("aspect_ratio", "16:9")
            )
        ),
    )

    raw_bytes = None
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            raw_bytes = part.inline_data.data

    if raw_bytes is None:
        raise RuntimeError("Gemini não retornou imagem.")

    img = Image.open(io.BytesIO(raw_bytes))

    output = ROOT / "media" / "images" / f"{word}.png"
    img.save(output)

    return str(output)
