import json
import os


def generate_youtube_json(
    output_path: str,
    title: str,
    description: str,
    tags: list[str],
    playlist: dict
):
    json_path = output_path.replace(".mp4", ".json")

    payload = {
        "title": title,
        "description": description,
        "tags": tags,
        "playlist": playlist
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"   ✅ JSON YouTube criado: {json_path}")
