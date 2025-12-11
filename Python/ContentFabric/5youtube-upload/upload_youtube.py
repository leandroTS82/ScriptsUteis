# -------------------------------------------------------
# upload_youtube.py — versão corrigida com erro técnico completo no relatório
# -------------------------------------------------------
# python upload_youtube.py "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\LTS SP Site - VideosGeradosPorScript\\Videos"
# python upload_youtube.py "C:\\dev\\scripts\\ScriptsUteis\\Python\\Gemini\\MakeVideoGemini\\outputs\\videos"

import os
import sys
import json
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# -------------------------------------------------------
# CONFIGURAÇÕES
# -------------------------------------------------------

DEFAULT_VIDEO_DIRECTORY = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Videos"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

TOKEN_PATH = "C:\\dev\\scripts\\ScriptsUteis\\Python\\secret_tokens_keys\\youtube_token.json"
CLIENT_SECRET_FILE = "C:\\dev\\scripts\\ScriptsUteis\\Python\\secret_tokens_keys\\youtube-upload-desktop.json"

REPORT_DIR = "./reports"

# -------------------------------------------------------
# CORES TERMINAL
# -------------------------------------------------------
RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"

# -------------------------------------------------------
# REPORT STRUCTURE
# -------------------------------------------------------

REPORT = {
    "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "end_time": None,
    "mode": "batch",
    "total_videos_found": 0,
    "total_uploaded": 0,
    "skipped_uploaded_files": 0,
    "failed_uploads": 0,
    "youtube_limit_error": False,
    "last_global_error": None,
    "videos": [],
    "warnings": []
}

# -------------------------------------------------------
# SAVE REPORT
# -------------------------------------------------------

def save_report():
    os.makedirs(REPORT_DIR, exist_ok=True)

    REPORT["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    output_path = os.path.join(REPORT_DIR, f"{timestamp}_report.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(REPORT, f, indent=4, ensure_ascii=False)

    print(f"\n{BLUE}📄 Relatório gerado em:{RESET} {output_path}")

# -------------------------------------------------------
# REPORT HELPERS
# -------------------------------------------------------

def add_error(file_name, message):
    REPORT["failed_uploads"] += 1
    REPORT["videos"].append({
        "file": file_name,
        "uploaded": False,
        "error": message
    })

def add_warning(file_name, message):
    REPORT["warnings"].append({
        "file": file_name,
        "warning": message
    })

# -------------------------------------------------------
# AUTHENTICATION
# -------------------------------------------------------

def get_authenticated_service():
    creds = None

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "r") as f:
            creds_data = json.load(f)
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.refresh_token:
            creds.refresh(Request())
        else:
            print(f"{BLUE}🔐 Abrindo navegador para autenticação...{RESET}")
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE,
                SCOPES
            )
            creds = flow.run_local_server(port=8080)

        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)

# -------------------------------------------------------
# LIMIT DETECTION
# -------------------------------------------------------

def is_upload_limit_error(error: HttpError):
    msg = str(error).lower()
    if error.resp.status == 403:
        return any(k in msg for k in [
            "uploadlimitexceeded",
            "daily limit",
            "quotaexceeded",
            "quota exceeded"
        ])
    return False

def handle_limit_and_exit():
    REPORT["youtube_limit_error"] = True
    print(f"\n{RED}🚫 YouTube atingiu o LIMITE DIÁRIO de uploads.{RESET}")
    print(f"{YELLOW}Motivo técnico completo:{RESET}")
    print(REPORT["last_global_error"])
    save_report()
    sys.exit(0)

# -------------------------------------------------------
# VIDEO UPLOAD
# -------------------------------------------------------

def upload_video(metadata, video_path):
    youtube = get_authenticated_service()

    try:
        snippet = {
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata["tags"],
            "categoryId": metadata["category_id"]
        }
        status = {
            "privacyStatus": metadata["visibility"],
            "selfDeclaredMadeForKids": metadata["made_for_kids"],
            "embeddable": metadata["embeddable"]
        }
    except KeyError as e:
        raise KeyError(f"JSON está faltando a chave obrigatória: {e}")

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

    try:
        print(f"{BLUE}📤 Enviando:{RESET} {video_path}")
        response = youtube.videos().insert(
            part="snippet,status",
            body={"snippet": snippet, "status": status},
            media_body=media
        ).execute()

        print(f"{GREEN}✔ Upload concluído!{RESET}")
        return response["id"]

    except HttpError as e:
        REPORT["last_global_error"] = str(e)

        if is_upload_limit_error(e):
            return "UPLOAD_LIMIT"

        return None

# -------------------------------------------------------
# PLAYLIST
# -------------------------------------------------------

def find_playlist(name):
    youtube = get_authenticated_service()
    resp = youtube.playlists().list(
        part="snippet",
        mine=True,
        maxResults=50
    ).execute()

    for item in resp.get("items", []):
        if item["snippet"]["title"].lower() == name.lower():
            return item["id"]

    return None

def create_playlist(name, desc):
    youtube = get_authenticated_service()
    print(f"{YELLOW}📁 Criando playlist:{RESET} {name}")
    resp = youtube.playlists().insert(
        part="snippet,status",
        body={"snippet": {"title": name, "description": desc},
              "status": {"privacyStatus": "public"}}
    ).execute()
    return resp["id"]

def resolve_playlist(metadata):
    info = metadata.get("playlist", {})

    if not info:
        return None

    if info.get("id"):
        return info["id"]

    name = info.get("name")
    desc = info.get("description", "")

    existing = find_playlist(name)
    if existing:
        print(f"{GREEN}✔ Playlist encontrada:{RESET} {name}")
        return existing

    if info.get("create_if_not_exists"):
        return create_playlist(name, desc)

    return None

# -------------------------------------------------------
# THUMBNAIL
# -------------------------------------------------------

def upload_thumbnail(video_id, thumb):
    if not thumb or not os.path.exists(thumb):
        return

    youtube = get_authenticated_service()

    try:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumb)
        ).execute()

        print(f"{GREEN}🖼 Thumbnail enviada!{RESET}")

    except HttpError as e:
        add_warning(thumb, str(e))

# -------------------------------------------------------
# FILE RENAME
# -------------------------------------------------------

def rename_uploaded(video_path, json_path, thumb):
    directory = os.path.dirname(video_path)

    new_video = os.path.join(directory, "uploaded_" + os.path.basename(video_path))
    os.rename(video_path, new_video)

    if json_path and os.path.exists(json_path):
        new_json = os.path.join(directory, "uploaded_" + os.path.basename(json_path))
        os.rename(json_path, new_json)

    if thumb and os.path.exists(thumb):
        new_thumb = os.path.join(directory, "uploaded_" + os.path.basename(thumb))
        os.rename(thumb, new_thumb)

# -------------------------------------------------------
# BATCH PROCESS
# -------------------------------------------------------

def process_batch(directory):
    supported = [".mp4", ".mov", ".mkv", ".avi"]
    images = [".jpg", ".jpeg", ".png"]

    files = os.listdir(directory)
    valid_videos = []

    # FILTRAGEM INICIAL
    for f in files:
        ext = os.path.splitext(f)[1].lower()

        if ext not in supported:
            continue

        if f.lower().startswith("uploaded_"):
            REPORT["skipped_uploaded_files"] += 1
            continue

        json_path = os.path.join(directory, f"{os.path.splitext(f)[0]}.json")
        if not os.path.exists(json_path):
            add_warning(f, "JSON não encontrado — vídeo ignorado")
            continue

        valid_videos.append(f)

    REPORT["total_videos_found"] = len(valid_videos)

    # LOOP PRINCIPAL
    for video in valid_videos:

        video_path = os.path.join(directory, video)
        json_path = os.path.join(directory, f"{os.path.splitext(video)[0]}.json")

        metadata = json.load(open(json_path, "r", encoding="utf-8"))

        # Thumbnail automática
        thumb = None
        for ext in images:
            candidate = os.path.join(directory, f"{os.path.splitext(video)[0]}{ext}")
            if os.path.exists(candidate):
                thumb = candidate
                break

        video_id = upload_video(metadata, video_path)

        if video_id == "UPLOAD_LIMIT":
            add_error(video, REPORT["last_global_error"])
            handle_limit_and_exit()

        if not video_id:
            add_error(video, REPORT["last_global_error"])
            continue

        upload_thumbnail(video_id, thumb)

        playlist_id = resolve_playlist(metadata)
        if playlist_id:
            youtube = get_authenticated_service()
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id}
                    }
                }
            ).execute()

        rename_uploaded(video_path, json_path, thumb)

        REPORT["videos"].append({"file": video, "uploaded": True, "error": None})
        REPORT["total_uploaded"] += 1

    save_report()
    print(f"\n{GREEN}✔ Batch upload concluído!{RESET}")

# -------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------

if __name__ == "__main__":

    # Se nenhum argumento for passado → usar diretório default
    if len(sys.argv) == 1:
        directory = DEFAULT_VIDEO_DIRECTORY
        print(f"{BLUE}Usando diretório DEFAULT:{RESET} {directory}")
    else:
        directory = sys.argv[1]
        print(f"{BLUE}Usando diretório:{RESET} {directory}")

    if not os.path.isdir(directory):
        print(f"{RED}❌ Diretório inválido:{RESET} {directory}")
        sys.exit(1)

    process_batch(directory)
