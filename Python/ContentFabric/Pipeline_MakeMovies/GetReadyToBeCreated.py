import json
from pathlib import Path
from datetime import datetime
import sys
import re

# ======================================================
# CONFIGURAÇÕES
# ======================================================

PIPELINE_DIR = Path(r"C:\dev\scripts\ScriptsUteis\Python\ContentFabric\Pipeline_MakeMovies")
RUNTIME_DIR = PIPELINE_DIR / "_runtime"
RUNTIME_DIR.mkdir(exist_ok=True)

READY_PATH = Path(
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\ReadyToBeCreated"
)

AI_HELPER_PATH = Path(
    r"C:\dev\scripts\ScriptsUteis\Python\AI_EnglishHelper"
)

CREATE_LATER_FILE = AI_HELPER_PATH / "CreateLater.json"
LOCK_FILE = RUNTIME_DIR / "pipeline.lock"

LOG_ROOT = Path(
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\pipeline_upload_videos_Logs"
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
    if not path.exists():
        raise FileNotFoundError("Arquivo não encontrado")

    if path.stat().st_size == 0:
        raise ValueError("Arquivo JSON vazio")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def safe_filename(name: str) -> str:
    """
    Remove caracteres inválidos para Windows:
    < > : " / \ | ? *
    """
    return re.sub(r'[<>:"/\\|?*]', "_", name)


# ======================================================
# MAIN
# ======================================================

def main() -> bool:
    log("START")

    # --------------------------------------------------
    # LOCK
    # --------------------------------------------------
    if LOCK_FILE.exists():
        log("LOCK ativo — abortando execução")
        return False

    # --------------------------------------------------
    # CreateLater.json deve existir e estar vazio
    # --------------------------------------------------
    if not CREATE_LATER_FILE.exists():
        log("CreateLater.json não existe — abortando")
        return False

    try:
        create_later = load_json(CREATE_LATER_FILE)
    except Exception as e:
        log(f"Erro ao ler CreateLater.json: {e}")
        return False

    if create_later.get("pending"):
        log("CreateLater.json não vazio — abortando")
        return False

    # --------------------------------------------------
    # Coleta candidatos
    # --------------------------------------------------
    candidates = [
        f for f in READY_PATH.iterdir()
        if f.is_file()
        and f.suffix.lower() == ".json"
        and not f.name.startswith(("processing_", "success_", "error_"))
    ]

    if not candidates:
        log("NOOP — nenhum JSON elegível")
        return False

    unified: list[str] = []

    # --------------------------------------------------
    # Processa arquivos individualmente (à prova de erro)
    # --------------------------------------------------
    for f in candidates:
        safe_name = safe_filename(f.name)

        try:
            data = load_json(f)

            if not isinstance(data, dict):
                raise ValueError("JSON não é um objeto")

            pending = data.get("pending")
            if not isinstance(pending, list):
                raise ValueError("Campo 'pending' inválido ou ausente")

            unified.extend(pending)

            target = f.parent / f"processing_{safe_name}"
            f.rename(target)

            log(f"OK → {f.name} ({len(pending)} termos)")

        except Exception as e:
            log(f"ERRO → {f.name}: {e}")

            try:
                error_target = f.parent / f"error_{safe_name}"
                if f.exists():
                    f.rename(error_target)
            except Exception as rename_error:
                log(f"ERRO CRÍTICO AO RENOMEAR {f.name}: {rename_error}")

    # --------------------------------------------------
    # Normalização
    # --------------------------------------------------
    unified = list(dict.fromkeys(unified))

    if not unified:
        log("NOOP — lista vazia após unificação")
        return False

    # --------------------------------------------------
    # LOCK + persistência
    # --------------------------------------------------
    LOCK_FILE.write_text(datetime.now().isoformat(), encoding="utf-8")
    log("LOCK criado")

    save_json(CREATE_LATER_FILE, {"pending": unified})
    log(f"CreateLater.json preenchido com {len(unified)} termos")

    return True


# ======================================================
# ENTRYPOINT
# ======================================================

if __name__ == "__main__":
    ok = main()

    # 0 = execução válida / noop controlado
    # 2 = pipeline liberado (há trabalho a fazer)
    sys.exit(2 if ok else 0)
