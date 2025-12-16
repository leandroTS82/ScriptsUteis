import json
import re
from gemini_config import GeminiConfig
from utils.known_terms_loader import load_known_terms


def extract_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else None


def generate_lesson_json(word):
    config = GeminiConfig()
    model = config.get_text()

    # -------------------------------------------------
    # 🔹 CARREGA TERMOS JÁ ESTUDADOS (70%)
    # -------------------------------------------------
    known_terms = load_known_terms(
        percentage=0.7,
        max_terms=25,
        verbose=True
    )

    known_terms_block = ""
    if known_terms:
        known_terms_block = (
            "\nKnown vocabulary to PRIORITIZE in examples:\n"
            + ", ".join(known_terms)
            + "\n\nRules:\n"
              "- Prefer using these terms whenever possible\n"
              "- At least 70% of example sentences should reuse them\n"
              "- New words are allowed only if necessary for natural flow\n"
              "- Focus on reinforcement, not novelty\n"
        )

    # -------------------------------------------------
    # 🔹 PROMPT FINAL
    # -------------------------------------------------
    prompt = f"""
You are an English teacher creating study material for Brazilian students.

Your goal is vocabulary reinforcement through repetition.

{known_terms_block}

Generate ONLY a valid JSON following EXACTLY this structure:

{{
  "repeat_each": {{ "pt": 1, "en": 2 }},
  "introducao": "Introdução curta e animada em um estilo jovem teacher YouTuber explicando a palavra '{word}'.",
  "nome_arquivos": "{word}",
  "WORD_BANK": [
    [
      {{ "lang": "en", "text": "{word}", "pause": 1000 }},
      {{ "lang": "pt", "text": "Explique o significado de '{word}' em português." }},
      {{ "lang": "en", "text": "Create a simple A2 sentence using '{word}'.", "pause": 1000 }},
      {{ "lang": "en", "text": "Create another short B1/B2 sentence using '{word}'.", "pause": 1000 }},
      {{ "lang": "en", "text": "Create a slightly longer B2 sentence using '{word}'.", "pause": 1500 }},
      {{ "lang": "pt", "text": "Mensagem final estilo YouTuber incentivando a prática contínua." }}
    ]
  ]
}}

STRICT RULES:
- Output ONLY valid JSON
- Do NOT explain anything outside JSON
- Use natural English
- Prefer known vocabulary when possible
"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    json_text = extract_json(raw)

    if not json_text:
        fix = model.generate_content(
            f"Corrija este JSON e retorne APENAS JSON válido:\n{raw}"
        )
        json_text = extract_json(fix.text.strip())

    lesson = json.loads(json_text)

    # -------------------------------------------------
    # 🔹 METADATA DE CONTROLE (NÃO QUEBRA PIPELINE)
    # -------------------------------------------------
    lesson["_known_terms_context"] = {
        "source": "english_terms.json",
        "percentage": 0.7,
        "max_terms": 25,
        "terms_used": known_terms
    }

    print("✅ [Script] JSON gerado com contexto de vocabulário conhecido.\n")

    return lesson
