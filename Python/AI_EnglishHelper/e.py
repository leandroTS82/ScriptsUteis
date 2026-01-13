import sys
import json
import requests
from itertools import cycle
import os

# =====================================================================
# GROQ CONFIG — MULTI KEY (JSON FIRST, INLINE FALLBACK)
# =====================================================================

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

GROQ_KEYS_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\FilesHelper\secret_tokens_keys\GroqKeys.json"

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in os.sys.path:
    os.sys.path.insert(0, BASE_DIR)

from groq_keys_loader import GROQ_KEYS

key_cycle = cycle(GROQ_KEYS)

# =====================================================================
# UTILS
# =====================================================================

def clear_console():
    os.system("cls" if os.name == "nt" else "clear")

# =====================================================================
# GROQ CALL (ROTATION + JSON HARD PARSE)
# =====================================================================

def call_groq(prompt: str) -> dict:
    key_info = next(key_cycle)

    headers = {
        "Authorization": f"Bearer {key_info['key']}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }

    res = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
    res.raise_for_status()

    raw = res.json()["choices"][0]["message"]["content"]
    json_text = raw[raw.find("{"): raw.rfind("}") + 1]

    data = json.loads(json_text)
    data["_key_used"] = key_info["name"]
    return data

# =====================================================================
# PROMPT BUILDER — FORMATO RÍGIDO
# =====================================================================

def build_prompt(term: str, context: str) -> str:
    return f"""
You are a senior English teacher with a young, charismatic, and friendly teaching style,
helping a Brazilian student build ACTIVE English.

Teaching style:
- Modern mentor, not classroom teacher
- Clear, human, practical
- Make the student think: "Ah, agora fez sentido"

Context so far:
{context}

Input concept or sentence:
"{term}"

Return ONLY valid JSON.
DO NOT repeat fields.
DO NOT change field names.
DO NOT add extra text.

{{
  "corrected_sentence": "...",

  "translation_pt": "...",
  "meaning_pt": "...",

  "why_this_is_better": "...",
  "explanation_pt": "...",

  "daily_usage_examples_en": [
    "...",
    "...",
    "..."
  ],

  "formal_version_developer": "...",

  "grammar_focus": "...",

  "timeline": {{
    "present_positive": "...",
    "present_negative": "...",
    "past_positive": "...",
    "past_negative": "...",
    "future_positive": "...",
    "future_negative": "...",
    "question_positive": "...",
    "question_negative": "..."
  }},

  "learning_tip_pt": "Dica curta em português para melhorar o inglês ativo"
}}
"""

# =====================================================================
# PREVIEW RENDER — FORMATO FIXO
# =====================================================================

def render_preview(data: dict):
    print("\n════════════════════════════════════════")
    print("        PREVIEW ENRIQUECIDO")
    print("════════════════════════════════════════\n")

    print(f"Key usada: {data.get('_key_used')}\n")

    print("Frase melhorada:")
    print(f"  {data['corrected_sentence']}\n")

    print("Tradução:")
    print(f"  {data['translation_pt']}\n")

    print("Significado:")
    print(f"  {data['meaning_pt']}\n")

    print("Por que ficou melhor:")
    print(f"  {data['why_this_is_better']}\n")

    print("Explicação clara (PT):")
    print(f"  {data['explanation_pt']}\n")

    print("Como os americanos usam no dia a dia:")
    for ex in data["daily_usage_examples_en"]:
        print(f"  - {ex}")

    print("\nVersão estritamente formal (developer):")
    print(f"  {data['formal_version_developer']}\n")

    print("Foco gramatical prático:")
    print(f"  {data['grammar_focus']}\n")

    print("Linha do tempo verbal:\n")
    timeline_order = [
        "present_positive",
        "present_negative",
        "past_positive",
        "past_negative",
        "future_positive",
        "future_negative",
        "question_positive",
        "question_negative"
    ]

    for key in timeline_order:
        print(f"  {key.replace('_', ' ').title():<25}: {data['timeline'][key]}")

    print("\nDica para inglês ativo:")
    print(f"  {data['learning_tip_pt']}")

    print("\n════════════════════════════════════════\n")

# =====================================================================
# MAIN LOOP
# =====================================================================

def main():
    context = ""
    current_term = None

    while True:
        if not current_term:
            current_term = input("Digite o termo/frase inicial: ").strip()
            if not current_term:
                print("Encerrando.")
                return

        prompt = build_prompt(current_term, context)
        result = call_groq(prompt)

        render_preview(result)

        context += f"\n{result['corrected_sentence']}"

        action = input(
            "\nDigite:\n"
            "m = gerar outro preview diferente (mesmo termo)\n"
            "s = sair\n"
            "ou digite o próximo termo: "
        ).strip().lower()

        if action == "s":
            break
        elif action == "m":
            continue
        else:
            current_term = action
            clear_console()

if __name__ == "__main__":
    main()
