from groq import Groq
import os

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
    if text in _cache:
        return _cache[text]

    client = _get_client()

    prompt = f"Translate to English only, no punctuation, no commentary:\n{text}"

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    translated = response.choices[0].message.content.strip().lower()
    _cache[text] = translated
    return translated
