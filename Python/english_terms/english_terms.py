import os
import json
import re
from typing import Any, Set
from langdetect import detect, LangDetectException

# =========================================================
# CONFIGURAÇÕES
# python english_terms.py
# =========================================================

ROOT_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript"
OUTPUT_FILE = "./english_terms.json"

MAX_TEXT_LENGTH = 40

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

    # normaliza espaços
    text_lower = re.sub(r"\s{2,}", " ", text_lower)

    return text_lower.strip()


def normalize(text: str) -> str:
    """
    Limpeza final e padronização.
    """
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
        print(f"⚠️ Erro ao processar {file_path}: {e}")


# =========================================================
# EXECUÇÃO PRINCIPAL
# =========================================================

def main():
    english_terms: Set[str] = set()
    ignored_files_lower = {f.lower() for f in IGNORED_FILES}

    for root, _, files in os.walk(ROOT_PATH):
        for file in files:
            if not file.lower().endswith(".json"):
                continue

            if file.lower() in ignored_files_lower:
                continue

            extract_from_json_file(os.path.join(root, file), english_terms)

    output = {
        "source_path": ROOT_PATH,
        "max_text_length": MAX_TEXT_LENGTH,
        "ignored_files": IGNORED_FILES,
        "removed_phrases": PHRASES_TO_REMOVE,
        "total_terms": len(english_terms),
        "terms": sorted(english_terms)
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("✅ Extração concluída — APENAS INGLÊS")
    print(f"📄 Arquivo gerado: {OUTPUT_FILE}")
    print(f"🔤 Total de termos únicos: {len(english_terms)}")


if __name__ == "__main__":
    main()
