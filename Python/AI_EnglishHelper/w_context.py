"""
====================================================================================
 Script: w_context.py (Groq Only)
 Versão: V3.7 — Modo Canção (Rimas) adicionado
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
You are a young, friendly and modern English teacher.

TASK:
- Detect if the input is Portuguese or incorrect English.
- Translate PT → EN only when needed.
- Correct grammar and spelling when needed.

RULES:
- If input is already correct English, keep meaning unchanged.
- Output ONLY valid JSON.
- Do NOT add explanations outside JSON.

Return JSON:
{
  "original": "{input}",
  "corrected": "final English sentence",
  "had_error": true,
  "was_translated": true,
  "reason": "very short explanation (max 15 words)"
}
""",

    "wordbank_accumulative": """
CURRENT TERM:
"{term}"

PREVIOUS CONTEXT TERMS:
{context_terms}

TASK:
Create a progressive learning entry for the CURRENT TERM only.

GLOBAL RULES:
- When people appear, ONLY use these characters:
  Leandro (father), Grace (mother), Geovanna, Vinnicius, Lucas, Melissa (children).
- Do NOT invent new names.

Return JSON:
{
  "definition_pt": "Tradução do termo + explicação clara em português. Inclua sinônimos em inglês e 1 uso comum em PT.",
  "examples": [
    {
      "level": "A1",
      "en": "Very simple English sentence using '{term}'.",
      "pt": "Tradução simples."
    },
    {
      "level": "A2",
      "en": "Slightly longer sentence using '{term}' and context.",
      "pt": "Tradução resumida."
    },
    {
      "level": "B1",
      "en": "More complete sentence using '{term}' naturally.",
      "pt": "Tradução curta."
    }
  ]
}

RULES:
- NO rhymes.
- Definition MUST NOT mention previous terms.
- ALL examples MUST include "{term}".
- Each example MUST be longer than the previous.
- Each English example MUST be under 200 characters.
- PT translation is secondary: short and simple.
- MAY reuse ONE previous context term if natural.
""",

    "narrative_step": """
STORY SO FAR:
{timeline}

NEW TERM:
"{term}"

TASK:
Continue the story naturally by adding ONE new sentence.

GLOBAL RULES:
- When people appear, ONLY use these characters:
  Leandro (father), Grace (mother), Geovanna, Vinnicius, Lucas, Melissa (children).
- Do NOT invent new names.

Return JSON:
{
  "sentence_en": "One clear, simple English sentence that continues the story and uses '{term}'.",
  "sentence_pt": "Tradução simples para apoio ao aprendizado."
}

RULES:
- Do NOT summarize or conclude the story.
- Do NOT restart the story.
- The new sentence MUST connect logically to the previous ones.
- Keep tone positive, simple, and educational.
""",

    "wordbank_song": """
CURRENT TERM:
"{term}"

PREVIOUS CONTEXT TERMS:
{context_terms}

TASK:
Create a small educational song entry using the CURRENT TERM.

GLOBAL RULES:
- When people appear, ONLY use these characters:
  Leandro (father), Grace (mother), Geovanna, Vinnicius, Lucas, Melissa (children).
- Do NOT invent new names.

Return JSON:
{
  "definition_pt": "Tradução e explicação clara do termo em português.",
  "song": {
    "lyrics_en": [
      "Rhyming line using '{term}'",
      "Another rhyming line using '{term}'",
      "Third rhyming line using '{term}'"
    ],
    "lyrics_pt": [
      "Tradução da linha 1",
      "Tradução da linha 2",
      "Tradução da linha 3"
    ]
  }
}

RULES:
- ALL English lines MUST rhyme.
- Rhythm must feel like a simple song.
- ALL lines MUST include "{term}".
- MAY include context terms if natural.
- English is primary; PT is supportive.
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
    print("3 - Canção (rimas)")

    opt = input("Opção: ").strip()
    if opt == "2":
        mode = "narrative"
    elif opt == "3":
        mode = "song"
    else:
        mode = "accumulative"

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

            if mode == "narrative":
                story = groq_text(
                    f"Refine this story into a {FINAL_STORY_SIZE} coherent narrative:\n"
                    + "\n".join(ctx["timeline"])
                )
            elif mode == "song":
                story = groq_text(
                    f"Create a {FINAL_STORY_SIZE} rhyming song using ALL these terms:\n"
                    f"{', '.join(ctx['inputs'])}\nThemes: {', '.join(STORY_THEMES)}"
                )
            else:
                story = groq_text(
                    f"Use ALL these terms in a {FINAL_STORY_SIZE} positive story:\n"
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

        if mode == "narrative":
            step = groq_json(
                PROMPTS["narrative_step"].format(
                    term=term,
                    timeline="\n".join(ctx["timeline"])
                )
            )
            for s in step["sentences"]:
                print(f"{C_BLUE}📖 {s}{C_RESET}")
                ctx["timeline"].append(s)

        else:
            key = "wordbank_song" if mode == "song" else "wordbank_accumulative"
            wb = groq_json(
                PROMPTS[key].format(
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

        ctx["inputs"].append(term)

        with open(TMP_CONTEXT, "w", encoding="utf-8") as f:
            json.dump(ctx, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()