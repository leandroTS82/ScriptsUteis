import json
from pathlib import Path
from datetime import datetime
import sys

# ======================================================
# CONFIGURAÇÕES
# ======================================================

PIPELINE_DIR = Path(r"C:\dev\scripts\ScriptsUteis\Python\ContentFabric\Pipeline_MakeMovies")
RUNTIME_DIR = PIPELINE_DIR / "_runtime"
RUNTIME_DIR.mkdir(exist_ok=True)

READY_PATH = Path(
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\ReadyToBeCreated"
)

AI_HELPER_PATH = Path(
    r"C:\dev\scripts\ScriptsUteis\Python\AI_EnglishHelper"
)

CREATE_LATER_FILE = AI_HELPER_PATH / "CreateLater.json"
LOCK_FILE = RUNTIME_DIR / "pipeline.lock"

LOG_ROOT = Path(
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\pipeline_upload_videos_Logs"
)

RUN_ID = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y%m%d%H%M")
LOG_DIR = LOG_ROOT / RUN_ID
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "gatekeeper.log"

# ======================================================
# HELPERS
# ======================================================

def log(msg: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} | {msg}\n")

def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ======================================================
# MAIN
# ======================================================

def main():
    log("START")

    if LOCK_FILE.exists():
        log("LOCK ativo — abortando execução")
        sys.exit(0)

    if not CREATE_LATER_FILE.exists() or load_json(CREATE_LATER_FILE) != {"pending": []}:
        log("CreateLater.json não vazio — abortando")
        sys.exit(0)

    candidates = [
        f for f in READY_PATH.iterdir()
        if f.is_file()
        and f.suffix.lower() == ".json"
        and not f.name.startswith(("processing_", "success_", "error_"))
    ]

    if not candidates:
        log("NOOP — nenhum JSON elegível")
        sys.exit(0)

    unified = []

    for f in candidates:
        data = load_json(f)
        unified.extend(data.get("pending", []))
        f.rename(f.parent / f"processing_{f.name}")

    unified = list(dict.fromkeys(unified))

    if not unified:
        log("NOOP — lista vazia após unificação")
        sys.exit(0)

    LOCK_FILE.write_text(datetime.now().isoformat(), encoding="utf-8")
    log("LOCK criado")

    save_json(CREATE_LATER_FILE, {"pending": unified})
    log(f"CreateLater.json preenchido com {len(unified)} termos")

    sys.exit(2)

if __name__ == "__main__":
    main()
