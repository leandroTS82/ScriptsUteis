# -------------------------------------------------------
# upload_youtube.py — FINAL
# Limite de uploads + feedback avançado + report robusto
#
# python upload_youtube.py "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\EnableToYoutubeUpload"
# -------------------------------------------------------

import os
import sys
import json
import shutil
import requests
import random
from datetime import datetime

# ======================================================
# CONFIGURAÇÃO DE LIMITE (YOUTUBE)
# ======================================================

MAX_UPLOADS_PER_RUN = 10

# ======================================================
# PATHS
# ======================================================

DEFAULT_VIDEO_DIRECTORY = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\EnableToYoutubeUpload"
THUMBNAIL_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Images"
FAULTY_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Youtube_Upload_Faulty_File"
REPORT_DIR = "./reports"

os.makedirs(FAULTY_DIR, exist_ok=True)

# ======================================================
# REGISTRA ThumbnailGenerator
# ======================================================

THUMBNAIL_GENERATOR_DIR = r"C:\dev\scripts\ScriptsUteis\Python\ContentFabric\ThumbnailGenerator"
sys.path.append(THUMBNAIL_GENERATOR_DIR)

from generate_thumbnail import generate_thumbnail

# ======================================================
# YOUTUBE IMPORTS
# ======================================================

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# ======================================================
# GROQ
# ======================================================

GROQ_API_KEY = open(
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\FilesHelper\secret_tokens_keys\groq_api_key.txt",
    encoding="utf-8"
).read().strip()

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

# ======================================================
# YOUTUBE AUTH
# ======================================================

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

TOKEN_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\FilesHelper\secret_tokens_keys\youtube_token.json"
CLIENT_SECRET_FILE = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\FilesHelper\secret_tokens_keys\youtube-upload-desktop.json"

# ======================================================
# CORES
# ======================================================

RESET = "\033[0m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"

# ======================================================
# REPORT
# ======================================================

REPORT = {
    "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "end_time": None,
    "max_uploads_per_run": MAX_UPLOADS_PER_RUN,
    "execution_stopped_reason": None,
    "total_videos_found": 0,
    "processed_videos": 0,
    "successful_uploads": 0,
    "failed_uploads": 0,
    "videos": []
}

# ======================================================
# HELPERS
# ======================================================

def save_report():
    os.makedirs(REPORT_DIR, exist_ok=True)
    REPORT["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    path = os.path.join(REPORT_DIR, f"{datetime.now():%Y%m%d%H%M%S}_report.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(REPORT, f, indent=4, ensure_ascii=False)
    print(f"{BLUE}Relatório salvo:{RESET} {path}")

def is_quota_error(error_msg: str) -> bool:
    msg = error_msg.lower()
    return any(k in msg for k in [
        "quota",
        "dailylimitexceeded",
        "uploadlimitexceeded"
    ])

def move_to_faulty(video_path, json_path):
    shutil.move(video_path, os.path.join(FAULTY_DIR, os.path.basename(video_path)))
    shutil.move(json_path, os.path.join(FAULTY_DIR, os.path.basename(json_path)))

# ======================================================
# AUTH
# ======================================================

def get_authenticated_service():
    from google.oauth2.credentials import Credentials
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_info(
            json.load(open(TOKEN_PATH)), SCOPES
        )

    if not creds or not creds.valid:
        if creds and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES
            )
            creds = flow.run_local_server(port=8080)

        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)

# ======================================================
# UPLOAD
# ======================================================

def upload_video(metadata, video_path):
    youtube = get_authenticated_service()
    media = MediaFileUpload(video_path, resumable=True)

    try:
        res = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": metadata["title"],
                    "description": metadata["description"],
                    "tags": metadata["tags"],
                    "categoryId": metadata["category_id"]
                },
                "status": {
                    "privacyStatus": metadata["visibility"]
                }
            },
            media_body=media
        ).execute()

        return res["id"]

    except HttpError as e:
        return str(e)

# ======================================================
# PROCESS
# ======================================================

def process_batch(directory):
    videos = [
        f for f in os.listdir(directory)
        if f.lower().endswith(".mp4")
        and not f.startswith("uploaded_")
        and os.path.exists(os.path.join(directory, os.path.splitext(f)[0] + ".json"))
    ]

    random.shuffle(videos)

    REPORT["total_videos_found"] = len(videos)

    print(f"{BLUE}Encontrados:{RESET} {len(videos)} vídeos\n")

    for video in videos:
        if REPORT["successful_uploads"] >= MAX_UPLOADS_PER_RUN:
            REPORT["execution_stopped_reason"] = "Upload limit reached"
            print(f"{YELLOW}Limite atingido. Encerrando execução.{RESET}")
            break

        REPORT["processed_videos"] += 1

        base = os.path.splitext(video)[0]
        video_path = os.path.join(directory, video)
        json_path = os.path.join(directory, base + ".json")
        metadata = json.load(open(json_path, encoding="utf-8"))

        print(f"{BLUE}Upload:{RESET} {video}")

        result = upload_video(metadata, video_path)

        if len(result) != 11:
            REPORT["failed_uploads"] += 1
            REPORT["videos"].append({
                "file": video,
                "uploaded": False,
                "error": result
            })

            if is_quota_error(result):
                REPORT["execution_stopped_reason"] = "YouTube quota error"
                print(f"{RED}Limite do YouTube detectado.{RESET}")
                break

            print(f"{RED}Falha -> movendo para Faulty{RESET}")
            move_to_faulty(video_path, json_path)
            continue

        shutil.move(video_path, os.path.join(directory, "uploaded_" + video))
        shutil.move(json_path, os.path.join(directory, "uploaded_" + base + ".json"))

        REPORT["successful_uploads"] += 1
        REPORT["videos"].append({"file": video, "uploaded": True})

        print(f"{GREEN}Upload concluído{RESET}\n")

    save_report()
    print(f"{GREEN}Execução finalizada{RESET}")

# ======================================================
# ENTRY
# ======================================================

if __name__ == "__main__":
    directory = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_VIDEO_DIRECTORY

    print(f"{BLUE}Diretório:{RESET} {directory}")

    if not os.path.isdir(directory):
        print(f"{RED}Diretório inválido{RESET}")
        sys.exit(1)

    process_batch(directory)
