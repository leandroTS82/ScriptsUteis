import json
from pathlib import Path
from datetime import datetime
import sys
import shutil

# ======================================================
# CONFIG
# ======================================================

READY_PATH = Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\ReadyToBeCreated")
AI_HELPER_PATH = Path(r"C:\dev\scripts\ScriptsUteis\Python\AI_EnglishHelper")

CREATE_LATER_FILE = AI_HELPER_PATH / "CreateLater.json"
LOCK_FILE = AI_HELPER_PATH / "pipeline.lock"

LOG_DIR = Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\pipeline_upload_videos_Logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / f"gatekeeper_{datetime.now():%Y%m%d_%H%M%S}.log"

# ======================================================
# HELPERS
# ======================================================

def log(msg):
    LOG_FILE.write_text(LOG_FILE.read_text() + f"{datetime.now()} | {msg}\n" if LOG_FILE.exists() else f"{datetime.now()} | {msg}\n")

def load_json(p: Path):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def save_json(p: Path, data):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ======================================================
# MAIN
# ======================================================

def main():
    log("START")

    if LOCK_FILE.exists():
        log("Pipeline locked – aborting")
        sys.exit(0)

    if not CREATE_LATER_FILE.exists() or load_json(CREATE_LATER_FILE) != {"pending": []}:
        log("CreateLater.json não vazio – aborting")
        sys.exit(0)

    candidates = [
        f for f in READY_PATH.iterdir()
        if f.is_file()
        and f.suffix == ".json"
        and not f.name.startswith(("processing_", "success_", "error_"))
    ]

    if not candidates:
        log("NOOP – nenhum json elegível")
        sys.exit(0)

    unified = []
    for f in candidates:
        data = load_json(f)
        unified.extend(data.get("pending", []))
        f.rename(f.parent / f"processing_{f.name}")

    unified = list(dict.fromkeys(unified))

    if not unified:
        log("NOOP – lista vazia")
        sys.exit(0)

    save_json(CREATE_LATER_FILE, {"pending": unified})
    log(f"CreateLater.json preenchido ({len(unified)} termos)")

    sys.exit(2)

if __name__ == "__main__":
    main()
