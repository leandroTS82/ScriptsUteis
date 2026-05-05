# -------------------------------------------------------
# Python list_channel_videos_with_playlists.py
# Gera listagem completa dos vídeos do canal
# com ID, título, descrição e playlists associadas
# -------------------------------------------------------

import os
import json
from datetime import datetime

from youtube_auth import get_youtube_client


# ======================================================
# OUTPUT
# ======================================================

OUTPUT_DIR = "./output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    f"youtube_videos_{datetime.now():%Y%m%d_%H%M%S}.json"
)


# ======================================================
# HELPERS
# ======================================================

def get_uploads_playlist_id(youtube):
    res = youtube.channels().list(
        part="contentDetails",
        mine=True
    ).execute()

    return res["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

def get_all_playlist_items(youtube, playlist_id):
    items = []
    page_token = None

    while True:
        res = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=page_token
        ).execute()

        items.extend(res.get("items", []))
        page_token = res.get("nextPageToken")

        if not page_token:
            break

    return items

def get_all_playlists(youtube):
    playlists = {}
    page_token = None

    while True:
        res = youtube.playlists().list(
            part="snippet",
            mine=True,
            maxResults=50,
            pageToken=page_token
        ).execute()

        for p in res.get("items", []):
            playlists[p["id"]] = p["snippet"]["title"]

        page_token = res.get("nextPageToken")
        if not page_token:
            break

    return playlists

def build_video_playlist_map(youtube, playlists):
    video_map = {}

    for playlist_id, playlist_title in playlists.items():
        page_token = None

        while True:
            res = youtube.playlistItems().list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=page_token
            ).execute()

            for item in res.get("items", []):
                video_id = item["contentDetails"]["videoId"]
                video_map.setdefault(video_id, []).append({
                    "playlist_id": playlist_id,
                    "playlist_title": playlist_title
                })

            page_token = res.get("nextPageToken")
            if not page_token:
                break

    return video_map

# ======================================================
# MAIN PROCESS
# ======================================================

def main():
    youtube = get_youtube_client()

    print(" Obtendo playlist de uploads do canal...")
    uploads_playlist_id = get_uploads_playlist_id(youtube)

    print("📼 Listando vídeos do canal...")
    upload_items = get_all_playlist_items(youtube, uploads_playlist_id)

    print("📂 Listando playlists do canal...")
    playlists = get_all_playlists(youtube)

    print("🔗 Mapeando vídeos → playlists...")
    video_playlist_map = build_video_playlist_map(youtube, playlists)

    result = []

    for item in upload_items:
        video_id = item["contentDetails"]["videoId"]
        snippet = item["snippet"]

        result.append({
            "video_id": video_id,
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "playlists": video_playlist_map.get(video_id, [])
        })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": datetime.now().isoformat(),
                "total_videos": len(result),
                "videos": result
            },
            f,
            indent=4,
            ensure_ascii=False
        )

    print("\n✅ Arquivo gerado com sucesso:")
    print(f"📄 {OUTPUT_FILE}")

# ======================================================
# ENTRY
# ======================================================

if __name__ == "__main__":
    main()
