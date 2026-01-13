"""
=====================================================================
 Script: groq_image_gen.py (versão final e 100% compatível com Groq)
 Modelo: luma-flux-schnell (via chat.completions)
=====================================================================
"""

import os
import json
import sys
import base64
import requests

API_URL_CHAT = "https://api.groq.com/openai/v1/chat/completions"
API_KEY_FILE = "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\LTS SP Site - Documentos de estudo de inglês\\FilesHelper\\secret_tokens_keys\\groq_api_key.txt"

TRANSLATOR_PROMPT = "./ImageGen_translator_prompt.json"

OUTPUT_DIR = "C:\\dev\\scripts\\ScriptsUteis\\Python\\ContentFabric\\ContentToCreate\\Images"
MODEL_IMAGE = "luma-flux-schnell"
MODEL_TRANSLATE = "openai/gpt-oss-20b"


# ----------------------------------------------
# Helpers
# ----------------------------------------------
def load_api_key():
    return open(API_KEY_FILE, "r", encoding="utf-8").read().strip()


def load_json(path):
    return json.load(open(path, "r", encoding="utf-8"))


# ----------------------------------------------
# Translation (PT → EN)
# ----------------------------------------------
def call_groq_translate(text):
    system_prompt = load_json(TRANSLATOR_PROMPT)

    payload = {
        "model": MODEL_TRANSLATE,
        "messages": [
            {"role": "system", "content": json.dumps(system_prompt)},
            {"role": "user", "content": text}
        ],
        "temperature": 0.1
    }

    headers = {
        "Authorization": f"Bearer {load_api_key()}",
        "Content-Type": "application/json"
    }

    res = requests.post(API_URL_CHAT, json=payload, headers=headers)
    res.raise_for_status()

    return res.json()["choices"][0]["message"]["content"].strip().lower()


# ----------------------------------------------
# Generate Image using FLUX Schnell
# ----------------------------------------------
def generate_image(prompt_en, save_as):
    headers = {
        "Authorization": f"Bearer {load_api_key()}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_IMAGE,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt_en
                    }
                ]
            }
        ]
    }

    res = requests.post(API_URL_CHAT, json=payload, headers=headers)
    res.raise_for_status()

    # A imagem agora vem assim:
    content = res.json()["choices"][0]["message"]["content"][0]

    if "image" not in content:
        raise ValueError("Resposta não contém imagem gerada.")

    image_b64 = content["image"]["b64_json"]

    img_bytes = base64.b64decode(image_b64)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, save_as)

    with open(out_path, "wb") as f:
        f.write(img_bytes)

    print(f"🖼️ Imagem salva: {out_path}")
    return out_path


# ----------------------------------------------
# Parse multiple words
# ----------------------------------------------
def parse_words(raw):
    raw = raw.strip()

    if raw.startswith("[") and raw.endswith("]"):
        return json.loads(raw)

    if "," in raw:
        return [w.strip() for w in raw.split(",")]

    return [raw]


# ----------------------------------------------
# MAIN
# ----------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Uso: python groq_image_gen.py palavra")
        return

    words_raw = parse_words(sys.argv[1])
    print("Palavras detectadas:", words_raw)

    print("\nTraduzindo...")
    words_en = [call_groq_translate(w) for w in words_raw]

    for original, w in zip(words_raw, words_en):
        print(f" - {original} → {w}")

    print("\nGerando imagens...\n")

    for word_en in words_en:
        filename = word_en.replace(" ", "_") + ".jpg"
        prompt = f"Ultra-detailed high quality illustration of: {word_en}"
        generate_image(prompt, filename)

    print("\n Todas as imagens foram geradas com sucesso!\n")


if __name__ == "__main__":
    main()
