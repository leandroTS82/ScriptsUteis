"""
step_03_execute.py

Responsabilidades:
  1. Autenticar na YouTube Data API via OAuth
  2. Resolver a playlist (ID direto | busca por nome | criação)
  3. Adicionar os vídeos classificados, pulando duplicatas
  4. Gerar relatório de execução
"""

import os
import json
import time
from datetime import datetime

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

# ── CONFIG ────────────────────────────────────────────────────────────────────

TOKEN_PATH = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS"
    r"\EKF - English Knowledge Framework - Base"
    r"\FilesHelper\secret_tokens_keys\youtube_token.json"
)

CLIENT_SECRET_FILE = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS"
    r"\EKF - English Knowledge Framework - Base"
    r"\FilesHelper\secret_tokens_keys\youtube-upload-desktop.json"
)

SCOPES = ["https://www.googleapis.com/auth/youtube"]

PLAYLIST_PRIVACY_STATUS = "public"
SLEEP_SECONDS           = 1.5   # pausa entre inserções para respeitar rate limit
DRY_RUN                 = False  # True = simula sem chamar API de escrita

# ── AUTH ──────────────────────────────────────────────────────────────────────

def _get_authenticated_service():
    creds = None

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "r", encoding="utf-8") as f:
            creds = Credentials.from_authorized_user_info(json.load(f), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow  = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)

        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


# ── YOUTUBE HELPERS ───────────────────────────────────────────────────────────

def _get_all_playlists(youtube) -> dict:
    """Retorna dict: title.lower() → {playlist_id, playlist_title}"""
    playlists  = {}
    page_token = None

    while True:
        resp = youtube.playlists().list(
            part="snippet",
            mine=True,
            maxResults=50,
            pageToken=page_token,
        ).execute()

        for item in resp.get("items", []):
            title = item["snippet"]["title"]
            playlists[title.lower()] = {
                "playlist_id"   : item["id"],
                "playlist_title": title,
            }

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return playlists


def _create_playlist(youtube, name: str, intention: str) -> str:
    if DRY_RUN:
        fake_id = f"DRY_RUN_{name.replace(' ', '_')}"
        print(f"  [DRY RUN] Criaria playlist: '{name}' → {fake_id}")
        return fake_id

    resp = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title"      : name,
                "description": (
                    f"Playlist automática criada pelo pipeline classified_playlist.\n"
                    f"Intenção: {intention}"
                ),
            },
            "status": {"privacyStatus": PLAYLIST_PRIVACY_STATUS},
        },
    ).execute()

    playlist_id = resp["id"]
    print(f"  ✅ Playlist criada: '{name}' → {playlist_id}")
    time.sleep(5)  # aguarda propagação da API
    return playlist_id


def _resolve_playlist(
    youtube,
    playlist_id_override: str | None,
    playlist_name: str,
    intention: str,
) -> tuple[str, bool]:
    """
    Retorna (playlist_id, foi_criada).

    Lógica:
      1. Se playlist_id_override começa com 'PL' → usa diretamente
      2. Busca por nome nos playlists existentes
      3. Se não encontrar → cria com o nome gerado
    """

    # ── 1. ID explícito ────────────────────────────────────────────────────────
    if playlist_id_override and playlist_id_override.startswith("PL"):
        print(f"  🆔 Usando ID de playlist fornecido: {playlist_id_override}")
        return playlist_id_override, False

    # ── 2. Busca por nome ──────────────────────────────────────────────────────
    print(f"\n  🔍 Buscando playlist existente: '{playlist_name}'...")
    existing = _get_all_playlists(youtube)
    key = playlist_name.lower()

    if key in existing:
        pid = existing[key]["playlist_id"]
        print(f"  ✅ Playlist encontrada: '{playlist_name}' → {pid}")
        return pid, False

    # ── 3. Criar ───────────────────────────────────────────────────────────────
    print(f"  📝 Playlist não encontrada. Criando: '{playlist_name}'...")
    pid = _create_playlist(youtube, playlist_name, intention)
    return pid, True


def _get_existing_video_ids(youtube, playlist_id: str) -> set[str]:
    ids        = set()
    page_token = None

    while True:
        resp = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=page_token,
        ).execute()

        for item in resp.get("items", []):
            ids.add(item["contentDetails"]["videoId"])

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return ids


def _add_video(youtube, playlist_id: str, video_id: str) -> str:
    if DRY_RUN:
        return "dry_run_item_id"

    resp = youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind"   : "youtube#video",
                    "videoId": video_id,
                },
            }
        },
    ).execute()

    time.sleep(SLEEP_SECONDS)
    return resp.get("id", "")


# ── ENTRY-POINT ───────────────────────────────────────────────────────────────

def run(
    classification_file: str,
    playlist_name_override: str  = "",
    playlist_id_override  : str | None = None,
    output_dir            : str  = "./output",
) -> dict:
    """
    Executa a inserção dos vídeos classificados na playlist do YouTube.

    Args:
        classification_file:    caminho para youtube_playlist_classification.json
        playlist_name_override: nome final da playlist (já resolvido pelo step 02)
        playlist_id_override:   ID da playlist (se o usuário informou direto)
        output_dir:             onde salvar o relatório

    Returns:
        dict com relatório de execução
    """
    os.makedirs(output_dir, exist_ok=True)

    with open(classification_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    intention    = data.get("intention", "")
    playlist_name = playlist_name_override or data.get("target_playlist", "Auto Playlist")
    videos        = data.get("videos", [])

    print(f"\n  🎬 Vídeos a inserir: {len(videos)}")
    print(f"  🎯 Intenção       : {intention}")
    print(f"  📋 Playlist alvo  : {playlist_name}")

    # ── autenticar ────────────────────────────────────────────────────────────
    print("\n  🔐 Autenticando na YouTube API...")
    youtube = _get_authenticated_service()

    # ── resolver playlist ─────────────────────────────────────────────────────
    try:
        playlist_id, created = _resolve_playlist(
            youtube,
            playlist_id_override=playlist_id_override,
            playlist_name=playlist_name,
            intention=intention,
        )
    except HttpError as ex:
        if "quota" in str(ex).lower():
            print("  ❌ Quota da YouTube API excedida. Tente novamente amanhã.")
            raise
        raise

    # ── vídeos já existentes (pular duplicatas) ────────────────────────────────
    existing_ids: set[str] = set() if created else _get_existing_video_ids(youtube, playlist_id)
    print(f"\n  🔎 Vídeos já na playlist: {len(existing_ids)}")

    # ── relatório ─────────────────────────────────────────────────────────────
    report = {
        "started_at"        : datetime.now().isoformat(),
        "intention"         : intention,
        "playlist_id"       : playlist_id,
        "playlist_name"     : playlist_name,
        "created_playlist"  : created,
        "dry_run"           : DRY_RUN,
        "added"             : [],
        "skipped_duplicates": [],
        "errors"            : [],
    }

    # ── inserção ──────────────────────────────────────────────────────────────
    for video in videos:
        video_id = video.get("youtube_video_id")
        title    = video.get("youtube_title", "")

        if not video_id:
            continue

        if video_id in existing_ids:
            report["skipped_duplicates"].append(video_id)
            print(f"  ⏭️  Já existe: {video_id} — {title[:60]}")
            continue

        try:
            item_id = _add_video(youtube, playlist_id, video_id)
            existing_ids.add(video_id)
            report["added"].append({"video_id": video_id, "playlist_item_id": item_id})
            print(f"  ✅ Adicionado: {video_id} — {title[:60]}")

        except HttpError as ex:
            err_msg = str(ex)
            report["errors"].append({"video_id": video_id, "error": err_msg})
            print(f"  ❌ Erro: {video_id} — {err_msg[:80]}")

            if "quota" in err_msg.lower():
                print("  ⛔ Quota excedida. Interrompendo.")
                break

    # ── finalizar relatório ───────────────────────────────────────────────────
    report["finished_at"] = datetime.now().isoformat()

    report_file = os.path.join(
        output_dir,
        f"youtube_playlist_execution_{datetime.now():%Y%m%d_%H%M%S}.json",
    )

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)

    # ── resumo ────────────────────────────────────────────────────────────────
    print(f"\n  ─────────────────────────────────────────")
    print(f"  Adicionados  : {len(report['added'])}")
    print(f"  Duplicatas   : {len(report['skipped_duplicates'])}")
    print(f"  Erros        : {len(report['errors'])}")
    print(f"  Relatório    : {report_file}")

    return report