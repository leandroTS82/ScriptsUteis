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
# PROMPTS – COMMON
# ================================================================================

PROMPTS_COMMON = {
    "correct_and_translate": """
You are an English teacher.

Input: "{input}"

Return ONLY valid JSON in this format:
{{
  "corrected": "corrected English sentence or term",
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
- Translations are secondary: keep them simple and direct.

Use the following people when referring to individuals:
Leandro (me), Grace (my wife), Geovanna, Vinnicius, Lucas, Melissa (my children).

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
- Use the same protagonists consistently:
  Leandro, Grace, Geovanna, Vinnicius, Lucas, Melissa.
- Do NOT summarize or restart the story.
- This sentence is part of an ongoing narrative.

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
You are an English teacher creating a short rhyming song.

Current term:
"{term}"

Previously learned terms:
{context_terms}

Rules:
- Create short rhyming lines.
- Use emotional and musical language.
- Use the same protagonists when people are mentioned:
  Leandro, Grace, Geovanna, Vinnicius, Lucas, Melissa.
- Group lines into short verses.
- Provide a translation per verse (not line by line).

Return ONLY valid JSON:
{{
  "definition_pt": "brief explanation in Brazilian Portuguese",
  "verses": [
    {{
      "lyrics_en": "short rhyming verse",
      "lyrics_pt": "Brazilian Portuguese translation of the verse"
    }},
    {{
      "lyrics_en": "another rhyming verse",
      "lyrics_pt": "Brazilian Portuguese translation of the verse"
    }}
  ]
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

            story_prompt = (
                f"Create a {FINAL_STORY_SIZE} rhyming song using ALL these terms:\n"
                if mode == "song"
                else f"Use ALL these terms in a {FINAL_STORY_SIZE} positive story:\n"
            )

            story = groq_text(
                story_prompt +
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

        print(f"{C_GREEN}✅ Frase correta.{C_RESET}")

        # -------------------------------
        # NARRATIVA
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

        # -------------------------------
        # ACUMULATIVO / CANÇÃO
        # -------------------------------
        else:
            if mode == "song":
                wb = groq_json(
                    PROMPTS_SONG["wordbank"].format(
                        term=term,
                        context_terms=", ".join(ctx["inputs"])
                    )
                )
                print(f"\n{C_BLUE}🎵 Definição PT:{C_RESET} {wb['definition_pt']}")
                for v in wb["verses"]:
                    print(f"♪ {v['lyrics_en']}")
                    print(f"{C_CYAN}  {v['lyrics_pt']}{C_RESET}")
            else:
                wb = groq_json(
                    PROMPTS_ACCUMULATIVE["wordbank"].format(
                        term=term,
                        context_terms=", ".join(ctx["inputs"])
                    )
                )

                print(f"\n{C_BLUE}📘 Definição PT:{C_RESET} {wb['definition_pt']}")
                print(f"{C_BLUE}🧩 Exemplos:{C_RESET}")

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
