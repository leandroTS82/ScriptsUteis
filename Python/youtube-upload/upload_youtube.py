# upload_youtube.py
# -------------------------------------------------------
# Script para upload de vídeos no YouTube.
# Funciona em dois modos:
#
# 1) Modo SINGLE (sem argumentos)
#       python upload_youtube.py
#    → Lê metadata.json
#    → Faz upload do vídeo indicado em metadata.json
#    → Resolve/Cria playlist
#    → Adiciona o vídeo à playlist
#    → Renomeia vídeo e JSON para uploaded_YYYYMMDDHHMM_nome.ext
#
# 2) Modo BATCH (com path de diretório)
#       python upload_youtube.py "C:/videos"
#    → Procura no diretório todos os arquivos:
#          *.mp4, *.mov, *.mkv, *.avi
#    → Para cada vídeo, procura um JSON com o mesmo nome:
#          Video1.mp4  → Video1.json
#          Aula10.mkv  → Aula10.json
#    → Cada JSON contém os metadados (igual ao metadata.json)
#    → Faz upload de cada vídeo individualmente
#    → Resolve/Cria playlist
#    → Adiciona o vídeo à playlist correspondente
#    → Renomeia vídeo + JSON para uploaded_YYYYMMDDHHMM_nome.ext
#
# NOVA MELHORIA (batch mode):
#    • Arquivos cujo nome começa com "uploaded_" são ignorados
#    • Notificação aparece no console:
#          "Skipping already uploaded file: uploaded_202501021300_Video1.mp4"

#Execução
# python upload_youtube.py "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\LTS SP Site - Audios para estudar inglês\\VideosGeradosPorScript\\GOOGLE_TTS\\WordBank"
# -------------------------------------------------------

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
# OAuth2 scopes
# -------------------------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

TOKEN_PATH = "token.json"
CLIENT_SECRET_FILE = "youtube-upload-desktop.json"


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
                CLIENT_SECRET_FILE, SCOPES
            )
            creds = flow.run_local_server(port=8080)

        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


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
        print(f"\nUploading video: {video_path}")
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        response = request.execute()
        print("Upload complete.")
        return response["id"]
    except HttpError as e:
        print(f"YouTube API error: {e}")
        return None


# -------------------------------------------------------
# Playlist helpers
# -------------------------------------------------------
def find_playlist_by_name(name):
    youtube = get_authenticated_service()

    request = youtube.playlists().list(
        part="snippet",
        mine=True,
        maxResults=50
    )
    response = request.execute()

    for item in response.get("items", []):
        if item["snippet"]["title"].strip().lower() == name.strip().lower():
            return item["id"]

    return None


def create_playlist(name, description):
    youtube = get_authenticated_service()

    body = {
        "snippet": {"title": name, "description": description},
        "status": {"privacyStatus": "public"}
    }

    print(f"Creating playlist: {name}")
    return youtube.playlists().insert(
        part="snippet,status",
        body=body
    ).execute()["id"]


def resolve_playlist(metadata):
    playlist_info = metadata.get("playlist", {})

    if not playlist_info:
        return None

    if playlist_info.get("id", "").strip():
        return playlist_info["id"]

    name = playlist_info.get("name", "")
    description = playlist_info.get("description", "")
    create_if_missing = playlist_info.get("create_if_not_exists", False)

    if not name:
        return None

    found_id = find_playlist_by_name(name)
    if found_id:
        print(f"Playlist found: {name}")
        return found_id

    if create_if_missing:
        print("Playlist not found. Creating...")
        return create_playlist(name, description)

    return None


def add_to_playlist(video_id, playlist_id):
    if not playlist_id:
        return

    youtube = get_authenticated_service()

    print(f"Adding video to playlist: {playlist_id}")
    youtube.playlistItems().insert(
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


# -------------------------------------------------------
# Renomear arquivos após upload
# -------------------------------------------------------
def rename_uploaded_files(video_path, json_path=None):
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    directory = os.path.dirname(video_path)

    video_name = os.path.basename(video_path)
    new_video_name = f"uploaded_{timestamp}_{video_name}"
    os.rename(video_path, os.path.join(directory, new_video_name))
    print(f"Renamed video → {new_video_name}")

    if json_path and os.path.exists(json_path):
        json_name = os.path.basename(json_path)
        new_json_name = f"uploaded_{timestamp}_{json_name}"
        os.rename(json_path, os.path.join(directory, new_json_name))
        print(f"Renamed metadata → {new_json_name}")


# -------------------------------------------------------
# Modo SINGLE
# -------------------------------------------------------
def process_single_mode():
    with open("metadata.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)

    video_path = metadata.get("video_file")
    if not video_path:
        print("Erro: metadata.json precisa conter video_file.")
        return

    video_id = upload_video(metadata, video_path)

    if video_id:
        playlist_id = resolve_playlist(metadata)
        add_to_playlist(video_id, playlist_id)
        rename_uploaded_files(video_path, "metadata.json")
        print("All tasks completed successfully.")


# -------------------------------------------------------
# Modo BATCH
# -------------------------------------------------------
def process_batch_mode(directory):
    print(f"\nBatch mode enabled.\nDirectory: {directory}")

    supported_ext = [".mp4", ".mov", ".mkv", ".avi"]

    files = os.listdir(directory)
    videos = [
        f for f in files
        if os.path.splitext(f)[1].lower() in supported_ext
    ]

    if not videos:
        print("Nenhum vídeo encontrado no diretório.")
        return

    for video in videos:

        # NOVA REGRA → ignorar arquivos uploaded_
        if video.lower().startswith("uploaded_"):
            print(f"Skipping already uploaded file: {video}")
            continue

        video_path = os.path.join(directory, video)

        base = os.path.splitext(video)[0]
        json_path = os.path.join(directory, f"{base}.json")

        if not os.path.exists(json_path):
            print(f"\nWARNING: JSON not found for video: {video}")
            print(f"Expected: {base}.json")
            continue

        print(f"\nProcessing video: {video}")

        with open(json_path, "r", encoding="utf-8") as jf:
            metadata = json.load(jf)

        video_id = upload_video(metadata, video_path)

        if video_id:
            playlist_id = resolve_playlist(metadata)
            add_to_playlist(video_id, playlist_id)
            rename_uploaded_files(video_path, json_path)

    print("\nBatch upload completed.")


# -------------------------------------------------------
# Execução principal
# -------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) == 1:
        process_single_mode()
        sys.exit()

    directory = sys.argv[1]

    if not os.path.isdir(directory):
        print("Erro: diretório inválido ou inexistente.")
        sys.exit()

    process_batch_mode(directory)
