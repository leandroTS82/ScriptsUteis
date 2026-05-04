# -------------------------------------------------------
# export_youtube_uploaded_inventory.py
# Lista todos os vídeos do YouTube e gera JSON com:
# - video_id
# - title
# - description
# - data de upload no YouTube
# - nome do arquivo uploaded_*.mp4 quando encontrado localmente
# - playlists associadas
#
# Usa as mesmas keys/paths do upload_youtube.py
# -------------------------------------------------------

import os
import json
from datetime import datetime

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# ======================================================
# PATHS - mesmos padrões do upload_youtube.py
# ======================================================

DEFAULT_VIDEO_DIRECTORY = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\EnableToYoutubeUpload"

OUTPUT_DIR = r".\output"

TOKEN_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\FilesHelper\secret_tokens_keys\youtube_token.json"
CLIENT_SECRET_FILE = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\FilesHelper\secret_tokens_keys\youtube-upload-desktop.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube"
]

os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    f"youtube_uploaded_inventory.json"
)

# ======================================================
# AUTH - mesmo comportamento do upload_youtube.py
# ======================================================

def get_authenticated_service():
    creds = None

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "r", encoding="utf-8") as f:
            creds = Credentials.from_authorized_user_info(
                json.load(f),
                SCOPES
            )

    if not creds or not creds.valid:
        if creds and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE,
                SCOPES
            )
            creds = flow.run_local_server(port=8080)

        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)

# ======================================================
# LOCAL FILE MAP
# ======================================================

def build_uploaded_file_map(directory):
    """
    Mapeia arquivos locais uploaded_*.mp4 e uploaded_*.json.

    Como o YouTube não retorna o nome do arquivo original,
    o match principal é feito pelo title salvo no JSON local.
    """

    result_by_title = {}
    result_by_base = {}

    if not os.path.isdir(directory):
        print(f"AVISO: Diretório local não encontrado: {directory}")
        return result_by_title, result_by_base

    files = os.listdir(directory)

    uploaded_videos = [
        f for f in files
        if f.lower().endswith(".mp4") and f.startswith("uploaded_")
    ]

    for video_file in uploaded_videos:
        base = os.path.splitext(video_file)[0]
        json_file = base + ".json"
        json_path = os.path.join(directory, json_file)

        item = {
            "uploaded_file_name": video_file,
            "uploaded_json_name": json_file if os.path.exists(json_path) else None,
            "uploaded_file_path": os.path.join(directory, video_file),
            "metadata_title": None,
            "metadata_description": None,
            "metadata": None
        }

        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                item["metadata"] = metadata
                item["metadata_title"] = metadata.get("title")
                item["metadata_description"] = metadata.get("description")

                if item["metadata_title"]:
                    result_by_title[item["metadata_title"].strip().lower()] = item

            except Exception as ex:
                item["metadata_error"] = str(ex)

        result_by_base[base.lower()] = item

    return result_by_title, result_by_base

# ======================================================
# YOUTUBE HELPERS
# ======================================================

def get_uploads_playlist_id(youtube):
    response = youtube.channels().list(
        part="contentDetails",
        mine=True
    ).execute()

    return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_all_upload_items(youtube, uploads_playlist_id):
    items = []
    page_token = None

    while True:
        response = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=page_token
        ).execute()

        items.extend(response.get("items", []))

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return items


def get_all_playlists(youtube):
    playlists = {}
    page_token = None

    while True:
        response = youtube.playlists().list(
            part="snippet",
            mine=True,
            maxResults=50,
            pageToken=page_token
        ).execute()

        for item in response.get("items", []):
            playlists[item["id"]] = {
                "playlist_id": item["id"],
                "playlist_title": item["snippet"]["title"]
            }

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return playlists


def build_video_playlist_map(youtube, playlists):
    video_playlist_map = {}

    for playlist_id, playlist_data in playlists.items():
        page_token = None

        while True:
            response = youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=page_token
            ).execute()

            for item in response.get("items", []):
                video_id = item["contentDetails"]["videoId"]

                video_playlist_map.setdefault(video_id, []).append({
                    "playlist_id": playlist_id,
                    "playlist_title": playlist_data["playlist_title"],
                    "position": item["snippet"].get("position")
                })

            page_token = response.get("nextPageToken")
            if not page_token:
                break

    return video_playlist_map


def enrich_video_details(youtube, videos):
    enriched = []

    for i in range(0, len(videos), 50):
        batch = videos[i:i + 50]
        ids = ",".join(v["video_id"] for v in batch if v["video_id"])

        if not ids:
            continue

        response = youtube.videos().list(
            part="snippet,status,statistics,contentDetails",
            id=ids
        ).execute()

        details_map = {
            item["id"]: item
            for item in response.get("items", [])
        }

        for video in batch:
            detail = details_map.get(video["video_id"], {})

            snippet = detail.get("snippet", {})
            status = detail.get("status", {})
            statistics = detail.get("statistics", {})
            content_details = detail.get("contentDetails", {})

            video.update({
                "youtube_uploaded_at": snippet.get("publishedAt") or video.get("youtube_uploaded_at"),
                "privacy_status": status.get("privacyStatus"),
                "duration": content_details.get("duration"),
                "view_count": statistics.get("viewCount"),
                "like_count": statistics.get("likeCount"),
                "comment_count": statistics.get("commentCount"),
                "tags": snippet.get("tags", [])
            })

            enriched.append(video)

    return enriched

# ======================================================
# MATCH LOCAL FILE
# ======================================================

def find_local_uploaded_file(title, uploaded_by_title):
    if not title:
        return None

    key = title.strip().lower()
    return uploaded_by_title.get(key)

# ======================================================
# MAIN
# ======================================================

def main():
    print("Autenticando no YouTube...")
    youtube = get_authenticated_service()

    print("Lendo arquivos locais uploaded_*.mp4 / uploaded_*.json...")
    uploaded_by_title, uploaded_by_base = build_uploaded_file_map(DEFAULT_VIDEO_DIRECTORY)

    print("Obtendo playlist de uploads do canal...")
    uploads_playlist_id = get_uploads_playlist_id(youtube)

    print("Listando todos os vídeos enviados...")
    upload_items = get_all_upload_items(youtube, uploads_playlist_id)

    print(f"Total de vídeos encontrados no YouTube: {len(upload_items)}")

    print("Listando playlists do canal...")
    playlists = get_all_playlists(youtube)

    print(f"Total de playlists encontradas: {len(playlists)}")

    print("Mapeando vídeos para playlists...")
    video_playlist_map = build_video_playlist_map(youtube, playlists)

    videos = []

    for item in upload_items:
        snippet = item.get("snippet", {})
        content_details = item.get("contentDetails", {})

        video_id = content_details.get("videoId")
        title = snippet.get("title")
        description = snippet.get("description")
        uploaded_at = content_details.get("videoPublishedAt") or snippet.get("publishedAt")

        video_playlists = video_playlist_map.get(video_id, [])
        local_file = find_local_uploaded_file(title, uploaded_by_title)

        videos.append({
            "video_id": video_id,
            "title": title,
            "description": description,
            "youtube_uploaded_at": uploaded_at,

            "uploaded_file_name": local_file.get("uploaded_file_name") if local_file else None,
            "uploaded_json_name": local_file.get("uploaded_json_name") if local_file else None,
            "has_local_uploaded_file": local_file is not None,

            "has_playlist": len(video_playlists) > 0,
            "playlists": video_playlists
        })

    print("Enriquecendo dados dos vídeos...")
    videos = enrich_video_details(youtube, videos)

    output = {
        "generated_at": datetime.now().isoformat(),
        "source": "youtube",
        "local_video_directory": DEFAULT_VIDEO_DIRECTORY,
        "uploads_playlist_id": uploads_playlist_id,

        "total_videos": len(videos),
        "total_playlists": len(playlists),

        "videos_with_playlist": len([v for v in videos if v["has_playlist"]]),
        "videos_without_playlist": len([v for v in videos if not v["has_playlist"]]),

        "videos_with_local_uploaded_file": len([v for v in videos if v["has_local_uploaded_file"]]),
        "videos_without_local_uploaded_file": len([v for v in videos if not v["has_local_uploaded_file"]]),

        "videos": videos
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print("")
    print("JSON gerado com sucesso:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()