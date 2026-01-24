import json
import random
from itertools import cycle
from groq import Groq

from engine.text.groq_keys_loader import GROQ_KEYS
from engine.project_root import get_project_root

ROOT = get_project_root()

cfg = json.load(open(ROOT / "settings" / "groq.json", encoding="utf-8"))

_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))

def generate_text(word: str) -> dict:
    key_info = next(_key_cycle)
    client = Groq(api_key=key_info["key"])

    prompt_template = json.load(
        open(ROOT / "prompts" / "groq" / "lesson_prompt.json", encoding="utf-8")
    )["template"]

    persona = json.load(
        open(ROOT / "prompts" / "shared" / "personality.json", encoding="utf-8")
    )["persona"]

    prompt = (
        prompt_template
        .replace("{{word}}", word)
        .replace("{{persona}}", persona)
    )

    response = client.chat.completions.create(
        model=cfg["model"],
        messages=[{"role": "user", "content": prompt}],
        temperature=cfg["temperature"]
    )

    return json.loads(response.choices[0].message.content.strip())
