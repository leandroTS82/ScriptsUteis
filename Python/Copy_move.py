"""
============================================================
 SMART FILE TRANSFER TOOL
 Autor: Leandro
 Descrição:
   - Copiar ou mover arquivos
   - Ignora arquivos ocultos e 'trashed'
   - Verifica duplicidade (considera prefixo uploaded_)
   - Gera log JSON detalhado
   - Move duplicados para {origem}/duplicados
   - Barra de progresso
============================================================
"""

import shutil
import json
import sys
from pathlib import Path
from datetime import datetime

# ==========================================================
# CONFIGURAÇÕES INLINE
# ==========================================================

DUPLICATE_PREFIXES = ["uploaded_"]
IGNORED_KEYWORDS = ["trashed"]
LOG_FILENAME = "operation_log.json"
DUPLICATES_FOLDER_NAME = "duplicados"

# ==========================================================
# UTILIDADES
# ==========================================================

def normalize_name(filename: str) -> str:
    name = Path(filename).stem.lower()
    for prefix in DUPLICATE_PREFIXES:
        if name.startswith(prefix):
            name = name[len(prefix):]
    return name


def is_hidden_or_ignored(file: Path) -> bool:
    if file.name.startswith("."):
        return True
    for keyword in IGNORED_KEYWORDS:
        if keyword.lower() in file.name.lower():
            return True
    return False


def get_user_input():
    print("\n=== SMART FILE TRANSFER TOOL ===\n")

    action = input("Digite 1 para COPIAR ou 2 para MOVER: ").strip()
    if action not in ["1", "2"]:
        print("Opção inválida.")
        sys.exit(1)

    origem = Path(input("Informe o caminho da ORIGEM: ").strip())
    destino = Path(input("Informe o caminho do DESTINO: ").strip())

    estrutura = input(
        "Digite 1 para copiar/mover estrutura completa ou 2 apenas arquivos do diretório atual: "
    ).strip()

    if estrutura not in ["1", "2"]:
        print("Opção inválida.")
        sys.exit(1)

    return action, origem, destino, estrutura


def collect_files(origem: Path, recursive: bool):
    if recursive:
        files = origem.rglob("*")
    else:
        files = origem.glob("*")

    files = [f for f in files if f.is_file() and not is_hidden_or_ignored(f)]
    return files


def ensure_directory(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def progress_bar(current, total, bar_length=40):
    percent = current / total
    filled = int(bar_length * percent)
    bar = "█" * filled + "-" * (bar_length - filled)
    print(f"\r[{bar}] {current}/{total}", end="", flush=True)


def save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ==========================================================
# PROCESSAMENTO PRINCIPAL
# ==========================================================

def process_files(action, origem: Path, destino: Path, recursive: bool):

    ensure_directory(destino)

    duplicates_folder = origem / DUPLICATES_FOLDER_NAME
    ensure_directory(duplicates_folder)

    log_data = []
    duplicate_records = []

    processed_index = {}

    files = collect_files(origem, recursive)
    total = len(files)

    print(f"\n🔍 Total de arquivos encontrados: {total}\n")

    if total == 0:
        print("Nenhum arquivo válido encontrado.")
        return

    processed = 0

    for file in files:
        processed += 1
        progress_bar(processed, total)

        relative_path = file.relative_to(origem)
        relative_dir = str(relative_path.parent).lower()

        normalized_name = normalize_name(file.name)
        duplicate_key = (relative_dir, normalized_name)

        # =====================================================
        # 🔎 DUPLICIDADE LÓGICA
        # =====================================================
        if duplicate_key in processed_index:

            duplicate_dest = duplicates_folder / file.name
            ensure_directory(duplicate_dest.parent)

            if action == "2":  # MOVE
                shutil.move(file, duplicate_dest)
            else:  # COPY
                shutil.copy2(file, duplicate_dest)

            duplicate_records.append({
                "original_file": processed_index[duplicate_key],
                "duplicated_file": str(file),
                "redirected_to": str(duplicate_dest),
                "reason": "Logical duplicate (normalized name match)",
                "timestamp": datetime.now().isoformat()
            })

            log_data.append({
                "file_name": file.name,
                "source": str(file),
                "destination": str(duplicate_dest),
                "action": "DUPLICATE_REDIRECT",
                "timestamp": datetime.now().isoformat()
            })

            print(f"\n⚠️ DUPLICADO LÓGICO: {file.name} → enviado para duplicados")
            continue

        processed_index[duplicate_key] = str(file)

        # =====================================================
        # 🎯 DESTINO NORMAL
        # =====================================================
        target_path = destino / relative_path if recursive else destino / file.name
        ensure_directory(target_path.parent)

        if action == "1":
            shutil.copy2(file, target_path)
            action_type = "COPY"
        else:
            shutil.move(file, target_path)
            action_type = "MOVE"

        log_data.append({
            "file_name": file.name,
            "source": str(file),
            "destination": str(target_path),
            "action": action_type,
            "timestamp": datetime.now().isoformat()
        })

    print("\n\n✅ Processamento concluído.")

    # =====================================================
    # 🧹 LIMPEZA DE PASTAS VAZIAS (APENAS SE MOVE + RECURSIVO)
    # =====================================================
    if action == "2" and recursive:
        print("🧹 Removendo pastas vazias da origem...")

        for folder in sorted(origem.rglob("*"), reverse=True):
            if folder.is_dir() and folder != duplicates_folder:
                try:
                    folder.rmdir()
                except:
                    pass

    # =====================================================
    # 💾 SALVAR LOGS
    # =====================================================

    log_path = destino / LOG_FILENAME
    save_json(log_path, log_data)
    print(f"📄 Log principal salvo em: {log_path}")

    if duplicate_records:
        duplicate_log_path = duplicates_folder / "duplicates_log.json"
        save_json(duplicate_log_path, duplicate_records)
        print(f"📄 Log de duplicados salvo em: {duplicate_log_path}")
    else:
        try:
            duplicates_folder.rmdir()
            print("🗑️ Pasta 'duplicados' removida (vazia).")
        except:
            pass


# ==========================================================
# MAIN
# ==========================================================

def main():
    action, origem, destino, estrutura = get_user_input()

    if not origem.exists():
        print("Origem não existe.")
        sys.exit(1)

    recursive = estrutura == "1"

    process_files(action, origem, destino, recursive)


if __name__ == "__main__":
    main()