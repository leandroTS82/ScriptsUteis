import os
import json
import requests

from generate_thumbnail import generate_thumbnail

# ==================================================
# CONFIG
# ==================================================

GROQ_API_KEY = open(
    r"C:\dev\scripts\ScriptsUteis\Python\secret_tokens_keys\groq_api_key.txt",
    "r",
    encoding="utf-8"
).read().strip()

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-20b"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.join(BASE_DIR, "samples")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
FONTS_DIR = os.path.join(BASE_DIR, "fonts")

FONT_MAP = {
    "bebas_neue": "BebasNeue-Regular.ttf",
    "montserrat": "Montserrat-Bold.ttf",
    "anton": "Anton-Regular.ttf"
}

SYSTEM_PROMPT = """You are a YouTube thumbnail copywriter and visual designer.
Generate short, bold, click-worthy thumbnails for young audiences."""

# ==================================================
# GROQ CALL
# ==================================================

def call_groq(video_json):
    prompt = f"""
You are a YouTube thumbnail copywriter.

Your task:
Create a SHORT, INVITING thumbnail text that summarizes the MAIN IDEA
of the video description, as a natural invitation to click.

Language:
- Portuguese (Brazil)

Tone:
- Conversational
- Natural
- Curious
- Not generic
- Not educational-sounding

Rules:
- MAX 6 words total
- ALL CAPS
- No emojis
- No generic hooks like:
  "VOCÊ SABIA", "APRENDA", "DICA", "INGLÊS FÁCIL"

The text should feel like:
- a subtle invitation
- a moment of realization
- a hint of what the learner will understand

Good examples of style (DO NOT copy literally):
- "QUANDO A FICHA CAI"
- "DO JEITO CERTO"
- "NA HORA CERTA"
- "QUANDO FAZ SENTIDO"
- "NO USO REAL"
- "NA PRÁTICA"

Structure:
- Title = short inviting phrase that reflects the description
- Highlight = the English term (or key part of it)

Layout:
- Text positioned TOP-LEFT
- Title smaller
- Highlight BIG and clear

Return ONLY valid JSON:

{{
  "title": "",
  "highlight": "",
  "font": "bebas_neue | montserrat | anton",
  "text_color": "#FFFFFF",
  "highlight_color": "#7C3AED",
  "stroke_color": "#000000"
}}

Context:
Video title: {video_json["title"]}
Description: {video_json["description"]}
Tags: {", ".join(video_json.get("tags", []))}
"""

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(GROQ_URL, headers=headers, json=payload)
    response.raise_for_status()

    text = response.json()["choices"][0]["message"]["content"]

    start = text.find("{")
    end = text.rfind("}") + 1
    return json.loads(text[start:end])

# ==================================================
# MAIN
# ==================================================

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for file in os.listdir(SAMPLES_DIR):
        if not file.endswith(".json"):
            continue

        base = os.path.splitext(file)[0]

        json_path = os.path.join(SAMPLES_DIR, file)
        image_path = os.path.join(SAMPLES_DIR, base + ".png")

        if not os.path.exists(image_path):
            print(f"⏭ Imagem não encontrada: {base}")
            continue

        data = json.load(open(json_path, "r", encoding="utf-8"))

        print(f"🎨 Gerando thumbnail via Groq: {base}")
        design = call_groq(data)

        font_file = FONT_MAP.get(design["font"], FONT_MAP["bebas_neue"])
        font_path = os.path.join(FONTS_DIR, font_file)

        output_path = os.path.join(OUTPUT_DIR, base + "_thumb.png")

        generate_thumbnail(
            image_path=image_path,
            output_path=output_path,
            title=design["title"],
            highlight=design["highlight"],
            font_path=font_path,
            text_color=design["text_color"],
            highlight_color=design["highlight_color"],
            stroke_color=design["stroke_color"]
        )

        print(f"✔ Thumbnail criada: {output_path}")

if __name__ == "__main__":
    main()
