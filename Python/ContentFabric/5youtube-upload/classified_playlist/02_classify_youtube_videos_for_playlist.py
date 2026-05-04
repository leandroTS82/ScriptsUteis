import os
import sys
import json
import re
import random
from datetime import datetime
from itertools import cycle

from groq import Groq

# ============================================================
# GROQ LOADER
# ============================================================

GROQ_LOADER_DIR = r"C:\dev\scripts\ScriptsUteis\Python"
if GROQ_LOADER_DIR not in sys.path:
    sys.path.insert(0, GROQ_LOADER_DIR)

from groq_keys_loader import GROQ_KEYS

# ============================================================
# CONFIG
# ============================================================

INPUT_CONTEXT_JSON = r"C:\dev\scripts\ScriptsUteis\Python\ContentFabric\5youtube-upload\output\youtube_playlist_context.json"

OUTPUT_DIR = r".\output"

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    f"youtube_playlist_classification.json"
)

GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_RETRIES = 3
TIMEOUT_SECONDS = 40

# Informe aqui a playlist/categoria desejada
TARGET_PLAYLIST_NAME = "Past Simple"

# Critérios livres
TARGET_CRITERIA = """
Classify videos that are clearly useful for a playlist about Past Simple in English.

Include videos about:
- past simple verbs
- irregular verbs in past
- words like bought, began, drove, went, got, made, performed, announced
- phrases explained in past tense
- practical examples of simple past usage

Do NOT include:
- generic vocabulary without past tense relevance
- phrasal verbs unless the focus is past tense
- business vocabulary unless clearly past simple
"""

BATCH_SIZE = 25

# ============================================================
# GROQ ROTATION
# ============================================================

_groq_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))

def get_client():
    key_info = next(_groq_key_cycle)
    return Groq(api_key=key_info["key"]), key_info["name"]


def extract_json_array(text):
    match = re.search(r"\[.*\]", text, re.DOTALL)
    return match.group(0) if match else None


def call_groq(messages, label="classify"):
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        client, key_name = get_client()

        try:
            print(f"[Groq {label}] tentativa {attempt} · key: {key_name}")

            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=0.1,
                timeout=TIMEOUT_SECONDS
            )

            return response.choices[0].message.content.strip()

        except Exception as ex:
            last_error = ex
            print(f"Falha Groq tentativa {attempt}: {ex}")

    raise RuntimeError(f"Todas as tentativas Groq falharam. Último erro: {last_error}")


# ============================================================
# CLASSIFICATION
# ============================================================

def build_prompt(videos):
    compact_videos = []

    for v in videos:
        compact_videos.append({
            "youtube_video_id": v.get("youtube_video_id"),
            "youtube_title": v.get("youtube_title"),
            "titleTheme": v.get("titleTheme"),
            "descriptionTheme": v.get("descriptionTheme")
        })

    return f"""
You are a strict YouTube video classifier.

Target playlist:
{TARGET_PLAYLIST_NAME}

Criteria:
{TARGET_CRITERIA}

Task:
Analyze each video and decide if it belongs to the target playlist.

Return ONLY a valid JSON array.
No markdown.
No explanation outside JSON.

Expected format:
[
  {{
    "youtube_video_id": "...",
    "include": true,
    "confidence": 0.95,
    "reason": "short reason",
    "target_playlist": "{TARGET_PLAYLIST_NAME}"
  }}
]

Rules:
- include=true only when the video clearly matches the criteria.
- confidence must be between 0 and 1.
- Use titleTheme and descriptionTheme as the strongest signals.
- If titleTheme is missing, use youtube_title.
- Do not invent video IDs.

Videos:
{json.dumps(compact_videos, ensure_ascii=False)}
"""


def classify_batch(videos):
    messages = [
        {
            "role": "system",
            "content": "You return only valid JSON. You are strict and conservative."
        },
        {
            "role": "user",
            "content": build_prompt(videos)
        }
    ]

    raw = call_groq(messages)
    json_text = extract_json_array(raw)

    if not json_text:
        raise ValueError(f"Groq did not return JSON array:\n{raw}")

    return json.loads(json_text)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(INPUT_CONTEXT_JSON, "r", encoding="utf-8") as f:
        context = json.load(f)

    videos = context.get("videos", [])

    # usa apenas vídeos com tema extraído
    candidates = [
        v for v in videos
        if v.get("youtube_video_id") and (v.get("titleTheme") or v.get("youtube_title"))
    ]

    all_results = []

    for i in range(0, len(candidates), BATCH_SIZE):
        batch = candidates[i:i + BATCH_SIZE]
        print(f"Classificando batch {i // BATCH_SIZE + 1} com {len(batch)} vídeos...")

        try:
            result = classify_batch(batch)
            all_results.extend(result)

        except Exception as ex:
            print(f"Erro no batch {i // BATCH_SIZE + 1}: {ex}")

    included_ids = {
        x["youtube_video_id"]
        for x in all_results
        if x.get("include") is True
    }

    included_videos = [
        v for v in videos
        if v.get("youtube_video_id") in included_ids
    ]

    output = {
        "generated_at": datetime.now().isoformat(),
        "target_playlist": TARGET_PLAYLIST_NAME,
        "target_criteria": TARGET_CRITERIA,
        "total_candidates": len(candidates),
        "total_included": len(included_videos),
        "classification": all_results,
        "videos": included_videos
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print("Classificação gerada:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()