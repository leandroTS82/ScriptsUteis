"""
====================================================================================
 Script: w_context.py (Groq Only)
 Versão: V3.8 — Contrato JSON alinhado (EN/PT separados)
====================================================================================
"""

import os
import sys
import json
import requests
import random
import re
from itertools import cycle
from datetime import datetime

# ================================================================================
# ANSI COLORS
# ================================================================================

C_RESET = "\033[0m"
C_GREEN = "\033[92m"
C_RED = "\033[91m"
C_BLUE = "\033[94m"
C_YELLOW = "\033[93m"
C_CYAN = "\033[96m"
C_BOLD = "\033[1m"

# ================================================================================
# CONFIG
# ================================================================================

STORY_THEMES = ["faith", "family", "technology"]
FINAL_STORY_SIZE = "short"

# ================================================================================
# PROMPTS – COMMON  ✅ CORRIGIDO (ESCAPE DE JSON)
# ================================================================================

PROMPTS_COMMON = {
    "correct_and_translate": """
You are an English teacher.

Input: "{input}"

Tasks:
1. Check if the input is correct English.
2. If it is wrong, explain briefly what is wrong and provide the correct form.
3. If it is correct, say it is correct.
4. Always provide the Brazilian Portuguese translation.

Return ONLY valid JSON:
{{
  "is_correct": true_or_false,
  "corrected": "correct English sentence or term",
  "error_explanation_en": "short explanation in English (empty if correct)",
  "error_explanation_pt": "short explanation in Brazilian Portuguese (empty if correct)",
  "translation_pt": "Brazilian Portuguese translation"
}}
"""
}

# ================================================================================
# PROMPTS – ACCUMULATIVE MODE
# ================================================================================

PROMPTS_ACCUMULATIVE = {
    "wordbank": """
You are an English teacher building a cumulative learning wordbank.

Current term:
"{term}"

Previously learned terms (reuse naturally when appropriate):
{context_terms}

Rules:
- Examples must NOT rhyme.
- ALL examples must include the current term.
- At least one example should naturally reuse one or more previous terms.
- Examples should gradually become richer as more terms are learned.
- Each example must stay under 200 characters.
- Focus on real, everyday usage.

Return ONLY valid JSON:
{{
  "definition_pt": "short and clear definition in Brazilian Portuguese",
  "examples": [
    {{
      "level": "A1",
      "en": "simple sentence",
      "pt": "simple translation"
    }},
    {{
      "level": "A2",
      "en": "slightly richer sentence",
      "pt": "simple translation"
    }},
    {{
      "level": "B1",
      "en": "contextual sentence reusing previous terms if possible",
      "pt": "simple translation"
    }}
  ]
}}
"""
}

# ================================================================================
# PROMPTS – NARRATIVE MODE
# ================================================================================

PROMPTS_NARRATIVE = {
    "step": """
You are progressively building a simple and coherent story.

New term:
"{term}"

Story so far:
{timeline}

Rules:
- Add ONLY one new sentence to continue the story.
- The sentence must use the new term naturally.
- Keep the language simple and coherent.

Return ONLY valid JSON:
{{
  "sentence_en": "next sentence of the story",
  "sentence_pt": "Brazilian Portuguese translation"
}}
"""
}

# ================================================================================
# PROMPTS – SONG MODE
# ================================================================================

PROMPTS_SONG = {
    "wordbank": """
You are an English teacher building a song progressively.

Current term:
"{term}"

Previously created lines:
{context_terms}

Rules:
- Create ONLY ONE short rhyming line (max 80 characters).
- The line must include the current term.
- Keep it musical and emotional.
- Do NOT repeat previous lines.

Return ONLY valid JSON:
{{
  "line_en": "single rhyming line",
  "line_pt": "Brazilian Portuguese translation of the line"
}}
"""
}

# ================================================================================
# BASE / IMPORTS
# ================================================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from groq_keys_loader import GROQ_KEYS

# ================================================================================
# GROQ CONFIG
# ================================================================================

_groq_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

# ================================================================================
# CONTEXT PATH
# ================================================================================

CONTEXT_DIR = "./01_wContext"
os.makedirs(CONTEXT_DIR, exist_ok=True)

TMP_CONTEXT = os.path.join(
    CONTEXT_DIR,
    datetime.now().strftime("%y%m%d%H%M") + "_context.json"
)

# ================================================================================
# GROQ HELPERS
# ================================================================================

def groq_json(prompt: str) -> dict:
    key = next(_groq_key_cycle)["key"]
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }
    r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
    r.raise_for_status()
    txt = r.json()["choices"][0]["message"]["content"]
    return json.loads(txt[txt.find("{"): txt.rfind("}") + 1])


def groq_text(prompt: str) -> str:
    key = next(_groq_key_cycle)["key"]
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }
    r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

# ================================================================================
# MAIN
# ================================================================================

def main():
    print(f"{C_BOLD}Selecione o modo:{C_RESET}")
    print("1 - Acumulativo")
    print("2 - Narrativa")
    print("3 - Canção (rimas)")

    opt = input("Opção: ").strip()
    mode = "narrative" if opt == "2" else "song" if opt == "3" else "accumulative"

    ctx = {
        "mode": mode,
        "inputs": [],
        "transcripts": [],
        "timeline": []
    }

    while True:
        text = input(
            f"\n{C_BOLD}Digite apenas 's' para sair{C_RESET}\n"
            "OU digite a frase/termo a ser processado: "
        ).strip()

        if text.lower() == "s":
            if not ctx["inputs"]:
                if os.path.exists(TMP_CONTEXT):
                    os.remove(TMP_CONTEXT)
                print(f"{C_YELLOW}🗑️ Contexto vazio. Encerrando.{C_RESET}")
                return

            if mode == "song":
                story = "\n".join(ctx["timeline"])
            else:
                story = groq_text(
                    f"Use ALL these terms in ONE short paragraph, positive and clear:\n"
                    f"{', '.join(ctx['inputs'])}\nThemes: {', '.join(STORY_THEMES)}"
                )

            title = groq_text(
                f"Create a short inspiring title (max 6 words) for this text:\n{story}"
            )

            fname = re.sub(r"[^\w\s-]", "", title).replace(" ", "_")[:60] + ".json"
            path = os.path.join(CONTEXT_DIR, fname)

            ctx["final_story"] = story
            ctx["title"] = title

            with open(path, "w", encoding="utf-8") as f:
                json.dump(ctx, f, indent=2, ensure_ascii=False)

            if os.path.exists(TMP_CONTEXT):
                os.remove(TMP_CONTEXT)

            print(f"\n{C_GREEN}✨ Resultado final:{C_RESET}\n{story}")
            print(f"\n{C_CYAN}📌 Título:{C_RESET} {title}")
            print(f"{C_CYAN}📂 Arquivo:{C_RESET} {path}")
            return

        # -------------------------------
        # CORREÇÃO / TRADUÇÃO
        # -------------------------------
        result = groq_json(
            PROMPTS_COMMON["correct_and_translate"].format(input=text)
        )

        term = result.get("corrected", "").strip()
        if not term:
            print(f"{C_RED}⚠️ Termo inválido, ignorado.{C_RESET}")
            continue

        if result.get("is_correct"):
            print(f"{C_GREEN}✅ Correto.{C_RESET}")
        else:
            print(f"{C_YELLOW}❌ Incorreto.{C_RESET}")
            print(f"{C_BLUE}✔ Correto:{C_RESET} {term}")
            print(f"{C_CYAN}ℹ️ EN:{C_RESET} {result.get('error_explanation_en')}")
            print(f"{C_CYAN}ℹ️ PT:{C_RESET} {result.get('error_explanation_pt')}")

        if result.get("translation_pt"):
            print(f"{C_CYAN}🌍 Tradução PT:{C_RESET} {result.get('translation_pt')}")

        # -------------------------------
        # MODOS
        # -------------------------------
        if mode == "narrative":
            step = groq_json(
                PROMPTS_NARRATIVE["step"].format(
                    term=term,
                    timeline="\n".join(ctx["timeline"])
                )
            )
            print(f"{C_BLUE}📖 {step['sentence_en']}{C_RESET}")
            print(f"{C_CYAN}   ↳ {step['sentence_pt']}{C_RESET}")
            ctx["timeline"].append(step["sentence_en"])

        elif mode == "song":
            wb = groq_json(
                PROMPTS_SONG["wordbank"].format(
                    term=term,
                    context_terms="\n".join(ctx["timeline"])
                )
            )
            print(f"\n{C_BLUE}🎵 Linha criada:{C_RESET}")
            print(f"♪ {wb['line_en']}")
            print(f"{C_CYAN}  {wb['line_pt']}{C_RESET}")
            ctx["timeline"].append(wb["line_en"])

        else:
            wb = groq_json(
                PROMPTS_ACCUMULATIVE["wordbank"].format(
                    term=term,
                    context_terms=", ".join(ctx["inputs"])
                )
            )
            print(f"\n{C_BLUE}📘 {wb['definition_pt']}{C_RESET}")
            for ex in wb["examples"]:
                print(f" ➜ ({ex['level']}) {ex['en']}")
                print(f"     {C_CYAN}{ex['pt']}{C_RESET}")

            ctx["transcripts"].append({
                "term": term,
                "definition_pt": wb["definition_pt"],
                "examples": wb["examples"]
            })

        ctx["inputs"].append(term)

        with open(TMP_CONTEXT, "w", encoding="utf-8") as f:
            json.dump(ctx, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
