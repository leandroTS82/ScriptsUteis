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
  - Correção automática da playlist (remove listas)
  - Rate limit inteligente (jitter + respeito ao "try again in X ms")
  - Ignora arquivos já processados
  - Remoção 100% da thumbnail
=====================================================================

Exemplos:
python groq_MakeVideo.py "C:\\Content"
python groq_MakeVideo.py "C:\\Content" --playlist "Inglês para Viagem"
python groq_MakeVideo.py "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\LTS SP Site - VideosGeradosPorScript\\Videos"
"""
import os
import json
import requests
import shutil
import argparse
import time
import random


# ======================================================================
# CONFIG
# ======================================================================

CONFIG_FILE = r"C:\dev\scripts\ScriptsUteis\Python\ContentFabric\4GroqIA\groq_MakeVideo.json"

if not os.path.exists(CONFIG_FILE):
    raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")

CONFIG = json.load(open(CONFIG_FILE, "r", encoding="utf-8"))

API_URL = "https://api.groq.com/openai/v1/chat/completions"

API_KEY_FILE = CONFIG["api_key_file"]
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


def load_text(path):
    return open(path, "r", encoding="utf-8").read().strip()


def load_json(path):
    return json.load(open(path, "r", encoding="utf-8"))


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def move_to_processed(src_path):
    """Move JSON original imediatamente."""
    ensure_dir(PROCESSED_DIR)
    new_path = os.path.join(PROCESSED_DIR, os.path.basename(src_path))
    shutil.move(src_path, new_path)
    return new_path


def find_video(video_dir, tag):
    """Procura vídeo cujo nome contém o nome_arquivos."""
    for f in os.listdir(video_dir):
        if any(f.lower().endswith(ext) for ext in VIDEO_EXTENSIONS):
            if tag.lower() in f.lower():
                return os.path.join(video_dir, f)

    raise FileNotFoundError(f"Nenhum vídeo contendo '{tag}' encontrado em: {video_dir}")


def write_final_json(video_path, metadata_json):
    """Salva metadados com o MESMO NOME do vídeo."""
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    final_path = os.path.join(os.path.dirname(video_path), f"{video_name}.json")

    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(metadata_json, f, ensure_ascii=False, indent=2)

    return final_path


# ======================================================================
# JSON FIX & VALIDATION
# ======================================================================

def safe_extract_json(text):
    """Extrai e corrige JSON malformado vindo do Groq."""
    first = text.find("{")
    last = text.rfind("}")

    if first == -1 or last == -1:
        raise ValueError("❌ Nenhum JSON válido encontrado.")

    raw = text[first:last+1]

    try:
        return json.loads(raw)
    except:
        pass

    # Tentar correção simples
    cleaned = raw.replace("\t", "").replace("\n\n", "\n")
    try:
        return json.loads(cleaned)
    except:
        print("❌ JSON retornado pela IA não pôde ser corrigido:")
        print(raw)
        raise


# ======================================================================
# GROQ API WITH RATE LIMIT CONTROL
# ======================================================================

def call_groq(system_prompt, user_prompt):
    api_key = load_text(API_KEY_FILE)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = [
        {"role": "system", "content": json.dumps(system_prompt)},
        {"role": "user", "content": json.dumps(user_prompt)}
    ]

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": TEMPERATURE
    }

    retries = 0

    while True:
        res = requests.post(API_URL, json=payload, headers=headers)

        # SUCESSO
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]

        # RATE LIMIT
        if res.status_code == 429:
            wait_ms = None
            try:
                msg = res.json().get("error", {}).get("message", "")
                if "try again in" in msg.lower():
                    wait_ms = int(msg.lower().split("try again in")[1].split("ms")[0])
            except:
                pass

            if wait_ms:
                wait = wait_ms / 1000
            else:
                wait = min(2 ** retries + random.uniform(0.1, 0.3), 30)

            print(f"[Groq] Rate limit detectado → aguardando {wait:.2f}s…")
            time.sleep(wait)

            retries += 1
            if retries > RETRY_MAX:
                raise RuntimeError("❌ Tentativas máximas atingidas no rate limit.")

            continue

        # OUTRO ERRO
        raise RuntimeError(f"Erro inesperado da API Groq:\n{res.text}")


# ======================================================================
# BUILD DEFINITIVE PLAYLIST OBJECT
# ======================================================================

def build_playlist_object(playlist_key, friendly):
    """Converte playlist_key → playlist final com name + description."""
    if playlist_key not in friendly:
        print(f"⚠ Playlist_key '{playlist_key}' não encontrada. Usando 'GeneralVocabulary'.")
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
    parser.add_argument("path", help="Pasta contendo JSONs e/ou vídeos")
    parser.add_argument("--videos", help="Pasta onde estão os vídeos")
    parser.add_argument("--playlist", help="Playlist fixa (sobrescreve IA)")
    args = parser.parse_args()

    json_dir = args.path
    video_dir = args.videos if args.videos else args.path

    ensure_dir(PROCESSED_DIR)

    system_prompt = load_json(SYSTEM_PROMPT_FILE)
    base_prompt = load_json(BASE_PROMPT_FILE)
    friendly_playlists = load_json(FRIENDLY_PLAYLISTS_FILE)

    # JSONs ainda não processados
    json_files = [
        f for f in os.listdir(json_dir)
        if f.endswith(".json") and not os.path.exists(os.path.join(PROCESSED_DIR, f))
    ]

    print(f"📄 JSONs encontrados: {len(json_files)}")

    for filename in json_files:

        full_path = os.path.join(json_dir, filename)
        print(f"\n🔎 Processando: {filename}")

        comp_json = load_json(full_path)

        if "nome_arquivos" not in comp_json:
            print("⚠ 'nome_arquivos' ausente. Ignorando.")
            continue

        tag = comp_json["nome_arquivos"]

        # Mover original imediatamente
        moved_path = move_to_processed(full_path)
        print(f"📁 JSON original movido para: {moved_path}")

        # Criar prompt
        user_prompt = {
            "base": base_prompt,
            "extra": comp_json,
            "friendly_keys": list(friendly_playlists.keys()),
            "force_playlist": args.playlist
        }

        print("🚀 Chamando Groq…")
        raw_output = call_groq(system_prompt, user_prompt)

        print("🧪 Validando JSON retornado...")
        metadata_json = safe_extract_json(raw_output)

        # ------------------------------
        # PLAYLIST KEY → PLAYLIST FINAL
        # ------------------------------
        if args.playlist:
            playlist_key = args.playlist
        else:
            playlist_key = metadata_json.get("playlist_key", "GeneralVocabulary")

        metadata_json["playlist"] = build_playlist_object(playlist_key, friendly_playlists)

        # remover a chave auxiliar
        if "playlist_key" in metadata_json:
            del metadata_json["playlist_key"]

        print(f"📌 Playlist selecionada: {metadata_json['playlist']['name']}")

        # Localizar vídeo
        print("🎥 Procurando vídeo…")
        video_path = find_video(video_dir, tag)

        # Escrever JSON final
        final_json_path = write_final_json(video_path, metadata_json)
        print(f"✔ JSON FINAL CRIADO: {final_json_path}")

    print("\n🎉 Processo concluído com sucesso!\n")


if __name__ == "__main__":
    main()