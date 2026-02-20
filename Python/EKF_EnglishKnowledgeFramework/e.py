import sys
import json
import requests
from itertools import cycle
import os
import time
from shutil import get_terminal_size

# =====================================================================
# GROQ CONFIG
# =====================================================================

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in os.sys.path:
    os.sys.path.insert(0, BASE_DIR)

from groq_keys_loader import GROQ_KEYS

key_cycle = cycle(GROQ_KEYS)

# =====================================================================
# ANSI COLORS
# =====================================================================

GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

# =====================================================================
# UX HELPERS
# =====================================================================

def clear_console():
    os.system("cls" if os.name == "nt" else "clear")

def print_header():
    print("\n" + CYAN + BOLD +
          "════════ ACTIVE ENGLISH BUILDER — ADVANCED MODE ════════"
          + RESET + "\n")

def loading_indicator():
    print(YELLOW + "⏳ Analisando estrutura gramatical...\n" + RESET)

# =====================================================================
# GROQ CALL
# =====================================================================

def call_groq(prompt: str, retries=2) -> dict:
    for attempt in range(retries):
        try:
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

            start = raw.find("{")
            end = raw.rfind("}") + 1
            json_text = raw[start:end]

            data = json.loads(json_text)
            data["_key_used"] = key_info["name"]
            return data

        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
                continue
            raise e

# =====================================================================
# PROMPT BUILDER EXPANDIDO
# =====================================================================

def build_prompt(term: str, context: str) -> str:
    return f"""
You are a senior English grammar analyst helping a Brazilian developer
build STRUCTURAL English for business and tech communication.

Focus on:
- Auxiliary logic
- Verb structure
- Inversion
- Agreement forms
- Modal usage (would, could, should, might, etc.)
- Perfect forms (have been, had been, will have been)

Context:
{context}

Input:
"{term}"

Return ONLY valid JSON with EXACT structure.

{{
  "corrected_sentence": "...",

  "translation_pt": "...",
  "meaning_pt": "...",

  "why_this_is_better": "...",
  "explanation_pt": "...",

  "agreement": {{
     "positive": "...",
     "negative": "..."
  }},

  "daily_usage_examples_en": [
    "...",
    "...",
    "..."
  ],

  "formal_version_developer": "...",

  "grammar_focus": "...",

  "timeline": {{
    "present_simple": "...",
    "present_continuous": "...",
    "present_perfect": "...",
    "past_simple": "...",
    "past_continuous": "...",
    "past_perfect": "...",
    "future_will": "...",
    "future_going_to": "...",
    "conditional_would": "...",
    "modal_can": "...",
    "modal_could": "...",
    "modal_should": "...",
    "modal_might": "...",
    "passive_voice": "...",
    "perfect_continuous": "...",
    "question_form": "...",
    "negative_form": "..."
  }},

  "learning_tip_pt": "Dica curta"
}}
"""

# =====================================================================
# TABLE RENDER
# =====================================================================

def render_table(data: dict):
    width = get_terminal_size((120, 20)).columns
    col1 = 28
    col2 = width - col1 - 5

    print(BOLD + CYAN + "\n📊 VERB STRUCTURE MATRIX\n" + RESET)

    print("-" * width)

    for key, value in data["timeline"].items():

        label = key.replace("_", " ").title()

        color = GREEN
        if "negative" in key:
            color = RED
        elif "question" in key:
            color = BLUE
        elif "modal" in key or "conditional" in key:
            color = YELLOW

        print(f"{color}{label:<{col1}} | {value[:col2]}{RESET}")

    print("-" * width)

# =====================================================================
# PREVIEW
# =====================================================================

def render_preview(data: dict):

    print(BOLD + "\n════════ RESULT ════════\n" + RESET)

    print(f"🔑 Key usada: {data.get('_key_used')}\n")

    print("📌 Corrected:")
    print(GREEN + data["corrected_sentence"] + RESET + "\n")

    print("🤝 Agreement:")
    print("   Positive:", GREEN + data["agreement"]["positive"] + RESET)
    print("   Negative:", RED + data["agreement"]["negative"] + RESET + "\n")

    print("📖 Translation:")
    print(data["translation_pt"] + "\n")

    print("🧠 Explanation:")
    print(data["explanation_pt"] + "\n")

    print("💼 Formal version:")
    print(data["formal_version_developer"] + "\n")

    render_table(data)

    print("\n🚀 Learning Tip:")
    print(data["learning_tip_pt"])

    print("\n════════════════════════════════════════\n")

# =====================================================================
# MAIN
# =====================================================================

def main():
    clear_console()
    print_header()

    context = ""
    current_term = None

    while True:

        if not current_term:
            current_term = input("Digite o termo/frase inicial: ").strip()
            if not current_term:
                print("Encerrando.")
                return

        prompt = build_prompt(current_term, context)

        loading_indicator()
        result = call_groq(prompt)

        render_preview(result)

        context += f"\n{result['corrected_sentence']}"

        action = input(
            "\nm = nova variação | n = novo termo | s = sair\nEscolha: "
        ).strip().lower()

        if action == "s":
            break
        elif action == "m":
            continue
        elif action == "n":
            current_term = None
            clear_console()
            print_header()
        else:
            current_term = action
            clear_console()
            print_header()

if __name__ == "__main__":
    main()