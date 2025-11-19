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
#
# 2) Modo BATCH (com path de diretório)
#       python upload_youtube.py "C:/videos"
#    → Procura no diretório todos os arquivos:
#           *.mp4, *.mov, *.mkv, *.avi
#    → Para cada vídeo, procura um JSON com o mesmo nome:
#           Video1.mp4  → Video1.json
#           Aula10.mkv  → Aula10.json
#    → Cada JSON contém os metadados (igual ao metadata.json)
#    → Faz upload de cada vídeo individualmente
#    → Resolve/Cria playlist
#    → Adiciona o vídeo à playlist correspondente
#
# OBS IMPORTANTE:
#   O JSON de cada vídeo NÃO contém path do vídeo.
#   O script deduz automaticamente que:
#       VideoX.json pertence ao VideoX.mp4

# python upload_youtube.py "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\LTS SP Site - Audios para estudar inglês\\VideosGeradosPorScript\\Lessons\\20251111_1459_Lessons5"
# -------------------------------------------------------

import os
import sys
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import google.auth

# -------------------------------------------------------
# OAuth2 scopes necessários para upload de vídeos
# -------------------------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

TOKEN_PATH = "token.json"
CLIENT_SECRET_FILE = "youtube-upload-desktop.json"


# -------------------------------------------------------
# Autenticação
# -------------------------------------------------------
def get_authenticated_service():
    """
    Realiza a autenticação OAuth2.
    Se já existir token.json, reutiliza.
    Senão, abre navegador para autenticação.
    """
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
    """
    Faz upload do vídeo com base nos metadados fornecidos.
    """
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
# Playlist helper
# -------------------------------------------------------
def find_playlist_by_name(name):
    youtube = get_authenticated_service()

    request = youtube.playlists().list(
        part="snippet",
        mine=True,
        maxResults=50
    )
    response = request.execute()

    items = response.get("items", [])
    for item in items:
        if item["snippet"]["title"].strip().lower() == name.strip().lower():
            return item["id"]

    return None


def create_playlist(name, description):
    youtube = get_authenticated_service()

    body = {
        "snippet": {
            "title": name,
            "description": description
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    print(f"Creating playlist: {name}")
    response = youtube.playlists().insert(
        part="snippet,status",
        body=body
    ).execute()

    return response["id"]


def resolve_playlist(metadata):
    """
    Resolve playlist:
    - usa ID se existir
    - procura por nome
    - cria se estiver marcado "create_if_not_exists": true
    """
    playlist_info = metadata.get("playlist", {})

    if not playlist_info:
        return None

    playlist_id = playlist_info.get("id", "").strip()

    if playlist_id:
        return playlist_id

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
    """
    Adiciona o vídeo à playlist.
    """
    if not playlist_id:
        return

    youtube = get_authenticated_service()

    print(f"Adding video to playlist: {playlist_id}")
    body = {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": video_id
            }
        }
    }

    youtube.playlistItems().insert(part="snippet", body=body).execute()


# -------------------------------------------------------
# Modo SINGLE (metadata.json)
# -------------------------------------------------------
def process_single_mode():
    """
    Processo tradicional:
    - Lê metadata.json
    - Faz upload
    - Resolve playlist
    """
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
        print("All tasks completed successfully.")


# -------------------------------------------------------
# Modo BATCH (processa vários vídeos)
# -------------------------------------------------------
def process_batch_mode(directory):
    """
    - Procura vídeos dentro do diretório
    - Cada vídeo precisa ter um JSON correspondente
    - Faz upload de cada vídeo
    - Resolve playlist para cada um
    """
    print(f"\nBatch mode enabled.\nDirectory: {directory}")

    supported_ext = [".mp4", ".mov", ".mkv", ".avi"]

    files = os.listdir(directory)
    videos = [f for f in files if os.path.splitext(f)[1].lower() in supported_ext]

    if not videos:
        print("Nenhum vídeo encontrado no diretório.")
        return

    for video in videos:
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

    print("\nBatch upload completed.")


# -------------------------------------------------------
# Execução principal
# -------------------------------------------------------
if __name__ == "__main__":

    # Se NÃO tiver argumentos → modo SINGLE
    if len(sys.argv) == 1:
        process_single_mode()
        sys.exit()

    # Se tiver path → modo BATCH
    directory = sys.argv[1]

    if not os.path.isdir(directory):
        print("Erro: diretório inválido ou inexistente.")
        sys.exit()

    process_batch_mode(directory)
