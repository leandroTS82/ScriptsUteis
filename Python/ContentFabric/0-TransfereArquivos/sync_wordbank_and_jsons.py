# ============================================================
# sync_wordbank_and_jsons.py
#
# OBJETIVOS
# ------------------------------------------------------------
# 1. Gerar WORDBANK.ZIP apenas com vídeos NOVOS
# 2. Incluir metadata COMPLETO (novo + antigo)
# 3. Gerar JSON_FILES.ZIP apenas com JSONs NOVOS
# 4. Atualizar old_metadata.json automaticamente
# 5. Compatibilidade com metadata antigo
# 6. Não gerar ZIP vazio
# ============================================================

import os
import json
import shutil
import zipfile
import hashlib

from datetime import datetime


# ============================================================
# PATHS BASE
# ============================================================

WORDBANK_PATH = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS"
    r"\EKF - English Knowledge Framework - LeandrinhoMovies"
)

BASE_LTS_PATH = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS"
    r"\EKF - English Knowledge Framework - Base"
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

OLD_METADATA_PATH = os.path.join(
    TRANSFER_PATH,
    "old_metadata.json"
)

NEW_METADATA_PATH = os.path.join(
    TRANSFER_PATH,
    "metadata.json"
)

WORDBANK_ZIP_PATH = os.path.join(
    TRANSFER_PATH,
    "wordbank.zip"
)

JSON_ZIP_PATH = os.path.join(
    TRANSFER_PATH,
    "json_files.zip"
)


# ============================================================
# SOURCES
# ============================================================

SOURCES = [
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\movies_processed",

    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\series_processed",

    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\youtube_processed",
]


# ============================================================
# HELPERS
# ============================================================

def ensure_dirs():

    os.makedirs(
        TRANSFER_PATH,
        exist_ok=True
    )


def sha1_file(path):

    sha1 = hashlib.sha1()

    with open(path, "rb") as f:

        while True:

            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            sha1.update(chunk)

    return sha1.hexdigest()


def build_fingerprint(path):

    stat = os.stat(path)

    return (
        f"{stat.st_size}_"
        f"{int(stat.st_mtime)}"
    )


# ============================================================
# LOAD OLD METADATA
# ============================================================

def load_old_metadata():

    if not os.path.exists(
        OLD_METADATA_PATH
    ):

        return {
            "generated_at": None,
            "pipeline_version": "2.0",
            "files": {}
        }

    with open(
        OLD_METADATA_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    files = data.get("files")

    # ========================================================
    # MIGRACAO AUTOMATICA
    # formato antigo -> novo
    # ========================================================
    if isinstance(files, list):

        migrated = {}

        for item in files:

            name = item.get("name")

            if not name:
                continue

            migrated[name] = {
                "path": name,
                "name": name,
                "size": 0,
                "created_at": item.get("created_at"),
                "modified_at": item.get("modified_at"),

                # fingerprint fake inicial
                "fingerprint": (
                    item.get("modified_at", "")
                )
            }

        return {
            "generated_at": datetime.now().isoformat(),
            "pipeline_version": "2.0",
            "files": migrated
        }

    # ========================================================
    # FORMATO NOVO
    # ========================================================
    return data


# ============================================================
# BUILD CURRENT METADATA
# ============================================================

def build_current_metadata():

    metadata = {
        "generated_at": datetime.now().isoformat(),
        "pipeline_version": "2.0",
        "files": {}
    }

    for source in SOURCES:

        if not os.path.exists(source):
            continue

        for root, _, files in os.walk(source):

            for file in files:

                if not file.lower().endswith(".mp4"):
                    continue

                full_path = os.path.join(
                    root,
                    file
                )

                relative_path = os.path.relpath(
                    full_path,
                    source
                )

                stat = os.stat(full_path)

                metadata["files"][relative_path] = {
                    "path": full_path,
                    "name": file,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(
                        stat.st_ctime
                    ).isoformat(),

                    "modified_at": datetime.fromtimestamp(
                        stat.st_mtime
                    ).isoformat(),

                    "fingerprint": build_fingerprint(
                        full_path
                    )
                }

    return metadata


# ============================================================
# GET NEW VIDEOS
# ============================================================

def get_new_videos(
    current_metadata,
    old_metadata
):

    current_files = current_metadata["files"]
    old_files = old_metadata["files"]

    new_files = []

    for relative_path, info in current_files.items():

        old_info = old_files.get(
            relative_path
        )

        # arquivo novo
        if not old_info:

            new_files.append(info)
            continue

        # alterado
        if (
            old_info.get("fingerprint")
            != info.get("fingerprint")
        ):

            new_files.append(info)

    return new_files


# ============================================================
# BUILD WORDBANK ZIP
# ============================================================

def build_wordbank_zip(
    new_videos,
    current_metadata
):

    if not new_videos:

        print(
            "Nenhum vídeo novo encontrado."
        )

        if os.path.exists(
            WORDBANK_ZIP_PATH
        ):

            os.remove(
                WORDBANK_ZIP_PATH
            )

        return

    with zipfile.ZipFile(
        WORDBANK_ZIP_PATH,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zipf:

        # ====================================================
        # VIDEOS NOVOS
        # ====================================================

        for video in new_videos:

            video_path = video["path"]

            arcname = os.path.basename(
                video_path
            )

            print(
                f"[VIDEO NOVO] {arcname}"
            )

            zipf.write(
                video_path,
                arcname
            )

        # ====================================================
        # METADATA COMPLETO
        # ====================================================

        temp_metadata_path = os.path.join(
            TRANSFER_PATH,
            "__temp_metadata.json"
        )

        with open(
            temp_metadata_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                current_metadata,
                f,
                ensure_ascii=False,
                indent=2
            )

        zipf.write(
            temp_metadata_path,
            "metadata.json"
        )

        os.remove(
            temp_metadata_path
        )

    print(
        f"\nwordbank.zip criado:"
        f"\n{WORDBANK_ZIP_PATH}"
    )


# ============================================================
# GET NEW JSON FILES
# ============================================================

def get_json_files():

    json_files = []

    if not os.path.exists(
        DESTINATION_PATH
    ):

        return json_files

    for root, _, files in os.walk(
        DESTINATION_PATH
    ):

        for file in files:

            if not file.lower().endswith(
                ".json"
            ):
                continue

            full_path = os.path.join(
                root,
                file
            )

            json_files.append(full_path)

    return json_files


def load_json_history():

    path = os.path.join(
        TRANSFER_PATH,
        "json_history.json"
    )

    if not os.path.exists(path):
        return {}

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def save_json_history(history):

    path = os.path.join(
        TRANSFER_PATH,
        "json_history.json"
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            history,
            f,
            ensure_ascii=False,
            indent=2
        )


def get_new_jsons():

    history = load_json_history()

    current = {}

    new_files = []

    for file_path in get_json_files():

        fingerprint = build_fingerprint(
            file_path
        )

        current[file_path] = fingerprint

        old_fingerprint = history.get(
            file_path
        )

        if old_fingerprint != fingerprint:

            new_files.append(file_path)

    save_json_history(current)

    return new_files


# ============================================================
# BUILD JSON ZIP
# ============================================================

def build_json_zip():

    new_jsons = get_new_jsons()

    if not new_jsons:

        print(
            "\nNenhum JSON novo encontrado."
        )

        if os.path.exists(
            JSON_ZIP_PATH
        ):

            os.remove(
                JSON_ZIP_PATH
            )

        return

    with zipfile.ZipFile(
        JSON_ZIP_PATH,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zipf:

        for file_path in new_jsons:

            arcname = os.path.relpath(
                file_path,
                DESTINATION_PATH
            )

            print(
                f"[JSON NOVO] {arcname}"
            )

            zipf.write(
                file_path,
                arcname
            )

    print(
        f"\njson_files.zip criado:"
        f"\n{JSON_ZIP_PATH}"
    )


# ============================================================
# SAVE METADATA
# ============================================================

def save_metadata(metadata):

    with open(
        OLD_METADATA_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            metadata,
            f,
            ensure_ascii=False,
            indent=2
        )

    with open(
        NEW_METADATA_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            metadata,
            f,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n=================================================="
    )

    print(
        "SYNC WORDBANK + JSON FILES"
    )

    print(
        "==================================================\n"
    )

    ensure_dirs()

    # ========================================================
    # LOAD
    # ========================================================

    old_metadata = load_old_metadata()

    current_metadata = (
        build_current_metadata()
    )

    # ========================================================
    # VIDEOS
    # ========================================================

    new_videos = get_new_videos(
        current_metadata,
        old_metadata
    )

    print(
        f"Vídeos novos:"
        f" {len(new_videos)}"
    )

    build_wordbank_zip(
        new_videos,
        current_metadata
    )

    # ========================================================
    # JSONS
    # ========================================================

    build_json_zip()

    # ========================================================
    # SAVE METADATA
    # ========================================================

    save_metadata(
        current_metadata
    )

    print(
        "\nMetadata atualizado com sucesso."
    )

    print(
        "\nProcesso finalizado."
    )


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":

    main()