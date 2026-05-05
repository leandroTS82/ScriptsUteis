import os
import json
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================

YOUTUBE_INVENTORY_JSON = r"C:\dev\scripts\ScriptsUteis\Python\ContentFabric\5youtube-upload\classified_playlist\output\youtube_uploaded_inventory.json"

UPLOAD_METADATA_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\EnableToYoutubeUpload"

MOVIES_PROCESSED_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\movies_processed"

OUTPUT_DIR = r"C:\dev\scripts\ScriptsUteis\Python\ContentFabric\5youtube-upload\classified_playlist\output"

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    f"youtube_playlist_context.json"
)

# ============================================================
# HELPERS
# ============================================================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize(text):
    return (text or "").strip().lower()


def build_metadata_title_map():
    """
    Varre EnableToYoutubeUpload buscando JSONs com prop title.
    Mapeia:
      title -> metadata_json_path
      title -> base file name
    """
    result = {}

    for root, _, files in os.walk(UPLOAD_METADATA_DIR):
        for file in files:
            if not file.lower().endswith(".json"):
                continue

            path = os.path.join(root, file)

            try:
                data = load_json(path)
            except Exception:
                continue

            title = data.get("title")
            if not title:
                continue

            base_name = os.path.splitext(file)[0]

            # remove uploaded_ se existir
            clean_base_name = base_name
            if clean_base_name.startswith("uploaded_"):
                clean_base_name = clean_base_name[len("uploaded_"):]

            result[normalize(title)] = {
                "metadata_json_file": file,
                "metadata_json_path": path,
                "base_file_name": clean_base_name
            }

    return result


def find_processed_json(base_file_name):
    """
    Busca no movies_processed um JSON relacionado ao nome base.
    Exemplo:
      base_file_name = upcoming_steps
      tenta encontrar upcoming_steps.json ou arquivo que contenha esse nome.
    """
    if not base_file_name:
        return None

    candidates = []

    for root, _, files in os.walk(MOVIES_PROCESSED_DIR):
        for file in files:
            if not file.lower().endswith(".json"):
                continue

            file_base = os.path.splitext(file)[0]

            if normalize(file_base) == normalize(base_file_name):
                return os.path.join(root, file)

            if normalize(base_file_name) in normalize(file_base):
                candidates.append(os.path.join(root, file))

    return candidates[0] if candidates else None


def extract_theme_from_processed_json(path):
    """
    Espera estrutura com WORD_BANK:
    WORD_BANK: [
      [
        {"lang": "en", "text": "..."},
        {"lang": "pt", "text": "..."}
      ]
    ]

    Retorna:
      titleTheme = primeiro text
      descriptionTheme = segundo text
    """
    if not path or not os.path.exists(path):
        return None, None

    try:
        data = load_json(path)
    except Exception:
        return None, None

    word_bank = data.get("WORD_BANK")

    if not word_bank or not isinstance(word_bank, list):
        return None, None

    first_group = word_bank[0] if word_bank else None

    if not first_group or not isinstance(first_group, list):
        return None, None

    title_theme = None
    description_theme = None

    if len(first_group) >= 1:
        title_theme = first_group[0].get("text")

    if len(first_group) >= 2:
        description_theme = first_group[1].get("text")

    return title_theme, description_theme


# ============================================================
# MAIN
# ============================================================

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Lendo inventário do YouTube...")
    inventory = load_json(YOUTUBE_INVENTORY_JSON)

    print("Mapeando JSONs locais por title...")
    metadata_title_map = build_metadata_title_map()

    enriched = []

    for video in inventory.get("videos", []):
        youtube_title = video.get("title")
        match = metadata_title_map.get(normalize(youtube_title))

        metadata_json_file = None
        metadata_json_path = None
        base_file_name = None
        processed_json_path = None
        title_theme = None
        description_theme = None

        if match:
            metadata_json_file = match["metadata_json_file"]
            metadata_json_path = match["metadata_json_path"]
            base_file_name = match["base_file_name"]

            processed_json_path = find_processed_json(base_file_name)
            title_theme, description_theme = extract_theme_from_processed_json(processed_json_path)

        enriched.append({
            "youtube_video_id": video.get("video_id"),
            "youtube_title": youtube_title,
            "youtube_description": video.get("description"),
            "youtube_uploaded_at": video.get("youtube_uploaded_at"),
            "duration": video.get("duration"),
            "has_playlist": video.get("has_playlist"),
            "playlists": video.get("playlists", []),

            "metadata_json_file": metadata_json_file,
            "metadata_json_path": metadata_json_path,
            "base_file_name": base_file_name,
            "processed_json_path": processed_json_path,

            "titleTheme": title_theme,
            "descriptionTheme": description_theme,

            "match_found": match is not None,
            "theme_found": title_theme is not None
        })

    output = {
        "generated_at": datetime.now().isoformat(),
        "source_inventory": YOUTUBE_INVENTORY_JSON,
        "total_videos": len(enriched),
        "matched_by_title": len([x for x in enriched if x["match_found"]]),
        "with_theme": len([x for x in enriched if x["theme_found"]]),
        "videos": enriched
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print("JSON enriquecido gerado:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()