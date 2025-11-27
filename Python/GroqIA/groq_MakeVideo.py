"""
=====================================================================
 Script: groq_MakeVideo.py
 Autor: Leandro
 Finalidade geral:
    Este script automatiza a geração de metadados para vídeos do YouTube
    com base no modelo Groq, unindo:
       - makevideoLabelPrompt.json (instruções base da lição)
       - JSONs complementares de um diretório de entrada
       - systemPrompt.json (regras fixas para criação do metadata)

 Nova melhoria:
    Em vez de sobrescrever JSONs existentes no diretório destino,
    o script agora:

       1) Procura um ARQUIVO DE VÍDEO que contenha "nome_arquivos"
       2) Cria um novo arquivo JSON com o mesmo nome do vídeo encontrado
          (ex: Lesson3_FULL.mp4 → Lesson3_FULL.json)
       3) Escreve o JSON retornado pela Groq nesse novo arquivo

 Outras capacidades:
    - Ignora arquivos do diretório de entrada cujo nome comece com "ToGroq_"
    - Renomeia arquivos já processados para ToGroq_<nome>
    - Retry e backoff para problemas de rate limit da Groq

 Uso:
    python groq_MakeVideo.py <path_jsons_complementares> <path_videos_destino>
exemplo:
python groq_MakeVideo.py "C:\\dev\\scripts\\ScriptsUteis\\Python\\MakeVideo\\Content\\20251124_wordBank" "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\LTS SP Site - Audios para estudar inglês\\VideosGeradosPorScript\\GOOGLE_TTS\\WordBank"
=====================================================================
"""

import os
import json
import requests
from datetime import datetime
import sys
import time
from generate_thumbnail import create_thumbnail

API_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY_FILE = "C:\\dev\\scripts\\ScriptsUteis\\Python\\GroqIA\\groq_api_key.txt"
SYSTEM_PROMPT_FILE = "C:\\dev\\scripts\\ScriptsUteis\\Python\\GroqIA\\systemPrompt.json"
BASE_PROMPT_FILE = "C:\\dev\\scripts\\ScriptsUteis\\Python\\GroqIA\\makevideoLabelPrompt.json"
OUTPUT_DIR = "C:\\dev\\scripts\\ScriptsUteis\\Python\\GroqIA\\output"
MODEL_NAME = "openai/gpt-oss-20b"

VIDEO_EXTENSIONS = [".mp4", ".mov", ".mkv", ".avi"]


"""
=====================================================================
 Funções utilitárias
=====================================================================
"""


def load_api_key():
    """Carrega a API key a partir de groq_api_key.txt"""
    if not os.path.exists(API_KEY_FILE):
        raise FileNotFoundError("groq_api_key.txt not found.")

    with open(API_KEY_FILE, "r", encoding="utf-8") as f:
        key = f.read().strip()

    if not key:
        raise ValueError("groq_api_key.txt is empty.")

    return key


def load_json(path):
    """Carrega um arquivo JSON validando erros"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in {path}: {str(e)}")


def save_output_json(content, suffix=""):
    """Salva o JSON retornado pela Groq no diretório ./output"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = os.path.join(
        OUTPUT_DIR,
        f"metadata_{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return filename


def find_video_by_tag(dest_directory, nome_arquivos):
    """
    Procura no diretório destino um arquivo de vídeo cujo nome contenha nome_arquivos.
    Retorna o caminho completo do arquivo.
    """
    for file in os.listdir(dest_directory):
        lower = file.lower()
        if any(lower.endswith(ext) for ext in VIDEO_EXTENSIONS):
            if nome_arquivos.lower() in lower:
                return os.path.join(dest_directory, file)

    raise FileNotFoundError(
        f"No video file containing '{nome_arquivos}' found in destination folder."
    )


def write_json_for_video(dest_directory, video_file_path, metadata_json):
    """
    Cria um arquivo JSON com o nome do arquivo de vídeo encontrado.
    Exemplo: video.mp4 → video.json
    """
    base_name = os.path.splitext(os.path.basename(video_file_path))[0]
    json_path = os.path.join(dest_directory, base_name + ".json")

    with open(json_path, "w", encoding="utf-8") as f:
        f.write(metadata_json)

    return json_path


def rename_to_processed(original_path):
    """Renomeia arquivo complementar para evitar reprocessamento."""
    directory = os.path.dirname(original_path)
    filename = os.path.basename(original_path)
    new_name = f"ToGroq_{filename}"
    new_path = os.path.join(directory, new_name)
    os.rename(original_path, new_path)
    return new_path


"""
=====================================================================
 Função de chamada para Groq com Retry e Backoff Inteligente
=====================================================================
"""


def call_groq(system_prompt, merged_prompt):
    """
    Envia o prompt para Groq com retry e backoff.
    """
    api_key = load_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = [
        {"role": "system", "content": json.dumps(system_prompt)},
        {"role": "user", "content": json.dumps(merged_prompt)}
    ]

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.2
    }

    max_retries = 5
    retry = 0

    while True:
        response = requests.post(API_URL, json=payload, headers=headers)

        # sucesso
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]

        # rate limit
        if response.status_code == 429:
            print("\n[Rate Limit] Groq solicitou espera...")

            try:
                data = response.json()
                message = data.get("error", {}).get("message", "")
                if "try again in" in message:
                    ms = int(message.split("try again in")[1].split("ms")[0].strip())
                    wait_seconds = ms / 1000
                else:
                    wait_seconds = 2 ** retry
            except Exception:
                wait_seconds = 2 ** retry

            print(f"Aguardando {wait_seconds} segundos...")
            time.sleep(wait_seconds)

            retry += 1
            if retry > max_retries:
                raise RuntimeError("Exceeded maximum retries due to rate limits.")

            continue

        # outros erros
        print("Groq API error:")
        print(response.text)
        response.raise_for_status()


"""
=====================================================================
 PROCESSAMENTO PRINCIPAL
=====================================================================
"""


def main():

    if len(sys.argv) < 3:
        print("Uso correto:")
        print("python groq_MakeVideo.py <path_jsons_complementares> <path_videos_destino>")
        sys.exit(1)

    source_dir = sys.argv[1]
    dest_dir = sys.argv[2]

    if not os.path.isdir(source_dir):
        raise NotADDirectoryError("Primeiro argumento deve ser um diretório válido.")

    if not os.path.isdir(dest_dir):
        raise NotADDirectoryError("Segundo argumento deve ser um diretório válido.")

    system_prompt = load_json(SYSTEM_PROMPT_FILE)
    base_prompt = load_json(BASE_PROMPT_FILE)

    print("Base prompt e system prompt carregados com sucesso.")

    # Processar apenas arquivos .json que NÃO começam com ToGroq_
    files = [
        f for f in os.listdir(source_dir)
        if f.endswith(".json") and not f.lower().startswith("togroq_")
    ]

    print(f"Encontrados {len(files)} arquivos para processar em: {source_dir}")

    for file in files:
        full_source_path = os.path.join(source_dir, file)
        print(f"\nProcessando: {file}")

        comp_json = load_json(full_source_path)

        if "nome_arquivos" not in comp_json:
            print("Arquivo ignorado pois não contém 'nome_arquivos'.")
            continue

        nome_arquivos = comp_json["nome_arquivos"]

        # Combinar prompts
        merged_prompt = {
            "base": base_prompt,
            "extra": comp_json
        }

        # Groq
        print("Chamando Groq...")
        metadata_json = call_groq(system_prompt, merged_prompt)

        # Salvar output em ./output
        saved_path = save_output_json(metadata_json, suffix=nome_arquivos)
        print(f"Metadata salva em: {saved_path}")

        # Procurar vídeo correspondente
        print("Localizando arquivo de vídeo...")
        video_file_path = find_video_by_tag(dest_dir, nome_arquivos)

        # Criar JSON com nome do vídeo
        new_json_path = write_json_for_video(dest_dir, video_file_path, metadata_json)
        print(f"JSON criado: {new_json_path}")
        
        # === NOVA ETAPA: GERAR THUMBNAIL ===
        try:
            print("🎨 Gerando Thumbnail...")
            create_thumbnail(new_json_path) # Gera o .jpg na mesma pasta do vídeo
        except Exception as e:
            print(f"⚠️ Erro ao gerar thumbnail: {e}")
        # ===================================

        # Renomear arquivo de entrada
        new_name = rename_to_processed(full_source_path)
        print(f"Arquivo complementar renomeado para: {new_name}")

    print("\nProcessamento concluído com sucesso.")


if __name__ == "__main__":
    main()
