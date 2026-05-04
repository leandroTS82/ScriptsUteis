import os
import json
import time
from datetime import datetime

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

# ============================================================
# CONFIG
# ============================================================

CLASSIFICATION_JSON = r".\output\youtube_playlist_classification.json"

OUTPUT_DIR = r".\output"

REPORT_FILE = os.path.join(
    OUTPUT_DIR,
    f"youtube_playlist_execution_{datetime.now():%Y%m%d_%H%M%S}.json"
)

TOKEN_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\FilesHelper\secret_tokens_keys\youtube_token.json"
CLIENT_SECRET_FILE = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\FilesHelper\secret_tokens_keys\youtube-upload-desktop.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube"
]

PLAYLIST_PRIVACY_STATUS = "public"
SLEEP_SECONDS = 1.5

DRY_RUN = False

# ============================================================
# AUTH
# ============================================================

def get_authenticated_service():
    creds = None

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "r", encoding="utf-8") as f:
            creds = Credentials.from_authorized_user_info(json.load(f), SCOPES)

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

# ============================================================
# YOUTUBE
# ============================================================

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
            playlists[item["snippet"]["title"].lower()] = {
                "playlist_id": item["id"],
                "playlist_title": item["snippet"]["title"]
            }

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return playlists


def create_playlist(youtube, playlist_name):
    if DRY_RUN:
        return f"DRY_RUN_{playlist_name}"

    response = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": playlist_name,
                "description": f"Playlist automática: {playlist_name}"
            },
            "status": {
                "privacyStatus": PLAYLIST_PRIVACY_STATUS
            }
        }
    ).execute()

    print("Playlist criada:", playlist_name)

    time.sleep(5)

    return response["id"]


def resolve_playlist(youtube, user_input, default_name):
    playlists = get_all_playlists(youtube)

    # ID direto
    if user_input.startswith("PL"):
        return user_input, False

    # Nome informado
    if user_input:
        key = user_input.lower()

        if key in playlists:
            return playlists[key]["playlist_id"], False

        return create_playlist(youtube, user_input), True

    # fallback JSON
    key = default_name.lower()

    if key in playlists:
        return playlists[key]["playlist_id"], False

    return create_playlist(youtube, default_name), True


def get_existing_video_ids(youtube, playlist_id):
    ids = set()
    page_token = None

    while True:
        response = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=page_token
        ).execute()

        for item in response.get("items", []):
            ids.add(item["contentDetails"]["videoId"])

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return ids


def add_video(youtube, playlist_id, video_id):
    if DRY_RUN:
        return "dry_run"

    response = youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
            }
        }
    ).execute()

    time.sleep(SLEEP_SECONDS)

    return response.get("id")

# ============================================================
# MAIN
# ============================================================

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(CLASSIFICATION_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    default_playlist_name = data["target_playlist"]
    videos = data.get("videos", [])

    print("")
    user_input = input(
        "Digite ID da playlist, nome da playlist ou ENTER para usar padrão: "
    ).strip()

    youtube = get_authenticated_service()

    try:
        playlist_id, created = resolve_playlist(
            youtube,
            user_input,
            default_playlist_name
        )
    except HttpError as ex:
        if "quota" in str(ex).lower():
            print("Quota excedida. Tente novamente amanhã.")
            return
        raise

    existing_ids = set() if created else get_existing_video_ids(youtube, playlist_id)

    report = {
        "started_at": datetime.now().isoformat(),
        "playlist_id": playlist_id,
        "playlist_name": user_input or default_playlist_name,
        "created_playlist": created,
        "added": [],
        "skipped_duplicates": [],
        "errors": []
    }

    for video in videos:
        video_id = video.get("youtube_video_id")

        if not video_id:
            continue

        if video_id in existing_ids:
            report["skipped_duplicates"].append(video_id)
            continue

        try:
            playlist_item_id = add_video(youtube, playlist_id, video_id)
            existing_ids.add(video_id)

            report["added"].append({
                "video_id": video_id,
                "playlist_item_id": playlist_item_id
            })

            print("Adicionado:", video_id)

        except Exception as ex:
            report["errors"].append({
                "video_id": video_id,
                "error": str(ex)
            })

    report["finished_at"] = datetime.now().isoformat()

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)

    print("\nExecução finalizada:")
    print(REPORT_FILE)


if __name__ == "__main__":
    main()