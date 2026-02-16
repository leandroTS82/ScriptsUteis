# ============================================================
# move_long_videos_and_clean_history.py
# ============================================================

import os
import json
import shutil
import subprocess
from datetime import datetime

# ============================================================
# CONFIGURAÇÕES INLINE
# ============================================================

SOURCE_PATHS = [
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\EnableToYoutubeUpload"
]

MIN_DURATION_SECONDS = 120  # duração mínima em segundos

DESTINATION_REPO = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS"
    r"\LTS SP Site - Documentos de estudo de inglês"
    r"\EKF_EnglishKnowledgeFramework_REPO\LongVideos_ProbalyFails"
)

# 🔹 NOVO PATH INLINE
BASETERMS_OUTPUT_PATH = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS"
    r"\LTS SP Site - Documentos de estudo de inglês"
    r"\EKF_EnglishKnowledgeFramework_REPO\BaseTerms"
)

PENDING_JSON_FILE = os.path.join(BASETERMS_OUTPUT_PATH, "pending_from_long_videos.json")

HISTORY_FILE = os.path.join(DESTINATION_REPO, "history_generated.json")

VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".avi")


# ============================================================
# UTIL
# ============================================================

def print_header():
    print("\n" + "=" * 60)
    print(" EKF - MOVE LONG VIDEOS + CLEAN HISTORY")
    print("=" * 60 + "\n")


def get_video_duration(file_path):
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(result.stdout.strip())
    except:
        print(f"⚠ Erro ao obter duração: {file_path}")
        return 0


def load_history():
    if not os.path.exists(HISTORY_FILE):
        print("⚠ history_generated.json não encontrado. Criando novo.")
        return []

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_pending_terms(terms):
    os.makedirs(BASETERMS_OUTPUT_PATH, exist_ok=True)

    data = {"pending": terms}

    with open(PENDING_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ============================================================
# PROCESSAMENTO
# ============================================================

def process():

    print_header()

    history_data = load_history()
    original_count = len(history_data)

    removed_terms = []
    pending_terms = []  # 🔥 NOVO
    moved_files = 0

    for source in SOURCE_PATHS:

        print(f"📂 Escaneando: {source}")

        if not os.path.exists(source):
            print("   ❌ Pasta não existe")
            continue

        for file in os.listdir(source):

            if not file.lower().endswith(VIDEO_EXTENSIONS):
                continue

            video_path = os.path.join(source, file)
            base_name = os.path.splitext(file)[0]
            json_path = os.path.join(source, base_name + ".json")

            duration = get_video_duration(video_path)

            print(f"\n🎬 {file}")
            print(f"   ⏱ Duração: {round(duration,2)}s")

            if duration < MIN_DURATION_SECONDS:
                print("   ➖ Ignorado (menor que duração mínima)")
                continue

            print("   ✅ Aprovado (maior ou igual duração mínima)")

            # Move vídeo
            dest_video = os.path.join(DESTINATION_REPO, file)
            shutil.move(video_path, dest_video)
            print("   📦 Vídeo movido")

            # Move JSON se existir
            if os.path.exists(json_path):
                dest_json = os.path.join(DESTINATION_REPO, base_name + ".json")
                shutil.move(json_path, dest_json)
                print("   📦 JSON movido")

            moved_files += 1

            # 🔥 NOVO: preparar termo sem underscore
            clean_term = base_name.replace("_", " ")
            pending_terms.append(clean_term)

            # Remove do history
            new_history = []
            for entry in history_data:
                if entry.get("term") == base_name:
                    removed_terms.append(base_name)
                    continue
                new_history.append(entry)

            history_data = new_history

    # Salva history atualizado
    save_history(history_data)

    # 🔥 NOVO: gerar JSON com termos pendentes
    if pending_terms:
        save_pending_terms(pending_terms)
        print(f"\n📝 JSON de pendentes gerado em:")
        print(f"   {PENDING_JSON_FILE}")

    # ============================================================
    # RELATÓRIO FINAL
    # ============================================================

    print("\n" + "=" * 60)
    print(" RESULTADO FINAL")
    print("=" * 60)

    print(f"\n📦 Arquivos movidos: {moved_files}")
    print(f"🗑 Termos removidos do history: {len(removed_terms)}")
    print(f"📝 Novos termos pendentes: {len(pending_terms)}")
    print(f"📊 Histórico antes: {original_count}")
    print(f"📊 Histórico depois: {len(history_data)}")

    if removed_terms:
        print("\n🔎 Termos removidos:")
        for term in removed_terms:
            print(f"   - {term}")

    print("\n✅ Processo finalizado com sucesso.")
    print("=" * 60 + "\n")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    process()
