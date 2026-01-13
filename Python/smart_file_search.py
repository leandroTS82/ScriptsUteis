"""
===========================================================
 Script: python smart_file_search.py
 Autor: Leandro
===========================================================

Busca inteligente por termos em arquivos (PDF),
com ranking de relevância baseado em:
- Nome do arquivo
- Corpo do texto

Compatível com:
- Windows / Linux / macOS
- Android (via Termux ou storage montado)
===========================================================
"""

import os
import re
from typing import List, Dict
from PyPDF2 import PdfReader

# =========================================================
# CONFIGURAÇÕES
# =========================================================

SEARCH_PATHS = [
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript",
    # "/storage/emulated/0"  # Android (Termux)
]

IGNORED_EXTENSIONS = [
    ".exe", ".dll", ".bin", ".jpg", ".png", ".mp4", ".zip",
    ".txt", ".json", ".md", ".html", ".htm"
]

SUPPORTED_EXTENSIONS = [
    ".pdf",".json"
]

CASE_INSENSITIVE = True

# 🧩 SNIPPET
SNIPPET_CHARS = 50  # caracteres antes e depois do termo

# 🎨 CORES (ANSI)
COLOR_HIGHLIGHT = "\033[93m"  # amarelo
COLOR_RESET = "\033[0m"

# =========================================================
# UTILITÁRIOS
# =========================================================

def normalize(text: str) -> str:
    return text.lower() if CASE_INSENSITIVE else text


def clean_text(text: str) -> str:
    text = text.replace("\n", " ")
    return re.sub(r"\s+", " ", text)


def read_file_content(path: str) -> str:
    try:
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return ""


def extract_snippets(content: str, term: str) -> List[str]:
    snippets = []

    clean = clean_text(content)
    clean_norm = normalize(clean)
    term_norm = normalize(term)

    start = 0
    while True:
        index = clean_norm.find(term_norm, start)
        if index == -1:
            break

        begin = max(0, index - SNIPPET_CHARS)
        end = min(len(clean), index + len(term) + SNIPPET_CHARS)

        snippet = clean[begin:end]

        # destaca termo
        snippet_highlighted = re.sub(
            re.escape(term),
            f"{COLOR_HIGHLIGHT}{term}{COLOR_RESET}",
            snippet,
            flags=re.IGNORECASE
        )

        snippets.append(f"... {snippet_highlighted} ...")
        start = index + len(term_norm)

    return snippets


def score_content(term: str, filename: str, content: str) -> Dict:
    score = 0
    occurrences = []
    snippets = []

    term_norm = normalize(term)
    filename_norm = normalize(filename)
    content_norm = normalize(content)

    # 🔥 Nome do arquivo
    if term_norm in filename_norm:
        score += 100
        occurrences.append("nome_do_arquivo")

    # ℹ️ Corpo do texto
    body_count = content_norm.count(term_norm)
    if body_count > 0:
        score += body_count * 10
        occurrences.append(f"corpo_texto({body_count})")
        snippets = extract_snippets(content, term)

    return {
        "score": score,
        "occurrences": occurrences,
        "snippets": snippets
    }

# =========================================================
# BUSCA PRINCIPAL
# =========================================================

def search(term: str) -> List[Dict]:
    results = []

    for base_path in SEARCH_PATHS:
        for root, _, files in os.walk(base_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()

                if ext in IGNORED_EXTENSIONS or ext not in SUPPORTED_EXTENSIONS:
                    continue

                full_path = os.path.join(root, file)
                content = read_file_content(full_path)

                if not content:
                    continue

                score_data = score_content(term, file, content)

                if score_data["score"] > 0:
                    results.append({
                        "file": file,
                        "path": full_path,
                        "score": score_data["score"],
                        "where": score_data["occurrences"],
                        "snippets": score_data["snippets"]
                    })

    return sorted(results, key=lambda x: x["score"], reverse=True)

# =========================================================
# CLI
# =========================================================

def main():
    print("\n Smart File Search\n")

    while True:
        term = input("Digite o termo de busca (ou 's' para sair): ").strip()
        if term.lower() == "s":
            break

        results = search(term)

        if not results:
            print("\n❌ Nenhum resultado encontrado.")
            continue

        print(f"\n✅ {len(results)} resultado(s) encontrado(s):\n")

        for r in results:
            print(f"📄 {r['file']}")
            print(f"📍 \"{r['path']}\"")
            print(f"⭐ Relevância: {r['score']}")
            print(f" Ocorrências: {', '.join(r['where'])}")

            if r["snippets"]:
                print("🧩 Trechos encontrados:")
                for s in r["snippets"]:
                    print(f"   {s}")

            print("-" * 60)

    print("\n👋 Encerrando busca.")


if __name__ == "__main__":
    main()
