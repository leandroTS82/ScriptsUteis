import json
import os
import random
import sys
import requests
from itertools import cycle
from pathlib import Path

# ======================================================
# BASE DIR
# ======================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from groq_keys_loader import GROQ_KEYS

# ======================================================
# GROQ CONFIG — IGUAL AO mainTranscript.py
# ======================================================

_groq_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

PROMPT_FILE = Path("./free_prompt.json")
TIMEOUT = 60

# ======================================================
# KEYS — MESMA LÓGICA
# ======================================================

def get_next_groq_key() -> str:
    """
    Reproduz EXATAMENTE a lógica usada no mainTranscript.py
    """
    for _ in range(len(GROQ_KEYS)):
        item = next(_groq_key_cycle)

        if not isinstance(item, dict):
            continue

        key = item.get("key", "").strip()

        if key.startswith("gsk_"):
            return key

    raise RuntimeError("❌ Nenhuma GROQ API Key válida encontrada.")

# ======================================================
# PROMPT
# ======================================================

def load_prompt() -> dict:
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"Prompt file not found: {PROMPT_FILE}")

    with PROMPT_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_messages(prompt_data: dict) -> list:
    messages = []

    system_prompt = prompt_data.get("system")
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })

    for msg in prompt_data.get("messages", []):
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            messages.append(msg)

    if not messages:
        raise RuntimeError("❌ Nenhuma mensagem válida encontrada no prompt.json")

    return messages

# ======================================================
# GROQ CALL
# ======================================================

def call_groq(messages: list) -> str:
    last_error = None

    for _ in range(len(GROQ_KEYS)):
        api_key = get_next_groq_key()

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": 0.4
        }

        try:
            res = requests.post(
                GROQ_URL,
                headers=headers,
                json=payload,
                timeout=TIMEOUT
            )

            if res.status_code == 429:
                last_error = "Rate limit"
                continue

            if res.status_code == 401:
                last_error = "Invalid API key"
                continue

            res.raise_for_status()

            data = res.json()
            return data["choices"][0]["message"]["content"]

        except requests.RequestException as e:
            last_error = str(e)
            continue

    raise RuntimeError(f"❌ Todas as GROQ keys falharam. Último erro: {last_error}")

# ======================================================
# MAIN
# ======================================================

def main():
    print(f"🔑 GROQ KEYS carregadas: {len(GROQ_KEYS)}")

    prompt_data = load_prompt()
    messages = build_messages(prompt_data)

    print("🧠 Enviando contexto para o GROQ...")
    answer = call_groq(messages)

    print("\n================ GROQ RESPONSE ================\n")
    print(answer)
    print("\n===============================================\n")


if __name__ == "__main__":
    main()
