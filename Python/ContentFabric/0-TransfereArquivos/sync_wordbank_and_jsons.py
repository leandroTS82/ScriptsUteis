# ============================================================
# sync_wordbank_and_jsons.py
# INCREMENTAL ZIP + METADATA MANIFEST
# ============================================================

import os
import zipfile
import shutil
import json
import hashlib

from datetime import datetime

# ------------------------------------------------------------
# PATHS BASE
# ------------------------------------------------------------
WORDBANK_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - LeandrinhoMovies"

BASE_LTS_PATH = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base"
)

DESTINATION_PATH = os.path.join(
    BASE_LTS_PATH,
    "FilesHelper",
    "Json_files"
)

TRANSFER_PATH = os.path.join(
    BASE_LTS_PATH,
    "TransferenciaFiles"
)

MANIFESTS_PATH = os.path.join(
    TRANSFER_PATH,
    "manifests"
)

# ------------------------------------------------------------
# SOURCES
# ------------------------------------------------------------
SOURCES = [
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\movies_processed",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Uploaded",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Videos",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\EnableToYoutubeUpload",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Youtube_Upload_Faulty_File",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Histories\NewHistory\subtitles",
]

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
ALLOWED_EXTENSIONS = {
    ".json",
    ".srt"
}

TRACKED_EXTENSIONS = {
    ".mp4",
    ".json",
    ".srt"
}

VIDEO_EXTENSIONS = {
    ".mp4"
}

IGNORED_FILES = {
    "desktop.ini",
    ".ds_store"
}

# ------------------------------------------------------------
# PREPARACAO
# ------------------------------------------------------------
if not os.path.exists(WORDBANK_PATH):
    raise RuntimeError(
        f"Pasta wordbank não encontrada: {WORDBANK_PATH}"
    )

os.makedirs(DESTINATION_PATH, exist_ok=True)
os.makedirs(TRANSFER_PATH, exist_ok=True)
os.makedirs(MANIFESTS_PATH, exist_ok=True)

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def has_files(path: str) -> bool:
    return any(
        os.path.isfile(os.path.join(path, f))
        for f in os.listdir(path)
    )


def load_manifest(path: str) -> dict:
    if not os.path.exists(path):
        return {
            "generated_at": None,
            "pipeline_version": "1.0",
            "files": {}
        }

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(path: str, manifest: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            manifest,
            f,
            indent=2,
            ensure_ascii=False
        )


def file_hash(path: str) -> str:
    sha = hashlib.sha256()

    with open(path, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)

    return sha.hexdigest()


# ------------------------------------------------------------
# METADATA
# ------------------------------------------------------------
def build_file_metadata(
    full_path: str,
    relative_path: str
) -> dict:

    stat = os.stat(full_path)

    extension = (
        os.path.splitext(full_path)[1]
        .lower()
    )

    metadata = {
        "path": normalize_path(relative_path),
        "name": os.path.basename(full_path),
        "extension": extension,
        "size": stat.st_size,
        "created_at": datetime.fromtimestamp(
            stat.st_ctime
        ).isoformat(),
        "modified_at": datetime.fromtimestamp(
            stat.st_mtime
        ).isoformat(),
    }

    # --------------------------------------------------------
    # SHA256 SOMENTE PARA ARQUIVOS PEQUENOS
    # --------------------------------------------------------
    if extension in {".json", ".srt"}:
        metadata["hash"] = file_hash(full_path)

    else:
        # fingerprint leve para mp4
        metadata["fingerprint"] = (
            f"{stat.st_size}_{int(stat.st_mtime)}"
        )

    return metadata


# ------------------------------------------------------------
# DETECTAR ALTERACOES
# ------------------------------------------------------------
def collect_changed_files(
    source_dir: str,
    manifest_path: str
):

    old_manifest = load_manifest(manifest_path)

    old_files = old_manifest.get("files", {})

    new_manifest = {
        "generated_at": datetime.now().isoformat(),
        "pipeline_version": "1.0",
        "files": {}
    }

    changed_files = []

    for root, _, files in os.walk(source_dir):

        for file in files:

            if file.lower() in IGNORED_FILES:
                continue

            if file.startswith(".") or file.startswith("~"):
                continue

            full_path = os.path.join(root, file)

            extension = (
                os.path.splitext(file)[1]
                .lower()
            )

            if extension not in TRACKED_EXTENSIONS:
                continue

            relative_path = normalize_path(
                os.path.relpath(
                    full_path,
                    source_dir
                )
            )

            metadata = build_file_metadata(
                full_path,
                relative_path
            )

            new_manifest["files"][relative_path] = metadata

            old_metadata = old_files.get(relative_path)

            if old_metadata != metadata:
                changed_files.append(
                    (full_path, relative_path)
                )

    return (
        changed_files,
        new_manifest
    )


# ------------------------------------------------------------
# ZIP DELTA
# ------------------------------------------------------------
def zip_delta_files(
    changed_files,
    source_dir: str,
    zip_path: str,
    manifest: dict
):

    count = 0

    with zipfile.ZipFile(
        zip_path,
        "w",
        zipfile.ZIP_DEFLATED,
        compresslevel=9
    ) as zf:

        # ----------------------------------------------------
        # ARQUIVOS ALTERADOS
        # ----------------------------------------------------
        for full_path, relative_path in changed_files:

            try:
                zf.write(
                    full_path,
                    relative_path
                )

                count += 1

            except PermissionError:
                print(
                    f"⚠️ Sem permissão: {full_path}"
                )

            except Exception as e:
                print(
                    f"⚠️ Erro ao zipar {full_path}: {e}"
                )

        # ----------------------------------------------------
        # METADATA
        # ----------------------------------------------------
        zf.writestr(
            "metadata.json",
            json.dumps(
                manifest,
                indent=2,
                ensure_ascii=False
            )
        )

    return count


# ------------------------------------------------------------
# COPY SMART
# ------------------------------------------------------------
def copy_smart(source: str, destination: str):

    copied = 0
    skipped = 0

    for root, _, files in os.walk(source):

        for file in files:

            extension = (
                os.path.splitext(file)[1]
                .lower()
            )

            if extension not in ALLOWED_EXTENSIONS:
                continue

            src = os.path.join(root, file)
            dst = os.path.join(destination, file)

            if os.path.exists(dst):
                skipped += 1
                continue

            shutil.copy2(src, dst)
            copied += 1

    return copied, skipped


# ============================================================
# EXECUCAO
# ============================================================
print("===================================================")
print("SYNC WORD BANK")
print("===================================================")

timestamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)

# ------------------------------------------------------------
# MANIFEST PATHS
# ------------------------------------------------------------
wordbank_manifest_path = os.path.join(
    MANIFESTS_PATH,
    "wordbank_manifest.json"
)

json_manifest_path = os.path.join(
    MANIFESTS_PATH,
    "json_files_manifest.json"
)

# ============================================================
# 1) WORDBANK DELTA ZIP
# ============================================================
print("\n[1/3] Verificando alterações do wordbank...")

(
    changed_wordbank_files,
    new_wordbank_manifest
) = collect_changed_files(
    WORDBANK_PATH,
    wordbank_manifest_path
)

if changed_wordbank_files:

    wordbank_zip = os.path.join(
        TRANSFER_PATH,
        "wordbank_delta.zip"
    )

    print(
        f"Arquivos alterados: "
        f"{len(changed_wordbank_files)}"
    )

    wordbank_count = zip_delta_files(
        changed_wordbank_files,
        WORDBANK_PATH,
        wordbank_zip,
        new_wordbank_manifest
    )

    save_manifest(
        wordbank_manifest_path,
        new_wordbank_manifest
    )

    print(
        f"ZIP incremental criado "
        f"com {wordbank_count} arquivos"
    )

    print(f"Local: {wordbank_zip}")

else:
    print(
        "Nenhuma alteração detectada no wordbank."
    )

# ============================================================
# 2) COPY SMART
# ============================================================
print("\n[2/3] Copiando arquivos para Json_files...")

total_copied = 0
total_skipped = 0

for source in SOURCES:

    if not os.path.exists(source):

        print(
            f"Fonte não encontrada. "
            f"Pulando: {source}"
        )

        continue

    copied, skipped = copy_smart(
        source,
        DESTINATION_PATH
    )

    total_copied += copied
    total_skipped += skipped

print(f"Copiados : {total_copied}")
print(f"Ignorados: {total_skipped}")

# ============================================================
# 3) JSON FILES DELTA ZIP
# ============================================================
print("\n[3/3] Verificando alterações em Json_files...")

if not has_files(DESTINATION_PATH):

    print(
        "Json_files vazio. "
        "ZIP não será gerado."
    )

else:

    (
        changed_json_files,
        new_json_manifest
    ) = collect_changed_files(
        DESTINATION_PATH,
        json_manifest_path
    )

    if changed_json_files:

        json_zip = os.path.join(
            TRANSFER_PATH,
            "json_files_delta.zip"
        )

        print(
            f"Arquivos alterados: "
            f"{len(changed_json_files)}"
        )

        json_count = zip_delta_files(
            changed_json_files,
            DESTINATION_PATH,
            json_zip,
            new_json_manifest
        )

        save_manifest(
            json_manifest_path,
            new_json_manifest
        )

        print(
            f"ZIP incremental criado "
            f"com {json_count} arquivos"
        )

        print(f"Local: {json_zip}")

    else:
        print(
            "Nenhuma alteração detectada "
            "em Json_files."
        )

# ============================================================
# FINAL
# ============================================================
print("\n===================================================")
print("PROCESSO CONCLUIDO COM SUCESSO")
print("===================================================")