from groq import Groq
import os
import logging

GROQ_KEY_PATH = r"C:\dev\scripts\ScriptsUteis\Python\secret_tokens_keys\groq_api_key.txt"

_client = None
_cache = {}

def _get_client():
    global _client
    if _client is None:
        key = open(GROQ_KEY_PATH).read().strip()
        _client = Groq(api_key=key)
    return _client


def translate_to_english(text: str) -> str:
    """
    Tradução resiliente:
    - Se Groq falhar, retorna o termo original
    - Nunca quebra o pipeline
    """
    if text in _cache:
        return _cache[text]

    try:
        client = _get_client()

        prompt = f"Translate to English only, no punctuation, no commentary:\n{text}"

        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            timeout=10
        )

        translated = response.choices[0].message.content.strip().lower()

        if translated:
            _cache[text] = translated
            return translated

    except Exception as e:
        print(f"⚠️ [Groq] Falha ao traduzir '{text}'. Usando original.")
        print(f"    Motivo: {e}")

    # fallback seguro
    _cache[text] = text.lower()
    return text.lower()
