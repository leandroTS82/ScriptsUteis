"""
===========================================================
 Script: smart_file_search.py
 Autor: Leandro
===========================================================

Busca inteligente por termos em arquivos (PDF, TXT, JSON, MD, HTML),
com ranking de relevância baseado em:
- Nome do arquivo
- Títulos / cabeçalhos
- Corpo do texto

Compatível com:
- Windows / Linux / macOS
- Android (via Termux ou storage montado)
===========================================================
"""

import os
import re
import json
from typing import List, Dict
from PyPDF2 import PdfReader

# =========================================================
# CONFIGURAÇÕES
# =========================================================

SEARCH_PATHS = [
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\EnglishReview",
    # "/storage/emulated/0"  # Android (Termux)
]

IGNORED_EXTENSIONS = [
    ".exe", ".dll", ".bin", ".jpg", ".png", ".mp4", ".zip", ".txt", ".json", ".md", ".html", ".htm"
]

SUPPORTED_EXTENSIONS = [
    ".pdf"
]

CASE_INSENSITIVE = True

# =========================================================
# UTILITÁRIOS
# =========================================================

def normalize(text: str) -> str:
    return text.lower() if CASE_INSENSITIVE else text


def read_file_content(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()

    try:
        if ext == ".pdf":
            reader = PdfReader(path)
            return "\n".join(page.extract_text() or "" for page in reader.pages)

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    except Exception:
        return ""


def score_content(term: str, filename: str, content: str) -> Dict:
    score = 0
    occurrences = []

    term_norm = normalize(term)
    filename_norm = normalize(filename)
    content_norm = normalize(content)

    # 🔥 Nome do arquivo
    if term_norm in filename_norm:
        score += 100
        occurrences.append("nome_do_arquivo")

    # ⚠️ Títulos / cabeçalhos
    header_patterns = [
        r"<h1.*?>.*?</h1>",
        r"<h2.*?>.*?</h2>",
        r"<title.*?>.*?</title>",
        r"^# .+$",
        r"^## .+$"
    ]

    for pattern in header_patterns:
        for match in re.findall(pattern, content, re.MULTILINE | re.IGNORECASE):
            if term_norm in normalize(match):
                score += 50
                occurrences.append("titulo/cabecalho")

    # ℹ️ Corpo do texto
    body_count = content_norm.count(term_norm)
    if body_count > 0:
        score += body_count * 10
        occurrences.append(f"corpo_texto({body_count})")

    return {
        "score": score,
        "occurrences": occurrences
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

                if ext in IGNORED_EXTENSIONS:
                    continue

                if ext not in SUPPORTED_EXTENSIONS:
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
                        "where": score_data["occurrences"]
                    })

    return sorted(results, key=lambda x: x["score"], reverse=True)


# =========================================================
# CLI INTERATIVO
# =========================================================

def main():
    print("\n🔎 Smart File Search\n")

    while True:
        term = input("Digite o termo de busca (ou 's' para sair): ").strip()
        if term.lower() == "s":
            break

        results = search(term)

        if not results:
            print("\n❌ Nenhum resultado encontrado.")
            retry = input("Deseja buscar outro termo? (Enter para continuar / 's' para sair): ")
            if retry.lower() == "s":
                break
            continue

        print(f"\n✅ {len(results)} resultado(s) encontrado(s):\n")

        for r in results:
            print(f"📄 {r['file']}")
            print(f"📍 \"{r['path']}\"")
            print(f"⭐ Relevância: {r['score']}")
            print(f"🔎 Ocorrências: {', '.join(r['where'])}")
            print("-" * 60)

    print("\n👋 Encerrando busca.")


if __name__ == "__main__":
    main()
