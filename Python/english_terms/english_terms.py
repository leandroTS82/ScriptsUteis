import os
import json
import re
from typing import Any, Set, List
from langdetect import detect, LangDetectException

# =========================================================
# CONFIGURAÇÕES
# python english_terms.py
# =========================================================

ROOT_PATHS: List[str] = [
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript"
]

OUTPUT_FILE = "./english_terms.json"

MAX_TEXT_LENGTH = 10

PHRASES_TO_REMOVE = [
    "você não vai acreditar",
    "você já usou",
    "você já se sentiu assim",
    "você já se pegou procrastinando",
    "você já recebeu um",
    "você já ouviu",
    "você vai se surpreender",
    " e ficou confuso "
]

IGNORED_FILES = [
    "Tema_Tirelessly_FULL.json"
]

# =========================================================
# NORMALIZAÇÃO E LIMPEZA
# =========================================================

def clean_unwanted_phrases(text: str) -> str:
    """
    Remove frases em português mesmo com variações de espaços.
    """
    text_lower = text.lower()

    for phrase in PHRASES_TO_REMOVE:
        phrase = phrase.lower().strip()
        pattern = r"\s*" + re.escape(phrase) + r"\s*"
        text_lower = re.sub(pattern, " ", text_lower)

    text_lower = re.sub(r"\s{2,}", " ", text_lower)
    return text_lower.strip()


def normalize(text: str) -> str:
    """
    Limpeza final e padronização.
    """
    if not text:
        return ""

    # 🔥 normalização crítica: underline vira espaço
    text = text.replace("_", " ")
    text = text.replace("'", "")

    text = clean_unwanted_phrases(text)
    text = re.sub(r"[^\w\s']", "", text)
    text = re.sub(r"\s{2,}", " ", text)

    return text.strip().lower()


def is_english(text: str) -> bool:
    """
    Garantia alta:
    - texto limpo
    - tamanho válido
    - idioma real
    """
    if not text:
        return False

    if len(text) < 4 or len(text) > MAX_TEXT_LENGTH:
        return False

    try:
        return detect(text) == "en"
    except LangDetectException:
        return False


# =========================================================
# EXTRAÇÃO RECURSIVA
# =========================================================

def extract_from_obj(obj: Any, results: Set[str]):
    if isinstance(obj, dict):

        if obj.get("lang") == "en" and isinstance(obj.get("text"), str):
            normalized = normalize(obj["text"])
            if is_english(normalized):
                results.add(normalized)

        for key, value in obj.items():
            if key in {"title", "description", "introducao", "name"} and isinstance(value, str):
                normalized = normalize(value)
                if is_english(normalized):
                    results.add(normalized)

            extract_from_obj(value, results)

    elif isinstance(obj, list):
        for item in obj:
            extract_from_obj(item, results)

    elif isinstance(obj, str):
        normalized = normalize(obj)
        if is_english(normalized):
            results.add(normalized)


def extract_from_json_file(file_path: str, results: Set[str]):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        extract_from_obj(data, results)

    except Exception as e:
        print(f"⚠️  Erro ao processar: {file_path}")
        print(f"    ↳ {e}")


# =========================================================
# EXECUÇÃO PRINCIPAL
# =========================================================

def main():
    english_terms: Set[str] = set()
    ignored_files_lower = {f.lower() for f in IGNORED_FILES}

    total_files = 0
    processed_files = 0

    print(" Iniciando varredura de paths...\n")

    for root_path in ROOT_PATHS:
        print(f"📂 Path base: {root_path}")

        for root, _, files in os.walk(root_path):
            json_files = [f for f in files if f.lower().endswith(".json")]
            total_files += len(json_files)

            for file in json_files:
                if file.lower() in ignored_files_lower:
                    continue

                full_path = os.path.join(root, file)
                processed_files += 1

                print(f"  ▶️  [{processed_files}/{total_files}] Processando: {file}")
                extract_from_json_file(full_path, english_terms)

    # 🔥 Garantia final de deduplicação sem underline
    normalized_final_terms = {
        normalize(term) for term in english_terms if normalize(term)
    }

    output = {
        "source_paths": ROOT_PATHS,
        "max_text_length": MAX_TEXT_LENGTH,
        "ignored_files": IGNORED_FILES,
        "removed_phrases": PHRASES_TO_REMOVE,
        "total_terms": len(normalized_final_terms),
        "terms": sorted(normalized_final_terms)
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\n✅ Extração concluída — APENAS INGLÊS")
    print(f"📄 Arquivo gerado: {OUTPUT_FILE}")
    print(f" Arquivos processados: {processed_files}")
    print(f"🔤 Total de termos únicos finais: {len(normalized_final_terms)}")


if __name__ == "__main__":
    main()
