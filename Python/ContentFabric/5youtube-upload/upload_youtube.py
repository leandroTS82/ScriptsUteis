# -------------------------------------------------------
# upload_youtube.py — FINAL
# Limite de uploads + feedback avançado + report robusto
# -------------------------------------------------------

import os
import sys
import json
import requests
from datetime import datetime

# ======================================================
# CONFIGURAÇÃO DE LIMITE (YOUTUBE)
# ======================================================

MAX_UPLOADS_PER_RUN = 10  # 🔥 AJUSTE AQUI SE NECESSÁRIO

# ======================================================
# REGISTRA ThumbnailGenerator NO PYTHONPATH
# ======================================================

THUMBNAIL_GENERATOR_DIR = r"C:\dev\scripts\ScriptsUteis\Python\ContentFabric\ThumbnailGenerator"

if THUMBNAIL_GENERATOR_DIR not in sys.path:
    sys.path.append(THUMBNAIL_GENERATOR_DIR)

from generate_thumbnail import generate_thumbnail

# ======================================================
# IMPORTS YOUTUBE
# ======================================================

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# ======================================================
# CONFIGURAÇÕES GERAIS
# ======================================================

DEFAULT_VIDEO_DIRECTORY = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Videos\Teste"
THUMBNAIL_DIR = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Images"
FONTS_DIR = r"C:\dev\scripts\ScriptsUteis\Python\ContentFabric\ThumbnailGenerator\fonts"

FONT_MAP = {
    "bebas_neue": "BebasNeue-Regular.ttf",
    "montserrat": "Montserrat-Bold.ttf",
    "anton": "Anton-Regular.ttf"
}

# ---------------- GROQ ----------------

GROQ_API_KEY = open(
    r"C:\dev\scripts\ScriptsUteis\Python\secret_tokens_keys\groq_api_key.txt",
    "r",
    encoding="utf-8"
).read().strip()

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

# ---------------- YOUTUBE ----------------

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

TOKEN_PATH = r"C:\dev\scripts\ScriptsUteis\Python\secret_tokens_keys\youtube_token.json"
CLIENT_SECRET_FILE = r"C:\dev\scripts\ScriptsUteis\Python\secret_tokens_keys\youtube-upload-desktop.json"

REPORT_DIR = "./reports"

# ======================================================
# CORES TERMINAL
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
    "mode": "batch",
    "max_uploads_per_run": MAX_UPLOADS_PER_RUN,
    "execution_stopped_reason": None,
    "total_videos_found": 0,
    "processed_videos": 0,
    "successful_uploads": 0,
    "failed_uploads": 0,
    "skipped_uploaded_files": 0,
    "remaining_videos_not_processed": 0,
    "videos": [],
    "warnings": []
}

# ======================================================
# HELPERS
# ======================================================

def save_report():
    os.makedirs(REPORT_DIR, exist_ok=True)
    REPORT["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    path = os.path.join(REPORT_DIR, f"{ts}_report.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(REPORT, f, indent=4, ensure_ascii=False)

    print(f"\n{BLUE}📄 Relatório gerado:{RESET} {path}")

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

# ======================================================
# AUTH YOUTUBE
# ======================================================

def get_authenticated_service():
    creds = None

    if os.path.exists(TOKEN_PATH):
        from google.oauth2.credentials import Credentials
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
# GROQ — THUMB DESIGN
# ======================================================

def generate_thumbnail_design(video_json):
    prompt = f"""
You are a YouTube thumbnail copywriter and visual designer.

Rules:
- Portuguese (Brazil)
- Max 5 words
- Uppercase
- Young YouTube style
- SEO optimized
- High contrast
- No emojis

Return ONLY valid JSON:
{{
  "title": "",
  "highlight": "",
  "font": "bebas_neue | montserrat | anton",
  "text_color": "#FFFFFF",
  "highlight_color": "#A855F7",
  "stroke_color": "#000000"
}}

Context:
Title: {video_json["title"]}
Description: {video_json["description"]}
"""

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    res = requests.post(GROQ_URL, json=payload, headers=headers)
    res.raise_for_status()

    text = res.json()["choices"][0]["message"]["content"]
    start, end = text.find("{"), text.rfind("}") + 1
    return json.loads(text[start:end])

# ======================================================
# UPLOAD VIDEO + THUMB
# ======================================================

def upload_video(metadata, video_path):
    youtube = get_authenticated_service()

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

    try:
        print(f"{BLUE}📤 Enviando vídeo:{RESET} {os.path.basename(video_path)}")
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
                    "privacyStatus": metadata["visibility"],
                    "selfDeclaredMadeForKids": metadata["made_for_kids"],
                    "embeddable": metadata["embeddable"]
                }
            },
            media_body=media
        ).execute()

        return res["id"]

    except HttpError as e:
        return str(e)

def upload_thumbnail(video_id, thumb_path):
    if not thumb_path or not os.path.exists(thumb_path):
        return

    youtube = get_authenticated_service()
    youtube.thumbnails().set(
        videoId=video_id,
        media_body=MediaFileUpload(thumb_path)
    ).execute()

# ======================================================
# BATCH PROCESS
# ======================================================

def process_batch(directory):
    video_exts = (".mp4", ".mov", ".mkv", ".avi")

    candidates = []
    for f in os.listdir(directory):
        if f.lower().startswith("uploaded_"):
            REPORT["skipped_uploaded_files"] += 1
            continue

        if f.lower().endswith(video_exts):
            base = os.path.splitext(f)[0]
            if os.path.exists(os.path.join(directory, base + ".json")):
                candidates.append(f)

    REPORT["total_videos_found"] = len(candidates)

    print(f"\n{BLUE}🎯 Vídeos encontrados:{RESET} {len(candidates)}")
    print(f"{BLUE}🚦 Limite por execução:{RESET} {MAX_UPLOADS_PER_RUN}\n")

    for index, video in enumerate(candidates, start=1):

        if REPORT["successful_uploads"] >= MAX_UPLOADS_PER_RUN:
            REPORT["execution_stopped_reason"] = "YouTube upload limit reached"
            break

        REPORT["processed_videos"] += 1

        print(
            f"{YELLOW}▶ Processando {index}/{len(candidates)} "
            f"(uploads: {REPORT['successful_uploads']}/{MAX_UPLOADS_PER_RUN}){RESET}"
        )

        base = os.path.splitext(video)[0]
        video_path = os.path.join(directory, video)
        json_path = os.path.join(directory, base + ".json")
        metadata = json.load(open(json_path, encoding="utf-8"))

        # Thumbnail
        raw_image = os.path.join(THUMBNAIL_DIR, base + ".png")
        thumb_path = None

        if os.path.exists(raw_image):
            try:
                design = generate_thumbnail_design(metadata)
                font_path = os.path.join(
                    FONTS_DIR,
                    FONT_MAP.get(design["font"], FONT_MAP["bebas_neue"])
                )

                thumb_path = os.path.join(THUMBNAIL_DIR, base + "_thumb.png")

                generate_thumbnail(
                    image_path=raw_image,
                    output_path=thumb_path,
                    title=design["title"],
                    highlight=design["highlight"],
                    font_path=font_path,
                    text_color=design["text_color"],
                    highlight_color=design["highlight_color"],
                    stroke_color=design["stroke_color"]
                )

                print(f"{GREEN}🎨 Thumbnail gerada{RESET}")

            except Exception as e:
                add_warning(video, f"Thumbnail falhou: {e}")

        result = upload_video(metadata, video_path)

        if len(result) != 11:
            add_error(video, result)
            continue

        upload_thumbnail(result, thumb_path)

        os.rename(video_path, os.path.join(directory, "uploaded_" + video))
        os.rename(json_path, os.path.join(directory, "uploaded_" + base + ".json"))

        REPORT["successful_uploads"] += 1
        REPORT["videos"].append({"file": video, "uploaded": True})

        print(f"{GREEN}✔ Upload concluído{RESET}\n")

    REPORT["remaining_videos_not_processed"] = (
        REPORT["total_videos_found"] - REPORT["processed_videos"]
    )

    save_report()
    print(f"\n{GREEN}🏁 Execução finalizada{RESET}")

# ======================================================
# ENTRY
# ======================================================

if __name__ == "__main__":
    directory = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_VIDEO_DIRECTORY

    print(f"{BLUE}📁 Diretório:{RESET} {directory}")

    if not os.path.isdir(directory):
        print(f"{RED}❌ Diretório inválido{RESET}")
        sys.exit(1)

    process_batch(directory)
