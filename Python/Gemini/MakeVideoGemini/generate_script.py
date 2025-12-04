import json
import re
from gemini_config import GeminiConfig

def extract_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else None

def generate_lesson_json(word):
    config = GeminiConfig()
    model = config.get_text()

    prompt = f"""
    Gere APENAS um JSON válido, seguindo exatamente este formato:

    {{
      "repeat_each": {{"pt": 1, "en": 2}},
      "introducao": "Introdução curta e animada estilo ten teacher YouTuber explicando a palavra '{word}'.",
      "nome_arquivos": "{word}",
      "WORD_BANK": [
        [
          {{ "lang": "en", "text": "{word}", "pause": 1000 }},
          {{ "lang": "pt", "text": "Explique o significado de '{word}'." }},
          {{ "lang": "en", "text": "Crie uma frase simples (A2) com '{word}'.", "pause": 1000 }},
          {{ "lang": "en", "text": "Crie outra frase curta (B2) com '{word}'.", "pause": 1000 }},
          {{ "lang": "en", "text": "Crie uma frase um pouco mais longa (B2) com '{word} (same times add here a small tip in portuguese)'.", "pause": 1000 }},
          {{ "lang": "pt", "text": "Mensagem final estilo YouTuber incentivando a continuar estudando." }}
        ]
      ]
    }}
    """

    response = model.generate_content(prompt)
    raw = response.text.strip()

    json_text = extract_json(raw)
    if not json_text:
        fix = model.generate_content(f"Corrija este JSON e retorne apenas JSON válido:\n{raw}")
        json_text = extract_json(fix.text.strip())

    return json.loads(json_text)
