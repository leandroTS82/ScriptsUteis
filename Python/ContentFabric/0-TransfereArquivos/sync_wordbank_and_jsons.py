# ============================================================
# sync_wordbank_and_jsons.py
#
# INCREMENTAL PIPELINE
#
# FEATURES:
# - Incremental wordbank.zip
# - Incremental json_files.zip
# - Full metadata persistence
# - Incremental detection via history metadata
# - Relative path preservation
# - Fault tolerance
# - Smart synchronization
#
# ============================================================

import os
import json
import shutil
import zipfile

from datetime import datetime

# ============================================================
# PATHS
# ============================================================

WORDBANK_PATH = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - LeandrinhoMovies"
)

BASE_LTS_PATH = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base"
)

TRANSFER_PATH = os.path.join(
    BASE_LTS_PATH,
    "TransferenciaFiles"
)

JSON_STAGING_PATH = os.path.join(
    BASE_LTS_PATH,
    "FilesHelper",
    "Json_files"
)

# ============================================================
# HISTORY FILES
# ============================================================

WORDBANK_HISTORY_METADATA = os.path.join(
    TRANSFER_PATH,
    "History/history_metadata.json"
)

JSON_HISTORY_METADATA = os.path.join(
    TRANSFER_PATH,
    "History/json_history_metadata.json"
)

# ============================================================
# ZIP FILES
# ============================================================

WORDBANK_ZIP = os.path.join(
    TRANSFER_PATH,
    "wordbank.zip"
)

JSON_FILES_ZIP = os.path.join(
    TRANSFER_PATH,
    "json_files.zip"
)

# ============================================================
# SOURCES
# ============================================================

SOURCES = [
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\movies_processed",

    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Uploaded",

    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Videos",

    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\EnableToYoutubeUpload",

    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Youtube_Upload_Faulty_File",

    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Histories\NewHistory\subtitles",
]

# ============================================================
# EXTENSIONS
# ============================================================

VIDEO_EXTENSIONS = {".mp4"}

JSON_EXTENSIONS = {
    ".json",
    ".srt"
}

# ============================================================
# PREPARATION
# ============================================================

os.makedirs(TRANSFER_PATH, exist_ok=True)

os.makedirs(JSON_STAGING_PATH, exist_ok=True)

if not os.path.exists(WORDBANK_PATH):
    raise RuntimeError(
        f"WORDBANK_PATH não encontrado: {WORDBANK_PATH}"
    )

# ============================================================
# HELPERS
# ============================================================

def normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def is_hidden_or_temp(file_name: str) -> bool:
    return (
        file_name.startswith(".")
        or file_name.startswith("~")
    )


# ============================================================
# METADATA COLLECTION
# ============================================================

def collect_metadata(
    source_dir: str,
    allowed_extensions: set
) -> dict:

    files_metadata = []

    for root, _, files in os.walk(source_dir):

        for file in files:

            if is_hidden_or_temp(file):
                continue

            extension = os.path.splitext(file)[1].lower()

            if extension not in allowed_extensions:
                continue

            full_path = os.path.join(root, file)

            try:

                stat = os.stat(full_path)

                relative_path = normalize_path(
                    os.path.relpath(
                        full_path,
                        source_dir
                    )
                )

                files_metadata.append({
                    "name": relative_path,
                    "modified_at": datetime.fromtimestamp(
                        stat.st_mtime
                    ).isoformat(),

                    "created_at": datetime.fromtimestamp(
                        stat.st_ctime
                    ).isoformat(),
                })

            except Exception as e:

                print(
                    f"⚠️ Erro ao coletar metadata: {full_path} -> {e}"
                )

    return {
        "files": files_metadata
    }

# ============================================================
# HISTORY
# ============================================================

def load_metadata(path: str):

    if not os.path.exists(path):
        return None

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception as e:

        print(
            f"⚠️ Erro ao carregar metadata: {path} -> {e}"
        )

        return None


def save_metadata(
    path: str,
    metadata: dict
):

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            metadata,
            f,
            indent=2,
            ensure_ascii=False
        )

# ============================================================
# INCREMENTAL DETECTION
# ============================================================

def detect_new_or_modified_files(
    current_metadata: dict,
    history_metadata: dict
):

    if history_metadata is None:
        return current_metadata["files"]

    history_index = {
        (
            item["name"],
            item["modified_at"]
        )
        for item in history_metadata.get("files", [])
    }

    changed_files = []

    for item in current_metadata["files"]:

        key = (
            item["name"],
            item["modified_at"]
        )

        if key not in history_index:
            changed_files.append(item)

    return changed_files

# ============================================================
# ZIP
# ============================================================

def zip_selected_files(
    base_dir: str,
    selected_files: list,
    metadata: dict,
    zip_path: str
):

    temp_metadata_path = os.path.join(
        base_dir,
        "__temp_metadata__.json"
    )

    count = 0
    skipped = 0

    try:

        with open(
            temp_metadata_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                metadata,
                f,
                indent=2,
                ensure_ascii=False
            )

        with zipfile.ZipFile(
            zip_path,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zf:

            # ----------------------------------------
            # METADATA
            # ----------------------------------------
            zf.write(
                temp_metadata_path,
                "metadata.json"
            )

            count += 1

            # ----------------------------------------
            # FILES
            # ----------------------------------------
            for item in selected_files:

                relative_path = item["name"]

                full_path = os.path.join(
                    base_dir,
                    relative_path
                )

                if not os.path.exists(full_path):

                    skipped += 1

                    print(
                        f"⚠️ Arquivo não encontrado: {full_path}"
                    )

                    continue

                try:

                    zf.write(
                        full_path,
                        relative_path
                    )

                    count += 1

                except PermissionError:

                    skipped += 1

                    print(
                        f"⚠️ Sem permissão: {full_path}"
                    )

                except Exception as e:

                    skipped += 1

                    print(
                        f"⚠️ Erro ao zipar {full_path}: {e}"
                    )

    finally:

        if os.path.exists(temp_metadata_path):
            os.remove(temp_metadata_path)

    return count, skipped

# ============================================================
# JSON STAGING SYNC
# ============================================================

def sync_json_staging():

    copied = 0
    skipped = 0

    for source in SOURCES:

        if not os.path.exists(source):

            print(
                f"⚠️ Fonte inexistente: {source}"
            )

            continue

        for root, _, files in os.walk(source):

            for file in files:

                if is_hidden_or_temp(file):
                    continue

                extension = os.path.splitext(file)[1].lower()

                if extension not in JSON_EXTENSIONS:
                    continue

                source_path = os.path.join(root, file)

                relative_path = normalize_path(
                    os.path.relpath(
                        source_path,
                        source
                    )
                )

                destination_path = os.path.join(
                    JSON_STAGING_PATH,
                    relative_path
                )

                os.makedirs(
                    os.path.dirname(destination_path),
                    exist_ok=True
                )

                should_copy = True

                if os.path.exists(destination_path):

                    src_mtime = os.path.getmtime(source_path)
                    dst_mtime = os.path.getmtime(destination_path)

                    should_copy = src_mtime > dst_mtime

                if should_copy:

                    try:

                        shutil.copy2(
                            source_path,
                            destination_path
                        )

                        copied += 1

                    except Exception as e:

                        print(
                            f"⚠️ Erro ao copiar {source_path}: {e}"
                        )

                else:
                    skipped += 1

    return copied, skipped

# ============================================================
# PROCESSOR
# ============================================================

def process_incremental_zip(
    name: str,
    source_dir: str,
    allowed_extensions: set,
    history_metadata_path: str,
    zip_path: str
):

    print("===================================================")
    print(f"PROCESSANDO: {name}")
    print("===================================================")

    # --------------------------------------------------------
    # CURRENT METADATA
    # --------------------------------------------------------
    current_metadata = collect_metadata(
        source_dir,
        allowed_extensions
    )

    # --------------------------------------------------------
    # HISTORY
    # --------------------------------------------------------
    history_metadata = load_metadata(
        history_metadata_path
    )

    # --------------------------------------------------------
    # DETECT CHANGES
    # --------------------------------------------------------
    changed_files = detect_new_or_modified_files(
        current_metadata,
        history_metadata
    )

    # --------------------------------------------------------
    # MODE
    # --------------------------------------------------------
    if history_metadata is None:

        print(
            "Modo FULL (history metadata inexistente)"
        )

    else:

        print(
            "Modo INCREMENTAL"
        )

    print(
        f"Arquivos novos/modificados: {len(changed_files)}"
    )

    # --------------------------------------------------------
    # NO CHANGES
    # --------------------------------------------------------
    if not changed_files:

        print(
            "Nenhum arquivo novo/modificado encontrado."
        )

        print(
            "ZIP não será gerado."
        )

        # Atualiza metadata mesmo sem mudanças
        save_metadata(
            history_metadata_path,
            current_metadata
        )

        return

    # --------------------------------------------------------
    # ZIP
    # --------------------------------------------------------
    count, skipped = zip_selected_files(
        base_dir=source_dir,
        selected_files=changed_files,
        metadata=current_metadata,
        zip_path=zip_path
    )

    # --------------------------------------------------------
    # SAVE HISTORY
    # --------------------------------------------------------
    save_metadata(
        history_metadata_path,
        current_metadata
    )

    print(f"ZIP criado: {zip_path}")
    print(f"Arquivos zipados : {count}")
    print(f"Arquivos ignorados: {skipped}")

# ============================================================
# EXECUTION
# ============================================================

print("===================================================")
print("SYNC PIPELINE STARTED")
print("===================================================")

# ============================================================
# WORDBANK
# ============================================================

process_incremental_zip(
    name="WORDBANK",
    source_dir=WORDBANK_PATH,
    allowed_extensions=VIDEO_EXTENSIONS,
    history_metadata_path=WORDBANK_HISTORY_METADATA,
    zip_path=WORDBANK_ZIP
)

# ============================================================
# JSON/SRT STAGING SYNC
# ============================================================

print("===================================================")
print("SINCRONIZANDO JSON STAGING")
print("===================================================")

copied, skipped = sync_json_staging()

print(f"Copiados : {copied}")
print(f"Ignorados: {skipped}")

# ============================================================
# JSON FILES ZIP
# ============================================================

process_incremental_zip(
    name="JSON_FILES",
    source_dir=JSON_STAGING_PATH,
    allowed_extensions=JSON_EXTENSIONS,
    history_metadata_path=JSON_HISTORY_METADATA,
    zip_path=JSON_FILES_ZIP
)

# ============================================================
# FINISHED
# ============================================================

print("===================================================")
print("PROCESSO CONCLUIDO COM SUCESSO")
print("===================================================")