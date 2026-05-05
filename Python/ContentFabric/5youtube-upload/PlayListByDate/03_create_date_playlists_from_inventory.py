# -------------------------------------------------------
# create_date_playlists_from_inventory.py
#
# Lê o JSON exportado do YouTube.
# Para vídeos sem playlist:
# - agrupa por data de upload
# - calcula duração total estimada
# - cria/usa playlist por data
# - adiciona vídeos na playlist da data
# - adiciona vídeos também na playlist "Word Bank - ALL"
#
# Corrigido:
# - evita playlistNotFound logo após criar playlist
# - adiciona retry/backoff
# - limita criação/processamento por execução
# - salva report parcial mesmo com erro
# -------------------------------------------------------

import os
import json
import re
import time
import sys
from datetime import datetime
from collections import defaultdict

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request

CURRENT_DIR = os.path.dirname(__file__)
SHARED_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "00_Shared"))

if SHARED_DIR not in sys.path:
    sys.path.append(SHARED_DIR)
from youtube_auth import get_youtube_client

# ======================================================
# CONFIG
# ======================================================

INPUT_JSON = r"C:\dev\scripts\ScriptsUteis\Python\ContentFabric\5youtube-upload\00_Shared\youtube_uploaded_inventory.json"

OUTPUT_DIR = r".\output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")

PLAN_OUTPUT = os.path.join(
    OUTPUT_DIR,
    f"youtube_playlist_plan_{RUN_ID}.json"
)

REPORT_OUTPUT = os.path.join(
    OUTPUT_DIR,
    f"youtube_playlist_execution_report_{RUN_ID}.json"
)


WORD_BANK_ALL_PLAYLIST_ID = "PLzVI0b1epy98y2vfCpkVXqrK84dV9RrJo"
WORD_BANK_ALL_PLAYLIST_TITLE = "Word Bank - ALL"

PLAYLIST_PRIVACY_STATUS = "public"

DRY_RUN = False

# Evita estourar quota/rate limit.
MAX_PLAYLISTS_PER_RUN = 5

# Pequeno intervalo entre inserts.
SLEEP_BETWEEN_INSERTS_SECONDS = 1.5

# Delay após criar playlist.
# Evita 404 playlistNotFound por eventual consistency.
SLEEP_AFTER_PLAYLIST_CREATE_SECONDS = 5

# Retry para erros temporários.
MAX_RETRIES = 4



# ======================================================
# HTTP / RETRY
# ======================================================

def is_rate_limit_error(ex: Exception) -> bool:
    msg = str(ex).lower()
    return (
        "rate_limit_exceeded" in msg
        or "quota" in msg
        or "resource has been exhausted" in msg
        or "dailylimitexceeded" in msg
    )


def is_playlist_not_found_error(ex: Exception) -> bool:
    msg = str(ex).lower()
    return "playlistnotfound" in msg or "playlist identified" in msg


def execute_with_retry(callable_fn, action_name: str):
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return callable_fn()

        except HttpError as ex:
            last_error = ex

            if is_rate_limit_error(ex):
                raise

            if is_playlist_not_found_error(ex):
                wait = attempt * 4
                print(f"AVISO: {action_name} retornou playlistNotFound. Retry em {wait}s...")
                time.sleep(wait)
                continue

            if ex.resp.status in [500, 502, 503, 504]:
                wait = attempt * 3
                print(f"AVISO: {action_name} erro temporário {ex.resp.status}. Retry em {wait}s...")
                time.sleep(wait)
                continue

            raise

        except Exception as ex:
            last_error = ex
            wait = attempt * 2
            print(f"AVISO: {action_name} falhou. Retry em {wait}s...")
            time.sleep(wait)

    raise last_error

# ======================================================
# DURATION
# ======================================================

def parse_iso8601_duration(duration: str) -> int:
    if not duration:
        return 0

    pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
    match = re.match(pattern, duration)

    if not match:
        return 0

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    return hours * 3600 + minutes * 60 + seconds


def format_duration(total_seconds: int) -> str:
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours:
        return f"{hours}h {minutes:02d}min"
    if minutes:
        return f"{minutes}min {seconds:02d}s"
    return f"{seconds}s"


def format_duration_for_title(total_seconds: int) -> str:
    minutes = round(total_seconds / 60)

    if minutes < 60:
        return f"{minutes} min"

    hours = minutes // 60
    rest = minutes % 60

    if rest == 0:
        return f"{hours}h"

    return f"{hours}h{rest:02d}"

# ======================================================
# DATE
# ======================================================

def get_upload_date_key(video: dict) -> str:
    uploaded_at = video.get("youtube_uploaded_at")

    if not uploaded_at:
        return "unknown-date"

    dt = datetime.fromisoformat(uploaded_at.replace("Z", "+00:00"))
    return dt.strftime("%Y-%m-%d")


def format_date_br(date_key: str) -> str:
    dt = datetime.strptime(date_key, "%Y-%m-%d")
    return dt.strftime("%d-%m-%Y")


def build_playlist_title(date_key: str, total_seconds: int) -> str:
    date_br = format_date_br(date_key)
    duration_title = format_duration_for_title(total_seconds)
    return f"Word Bank - {date_br} - {duration_title}"

# ======================================================
# YOUTUBE HELPERS
# ======================================================

def get_all_playlists(youtube):
    playlists = {}
    page_token = None

    while True:
        response = execute_with_retry(
            lambda: youtube.playlists().list(
                part="snippet",
                mine=True,
                maxResults=50,
                pageToken=page_token
            ).execute(),
            "get_all_playlists"
        )

        for item in response.get("items", []):
            title = item["snippet"]["title"]
            playlists[title.lower()] = {
                "playlist_id": item["id"],
                "playlist_title": title
            }

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return playlists


def create_playlist(youtube, title, description):
    if DRY_RUN:
        return f"DRY_RUN_{title}"

    response = execute_with_retry(
        lambda: youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description
                },
                "status": {
                    "privacyStatus": PLAYLIST_PRIVACY_STATUS
                }
            }
        ).execute(),
        f"create_playlist:{title}"
    )

    playlist_id = response["id"]

    print(f"Playlist criada: {title} -> {playlist_id}")
    print(f"Aguardando {SLEEP_AFTER_PLAYLIST_CREATE_SECONDS}s para evitar playlistNotFound...")
    time.sleep(SLEEP_AFTER_PLAYLIST_CREATE_SECONDS)

    return playlist_id


def get_or_create_playlist(youtube, existing_playlists, title, description):
    key = title.lower()

    if key in existing_playlists:
        return existing_playlists[key]["playlist_id"], False

    playlist_id = create_playlist(youtube, title, description)

    existing_playlists[key] = {
        "playlist_id": playlist_id,
        "playlist_title": title
    }

    return playlist_id, True


def get_existing_video_ids_in_playlist(youtube, playlist_id):
    video_ids = set()
    page_token = None

    while True:
        response = execute_with_retry(
            lambda: youtube.playlistItems().list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=page_token
            ).execute(),
            f"get_existing_video_ids_in_playlist:{playlist_id}"
        )

        for item in response.get("items", []):
            video_ids.add(item["contentDetails"]["videoId"])

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return video_ids


def add_video_to_playlist(youtube, playlist_id, video_id):
    if DRY_RUN:
        return {
            "status": "dry_run",
            "video_id": video_id,
            "playlist_id": playlist_id
        }

    response = execute_with_retry(
        lambda: youtube.playlistItems().insert(
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
        ).execute(),
        f"add_video_to_playlist:{video_id}"
    )

    time.sleep(SLEEP_BETWEEN_INSERTS_SECONDS)

    return {
        "status": "added",
        "playlist_item_id": response.get("id"),
        "video_id": video_id,
        "playlist_id": playlist_id
    }

# ======================================================
# PLAN
# ======================================================

def build_plan(inventory):
    groups = defaultdict(list)

    for video in inventory.get("videos", []):
        if video.get("has_playlist") is True:
            continue

        video_id = video.get("video_id")
        if not video_id:
            continue

        duration_seconds = parse_iso8601_duration(video.get("duration"))

        if duration_seconds > 120:
            continue

        date_key = get_upload_date_key(video)
        groups[date_key].append(video)

    playlists = []

    for date_key, videos in sorted(groups.items(), reverse=True):
        total_seconds = sum(
            parse_iso8601_duration(v.get("duration"))
            for v in videos
        )

        playlist_title = build_playlist_title(date_key, total_seconds)

        playlists.append({
            "upload_date": date_key,
            "upload_date_br": format_date_br(date_key),
            "playlist_title": playlist_title,
            "privacy_status": PLAYLIST_PRIVACY_STATUS,
            "total_videos": len(videos),
            "total_duration_seconds": total_seconds,
            "total_duration_label": format_duration(total_seconds),
            "also_add_to": {
                "playlist_id": WORD_BANK_ALL_PLAYLIST_ID,
                "playlist_title": WORD_BANK_ALL_PLAYLIST_TITLE
            },
            "videos": [
                {
                    "video_id": v.get("video_id"),
                    "title": v.get("title"),
                    "youtube_uploaded_at": v.get("youtube_uploaded_at"),
                    "duration": v.get("duration"),
                    "duration_seconds": parse_iso8601_duration(v.get("duration")),
                    "uploaded_file_name": v.get("uploaded_file_name")
                }
                for v in videos
            ]
        })

    return {
        "generated_at": datetime.now().isoformat(),
        "source_json": INPUT_JSON,
        "dry_run": DRY_RUN,
        "max_playlists_per_run": MAX_PLAYLISTS_PER_RUN,
        "rule": "Only videos with has_playlist=false are grouped by youtube_uploaded_at date.",
        "word_bank_all_playlist": {
            "playlist_id": WORD_BANK_ALL_PLAYLIST_ID,
            "playlist_title": WORD_BANK_ALL_PLAYLIST_TITLE
        },
        "total_playlists_to_process": len(playlists),
        "total_videos_to_process": sum(p["total_videos"] for p in playlists),
        "playlists": playlists
    }

# ======================================================
# REPORT
# ======================================================

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def create_empty_report():
    return {
        "started_at": datetime.now().isoformat(),
        "finished_at": None,
        "dry_run": DRY_RUN,
        "created_playlists": [],
        "used_existing_playlists": [],
        "added_to_date_playlists": [],
        "skipped_date_playlist_duplicates": [],
        "added_to_word_bank_all": [],
        "skipped_word_bank_all_duplicates": [],
        "errors": [],
        "stopped_reason": None
    }

# ======================================================
# EXECUTION
# ======================================================

def execute_plan(youtube, plan):
    report = create_empty_report()

    existing_playlists = get_all_playlists(youtube)

    print("Carregando vídeos já existentes em Word Bank - ALL...")
    word_bank_existing_video_ids = get_existing_video_ids_in_playlist(
        youtube,
        WORD_BANK_ALL_PLAYLIST_ID
    )

    processed_playlists = 0

    for playlist in plan["playlists"]:
        if processed_playlists >= MAX_PLAYLISTS_PER_RUN:
            report["stopped_reason"] = f"MAX_PLAYLISTS_PER_RUN reached: {MAX_PLAYLISTS_PER_RUN}"
            print(f"Limite por execução atingido: {MAX_PLAYLISTS_PER_RUN}")
            break

        playlist_title = playlist["playlist_title"]

        description = (
            f"Playlist automática gerada para vídeos enviados em "
            f"{playlist['upload_date_br']}.\n"
            f"Duração estimada total: {playlist['total_duration_label']}.\n"
            f"Total de vídeos: {playlist['total_videos']}."
        )

        print("")
        print(f"Processando playlist: {playlist_title}")

        try:
            playlist_id, created = get_or_create_playlist(
                youtube,
                existing_playlists,
                playlist_title,
                description
            )

            playlist["playlist_id"] = playlist_id

            if created:
                report["created_playlists"].append({
                    "playlist_id": playlist_id,
                    "playlist_title": playlist_title
                })

                # CORREÇÃO:
                # Playlist recém-criada ainda pode não estar disponível para playlistItems.list.
                date_playlist_existing_video_ids = set()
            else:
                report["used_existing_playlists"].append({
                    "playlist_id": playlist_id,
                    "playlist_title": playlist_title
                })

                print("Carregando vídeos já existentes na playlist da data...")
                date_playlist_existing_video_ids = get_existing_video_ids_in_playlist(
                    youtube,
                    playlist_id
                )

            for video in playlist["videos"]:
                video_id = video["video_id"]

                # 1) Playlist da data
                if video_id in date_playlist_existing_video_ids:
                    report["skipped_date_playlist_duplicates"].append({
                        "video_id": video_id,
                        "title": video["title"],
                        "playlist_id": playlist_id,
                        "playlist_title": playlist_title
                    })
                else:
                    result = add_video_to_playlist(youtube, playlist_id, video_id)
                    date_playlist_existing_video_ids.add(video_id)

                    report["added_to_date_playlists"].append({
                        **result,
                        "title": video["title"],
                        "playlist_title": playlist_title
                    })

                # 2) Word Bank - ALL
                if video_id in word_bank_existing_video_ids:
                    report["skipped_word_bank_all_duplicates"].append({
                        "video_id": video_id,
                        "title": video["title"],
                        "playlist_id": WORD_BANK_ALL_PLAYLIST_ID,
                        "playlist_title": WORD_BANK_ALL_PLAYLIST_TITLE
                    })
                else:
                    result = add_video_to_playlist(
                        youtube,
                        WORD_BANK_ALL_PLAYLIST_ID,
                        video_id
                    )
                    word_bank_existing_video_ids.add(video_id)

                    report["added_to_word_bank_all"].append({
                        **result,
                        "title": video["title"],
                        "playlist_title": WORD_BANK_ALL_PLAYLIST_TITLE
                    })

            processed_playlists += 1
            save_json(REPORT_OUTPUT, report)

        except HttpError as ex:
            report["errors"].append({
                "playlist_title": playlist_title,
                "error": str(ex)
            })

            if is_rate_limit_error(ex):
                report["stopped_reason"] = "YouTube rate limit/quota reached"
                print("Rate limit/quota detectado. Encerrando execução com report parcial.")
                break

            save_json(REPORT_OUTPUT, report)

        except Exception as ex:
            report["errors"].append({
                "playlist_title": playlist_title,
                "error": str(ex)
            })
            save_json(REPORT_OUTPUT, report)

    report["finished_at"] = datetime.now().isoformat()
    save_json(REPORT_OUTPUT, report)

    return report

def prompt_manual_playlist_creation(plan):
    print("")
    choice = input("Deseja criar playlists manualmente? (s/n): ").strip().lower()

    if choice != "s":
        return

    print("")
    print("=== PLAYLISTS A SEREM CRIADAS ===")

    for idx, playlist in enumerate(plan["playlists"], start=1):
        print(f"{idx}. {playlist['playlist_title']}")
        print(f"   Data: {playlist['upload_date_br']}")
        print(f"   Duração: {playlist['total_duration_label']}")
        print(f"   Vídeos: {playlist['total_videos']}")
        print("")

    print("Crie as playlists manualmente no YouTube.")
    input("Pressione ENTER para continuar...")

# ======================================================
# MAIN
# ======================================================

def main():
    print("Lendo JSON de inventário...")
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        inventory = json.load(f)

    print("Gerando plano de playlists...")

    plan = build_plan(inventory)
    save_json(PLAN_OUTPUT, plan)

    prompt_manual_playlist_creation(plan)

    print(f"Plano gerado: {PLAN_OUTPUT}")
    print(f"Playlists a processar: {plan['total_playlists_to_process']}")
    print(f"Vídeos a processar: {plan['total_videos_to_process']}")
    print(f"Máximo de playlists por execução: {MAX_PLAYLISTS_PER_RUN}")

    if plan["total_videos_to_process"] == 0:
        print("Nenhum vídeo sem playlist encontrado.")
        return

    print("Autenticando no YouTube...")
    youtube = get_youtube_client()

    print("Executando plano...")
    report = execute_plan(youtube, plan)

    print("")
    print("Execução finalizada.")
    print(f"Report gerado: {REPORT_OUTPUT}")
    print(f"Playlists criadas: {len(report['created_playlists'])}")
    print(f"Playlists existentes usadas: {len(report['used_existing_playlists'])}")
    print(f"Adicionados em playlists por data: {len(report['added_to_date_playlists'])}")
    print(f"Adicionados em Word Bank - ALL: {len(report['added_to_word_bank_all'])}")
    print(f"Duplicados ignorados em playlists por data: {len(report['skipped_date_playlist_duplicates'])}")
    print(f"Duplicados ignorados em Word Bank - ALL: {len(report['skipped_word_bank_all_duplicates'])}")
    print(f"Erros: {len(report['errors'])}")
    print(f"Motivo de parada: {report['stopped_reason']}")


if __name__ == "__main__":
    main()