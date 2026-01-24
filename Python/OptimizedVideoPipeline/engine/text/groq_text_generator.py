import json
import random
import re
from itertools import cycle
from groq import Groq

from engine.text.groq_keys_loader import GROQ_KEYS
from engine.project_root import get_project_root

# ============================================================
# ROOT
# ============================================================

ROOT = get_project_root()

# ============================================================
# CONFIG
# ============================================================

cfg = json.load(
    open(ROOT / "settings" / "groq.json", encoding="utf-8")
)

_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))

# ============================================================
# HELPERS
# ============================================================

def extract_json(text: str) -> dict:
    """
    Extrai o primeiro JSON válido encontrado no texto.
    """
    if not text:
        raise ValueError("Resposta vazia da Groq")

    # remove markdown ```json
    text = text.strip()
    text = re.sub(r"^```json|```$", "", text, flags=re.IGNORECASE).strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("Nenhum JSON encontrado na resposta")

    return json.loads(match.group(0))


# ============================================================
# MAIN
# ============================================================

def generate_text(word: str) -> dict:
    key_info = next(_key_cycle)
    client = Groq(api_key=key_info["key"])

    prompt_template = json.load(
        open(ROOT / "prompts" / "groq" / "lesson_prompt.json", encoding="utf-8")
    )["template"]

    persona = json.load(
        open(ROOT / "prompts" / "shared" / "personality.json", encoding="utf-8")
    )["persona"]

    base_prompt = (
        prompt_template
        .replace("{{word}}", word)
        .replace("{{persona}}", persona)
    )

    # --------------------------------------------------------
    # 1ª TENTATIVA
    # --------------------------------------------------------

    response = client.chat.completions.create(
        model=cfg["model"],
        messages=[{"role": "user", "content": base_prompt}],
        temperature=cfg["temperature"]
    )

    raw = response.choices[0].message.content or ""

    try:
        return extract_json(raw)
    except Exception:
        pass

    # --------------------------------------------------------
    # 2ª TENTATIVA (REPAIR MODE)
    # --------------------------------------------------------

    repair_prompt = (
        "You MUST return ONLY valid JSON.\n"
        "Do NOT explain anything.\n"
        "Do NOT use markdown.\n\n"
        f"Fix this content and return JSON only:\n{raw}"
    )

    response = client.chat.completions.create(
        model=cfg["model"],
        messages=[{"role": "user", "content": repair_prompt}],
        temperature=0
    )

    repaired = response.choices[0].message.content or ""

    try:
        return extract_json(repaired)
    except Exception as e:
        raise RuntimeError(
            "Groq failed to return valid JSON after retry.\n"
            f"Raw response:\n{raw}\n\n"
            f"Repaired response:\n{repaired}"
        ) from e
