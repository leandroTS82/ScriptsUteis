# ============================================================
# delete_selected_videos_and_generate_pending.py
# ============================================================

import os
import json
from datetime import datetime

# ============================================================
# CONFIGURAÇÕES INLINE
# ============================================================

SOURCE_PATHS = [
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\EnableToYoutubeUpload"
]

OUTPUT_FOLDER = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\TermsReadyToBeCreated"
)

VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".avi")

# ============================================================
# UTIL
# ============================================================

def print_header():
    print("\n" + "=" * 60)
    print(" EKF - DELETE SELECTED VIDEOS")
    print("=" * 60 + "\n")


def list_videos():
    videos = []

    for source in SOURCE_PATHS:
        if not os.path.exists(source):
            continue

        for file in os.listdir(source):
            if file.lower().endswith(VIDEO_EXTENSIONS):
                full_path = os.path.join(source, file)
                videos.append(full_path)

    return videos


def save_pending_json(terms):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    filename = f"deleted_videos_pending_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    full_path = os.path.join(OUTPUT_FOLDER, filename)

    data = {"pending": terms}

    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return full_path


# ============================================================
# MAIN PROCESS
# ============================================================

def process():

    print_header()

    videos = list_videos()

    if not videos:
        print("⚠ Nenhum vídeo encontrado.")
        return

    print("🎬 Vídeos encontrados:\n")

    for idx, video in enumerate(videos, start=1):
        print(f"{idx:02d} - {os.path.basename(video)}")

    print("\nDigite os números separados por vírgula (ex: 1,3,5)")
    selected_input = input("Seleção: ").strip()

    if not selected_input:
        print("❌ Nenhuma seleção feita.")
        return

    try:
        selected_indexes = [
            int(x.strip()) - 1
            for x in selected_input.split(",")
            if x.strip().isdigit()
        ]
    except:
        print("❌ Entrada inválida.")
        return

    deleted_terms = []

    for index in selected_indexes:
        if 0 <= index < len(videos):

            video_path = videos[index]
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            json_path = os.path.join(os.path.dirname(video_path), base_name + ".json")

            # Deletar vídeo
            os.remove(video_path)
            print(f"🗑 Vídeo excluído: {os.path.basename(video_path)}")

            # Deletar JSON correspondente
            if os.path.exists(json_path):
                os.remove(json_path)
                print(f"🗑 JSON excluído: {base_name}.json")

            # Preparar termo limpo
            clean_term = base_name.replace("_", " ")
            deleted_terms.append(clean_term)

    if deleted_terms:
        json_path = save_pending_json(deleted_terms)
        print("\n📝 JSON criado com termos pendentes:")
        print(f"   {json_path}")

    print("\n✅ Processo finalizado.")
    print("=" * 60 + "\n")


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    process()
