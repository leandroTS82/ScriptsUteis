import json
from pathlib import Path
from datetime import datetime
import shutil
import traceback
import sys

# ======================================================
# CONFIGURAÇÕES INLINE
# ======================================================

READY_PATH = Path(
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\ReadyToBeCreated"
)

SENT_PATH = READY_PATH / "Sent"

AI_HELPER_PATH = Path(
    r"C:\dev\scripts\ScriptsUteis\Python\AI_EnglishHelper"
)

CREATE_LATER_FILE = AI_HELPER_PATH / "CreateLater.json"

UNIFIED_FILENAME = "pending_unificado.json"

# ======================================================
# HELPERS
# ======================================================

def log(msg: str):
    print(f"> {msg}")

def load_json_raw(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_json_safe(path: Path) -> dict:
    try:
        return load_json_raw(path)
    except Exception:
        return {"pending": []}

def save_json(path: Path, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def write_report(path: Path, lines: list[str]):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def should_ignore(file: Path) -> bool:
    return (
        file.suffix.lower() != ".json"
        or file.name.startswith("success_")
        or file.name.startswith("error_")
    )

def prefix_file(file: Path, prefix: str) -> Path:
    new_path = file.parent / f"{prefix}{file.name}"
    if not new_path.exists():
        file.rename(new_path)
    return new_path

# ======================================================
# VALIDAÇÃO CRÍTICA (STOP EARLY)
# ======================================================

def validate_create_later_empty():
    if not CREATE_LATER_FILE.exists():
        log("CreateLater.json não existe — execução interrompida")
        sys.exit(0)

    data = load_json_raw(CREATE_LATER_FILE)

    if data != {"pending": []}:
        log("CreateLater.json possui conteúdo — nenhuma ação será realizada")
        sys.exit(0)

# ======================================================
# MAIN
# ======================================================

def main():
    validate_create_later_empty()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    status_prefix = "success_"
    error_details = None

    processed_files: list[Path] = []
    unified_pending: list[str] = []

    copy_performed = False
    create_later_status = ""

    try:
        log("CreateLater.json validado como vazio")
        log("Iniciando leitura de ReadyToBeCreated")

        if not READY_PATH.exists():
            raise FileNotFoundError("READY_PATH não encontrado")

        SENT_PATH.mkdir(exist_ok=True)

        json_files = [
            f for f in READY_PATH.iterdir()
            if f.is_file() and not should_ignore(f)
        ]

        if not json_files:
            log("Nenhum arquivo JSON elegível encontrado.")
            return

        for file in json_files:
            data = load_json_safe(file)
            pending = data.get("pending", [])

            if isinstance(pending, list) and pending:
                unified_pending.extend(pending)
                processed_files.append(file)
                log(f"Lido: {file.name} ({len(pending)} termos)")

        unified_pending = list(dict.fromkeys(unified_pending))

        if not unified_pending:
            log("Nenhum termo encontrado — execução encerrada")
            return

        # ======================================================
        # CREATE LATER (AGORA É SEGURO)
        # ======================================================

        save_json(CREATE_LATER_FILE, {"pending": unified_pending})
        create_later_status = "CreateLater.json preenchido com sucesso"

        temp_unified = READY_PATH / UNIFIED_FILENAME
        save_json(temp_unified, {"pending": unified_pending})

        final_unified = (
            SENT_PATH / f"{status_prefix}{timestamp}_{UNIFIED_FILENAME}"
        )
        shutil.move(str(temp_unified), final_unified)

        copy_performed = True
        log("Conteúdo copiado com sucesso")

    except Exception:
        status_prefix = "error_"
        error_details = traceback.format_exc()
        log("Erro durante a execução")

    # ======================================================
    # PREFIXA ARQUIVOS DE ORIGEM (SOMENTE SE PASSOU DO GATE)
    # ======================================================

    prefixed_files = []

    for file in processed_files:
        try:
            new_path = prefix_file(file, status_prefix)
            prefixed_files.append(new_path.name)
        except Exception as e:
            log(f"Erro ao prefixar {file.name}: {e}")

    # ======================================================
    # RELATÓRIO
    # ======================================================

    report_path = (
        SENT_PATH / f"{status_prefix}{timestamp}_execution_report.txt"
    )

    report_lines = [
        "EXECUTION REPORT",
        "================",
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Status: {status_prefix.replace('_', '').upper()}",
        "",
        "Source files:",
        *[f" - {f.name}" for f in processed_files],
        "",
        f"Total unique terms copied: {len(unified_pending)}",
        "",
        f"Copy performed: {'YES' if copy_performed else 'NO'}",
        create_later_status,
    ]

    if error_details:
        report_lines.extend([
            "",
            "ERROR DETAILS:",
            error_details
        ])

    write_report(report_path, report_lines)

    log(f"Relatório gerado em: {report_path}")
    log("Execução finalizada.")

# ======================================================
# EXECUÇÃO
# ======================================================

if __name__ == "__main__":
    main()
