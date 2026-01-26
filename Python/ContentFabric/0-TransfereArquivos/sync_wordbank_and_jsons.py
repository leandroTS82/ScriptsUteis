# ============================================================
# sync_wordbank_and_jsons.py
# ZIP WORDBANK + COPY SMART + ZIP JSON_FILES
# ============================================================

import os
import zipfile
import shutil
from datetime import datetime

# ------------------------------------------------------------
# PATHS BASE
# ------------------------------------------------------------
WORDBANK_PATH = r"C:\Users\leand\Desktop\wordbank"

BASE_LTS_PATH = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVIMENTO DE SISTEMAS"
    r"\LTS SP Site - Documentos de estudo de inglês"
)

DESTINATION_PATH = os.path.join(
    BASE_LTS_PATH, "FilesHelper", "Json_files"
)

TRANSFER_PATH = os.path.join(
    BASE_LTS_PATH, "TransferenciaFiles"
)

# ------------------------------------------------------------
# SOURCES
# ------------------------------------------------------------
SOURCES = [
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\movies_processed",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Uploaded",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Videos",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\EnableToYoutubeUpload",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Youtube_Upload_Faulty_File",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Histories\NewHistory\subtitles",
]

ALLOWED_EXTENSIONS = {".json", ".srt"}

# ------------------------------------------------------------
# PREPARACAO
# ------------------------------------------------------------
if not os.path.exists(WORDBANK_PATH):
    raise RuntimeError(f"Pasta wordbank não encontrada: {WORDBANK_PATH}")

os.makedirs(DESTINATION_PATH, exist_ok=True)
os.makedirs(TRANSFER_PATH, exist_ok=True)

# ------------------------------------------------------------
# FUNCOES
# ------------------------------------------------------------
def zip_directory(source_dir: str, zip_path: str):
    source_dir = os.path.abspath(source_dir)
    base_len = len(source_dir.rstrip(os.sep)) + 1
    count = 0

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = full_path[base_len:]
                zf.write(full_path, arcname)
                count += 1

    return count


def copy_smart(source: str, destination: str):
    copied = 0
    skipped = 0

    for root, _, files in os.walk(source):
        for file in files:
            if os.path.splitext(file)[1].lower() not in ALLOWED_EXTENSIONS:
                continue

            src = os.path.join(root, file)
            dst = os.path.join(destination, file)

            if os.path.exists(dst):
                skipped += 1
                continue

            shutil.copy2(src, dst)
            copied += 1

    return copied, skipped


def has_files(path: str) -> bool:
    return any(
        os.path.isfile(os.path.join(path, f))
        for f in os.listdir(path)
    )

# ------------------------------------------------------------
# EXECUCAO
# ------------------------------------------------------------
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# -------------------------------
# 1) ZIP WORDBANK
# -------------------------------
print("Compactando wordbank...")

wordbank_zip = os.path.join(
    TRANSFER_PATH, f"wordbank_{timestamp}.zip"
)

wordbank_count = zip_directory(WORDBANK_PATH, wordbank_zip)

print(f"ZIP wordbank criado com {wordbank_count} arquivos")
print(f"Local: {wordbank_zip}")

# -------------------------------
# 2) COPY SMART -> JSON_FILES
# -------------------------------
print("Copiando arquivos para Json_files...")

total_copied = 0
total_skipped = 0

for source in SOURCES:
    if not os.path.exists(source):
        print(f"Fonte não encontrada. Pulando: {source}")
        continue

    copied, skipped = copy_smart(source, DESTINATION_PATH)
    total_copied += copied
    total_skipped += skipped

print(f"Copiados : {total_copied}")
print(f"Ignorados: {total_skipped}")

# -------------------------------
# 3) ZIP JSON_FILES (SE NAO VAZIO)
# -------------------------------
if not has_files(DESTINATION_PATH):
    print("Json_files vazio. ZIP não será gerado.")
else:
    print("Compactando Json_files...")

    json_zip = os.path.join(
        TRANSFER_PATH, f"json_files_{timestamp}.zip"
    )

    json_count = zip_directory(DESTINATION_PATH, json_zip)

    print(f"ZIP Json_files criado com {json_count} arquivos")
    print(f"Local: {json_zip}")

print("===================================================")
print("PROCESSO CONCLUIDO COM SUCESSO")
print("===================================================")
