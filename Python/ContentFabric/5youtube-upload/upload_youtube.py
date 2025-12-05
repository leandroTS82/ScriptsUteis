# -------------------------------------------------------
# upload_youtube.py
# -------------------------------------------------------
# NOVAS MELHORIAS:
#
# ✔ Detecta limite diário do YouTube (uploadLimitExceeded)
# ✔ Ao primeiro erro desse tipo → PARA o script imediatamente
# ✔ Exibe mensagem amigável ao usuário
# ✔ Salva relatório JSON antes de encerrar
# ✔ Funciona em modo SINGLE ou BATCH
# -------------------------------------------------------
# python upload_youtube.py "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\LTS SP Site - VideosGeradosPorScript\\Videos"
import os
import sys
import json
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import google.auth

# -------------------------------------------------------
# OAuth2 scopes e arquivos
# -------------------------------------------------------

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

TOKEN_PATH = "token.json"
CLIENT_SECRET_FILE = "youtube-upload-desktop.json"


# -------------------------------------------------------
# Estrutura do relatório
# -------------------------------------------------------

REPORT = {
    "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "end_time": None,
    "mode": None,
    "total_videos_found": 0,
    "total_uploaded": 0,
    "skipped_uploaded_files": 0,
    "failed_uploads": 0,
    "youtube_limit_error": False,
    "last_global_error": None,
    "videos": []
}


# -------------------------------------------------------
# Salvar relatório
# -------------------------------------------------------

def save_report(output_dir):
    REPORT["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    report_path = os.path.join(output_dir, f"{timestamp}_report.json")

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(REPORT, f, indent=4, ensure_ascii=False)

    print(f"\n📄 Relatório gerado em: {report_path}")


# -------------------------------------------------------
# Adicionar erro no relatório
# -------------------------------------------------------

def add_error_to_report(video_name, error_message):
    REPORT["failed_uploads"] += 1
    REPORT["videos"].append({
        "file": video_name,
        "uploaded": False,
        "error": error_message
    })


# -------------------------------------------------------
# Autenticação OAuth2
# -------------------------------------------------------

def get_authenticated_service():
    creds = None

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "r") as token:
            creds = google.oauth2.credentials.Credentials.from_authorized_user_info(
                json.load(token), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)

        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


# -------------------------------------------------------
# Detectar limite diário
# -------------------------------------------------------

def is_youtube_limit_error(error: HttpError):
    if error.resp.status == 403:
        msg = str(error).lower()
        keywords = [
            "uploadlimitexceeded",
            "user rate limit",
            "rate limit",
            "quota",
            "daily limit"
        ]
        return any(k in msg for k in keywords)
    return False


def handle_youtube_limit_reached(directory=None):
    """
    Exibe mensagem amigável e encerra o script.
    """
    print("\n🚫 O YouTube informou que o LIMITE DIÁRIO de uploads foi atingido.")
    print("⏳ Não há erro no seu vídeo, JSON ou script.")
    print("💡 Isso é uma restrição automática do YouTube para todos os canais.")
    print("🔁 Tente novamente após o reset diário (normalmente após 21h no Brasil).")

    REPORT["youtube_limit_error"] = True
    REPORT["last_global_error"] = "Daily upload limit reached"

    if directory is None:
        directory = os.getcwd()

    save_report("./")
    sys.exit(0)


# -------------------------------------------------------
# Upload de vídeo
# -------------------------------------------------------

def upload_video(metadata, video_path):
    youtube = get_authenticated_service()

    body = {
        "snippet": {
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata["tags"],
            "categoryId": metadata["category_id"]
        },
        "status": {
            "privacyStatus": metadata["visibility"],
            "selfDeclaredMadeForKids": metadata["made_for_kids"],
            "embeddable": metadata["embeddable"]
        }
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

    try:
        print(f"\n📤 Uploading video: {video_path}")
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        response = request.execute()
        print("✔ Upload complete.")
        return response["id"]

    except HttpError as e:
        REPORT["last_global_error"] = str(e)

        if is_youtube_limit_error(e):
            return "YOUTUBE_LIMIT"

        return None


# -------------------------------------------------------
# Upload da Thumbnail
# -------------------------------------------------------

def upload_thumbnail(video_id, thumbnail_path):
    if not thumbnail_path or not os.path.exists(thumbnail_path):
        return

    youtube = get_authenticated_service()

    try:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path)
        ).execute()
        print("🖼 Thumbnail enviada.")
    except HttpError as e:
        REPORT["last_global_error"] = str(e)
        add_error_to_report(thumbnail_path, f"Thumbnail upload failed: {e}")


# -------------------------------------------------------
# Playlist helpers
# -------------------------------------------------------

def find_playlist_by_name(name):
    youtube = get_authenticated_service()
    response = youtube.playlists().list(
        part="snippet",
        mine=True,
        maxResults=50
    ).execute()

    for item in response.get("items", []):
        if item["snippet"]["title"].lower() == name.lower():
            return item["id"]
    return None


def create_playlist(name, description):
    youtube = get_authenticated_service()
    body = {
        "snippet": {"title": name, "description": description},
        "status": {"privacyStatus": "public"}
    }

    print(f"📁 Creating playlist: {name}")
    return youtube.playlists().insert(
        part="snippet,status",
        body=body
    ).execute()["id"]


def resolve_playlist(metadata):
    info = metadata.get("playlist", {})

    if not info:
        return None

    if info.get("id", "").strip():
        return info["id"]

    name = info.get("name", "")
    description = info.get("description", "")
    create_if_missing = info.get("create_if_not_exists", False)

    found = find_playlist_by_name(name)
    if found:
        print(f"✔ Playlist found: {name}")
        return found

    if create_if_missing:
        return create_playlist(name, description)

    return None


def add_to_playlist(video_id, playlist_id):
    if not playlist_id:
        return

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


# -------------------------------------------------------
# Renomear arquivos enviados
# -------------------------------------------------------

def rename_uploaded_files(video_path, json_path=None, thumb_path=None):
    directory = os.path.dirname(video_path)

    new_video = "uploaded_" + os.path.basename(video_path)
    os.rename(video_path, os.path.join(directory, new_video))
    print(f"🔄 Renamed video → {new_video}")

    if json_path and os.path.exists(json_path):
        new_json = "uploaded_" + os.path.basename(json_path)
        os.rename(json_path, os.path.join(directory, new_json))
        print(f"🔄 Renamed metadata → {new_json}")

    if thumb_path and os.path.exists(thumb_path):
        new_thumb = "uploaded_" + os.path.basename(thumb_path)
        os.rename(thumb_path, os.path.join(directory, new_thumb))
        print(f"🔄 Renamed thumbnail → {new_thumb}")


# -------------------------------------------------------
# SINGLE MODE
# -------------------------------------------------------

def process_single_mode():
    REPORT["mode"] = "single"

    with open("metadata.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)

    video_path = metadata.get("video_file")

    thumb_path = metadata.get("thumbnail_path")
    if not thumb_path:
        base = os.path.splitext(video_path)[0]
        for ext in [".jpg", ".png", ".jpeg"]:
            if os.path.exists(base + ext):
                thumb_path = base + ext

    video_id = upload_video(metadata, video_path)

    if video_id == "YOUTUBE_LIMIT":
        handle_youtube_limit_reached(os.path.dirname(video_path))

    if not video_id:
        add_error_to_report(video_path, REPORT["last_global_error"])
        save_report("./")
        return

    upload_thumbnail(video_id, thumb_path)

    playlist_id = resolve_playlist(metadata)
    add_to_playlist(video_id, playlist_id)

    rename_uploaded_files(video_path, "metadata.json", thumb_path)

    REPORT["total_uploaded"] = 1
    REPORT["videos"].append({"file": video_path, "uploaded": True, "error": None})

    save_report("./")

    print("\n✔ Upload concluído com sucesso!")


# -------------------------------------------------------
# BATCH MODE
# -------------------------------------------------------

def process_batch_mode(directory):
    REPORT["mode"] = "batch"

    supported_ext = [".mp4", ".mov", ".mkv", ".avi"]
    image_exts = [".jpg", ".png", ".jpeg"]

    files = os.listdir(directory)
    videos = [f for f in files if os.path.splitext(f)[1].lower() in supported_ext]

    REPORT["total_videos_found"] = len(videos)

    for video in videos:

        if video.lower().startswith("uploaded_"):
            REPORT["skipped_uploaded_files"] += 1
            print(f"⏭ Skipping already uploaded file: {video}")
            continue

        video_path = os.path.join(directory, video)
        json_path = os.path.join(directory, f"{os.path.splitext(video)[0]}.json")

        thumb_path = None
        for ext in image_exts:
            t = os.path.join(directory, f"{os.path.splitext(video)[0]}{ext}")
            if os.path.exists(t):
                thumb_path = t
                break

        if not os.path.exists(json_path):
            add_error_to_report(video, "JSON not found")
            print(f"⚠ JSON not found for {video}")
            continue

        metadata = json.load(open(json_path, "r", encoding="utf-8"))

        video_id = upload_video(metadata, video_path)

        if video_id == "YOUTUBE_LIMIT":
            add_error_to_report(video, "Daily upload limit reached")
            handle_youtube_limit_reached(directory)

        if not video_id:
            add_error_to_report(video, REPORT["last_global_error"])
            continue

        upload_thumbnail(video_id, thumb_path)
        playlist_id = resolve_playlist(metadata)
        add_to_playlist(video_id, playlist_id)

        rename_uploaded_files(video_path, json_path, thumb_path)

        REPORT["videos"].append({"file": video, "uploaded": True, "error": None})
        REPORT["total_uploaded"] += 1

    save_report("./")
    print("\n✔ Batch upload completed!")


# -------------------------------------------------------
# EXECUÇÃO
# -------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) == 1:
        process_single_mode()
    else:
        directory = sys.argv[1]
        if not os.path.isdir(directory):
            print("❌ Diretório inválido.")
            sys.exit()
        process_batch_mode(directory)
