# ============================================================
# sync_audios_to_zip.py
# COMPACTA AUDIOS + METADATA, ENVIA PARA DESTINO
# E MOVE ARQUIVOS JÁ ENVIADOS PARA ./moved
# ============================================================

import os
import zipfile
import json
import shutil
from datetime import datetime

# ------------------------------------------------------------
# PATHS
# ------------------------------------------------------------

AUDIO_SOURCE_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Audios"

DESTINATION_PATH = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\TransferenciaFiles"
)

MOVED_PATH = os.path.join(AUDIO_SOURCE_PATH, "moved")

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
GENERATE_METADATA = True

# ------------------------------------------------------------
# PREPARAÇÃO
# ------------------------------------------------------------

if not os.path.exists(AUDIO_SOURCE_PATH):
    raise RuntimeError(f"Pasta de áudio não encontrada: {AUDIO_SOURCE_PATH}")

os.makedirs(DESTINATION_PATH, exist_ok=True)
os.makedirs(MOVED_PATH, exist_ok=True)

# ------------------------------------------------------------
# FUNÇÕES
# ------------------------------------------------------------

def is_inside_moved(path: str) -> bool:
    """Ignora qualquer arquivo dentro da pasta ./moved"""
    return os.path.commonpath([path, MOVED_PATH]) == MOVED_PATH


def collect_audio_metadata(source_dir: str) -> dict:
    files = []

    for root, _, filenames in os.walk(source_dir):
        if is_inside_moved(root):
            continue

        for file in filenames:
            if os.path.splitext(file)[1].lower() not in AUDIO_EXTENSIONS:
                continue

            full_path = os.path.join(root, file)
            stat = os.stat(full_path)

            files.append({
                "name": file,
                "relative_path": os.path.relpath(full_path, source_dir),
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

    return {"files": files}


def zip_audios(source_dir: str, zip_path: str):
    base_len = len(source_dir.rstrip(os.sep)) + 1
    count = 0
    zipped_files = []

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(source_dir):
            if is_inside_moved(root):
                continue

            for file in files:
                if os.path.splitext(file)[1].lower() not in AUDIO_EXTENSIONS:
                    continue

                full_path = os.path.join(root, file)
                arcname = full_path[base_len:]
                zf.write(full_path, arcname)

                zipped_files.append(full_path)
                count += 1

    return count, zipped_files


def move_files(files):
    moved = 0

    for src in files:
        dest = os.path.join(MOVED_PATH, os.path.basename(src))

        # evita sobrescrever
        if os.path.exists(dest):
            name, ext = os.path.splitext(dest)
            dest = f"{name}_{int(datetime.now().timestamp())}{ext}"

        shutil.move(src, dest)
        moved += 1

    return moved

# ------------------------------------------------------------
# EXECUÇÃO
# ------------------------------------------------------------

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

zip_name = f"audios_{timestamp}.zip"
zip_path = os.path.join(DESTINATION_PATH, zip_name)

print("🎧 Processando áudios...")

# --- metadata.json temporário ---
metadata_path = None
if GENERATE_METADATA:
    print("📝 Gerando metadata dos áudios...")
    metadata = collect_audio_metadata(AUDIO_SOURCE_PATH)
    metadata_path = os.path.join(AUDIO_SOURCE_PATH, "metadata.json")

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

# --- ZIP ---
print("📦 Compactando áudios...")
audio_count, zipped_files = zip_audios(AUDIO_SOURCE_PATH, zip_path)

# --- remove metadata temporário ---
if metadata_path and os.path.exists(metadata_path):
    os.remove(metadata_path)

# --- move arquivos já enviados ---
print("📂 Movendo áudios já enviados para ./moved ...")
moved_count = move_files(zipped_files)

# ------------------------------------------------------------
# RESULTADO
# ------------------------------------------------------------

print("===================================================")
print("PROCESSO CONCLUÍDO COM SUCESSO")
print(f"🎶 Arquivos compactados: {audio_count}")
print(f"📂 Arquivos movidos     : {moved_count}")
print(f"📦 ZIP gerado           : {zip_path}")
print("===================================================")