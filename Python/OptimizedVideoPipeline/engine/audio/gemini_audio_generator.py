import json
from google import genai
from engine.project_root import get_project_root

ROOT = get_project_root()

cfg = json.load(
    open(ROOT / "settings" / "gemini_audio.json", encoding="utf-8")
)

genai.configure(
    api_key=open(
        ROOT / "secrets" / "gemini_key.txt",
        encoding="utf-8"
    ).read().strip()
)

def generate_audio(lesson: dict, safe_word: str) -> str:
    text = " ".join(item["text"] for item in lesson["WORD_BANK"][0])

    model = genai.GenerativeModel(cfg["model"])
    response = model.generate_content(text)

    output = ROOT / "media" / "audio" / f"{safe_word}.wav"
    with open(output, "wb") as f:
        f.write(response.candidates[0].content.parts[0].inline_data.data)

    return str(output)
