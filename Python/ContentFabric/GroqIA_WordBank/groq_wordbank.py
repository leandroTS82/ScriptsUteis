"""
=====================================================================
 Script: groq_wordbank.py
 Autor: Leandro
 Finalidade:
    - Detectar idioma (PT/EN)
    - Traduzir automaticamente para inglês
    - Suportar lista de palavras
    - Suportar múltiplas words separadas por vírgula
    - Gerar WordBank agrupado ou separado
    - Exibir preview amigável no terminal
    - Aceitar WordBank no formato correto OU achatado
=====================================================================
"""

import os
import json
import sys
import requests
from datetime import datetime

API_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY_FILE = "./groq_api_key.txt"

SYSTEM_PROMPT_FILE = "./systemPrompt.json"
BASE_PROMPT_FILE = "./userPromptBase.json"
TRANSLATOR_PROMPT = "./translator_prompt.json"

OUTPUT_DIR = "C:\\dev\\scripts\\ScriptsUteis\\Python\\ContentFabric\\ContentToCreate"
MODEL_NAME = "openai/gpt-oss-20b"


# ---------------------------------------------
# Load helpers
# ---------------------------------------------
def load_json(path):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    return json.load(open(path, "r", encoding="utf-8"))


def load_api_key():
    return open(API_KEY_FILE, "r", encoding="utf-8").read().strip()


# ---------------------------------------------
# Groq helpers
# ---------------------------------------------
def call_groq(system_prompt, user_prompt):
    headers = {
        "Authorization": f"Bearer {load_api_key()}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": json.dumps(system_prompt)},
            {"role": "user", "content": json.dumps(user_prompt)}
        ],
        "temperature": 0.2
    }

    res = requests.post(API_URL, json=payload, headers=headers)
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"]


# ---------------------------------------------
# Language translation PT → EN
# ---------------------------------------------
def translate_to_en(text):
    system = load_json(TRANSLATOR_PROMPT)
    translated = call_groq(system, text).strip()
    return translated.lower()


# ---------------------------------------------
# Format words input
# ---------------------------------------------
def parse_words(arg):
    arg = arg.strip()

    if arg.startswith("[") and arg.endswith("]"):
        words = json.loads(arg)
        return [w.strip() for w in words], True

    if "," in arg:
        words = [w.strip() for w in arg.split(",")]
        return words, False

    return [arg], False


# ---------------------------------------------
# Save output
# ---------------------------------------------
def save_output(content, outname):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, outname)
    open(path, "w", encoding="utf-8").write(content)
    return path


# ---------------------------------------------
# Ensure WORD_BANK grouped correctly
# ---------------------------------------------
def ensure_grouped(wordbank):
    """
    Garante que:
    - Se vier no formato ideal       => [[{obj},{obj}]]
    - Se vier achatado (lista plana) => [[{obj},{obj}]]
    """
    if len(wordbank) == 0:
        return [[]]

    # Caso típico errado: [{"lang": ...}, {...}, {...}]
    if isinstance(wordbank[0], dict):
        return [wordbank]

    # Caso WORD_BANK já esteja agrupado
    return wordbank


# ---------------------------------------------
# Normalize possible wrong items
# ---------------------------------------------
def normalize_wordbank(wordbank):
    normalized = []

    for group in wordbank:
        new_group = []

        for item in group:

            if isinstance(item, str):
                item_str = item.strip()
                if item_str.startswith("{") and item_str.endswith("}"):
                    try:
                        item = json.loads(item_str)
                    except:
                        item = {"lang": "unknown", "text": item_str}
                else:
                    item = {"lang": "unknown", "text": item_str}

            if not isinstance(item, dict):
                item = {"lang": "unknown", "text": str(item)}

            new_group.append(item)

        normalized.append(new_group)

    return normalized


# ---------------------------------------------
# Terminal Preview
# ---------------------------------------------
def preview_terminal(json_path):
    data = load_json(json_path)

    print("\n\n===============================")
    print("📝 PREVIEW DO CONTEÚDO GERADO")
    print("===============================\n")

    print("📌 Introdução:")
    print(data.get("introducao", ""))
    print()

    print("📁 nome_arquivos:")
    print(data.get("nome_arquivos", ""))
    print()

    print("🧠 WORD BANK:\n")

    raw_wordbank = data.get("WORD_BANK", [])

    grouped_wordbank = ensure_grouped(raw_wordbank)

    wordbank = normalize_wordbank(grouped_wordbank)

    for i, group in enumerate(wordbank):
        print(f"--- Grupo {i+1} ---")
        
        first = True
        is_last_group = (i == len(wordbank) - 1)

        for item in group:
            lang = item.get("lang")
            text = item.get("text")
            pause = item.get("pause", None)

            if first and lang == "en":
                print(f"🇺🇸 EN → {text}  (pause={pause})")
                first = False
                continue

            if lang == "pt" and text.startswith("Significa"):
                print(f"🇧🇷 PT (definição) → {text}")
                continue

            if lang == "en":
                print(f"    ➜ Exemplo EN: {text}")
                continue

            if lang == "pt" and not text.startswith("Significa"):
                if is_last_group:
                    print(f"⭐ Finalização PT: {text}")
                else:
                    print(f"🔄 Transição PT: {text}")
                continue

            print(f"❓ {text}")

        print("\n")

    print("===============================")
    print("✔ Fim do preview\n")


# ---------------------------------------------
# MAIN
# ---------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Uso: python groq_wordbank.py WORD")
        return

    raw_input = sys.argv[1]

    words_raw, is_grouped = parse_words(raw_input)

    translated_words = [translate_to_en(w) for w in words_raw]

    base_prompt = load_json(BASE_PROMPT_FILE)
    system_prompt = load_json(SYSTEM_PROMPT_FILE)

    base_prompt["words"] = translated_words

    print("Gerando JSON para:", translated_words)

    json_output = call_groq(system_prompt, base_prompt)

    if is_grouped:
        outname = "Group_" + "_".join(translated_words).replace(" ", "_") + ".json"
    else:
        if len(translated_words) == 1:
            outname = translated_words[0].replace(" ", "_") + ".json"
        else:
            outname = "Multiple_" + "_".join(translated_words) + ".json"

    outpath = save_output(json_output, outname)

    preview_terminal(outpath)


if __name__ == "__main__":
    main()
