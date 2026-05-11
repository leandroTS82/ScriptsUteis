# ============================================================
# multilingual_tts_enricher_groq.py
# AI Voice Direction Layer
# ============================================================

import sys
import json
import random
from itertools import cycle

_GROQ_LOADER_DIR = r"C:\dev\scripts\ScriptsUteis\Python"

if _GROQ_LOADER_DIR not in sys.path:
    sys.path.insert(0, _GROQ_LOADER_DIR)

from groq import Groq
from groq_keys_loader import GROQ_KEYS


GROQ_MODEL = "llama-3.3-70b-versatile"

MAX_RETRIES = 3

TIMEOUT_SECONDS = 30

TEMPERATURE = 0.2


_groq_key_cycle = cycle(
    random.sample(
        GROQ_KEYS,
        len(GROQ_KEYS)
    )
)


def _get_client():

    key_info = next(_groq_key_cycle)

    return (
        Groq(api_key=key_info["key"]),
        key_info["name"]
    )


def _call_groq(messages, label=""):

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):

        client, key_name = _get_client()

        try:

            print(
                f"[Groq {label}] "
                f"tentativa {attempt} "
                f"· {key_name}"
            )

            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=TEMPERATURE,
                timeout=TIMEOUT_SECONDS,
            )

            return (
                response
                .choices[0]
                .message
                .content
                .strip()
            )

        except Exception as e:

            last_error = e

            print(e)

    raise RuntimeError(last_error)


def enrich_text(text: str):

    messages = [

        {
            "role": "system",

            "content": """
You are an AI voice direction system.

Your task:
Prepare multilingual text for TTS rendering.

Return ONLY valid JSON.

You must:
- split PT-BR and EN naturally
- preserve original wording
- preserve punctuation
- preserve spoken rhythm
- detect emotional intensity
- detect pacing
- detect creator-style energy

Output format:

[
  {
    "lang": "pt",
    "text": "...",
    "energy": "high",
    "style": "intro",
    "pause_ms": 240
  }
]

Energy values:
- low
- medium
- high

Style values:
- intro
- teaching
- explanation
- english
- closing

IMPORTANT:
- NEVER rewrite text
- NEVER translate
- NEVER summarize
- ONLY segment + annotate
"""
        },

        {
            "role": "user",
            "content": text
        }
    ]

    raw = _call_groq(
        messages,
        label="enrich"
    )

    raw = raw.replace("```json", "")
    raw = raw.replace("```", "")
    raw = raw.strip()

    return json.loads(raw)


if __name__ == "__main__":

    text = (
        "Fala galera! "
        "Hoje você vai aprender "
        "what's your name. "
        "Essa expressão aparece muito!"
    )

    result = enrich_text(text)

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )