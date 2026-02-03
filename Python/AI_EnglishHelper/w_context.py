"""
====================================================================================
 Script: w_context.py (Groq Only)
 Versão: V3.6 — Contexto validado + Narrativa real
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
# ANSI COLORS (TERMINAL ONLY)
# ================================================================================

C_RESET = "\033[0m"
C_GREEN = "\033[92m"
C_RED = "\033[91m"
C_BLUE = "\033[94m"
C_YELLOW = "\033[93m"
C_CYAN = "\033[96m"
C_BOLD = "\033[1m"

# ================================================================================
# CONFIG INLINE
# ================================================================================

STORY_THEMES = ["faith", "family", "technology"]
FINAL_STORY_SIZE = "short"  # short | medium | long

# ================================================================================
# PROMPTS
# ================================================================================

PROMPTS = {
    "correct_and_translate": """
You are an English teacher.

Rules:
- Translate PT → EN when needed.
- Correct grammar and spelling.
- Output ONLY final English.

Return JSON:
{{
  "original": "{input}",
  "corrected": "final English",
  "had_error": true,
  "was_translated": true,
  "reason": "short explanation"
}}
""",

    "wordbank_accumulative": """
CURRENT TERM:
"{term}"

PREVIOUS CONTEXT TERMS:
{context_terms}

Create JSON:
{{
  "definition_pt": "Explique SOMENTE o significado do termo atual em português.",
  "examples": [
    {{"level":"A1","phrase":"English sentence"}},
    {{"level":"A2","phrase":"English sentence"}},
    {{"level":"B1","phrase":"English sentence"}}
  ]
}}

RULES:
- Definition MUST NOT mention previous terms.
- ALL examples must include "{term}".
- Examples SHOULD reuse at least ONE previous context term if natural.
- ALL examples in English.
""",

    "narrative_step": """
STORY SO FAR:
{timeline}

NEW TERM:
"{term}"

Write 2–3 natural English sentences that CONTINUE the story
and clearly integrate the new term.

Return JSON:
{{
  "sentences": ["...", "..."]
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

CONTEXT_DIR = "./context"
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
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {"model": GROQ_MODEL, "messages": [{"role": "user", "content": prompt}]}
    r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
    r.raise_for_status()
    txt = r.json()["choices"][0]["message"]["content"]
    return json.loads(txt[txt.find("{"): txt.rfind("}") + 1])


def groq_text(prompt: str) -> str:
    key = next(_groq_key_cycle)["key"]
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {"model": GROQ_MODEL, "messages": [{"role": "user", "content": prompt}]}
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

    mode = input("Opção: ").strip()
    mode = "narrative" if mode == "2" else "accumulative"

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

            if mode == "accumulative":
                story = groq_text(
                    f"Use ALL these terms in a {FINAL_STORY_SIZE} positive story: "
                    f"{', '.join(ctx['inputs'])}. Themes: {', '.join(STORY_THEMES)}"
                )
            else:
                story = groq_text(
                    f"Refine this story into a coherent {FINAL_STORY_SIZE} narrative:\n"
                    + "\n".join(ctx["timeline"])
                )

            title = groq_text(
                f"Create a short inspiring title (max 6 words) for this story:\n{story}"
            )

            fname = re.sub(r"[^\w\s-]", "", title).replace(" ", "_")[:60] + ".json"
            path = os.path.join(CONTEXT_DIR, fname)

            ctx["final_story"] = story
            ctx["title"] = title

            with open(path, "w", encoding="utf-8") as f:
                json.dump(ctx, f, indent=2, ensure_ascii=False)

            if os.path.exists(TMP_CONTEXT):
                os.remove(TMP_CONTEXT)

            print(f"\n{C_GREEN}✨ História final:{C_RESET}\n{story}")
            print(f"\n{C_CYAN}📌 Título:{C_RESET} {title}")
            print(f"{C_CYAN}📂 Arquivo:{C_RESET} {path}")
            return

        result = groq_json(
            PROMPTS["correct_and_translate"].format(input=text)
        )

        term = result.get("corrected", "").strip()
        if not term:
            print(f"{C_RED}⚠️ Termo inválido, ignorado.{C_RESET}")
            continue

        if result["was_translated"]:
            print(f"{C_CYAN}🌍 Tradução aplicada (PT → EN){C_RESET}")

        if result["had_error"]:
            print(f"{C_YELLOW}✏️ Correção aplicada:{C_RESET}")
            print(f"{C_RED}❌ {result['original']}{C_RESET}")
            print(f"{C_GREEN}✅ {term}{C_RESET}")
        else:
            print(f"{C_GREEN}✅ Frase correta.{C_RESET}")

        if mode == "accumulative":
            wb = groq_json(
                PROMPTS["wordbank_accumulative"].format(
                    term=term,
                    context_terms=", ".join(ctx["inputs"])
                )
            )

            print(f"\n{C_BLUE}📘 Definição PT:{C_RESET} {wb['definition_pt']}")
            print(f"{C_BLUE}🧩 Exemplos:{C_RESET}")
            for ex in wb["examples"]:
                print(f" ➜ ({ex['level']}) {ex['phrase']}")

            ctx["transcripts"].append({
                "term": term,
                "definition_pt": wb["definition_pt"],
                "examples": wb["examples"]
            })

        else:
            step = groq_json(
                PROMPTS["narrative_step"].format(
                    term=term,
                    timeline="\n".join(ctx["timeline"])
                )
            )
            for s in step["sentences"]:
                print(f"{C_BLUE}📖 {s}{C_RESET}")
                ctx["timeline"].append(s)

        ctx["inputs"].append(term)

        with open(TMP_CONTEXT, "w", encoding="utf-8") as f:
            json.dump(ctx, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()