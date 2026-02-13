# ============================================================
# consolidate_base_terms.py
# Consolida BaseTerms vs TermsReadyToBeCreated
# Autor: Leandro
# ============================================================

import os
import json
import sys
from datetime import datetime
from pathlib import Path

# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_TERMS_DIR = Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\EKF_EnglishKnowledgeFramework_REPO\BaseTerms")

TERMS_READY_DIR = Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\EKF_EnglishKnowledgeFramework_REPO\TermsReadyToBeCreated")
EXCLUDED_FILE = Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\EKF_EnglishKnowledgeFramework_REPO\ExcludedTerms.json")

TEMP_FILE = Path("temp_consolidated_terms.json")

# ============================================================
# UTIL
# ============================================================

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def pause():
    input("\nPressione ENTER para continuar...")

def normalize(term: str) -> str:
    return term.strip().lower()

# ============================================================
# LEITURA JSONs
# ============================================================

def collect_terms_from_directory(directory: Path):
    terms = []

    for file in directory.glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "pending" in data and isinstance(data["pending"], list):
                    terms.extend(data["pending"])
        except Exception:
            pass

    return terms

# ============================================================
# EXCLUDED TERMS
# ============================================================

def load_excluded_terms():
    if not EXCLUDED_FILE.exists():
        return []

    try:
        with open(EXCLUDED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "excluded" in data and isinstance(data["excluded"], list):
                return data["excluded"]
    except Exception:
        pass

    return []


def add_to_excluded(term: str):
    excluded = load_excluded_terms()
    normalized_set = set(normalize(t) for t in excluded)

    if normalize(term) not in normalized_set:
        excluded.append(term)

    with open(EXCLUDED_FILE, "w", encoding="utf-8") as f:
        json.dump({"excluded": excluded}, f, indent=2, ensure_ascii=False)


# ============================================================
# CONSOLIDAÇÃO
# ============================================================

def build_filtered_list():
    base_terms = collect_terms_from_directory(BASE_TERMS_DIR)
    ready_terms = collect_terms_from_directory(TERMS_READY_DIR)
    excluded_terms = load_excluded_terms()

    ready_normalized = set(normalize(t) for t in ready_terms)
    excluded_normalized = set(normalize(t) for t in excluded_terms)

    filtered = []
    seen = set()

    for term in base_terms:
        norm = normalize(term)
        if (
            norm not in ready_normalized
            and norm not in excluded_normalized
            and norm not in seen
        ):
            filtered.append(term.strip())
            seen.add(norm)

    return sorted(filtered)


# ============================================================
# LISTA INTERATIVA
# ============================================================

def display_list(term_list):
    clear()
    print("=" * 60)
    print(" BASE TERMS CONSOLIDADO (FALTANTES PARA CRIAR)")
    print("=" * 60)
    print()

    if not term_list:
        print("Nenhum termo pendente.")
        return

    for idx, term in enumerate(term_list, start=1):
        print(f"{idx:03d} - {term}")

    print()
    print("=" * 60)
    print("Opções:")
    print("1 - Sair")
    print("2 - Escolher termo")
    print("3 - Gerar conteúdo para vídeos")
    print("=" * 60)


def term_menu(term_list):
    while True:
        display_list(term_list)

        if not term_list:
            pause()
            return

        option = input("\nEscolha: ").strip()

        if option == "1":
            if TEMP_FILE.exists():
                TEMP_FILE.unlink()
            print("Saindo e removendo lista temporária.")
            pause()
            return

        elif option == "2":
            choose_term(term_list)

        elif option == "3":
            generate_output_file(term_list)
            return

        else:
            print("Opção inválida.")
            pause()


def choose_term(term_list):
    try:
        number = int(input("Digite o número do termo: "))
        if number < 1 or number > len(term_list):
            raise ValueError
    except ValueError:
        print("Número inválido.")
        pause()
        return

    selected = term_list[number - 1]

    while True:
        clear()
        print(f"Termo selecionado: {selected}")
        print("\n1 - Excluir")
        print("2 - Editar")
        print("3 - Voltar")

        op = input("\nEscolha: ").strip()

        if op == "1":
            add_to_excluded(selected)
            term_list.pop(number - 1)
            save_temp(term_list)
            print("Termo movido para ExcludedTerms.")
            pause()
            return

        elif op == "2":
            new_term = input("Digite o novo termo ou (v) para voltar: ").strip()
            if new_term.lower() == "v":
                return
            if new_term:
                term_list[number - 1] = new_term
                save_temp(term_list)
                print("Termo atualizado.")
                pause()
                return

        elif op == "3":
            return
        else:
            print("Opção inválida.")
            pause()

# ============================================================
# SALVAR TEMP
# ============================================================

def save_temp(term_list):
    with open(TEMP_FILE, "w", encoding="utf-8") as f:
        json.dump({"pending": term_list}, f, indent=2, ensure_ascii=False)

# ============================================================
# GERAR JSON FINAL
# ============================================================

def generate_output_file(term_list):
    if not term_list:
        print("Lista vazia.")
        pause()
        return

    filename = datetime.now().strftime("%y%m%d%H%M") + ".json"
    output_path = TERMS_READY_DIR / filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"pending": term_list}, f, indent=2, ensure_ascii=False)

    if TEMP_FILE.exists():
        TEMP_FILE.unlink()

    print(f"\nArquivo gerado com sucesso:\n{output_path}")
    pause()

# ============================================================
# MAIN
# ============================================================

def main():
    terms = build_filtered_list()

    if not terms:
        print("Nenhum termo novo encontrado.")
        return

    save_temp(terms)
    term_menu(terms)


if __name__ == "__main__":
    main()
