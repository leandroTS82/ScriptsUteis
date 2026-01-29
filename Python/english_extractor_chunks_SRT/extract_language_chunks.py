import os
import sys
import json
import random
import requests
import re
from pathlib import Path
from itertools import cycle
from typing import List, Set

# =====================================================================================
# CONFIGURAÇÕES DO SISTEMA — MULTI GROQ KEYS (ROTATION / RANDOM)
# =====================================================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from groq_keys_loader import GROQ_KEYS

if not GROQ_KEYS or not all(isinstance(k, dict) and "key" in k for k in GROQ_KEYS):
    raise RuntimeError("❌ GROQ_KEYS inválidas ou mal carregadas")

_groq_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

# =====================================================================================
# CONFIGURAÇÃO DE CHUNKING
# =====================================================================================

QTD_LINES_EN = 150   # 🔥 quantidade de linhas por request (ajuste se necessário)

# =====================================================================================
# PATHS
# =====================================================================================

SRT_DIR = Path("./filesSrt")
PROMPTS_DIR = Path("./prompts")
OUTPUT_FILE = Path("./output_chunks.json")

PROMPT_FILE = PROMPTS_DIR / "extract_chunks.txt"

TIMEOUT = 60

# =====================================================================================
# HELPERS
# =====================================================================================

def load_prompt() -> str:
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"Prompt não encontrado: {PROMPT_FILE}")
    return PROMPT_FILE.read_text(encoding="utf-8").strip()


def extract_clean_lines_from_srt(text: str) -> List[str]:
    """
    Retorna apenas linhas válidas de texto (sem timestamps, índices, tags)
    """
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r"^\d+$", line):
            continue
        if "-->" in line:
            continue
        line = re.sub(r"<[^>]+>", "", line)
        lines.append(line)
    return lines


def chunk_lines(lines: List[str], size: int) -> List[List[str]]:
    return [lines[i:i + size] for i in range(0, len(lines), size)]


def call_groq(prompt: str, content: str) -> List[str]:
    """
    Executa UMA chamada Groq usando UMA key
    """
    key_info = next(_groq_key_cycle)
    api_key = key_info["key"]
    key_name = key_info.get("name", "unknown")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ],
        "temperature": 0.2
    }

    response = requests.post(
        GROQ_URL,
        headers=headers,
        json=payload,
        timeout=TIMEOUT
    )

    if response.status_code == 401:
        raise RuntimeError(f"API Key inválida ({key_name})")

    if response.status_code == 413:
        raise RuntimeError(f"Payload grande demais ({key_name})")

    if response.status_code != 200:
        raise RuntimeError(
            f"Groq error {response.status_code} ({key_name}): {response.text}"
        )

    raw = response.json()["choices"][0]["message"]["content"]

    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("Resposta Groq não é uma lista JSON")

    return [str(x).strip() for x in data if str(x).strip()]


# =====================================================================================
# MAIN
# =====================================================================================

def main():
    prompt = load_prompt()

    if not SRT_DIR.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {SRT_DIR}")

    global_seen: Set[str] = set()
    result = []

    srt_files = sorted(SRT_DIR.glob("*.srt"))

    for srt_file in srt_files:
        print(f"\n🔍 Processando: {srt_file.name}")

        raw_text = srt_file.read_text(encoding="utf-8", errors="ignore")
        clean_lines = extract_clean_lines_from_srt(raw_text)

        if not clean_lines:
            print("⚠️  Nenhuma linha válida encontrada")
            continue

        chunks_per_file = []
        line_chunks = chunk_lines(clean_lines, QTD_LINES_EN)

        for idx, lines_block in enumerate(line_chunks, start=1):
            block_text = "\n".join(lines_block)

            try:
                extracted = call_groq(prompt, block_text)
            except Exception as e:
                print(f"❌ Chunk {idx}/{len(line_chunks)} falhou: {e}")
                continue

            for chunk in extracted:
                key = chunk.lower()
                if key not in global_seen:
                    global_seen.add(key)
                    chunks_per_file.append(chunk)

            print(f"   ✔ Chunk {idx}/{len(line_chunks)} → {len(extracted)} itens")

        result.append({
            "fileName": srt_file.name,
            "pending": chunks_per_file
        })

        print(f"   ✅ Total arquivo: {len(chunks_per_file)} chunks únicos")

    OUTPUT_FILE.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\n🏁 FINALIZADO")
    print(f"📄 Arquivo gerado: {OUTPUT_FILE}")
    print(f"📊 Total global único: {len(global_seen)} chunks")


if __name__ == "__main__":
    main()
