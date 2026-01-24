import json
import random
from itertools import cycle
from groq import Groq

from engine.text.groq_keys_loader import GROQ_KEYS

# ============================================================
# CONFIG
# ============================================================

cfg = json.load(open("settings/groq.json", encoding="utf-8"))

# Randomização + rotação segura
_groq_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))

# ============================================================
# MAIN
# ============================================================

def generate_text(word: str) -> dict:
    key_info = next(_groq_key_cycle)
    client = Groq(api_key=key_info["key"])

    prompt_template = json.load(
        open("prompts/groq/lesson_prompt.json", encoding="utf-8")
    )["template"]

    persona = json.load(
        open("prompts/shared/personality.json", encoding="utf-8")
    )["persona"]

    prompt = (
        prompt_template
        .replace("{{word}}", word)
        .replace("{{persona}}", persona)
    )

    response = client.chat.completions.create(
        model=cfg["model"],
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=cfg["temperature"]
    )

    raw = response.choices[0].message.content.strip()

    return json.loads(raw)
