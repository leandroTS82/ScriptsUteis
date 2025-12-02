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
    Gere APENAS um JSON válido, seguindo EXATAMENTE este formato:

    {{
      "repeat_each": {{"pt": 1, "en": 2}},
      "introducao": "Introdução curta explicando a palavra '{word}'.",
      "nome_arquivos": "Tema_{word}",
      "WORD_BANK": [
        [
          {{ "lang": "en", "text": "{word}", "pause": 1000 }},
          {{ "lang": "pt", "text": "Explique o significado de '{word}'." }},
          {{ "lang": "en", "text": "Crie frase simples com '{word}'.", "pause": 1000 }},
          {{ "lang": "en", "text": "Crie segunda frase curta com '{word}'.", "pause": 1000 }},
          {{ "lang": "en", "text": "Crie frase longa contendo '{word}'.", "pause": 1000 }},
          {{ "lang": "pt", "text": "Mensagem final estilo YouTuber." }}
        ]
      ]
    }}
    """

    response = model.generate_content(prompt)
    raw = response.text.strip()
    json_text = extract_json(raw)

    if not json_text:
        fix_prompt = f"Corrija este conteúdo e retorne APENAS JSON válido:\n\n{raw}"
        fix_response = model.generate_content(fix_prompt)
        json_text = extract_json(fix_response.text.strip())

    if not json_text:
        raise ValueError("❌ ERRO: Gemini não retornou JSON válido.")

    return json.loads(json_text)
