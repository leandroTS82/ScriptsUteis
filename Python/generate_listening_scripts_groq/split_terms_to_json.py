import os
import json
import math
from datetime import datetime

# ==========================================================
# CONFIGURAÇÕES
# python split_terms_to_json.py
# ==========================================================

INPUT_TXT = "bigTerms.txt"          # arquivo de entrada
OUTPUT_DIR = "./CreateLater"        # pasta de saída
ITEMS_PER_FILE = 20                 # <<< QUANTIDADE POR JSON

JSON_KEY = "pending"                # chave fixa do JSON

# ==========================================================
# FUNÇÕES
# ==========================================================

def clean_line(line: str) -> str:
    """
    Remove aspas, vírgulas e espaços extras.
    """
    return line.strip().strip(",").strip('"').strip("'").strip()


def load_terms(txt_path: str) -> list[str]:
    if not os.path.exists(txt_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {txt_path}")

    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    terms = [clean_line(l) for l in lines if clean_line(l)]
    return terms


def chunk_list(data: list, chunk_size: int):
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]


def save_json(data: list[str], index: int):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%y%m%d%H%M")
    filename = f"{timestamp}_terms_part_{index:02d}.json"
    path = os.path.join(OUTPUT_DIR, filename)

    payload = {
        JSON_KEY: data
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"✔ Arquivo gerado: {path} ({len(data)} itens)")


# ==========================================================
# MAIN
# ==========================================================

def main():
    terms = load_terms(INPUT_TXT)

    total_terms = len(terms)
    total_files = math.ceil(total_terms / ITEMS_PER_FILE)

    print(f"📄 Total de termos: {total_terms}")
    print(f"📦 Itens por arquivo: {ITEMS_PER_FILE}")
    print(f"🗂 Total de arquivos a gerar: {total_files}")
    print("-" * 50)

    for idx, chunk in enumerate(chunk_list(terms, ITEMS_PER_FILE), start=1):
        save_json(chunk, idx)

    print("\n✅ Processo finalizado com sucesso.")


if __name__ == "__main__":
    main()
