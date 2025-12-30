r"""
Fluxo FINAL garantido

Percorre Videos

Detecta vídeos sem JSON

Busca JSON em _movies_processed

Se encontrar → move JSON para Videos

Se continuar sem JSON → move vídeo para VideosSemJson

Log completo no console

Seguro para reexecução

Python sync_missing_jsons.py
"""

import os
import shutil

# ==========================================================
# CONFIGURAÇÃO DE PATHS (AJUSTE AQUI SE NECESSÁRIO)
# ==========================================================

VIDEOS_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Videos"

PROCESSED_MOVIES_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\movies_processed"

VIDEOS_WITHOUT_JSON_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\VideosSemJson"

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
JSON_EXTENSION = ".json"

# ==========================================================
# FUNÇÕES AUXILIARES
# ==========================================================

def get_files_by_stem(directory, extensions):
    """
    Retorna um dict:
    {
        'nome_base': 'arquivo.ext'
    }
    """
    result = {}

    if not os.path.exists(directory):
        return result

    for file in os.listdir(directory):
        full_path = os.path.join(directory, file)

        if not os.path.isfile(full_path):
            continue

        name, ext = os.path.splitext(file)
        if ext.lower() in extensions:
            result[name] = file

    return result


# ==========================================================
# PROCESSAMENTO PRINCIPAL
# ==========================================================

def main():
    print("🔍 Iniciando verificação de vídeos sem JSON...\n")

    os.makedirs(VIDEOS_WITHOUT_JSON_DIR, exist_ok=True)

    videos = get_files_by_stem(VIDEOS_DIR, VIDEO_EXTENSIONS)
    jsons_in_videos = get_files_by_stem(VIDEOS_DIR, {JSON_EXTENSION})
    jsons_in_processed = get_files_by_stem(PROCESSED_MOVIES_DIR, {JSON_EXTENSION})

    missing_count = 0
    recovered_count = 0
    moved_videos_count = 0

    for video_stem, video_file in videos.items():
        video_path = os.path.join(VIDEOS_DIR, video_file)

        # JSON já existe → nada a fazer
        if video_stem in jsons_in_videos:
            continue

        missing_count += 1
        print(f"❌ JSON ausente para vídeo: {video_file}")

        # Tenta recuperar JSON da pasta _movies_processed
        if video_stem in jsons_in_processed:
            source_json = os.path.join(
                PROCESSED_MOVIES_DIR, jsons_in_processed[video_stem]
            )
            target_json = os.path.join(
                VIDEOS_DIR, jsons_in_processed[video_stem]
            )

            if not os.path.exists(target_json):
                shutil.move(source_json, target_json)
                recovered_count += 1
                print("   ✅ JSON recuperado e movido para Videos.")
            else:
                print("   ⚠ JSON já existia no destino. Ignorado.")

        else:
            print("   🔎 JSON não encontrado em _movies_processed.")

        # Reavalia: ainda está sem JSON? → mover vídeo
        if video_stem not in get_files_by_stem(VIDEOS_DIR, {JSON_EXTENSION}):
            target_video = os.path.join(VIDEOS_WITHOUT_JSON_DIR, video_file)

            if os.path.exists(target_video):
                print("   ⚠ Vídeo já existe em VideosSemJson. Ignorado.")
            else:
                shutil.move(video_path, target_video)
                moved_videos_count += 1
                print("   📦 Vídeo movido para VideosSemJson.")

    print("\n==================================================")
    print(f"📊 Total de vídeos analisados: {len(videos)}")
    print(f"📄 Vídeos inicialmente sem JSON: {missing_count}")
    print(f"♻ JSONs recuperados: {recovered_count}")
    print(f"📦 Vídeos movidos para VideosSemJson: {moved_videos_count}")
    print("✔ Processo finalizado.")
    print("==================================================")


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":
    main()
