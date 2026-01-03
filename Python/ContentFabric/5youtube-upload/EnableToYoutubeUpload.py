import os
import json
import shutil
from datetime import datetime, timezone

# ==========================================================
# CONFIGURAÇÕES (AJUSTE AQUI)
# Python EnableToYoutubeUpload.py
# ==========================================================

PATH_MAPPINGS = [
    {
        "SourcePath": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Histories\NewHistory",
        "DestinationPath": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\EnableToYoutubeUpload\NewHistory"
    },
    {
        "SourcePath": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Videos",
        "DestinationPath": r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\EnableToYoutubeUpload"
    }
]

# ==========================================================
# DEFAULTS DE NEGÓCIO (AUTO-PREENCHIMENTO)
# ==========================================================

DEFAULT_VALUES = {
    "category_id": 27,
    "visibility": "public",
    "made_for_kids": True,
    "embeddable": True,
    "publishAt": lambda: datetime.now(timezone.utc).isoformat()
}

PLAYLIST_DEFAULTS = {
    "Id": "",
    "create_if_not_exists": True,
    "description": ""
}

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
# NORMALIZAÇÃO DO JSON
# ==========================================================

def normalize_upload_json(data: dict) -> tuple[dict, list[str]]:
    filled_fields = []

    for field, default in DEFAULT_VALUES.items():
        if field not in data or data[field] in (None, "", []):
            data[field] = default() if callable(default) else default
            filled_fields.append(field)

    if "playlist" not in data or not isinstance(data["playlist"], dict):
        data["playlist"] = {}
        filled_fields.append("playlist")

    for field, default in PLAYLIST_DEFAULTS.items():
        if field not in data["playlist"]:
            data["playlist"][field] = default
            filled_fields.append(f"playlist.{field}")

    return data, filled_fields


# ==========================================================
# PROCESSAMENTO POR MAPEAMENTO
# ==========================================================

def process_mapping(mapping: dict) -> tuple[int, int]:
    source_dir = mapping.get("SourcePath")
    destination_dir = mapping.get("DestinationPath")

    if not source_dir or not destination_dir:
        raise ValueError("Cada mapping deve conter SourcePath e DestinationPath")

    print(f"\n📁 Origem: {source_dir}")
    print(f"📦 Destino: {destination_dir}\n")

    os.makedirs(destination_dir, exist_ok=True)

    total_jsons = 0
    moved = 0

    for root, _, files in os.walk(source_dir):
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

            data, filled_fields = normalize_upload_json(data)

            if filled_fields:
                print(f"   🛠 Campos preenchidos automaticamente: {', '.join(filled_fields)}")

            valid, reason = is_valid_upload_json(data)

            if not valid:
                print(f"   ❌ JSON inválido mesmo após normalização: {reason}\n")
                continue

            # Salva JSON normalizado
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            dest_json = os.path.join(destination_dir, file)
            dest_video = os.path.join(destination_dir, base_name + ".mp4")

            shutil.move(json_path, dest_json)
            shutil.move(video_path, dest_video)

            print("   ✅ JSON e vídeo movidos com sucesso\n")
            moved += 1

    return total_jsons, moved


# ==========================================================
# MAIN
# ==========================================================

def main():
    print("🔍 Iniciando varredura de conteúdos prontos para upload...\n")

    total_analyzed = 0
    total_moved = 0

    for mapping in PATH_MAPPINGS:
        analyzed, moved = process_mapping(mapping)
        total_analyzed += analyzed
        total_moved += moved

    print("===================================================")
    print("📊 Resumo final geral:")
    print(f"   JSONs analisados: {total_analyzed}")
    print(f"   Conteúdos prontos movidos: {total_moved}")
    print("===================================================")


if __name__ == "__main__":
    main()
