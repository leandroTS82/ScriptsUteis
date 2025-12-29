import os
import json
import shutil

# ==========================================================
# CONFIGURAÇÕES (AJUSTE AQUI)
# Python EnableToYoutubeUpload.py
# ==========================================================

SOURCE_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Videos"
DESTINATION_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\EnableToYoutubeUpload"

# ==========================================================
# VALIDAÇÃO DO JSON DE UPLOAD
# ==========================================================

REQUIRED_FIELDS = {
    "title": str,
    "description": str,
    "tags": list,
    "category_id": int,
    "visibility": str,
    "made_for_kids": bool,
    "embeddable": bool,
    "playlist": dict
}

REQUIRED_PLAYLIST_FIELDS = {
    "name": str
}


def is_valid_upload_json(data: dict) -> tuple[bool, str]:
    """
    Valida se o JSON possui a estrutura mínima para upload no YouTube
    Retorna (True, "") se válido
    Retorna (False, motivo) se inválido
    """

    for field, field_type in REQUIRED_FIELDS.items():
        if field not in data:
            return False, f"Campo obrigatório ausente: {field}"
        if not isinstance(data[field], field_type):
            return False, f"Campo inválido: {field}"

        if isinstance(data[field], str) and not data[field].strip():
            return False, f"Campo vazio: {field}"

        if isinstance(data[field], list) and len(data[field]) == 0:
            return False, f"Lista vazia: {field}"

    playlist = data.get("playlist", {})
    for field, field_type in REQUIRED_PLAYLIST_FIELDS.items():
        if field not in playlist:
            return False, f"Playlist sem campo obrigatório: {field}"
        if not isinstance(playlist[field], field_type):
            return False, f"Campo inválido em playlist: {field}"

    return True, ""


# ==========================================================
# PROCESSAMENTO PRINCIPAL
# ==========================================================

def main():
    print("🔍 Iniciando varredura de vídeos prontos para upload...\n")

    os.makedirs(DESTINATION_DIR, exist_ok=True)

    total_jsons = 0
    moved = 0

    for root, _, files in os.walk(SOURCE_DIR):
        for file in files:
            if not file.lower().endswith(".json"):
                continue

            total_jsons += 1

            json_path = os.path.join(root, file)
            base_name = os.path.splitext(file)[0]
            video_path = os.path.join(root, base_name + ".mp4")

            print(f"📄 Analisando: {file}")

            if not os.path.exists(video_path):
                print("   ⚠ Vídeo correspondente não encontrado (.mp4). Ignorado.\n")
                continue

            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"   ❌ Erro ao ler JSON: {e}\n")
                continue

            valid, reason = is_valid_upload_json(data)

            if not valid:
                print(f"   ⚠ JSON inválido para upload: {reason}\n")
                continue

            # ===========================
            # MOVE JSON E MP4
            # ===========================

            dest_json = os.path.join(DESTINATION_DIR, file)
            dest_video = os.path.join(DESTINATION_DIR, base_name + ".mp4")

            shutil.move(json_path, dest_json)
            shutil.move(video_path, dest_video)

            print("   ✅ JSON e vídeo movidos para EnableToYoutubeUpload\n")
            moved += 1

    print("===================================================")
    print(f"📊 Resumo final:")
    print(f"   JSONs analisados: {total_jsons}")
    print(f"   Conteúdos prontos movidos: {moved}")
    print("===================================================")


if __name__ == "__main__":
    main()
