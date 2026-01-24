import json
import os

GROQ_KEYS_PATH = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS"
    r"\LTS SP Site - Documentos de estudo de inglês"
    r"\FilesHelper\secret_tokens_keys\GroqKeys.json"
)

GROQ_KEYS_FALLBACK = [
    {"name": "lts@gmail.com", "key": "gsk_r***"},
    {"name": "ltsCV@gmail", "key": "gsk_4***"},
    {"name": "butterfly", "key": "gsk_n***"},
    {"name": "??", "key": "gsk_P***"},
    {"name": "MelLuz201811@gmail.com", "key": "gsk_***i"}
]

def load_groq_keys():
    if os.path.exists(GROQ_KEYS_PATH):
        try:
            with open(GROQ_KEYS_PATH, "r", encoding="utf-8") as f:
                keys = json.load(f)
            if isinstance(keys, list) and all("key" in k for k in keys):
                return keys
        except Exception:
            pass
    return GROQ_KEYS_FALLBACK

GROQ_KEYS = load_groq_keys()
