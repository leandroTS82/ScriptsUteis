import json
import requests
from itertools import cycle

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

GROQ_KEYS_PATH = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS"
    r"\LTS SP Site - Documentos de estudo de inglês"
    r"\FilesHelper\secret_tokens_keys\GroqKeys.json"
)

with open(GROQ_KEYS_PATH, "r", encoding="utf-8") as f:
    _KEYS = json.load(f)

_key_cycle = cycle(_KEYS)


def groq_chat(prompt: str) -> str:
    key_obj = next(_key_cycle)

    headers = {
        "Authorization": f"Bearer {key_obj['key']}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are an expert English linguist and ESL teacher."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2
    }

    response = requests.post(
        GROQ_URL,
        headers=headers,
        json=payload,
        timeout=60
    )

    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
