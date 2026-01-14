"""
=====================================================================
 Script: groq_MakeVideo.py
 Autor: Leandro

 VERSÃO FINAL:
  - Playlist sempre em OBJETO ÚNICO
  - Forçar playlist via CLI (--playlist)
  - Playlist automática via friendly_playlist_names.json
  - JSON original movido imediatamente para processed_json_dir
  - JSON final sempre salvo com o NOME DO VÍDEO
  - Correção automática de JSON malformado
  - Rate limit inteligente (jitter + respeito ao "try again in X ms")
  - Ignora arquivos já processados
  - Ignora arquivos que iniciam com uploaded_
  - Exibe total de arquivos ignorados por uploaded_
  - Remoção 100% da thumbnail
  - Delay entre chamadas ao Groq
  - SUPORTE A MÚLTIPLAS GROQ API KEYS (ROTATION)
  - ERROR REPORT JSON (RESILIÊNCIA)
=====================================================================

Exemplos:
python groq_MakeVideo.py "C:\\Content"
python groq_MakeVideo.py "C:\\Content" --playlist "Inglês para Viagem"
python groq_MakeVideo.py "C:\\Content" --sleep-between 30
python groq_MakeVideo.py "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\LTS SP Site - VideosGeradosPorScript\\Videos"
"""

import os
import json
import requests
import shutil
import argparse
import time
import random
import traceback
from datetime import datetime

# ======================================================================
# CONFIG
# ======================================================================

CONFIG_FILE = r"C:\dev\scripts\ScriptsUteis\Python\ContentFabric\4GroqIA\groq_MakeVideo.json"
ERROR_REPORT_FILE = "./groq_MakeVideo_error_report.json"

if not os.path.exists(CONFIG_FILE):
    raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")

CONFIG = json.load(open(CONFIG_FILE, "r", encoding="utf-8"))

API_URL = "https://api.groq.com/openai/v1/chat/completions"

API_KEYS_FILE = CONFIG["api_key_file"]
SYSTEM_PROMPT_FILE = CONFIG["system_prompt_file"]
BASE_PROMPT_FILE = CONFIG["base_prompt_file"]
FRIENDLY_PLAYLISTS_FILE = CONFIG["friendly_playlists_file"]

PROCESSED_DIR = CONFIG["processed_json_dir"]

MODEL_NAME = CONFIG["model"]
TEMPERATURE = CONFIG["temperature"]
VIDEO_EXTENSIONS = CONFIG["video_extensions"]
RETRY_MAX = CONFIG["retry_max_attempts"]
DEBUG = CONFIG["debug"]

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

def move_to_processed(src_path):
    ensure_dir(PROCESSED_DIR)
    new_path = os.path.join(PROCESSED_DIR, os.path.basename(src_path))
    shutil.move(src_path, new_path)
    return new_path

def find_video(video_dir, tag):
    for f in os.listdir(video_dir):
        if any(f.lower().endswith(ext) for ext in VIDEO_EXTENSIONS):
            if tag.lower() in f.lower():
                return os.path.join(video_dir, f)
    raise FileNotFoundError(f"Nenhum vídeo contendo '{tag}' encontrado em: {video_dir}")

def write_final_json(video_path, metadata_json):
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    final_path = os.path.join(os.path.dirname(video_path), f"{video_name}.json")
    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(metadata_json, f, ensure_ascii=False, indent=2)
    return final_path

# ======================================================================
# ERROR REPORT
# ======================================================================

def log_error_report(json_file, stage, exc: Exception):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "json_file": json_file,
        "stage": stage,
        "error_type": type(exc).__name__,
        "message": str(exc),
        "details": repr(exc),
        "stacktrace": traceback.format_exc()
    }

    if os.path.exists(ERROR_REPORT_FILE):
        report = load_json(ERROR_REPORT_FILE)
    else:
        report = []

    report.append(entry)

    with open(ERROR_REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"  Erro registrado em {ERROR_REPORT_FILE}")

# ======================================================================
# JSON FIX
# ======================================================================

def safe_extract_json(text):
    first = text.find("{")
    last = text.rfind("}")

    if first == -1 or last == -1:
        raise ValueError("Nenhum JSON válido encontrado.")

    raw = text[first:last + 1]

    try:
        return json.loads(raw)
    except:
        cleaned = raw.replace("\t", "").replace("\n\n", "\n")
        return json.loads(cleaned)

# ======================================================================
# GROQ KEYS MANAGER
# ======================================================================

def load_groq_keys(path):
    data = load_json(path)
    keys = [k["key"] for k in data if k.get("key")]
    if not keys:
        raise RuntimeError("Nenhuma API key válida encontrada em GroqKeys.json")
    return keys

class GroqKeyManager:
    def __init__(self, keys):
        self.keys = keys
        self.index = 0

    def next_key(self):
        key = self.keys[self.index]
        self.index = (self.index + 1) % len(self.keys)
        return key

# ======================================================================
# GROQ API
# ======================================================================

def call_groq(system_prompt, user_prompt, key_manager):
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": json.dumps(system_prompt)},
            {"role": "user", "content": json.dumps(user_prompt)}
        ],
        "temperature": TEMPERATURE
    }

    retries = 0
    attempted_keys = 0
    max_keys = len(key_manager.keys)

    while True:
        api_key = key_manager.next_key()
        attempted_keys += 1

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        res = requests.post(API_URL, json=payload, headers=headers)

        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]

        if res.status_code == 429:
            if attempted_keys < max_keys:
                continue

            wait = min(2 ** retries + random.uniform(0.5, 1.2), 60)
            time.sleep(wait)
            retries += 1
            attempted_keys = 0

            if retries > RETRY_MAX:
                raise RuntimeError("Rate limit excedido em todas as keys.")

            continue

        raise RuntimeError(res.text)

# ======================================================================
# PLAYLIST
# ======================================================================

def build_playlist_object(playlist_key, friendly):
    if playlist_key not in friendly:
        playlist_key = "GeneralVocabulary"

    entry = friendly[playlist_key]

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
    parser.add_argument("--sleep-between", type=int, default=20)
    args = parser.parse_args()

    json_dir = args.path
    video_dir = args.videos if args.videos else args.path

    ensure_dir(PROCESSED_DIR)

    system_prompt = load_json(SYSTEM_PROMPT_FILE)
    base_prompt = load_json(BASE_PROMPT_FILE)
    friendly_playlists = load_json(FRIENDLY_PLAYLISTS_FILE)

    key_manager = GroqKeyManager(load_groq_keys(API_KEYS_FILE))

    json_files = [
        f for f in os.listdir(json_dir)
        if f.endswith(".json")
        and not f.startswith("uploaded_")
        and not os.path.exists(os.path.join(PROCESSED_DIR, f))
    ]

    for idx, filename in enumerate(json_files, start=1):
        print(f"\n [{idx}/{len(json_files)}] Processando: {filename}")
        try:
            full_path = os.path.join(json_dir, filename)
            comp_json = load_json(full_path)

            if "nome_arquivos" not in comp_json:
                raise ValueError("'nome_arquivos' ausente")

            tag = comp_json["nome_arquivos"]
            move_to_processed(full_path)

            raw = call_groq(
                system_prompt,
                {
                    "base": base_prompt,
                    "extra": comp_json,
                    "friendly_keys": list(friendly_playlists.keys()),
                    "force_playlist": args.playlist
                },
                key_manager
            )

            metadata_json = safe_extract_json(raw)
            playlist_key = args.playlist or metadata_json.get("playlist_key", "GeneralVocabulary")
            metadata_json["playlist"] = build_playlist_object(playlist_key, friendly_playlists)
            metadata_json.pop("playlist_key", None)

            video_path = find_video(video_dir, tag)
            write_final_json(video_path, metadata_json)

            print("Sucesso")

        except Exception as e:
            log_error_report(filename, "processing", e)
            print("Erro tratado. Seguindo para o próximo.")

        time.sleep(args.sleep_between)

    print("\n Processo concluído com resiliência total.")

if __name__ == "__main__":
    main()
