"""
=====================================================================
 Script: groq_MakeVideo.py
 Autor: Leandro

 Versão com:
  - Configuração completa via groq_MakeVideo.json
  - Controle de thumbnail
  - Mudança fácil de modelo/temperatura
  - Suporte a debug
  - NOVO: Se apenas 1 path for informado → usar o mesmo diretório
=====================================================================

python groq_MakeVideo.py "C:\\dev\\scripts\\ScriptsUteis\\Python\\Gemini\\MakeVideoGemini\\outputs\\videos"

"""

import os
import json
import requests
from datetime import datetime
import sys
import time
from generate_thumbnail import create_thumbnail


# ======================================================================
# LOAD GLOBAL CONFIG
# ======================================================================

CONFIG_FILE = "C:\\dev\\scripts\\ScriptsUteis\\Python\\ContentFabric\\4GroqIA\\groq_MakeVideo.json"

if not os.path.exists(CONFIG_FILE):
    raise FileNotFoundError(f"Config file not found: {CONFIG_FILE}")

CONFIG = json.load(open(CONFIG_FILE, "r", encoding="utf-8"))

API_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY_FILE = CONFIG["api_key_file"]
SYSTEM_PROMPT_FILE = CONFIG["system_prompt_file"]
BASE_PROMPT_FILE = CONFIG["base_prompt_file"]
OUTPUT_DIR = CONFIG["output_dir"]

MODEL_NAME = CONFIG["model"]
TEMPERATURE = CONFIG["temperature"]
VIDEO_EXTENSIONS = CONFIG["video_extensions"]
RETRY_MAX = CONFIG["retry_max_attempts"]
ENABLE_THUMB = CONFIG["enable_thumbnail"]
DEBUG = CONFIG["debug"]


# ======================================================================
# Utils
# ======================================================================

def log(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")


def load_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    return open(path, "r", encoding="utf-8").read().strip()


def load_json(path):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    return json.load(open(path, "r", encoding="utf-8"))


# ✔ AJUSTADO — metadata agora tem o nome EXATO do arquivo
def save_output_json(content, base_name):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    filename = os.path.join(OUTPUT_DIR, f"{base_name}.json")

    open(filename, "w", encoding="utf-8").write(content)
    return filename


def find_video(dest_directory, tag):
    for f in os.listdir(dest_directory):
        f_low = f.lower()
        if any(f_low.endswith(ext) for ext in VIDEO_EXTENSIONS):
            if tag.lower() in f_low:
                return os.path.join(dest_directory, f)
    raise FileNotFoundError(f"No video containing '{tag}' found.")


def write_json_for_video(dest_dir, video_path, metadata_text):
    base = os.path.splitext(os.path.basename(video_path))[0]
    out_json = os.path.join(dest_dir, base + ".json")
    open(out_json, "w", encoding="utf-8").write(metadata_text)
    return out_json


# ✔ AJUSTADO — agora o prefixo é AlteradoPorgroq_MakeVideo_
def rename_processed(input_path):
    folder = os.path.dirname(input_path)
    old = os.path.basename(input_path)

    new_name = f"AlteradoPorgroq_MakeVideo_{old}"
    new_path = os.path.join(folder, new_name)

    os.rename(input_path, new_path)
    return new_path


# ======================================================================
# Groq API call with retry
# ======================================================================

def call_groq(system_prompt, user_prompt):
    api_key = load_file(API_KEY_FILE)

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
        log(f"Sending request to Groq... attempt {retries+1}")

        res = requests.post(API_URL, json=payload, headers=headers)

        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]

        if res.status_code == 429:
            print("\n[Rate Limit] Groq pediu para aguardar...")

            try:
                msg = res.json().get("error", {}).get("message", "")
                if "try again in" in msg:
                    ms = int(msg.split("try again in")[1].split("ms")[0].strip())
                    wait = ms / 1000
                else:
                    wait = 2 ** retries
            except:
                wait = 2 ** retries

            print(f"Aguardando {wait:.2f} segundos...\n")
            time.sleep(wait)

            retries += 1
            if retries > RETRY_MAX:
                raise RuntimeError("Max retry reached!")

            continue

        print("ERRO:", res.text)
        res.raise_for_status()


# ======================================================================
# MAIN
# ======================================================================

def main():

    if len(sys.argv) < 2:
        print("Uso:")
        print("python groq_MakeVideo.py <path> [videos_dir]")
        sys.exit(1)

    # Caso só um path seja informado → tudo acontece nele
    if len(sys.argv) == 2:
        json_dir = sys.argv[1]
        video_dir = sys.argv[1]
        print("📁 Modo simplificado: usando o mesmo diretório para JSONs e Vídeos.\n")
    else:
        json_dir = sys.argv[1]
        video_dir = sys.argv[2]

    if not os.path.isdir(json_dir):
        raise NotADirectoryError(json_dir)
    if not os.path.isdir(video_dir):
        raise NotADirectoryError(video_dir)

    print(f"📦 Processando JSONs em: {json_dir}")
    print(f"🎥 Buscando vídeos em: {video_dir}\n")

    system_prompt = load_json(SYSTEM_PROMPT_FILE)
    base_prompt = load_json(BASE_PROMPT_FILE)

    files = [
        f for f in os.listdir(json_dir)
        if f.endswith(".json") and not f.lower().startswith("alteradoporgroq_makevideo_")
    ]

    print(f"Encontrados {len(files)} arquivo(s)\n")

    for file in files:

        full_path = os.path.join(json_dir, file)
        print(f"\n📄 Processando: {file}")

        comp_json = load_json(full_path)

        if "nome_arquivos" not in comp_json:
            print("⚠ Ignorado (sem nome_arquivos)")
            continue

        nome = comp_json["nome_arquivos"]

        merged_prompt = {
            "base": base_prompt,
            "extra": comp_json
        }

        print("🚀 Chamando Groq...")
        metadata = call_groq(system_prompt, merged_prompt)

        # ✔ AJUSTADO — metadata salva com nome EXATO
        out_meta_path = save_output_json(metadata, base_name=nome)
        print(f"✔ Metadata salva: {out_meta_path}")

        print("🎥 Localizando vídeo...")
        video_path = find_video(video_dir, nome)

        new_json_path = write_json_for_video(video_dir, video_path, metadata)
        print(f"✔ JSON criado: {new_json_path}")

        if ENABLE_THUMB:
            print("🖼 Gerando Thumbnail...")
            try:
                create_thumbnail(new_json_path)
                print("✔ Thumbnail criada.")
            except Exception as e:
                print(f"⚠ Erro no thumbnail: {e}")
        else:
            print("⏭ Thumbnail desativado (config).")

        # ✔ AJUSTADO — renomeia com prefixo correto
        new_path = rename_processed(full_path)
        print(f"🔁 Renomeado para: {new_path}")

    print("\n🎉 Processo concluído!\n")


if __name__ == "__main__":
    main()
