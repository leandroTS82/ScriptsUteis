import json
import io
from PIL import Image
from google import genai
from engine.project_root import get_project_root

ROOT = get_project_root()

cfg = json.load(
    open(ROOT / "settings" / "gemini_image.json", encoding="utf-8")
)

genai.configure(
    api_key=open(
        ROOT / "secrets" / "gemini_key.txt",
        encoding="utf-8"
    ).read().strip()
)

def generate_image(word: str) -> str:
    prompt = json.load(
        open(ROOT / "prompts" / "gemini" / "image_prompt.json", encoding="utf-8")
    )["template"].replace("{{word}}", word)

    model = genai.GenerativeModel(cfg["model"])
    response = model.generate_content(prompt)

    img = Image.open(io.BytesIO(response.parts[0].inline_data.data))
    output = ROOT / "media" / "images" / f"{word}.png"
    img.save(output)

    return str(output)
