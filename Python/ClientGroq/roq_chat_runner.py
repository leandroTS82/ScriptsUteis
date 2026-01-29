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
# 🔧 PROMPT MODES (AJUSTE AQUI)
# ======================================================
# Fácil adicionar novos modos

PROMPT_MODES = {
    "programador": "promptA.json",
    "curiosidade": "promptB.json"
}

DEFAULT_MODE = "programador"

PROMPTS_DIR = Path("./prompts")

# ======================================================
# GROQ CONFIG (INALTERADO)
# ======================================================

_groq_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"
TIMEOUT = 60

# ======================================================
# KEYS — MESMA LÓGICA DO mainTranscript.py
# ======================================================

def get_next_groq_key() -> str:
    for _ in range(len(GROQ_KEYS)):
        item = next(_groq_key_cycle)
        if isinstance(item, dict):
            key = item.get("key", "").strip()
            if key.startswith("gsk_"):
                return key
    raise RuntimeError("❌ Nenhuma GROQ API Key válida encontrada.")

# ======================================================
# PROMPT LOADING
# ======================================================

def load_prompt(mode: str) -> dict:
    if mode not in PROMPT_MODES:
        raise RuntimeError(f"Modo inválido: {mode}")

    prompt_path = PROMPTS_DIR / PROMPT_MODES[mode]

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt não encontrado: {prompt_path}")

    with prompt_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_messages(prompt_data: dict, user_extra: str | None) -> list:
    messages = []

    if system := prompt_data.get("system"):
        messages.append({"role": "system", "content": system})

    for msg in prompt_data.get("messages", []):
        if isinstance(msg, dict):
            messages.append(msg)

    if user_extra:
        messages.append({
            "role": "user",
            "content": user_extra
        })

    if not messages:
        raise RuntimeError("❌ Nenhuma mensagem válida para envio")

    return messages

# ======================================================
# GROQ CALL
# ======================================================

def call_groq(messages: list) -> str:
    last_error = None

    for _ in range(len(GROQ_KEYS)):
        api_key = get_next_groq_key()

        try:
            res = requests.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "temperature": 0.4
                },
                timeout=TIMEOUT
            )

            if res.status_code in (401, 429):
                last_error = res.text
                continue

            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]

        except requests.RequestException as e:
            last_error = str(e)
            continue

    raise RuntimeError(f"❌ Todas as GROQ keys falharam. Último erro: {last_error}")

# ======================================================
# MAIN
# ======================================================

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODE
    user_extra = " ".join(sys.argv[2:]).strip() if len(sys.argv) > 2 else None

    print(f"🔧 Modo selecionado: {mode}")
    print(f"🔑 GROQ keys: {len(GROQ_KEYS)}")

    prompt_data = load_prompt(mode)
    messages = build_messages(prompt_data, user_extra)

    print("🧠 Enviando contexto para o GROQ...")
    answer = call_groq(messages)

    print("\n================ GROQ RESPONSE ================\n")
    print(answer)
    print("\n===============================================\n")


if __name__ == "__main__":
    main()
