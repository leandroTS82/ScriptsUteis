r"""
=====================================================================
 Script: gemini_MakeVideo.py
 Autor: Leandro

 VERSÃO DEFINITIVA — GEMINI SDK (SEGURA):
  - Nunca gera JSON vazio
  - Nunca move JSON original em falso sucesso
  - Ignora uploaded_*.json
  - Ignora JSONs já processados
  - Pipeline idempotente
=====================================================================
"""

import os
import json
import shutil
import argparse
import time
import random
import google.generativeai as genai

# ======================================================================
# CONFIG
# ======================================================================

CONFIG_FILE = r"C:\dev\scripts\ScriptsUteis\Python\ContentFabric\4GroqIA\groq_MakeVideo.json"
CONFIG = json.load(open(CONFIG_FILE, "r", encoding="utf-8"))

API_KEY_FILE = CONFIG["Gemini_api_key_file"]
SYSTEM_PROMPT_FILE = CONFIG["system_prompt_file"]
BASE_PROMPT_FILE = CONFIG["base_prompt_file"]
FRIENDLY_PLAYLISTS_FILE = CONFIG["friendly_playlists_file"]
PROCESSED_DIR = CONFIG["processed_json_dir"]

VIDEO_EXTENSIONS = CONFIG["video_extensions"]
RETRY_MAX = CONFIG.get("retry_max_attempts", 5)
TEMPERATURE = CONFIG.get("temperature", 0.4)
DEBUG = CONFIG.get("debug", True)

MODEL_NAME = "models/gemini-2.5-flash"

# ======================================================================
# INIT GEMINI
# ======================================================================

api_key = open(API_KEY_FILE).read().strip()
genai.configure(api_key=api_key)
model = genai.GenerativeModel(MODEL_NAME)

# ======================================================================
# UTILS
# ======================================================================

def log(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")

def load_json(path):
    return json.load(open(path, "r", encoding="utf-8"))

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def move_to_processed(src):
    ensure_dir(PROCESSED_DIR)
    dst = os.path.join(PROCESSED_DIR, os.path.basename(src))
    shutil.move(src, dst)
    return dst

def find_video(video_dir, tag):
    for f in os.listdir(video_dir):
        if any(f.lower().endswith(ext) for ext in VIDEO_EXTENSIONS):
            if tag.lower() in f.lower():
                return os.path.join(video_dir, f)
    raise FileNotFoundError(f"Nenhum vídeo encontrado para '{tag}'")

def write_final_json(video_path, data):
    name = os.path.splitext(os.path.basename(video_path))[0]
    path = os.path.join(os.path.dirname(video_path), f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path

# ======================================================================
# JSON EXTRACTION (RIGOROSA)
# ======================================================================

def safe_extract_json(text):
    if not text or not isinstance(text, str):
        raise ValueError("Resposta Gemini vazia")

    if "{" not in text or "}" not in text:
        raise ValueError("Resposta Gemini não contém JSON")

    first = text.find("{")
    last = text.rfind("}")

    parsed = json.loads(text[first:last + 1])

    if not parsed or not isinstance(parsed, dict):
        raise ValueError("JSON retornado está vazio ou inválido")

    return parsed

# ======================================================================
# GEMINI CALL (SEGURA)
# ======================================================================

def call_gemini(system_prompt, user_prompt):
    prompt = (
        "SYSTEM:\n"
        + json.dumps(system_prompt, ensure_ascii=False)
        + "\n\nUSER:\n"
        + json.dumps(user_prompt, ensure_ascii=False)
    )

    for attempt in range(RETRY_MAX + 1):
        try:
            response = model.generate_content(
                prompt,
                generation_config={"temperature": TEMPERATURE}
            )

            text = getattr(response, "text", None)
            log(f"Gemini raw text: {repr(text)}")

            if not text:
                raise RuntimeError("Gemini retornou resposta sem texto")

            return text

        except Exception as e:
            wait = min(2 ** attempt + random.uniform(0.5, 1.5), 30)
            print(f"[Gemini SDK] Retry em {wait:.1f}s → {str(e)}")
            time.sleep(wait)

    raise RuntimeError("Gemini SDK: tentativas excedidas")

# ======================================================================
# PLAYLIST
# ======================================================================

def build_playlist_object(key, friendly):
    if key not in friendly:
        key = "GeneralVocabulary"
    entry = friendly[key]
    return {
        "Id": "",
        "create_if_not_exists": True,
        "name": entry["name"],
        "description": entry["description"]
    }

# ======================================================================
# MAIN
# ======================================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--videos")
    parser.add_argument("--playlist")
    parser.add_argument("--sleep-between", type=int, default=60)
    args = parser.parse_args()

    json_dir = args.path
    video_dir = args.videos or args.path

    ensure_dir(PROCESSED_DIR)

    system_prompt = load_json(SYSTEM_PROMPT_FILE)
    base_prompt = load_json(BASE_PROMPT_FILE)
    friendly = load_json(FRIENDLY_PLAYLISTS_FILE)

    files = [
        f for f in os.listdir(json_dir)
        if f.endswith(".json")
        and not f.startswith("uploaded_")
        and not os.path.exists(os.path.join(PROCESSED_DIR, f))
    ]

    print(f"📄 JSONs encontrados: {len(files)}")

    for idx, file in enumerate(files, 1):
        print(f"\n [{idx}/{len(files)}] {file}")
        path = os.path.join(json_dir, file)
        data = load_json(path)

        if "nome_arquivos" not in data:
            print("⚠ nome_arquivos ausente")
            continue

        try:
            raw = call_gemini(system_prompt, {
                "base": base_prompt,
                "extra": data,
                "friendly_keys": list(friendly.keys()),
                "force_playlist": args.playlist
            })

            meta = safe_extract_json(raw)

            key = args.playlist or meta.get("playlist_key", "GeneralVocabulary")
            meta["playlist"] = build_playlist_object(key, friendly)
            meta.pop("playlist_key", None)

            video = find_video(video_dir, data["nome_arquivos"])
            final = write_final_json(video, meta)

            move_to_processed(path)

            print(f"✔ JSON FINAL: {final}")
            time.sleep(args.sleep_between)

        except Exception as e:
            print(f"❌ ERRO: {str(e)}")
            print("   JSON ORIGINAL PRESERVADO")

    print("\n Execução concluída")

if __name__ == "__main__":
    main()
