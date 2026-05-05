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
from youtube_auth import get_youtube_client
from googleapiclient.errors import HttpError


# ── CONFIG ────────────────────────────────────────────────────────────────────
PLAYLIST_PRIVACY_STATUS = "public"
SLEEP_SECONDS           = 1.5   # pausa entre inserções para respeitar rate limit
DRY_RUN                 = False  # True = simula sem chamar API de escrita
inventory_file = r"C:\dev\scripts\ScriptsUteis\Python\ContentFabric\5youtube-upload\classified_playlist\output\youtube_uploaded_inventory.json"


def _get_all_playlists_from_inventory(inventory_file: str) -> dict:
    """
    Retorna playlists a partir do inventory local.

    Formato:
    title.lower() → {playlist_id, playlist_title}
    """

    with open(inventory_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    playlists_map = {}

    for video in data.get("videos", []):
        for pl in video.get("playlists", []):
            title = pl.get("playlist_title")
            pid = pl.get("playlist_id")

            if title and pid:
                playlists_map[title.lower()] = {
                    "playlist_id": pid,
                    "playlist_title": title
                }

    return playlists_map

def _create_playlist(youtube, name: str, intention: str) -> str:
    resp = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": name,
                "description": f"Playlist automática - Intenção: {intention}"
            },
            "status": {"privacyStatus": PLAYLIST_PRIVACY_STATUS}
        }
    ).execute()

    time.sleep(3)
    return resp["id"]

def _resolve_playlist(
    youtube,
    playlist_id_override: str | None,
    playlist_name: str,
    intention: str,
) -> tuple[str, bool]:
    if playlist_id_override and playlist_id_override.startswith("PL"):
        print(f"  🆔 Usando ID de playlist fornecido: {playlist_id_override}")
        return playlist_id_override, False

    print(f"\n  🔍 Buscando playlist existente: '{playlist_name}'...")
    
    existing = _get_all_playlists_from_inventory(inventory_file)
    
    key = playlist_name.lower()

    if key in existing:
        pid = existing[key]["playlist_id"]
        print(f"  ✅ Playlist encontrada: '{playlist_name}' → {pid}")
        return pid, False

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


# ── ENTRY-POINT (função) ──────────────────────────────────────────────────────

def run(
    classification_file   : str,
    playlist_name_override: str        = "",
    playlist_id_override  : str | None = None,
    output_dir            : str        = "./output",
) -> dict:

    os.makedirs(output_dir, exist_ok=True)

    with open(classification_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    intention     = data.get("intention", "")
    playlist_name = playlist_name_override or data.get("target_playlist", "Auto Playlist")
    videos        = data.get("videos", [])

    # deduplica pelo youtube_video_id (Groq às vezes repete)
    seen, unique = set(), []

    for v in videos:
        vid = v.get("youtube_video_id")
        if vid and vid.lower() not in ("none", "") and vid not in seen:
            seen.add(vid)
            unique.append(v)

    progress_file = os.path.join(output_dir, "playlist_progress.json")
    processed_ids = set()

    if os.path.exists(progress_file):
        with open(progress_file, "r", encoding="utf-8") as f:
            processed_ids = set(json.load(f))

    # filtra apenas os que ainda não foram processados
    videos = [
        v for v in unique
        if v["youtube_video_id"] not in processed_ids
    ]

    print(f"\n  🎬 Vídeos a inserir (únicos): {len(videos)}")
    print(f"  🎯 Intenção                 : {intention}")
    print(f"  📋 Playlist alvo            : {playlist_name}")

    print("\n  🔐 Autenticando na YouTube API...")
    youtube = get_youtube_client()
    print("  ✅ Autenticado.")

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

    # quando o ID foi passado direto ou a playlist acabou de ser criada,
    # pula o prefetch para economizar cota
    skip_prefetch = created or bool(playlist_id_override and playlist_id_override.startswith("PL"))
    existing_ids: set[str] = set()
    if not skip_prefetch:
        print("  🔎 Carregando vídeos já existentes na playlist...")
        existing_ids = _get_existing_video_ids(youtube, playlist_id)
    print(f"  🔎 Vídeos pré-carregados da playlist: {len(existing_ids)}")

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

    print(f"\n  ── Iniciando inserção de {len(videos)} vídeos ──")

    for idx, video in enumerate(videos, 1):
        video_id = video.get("youtube_video_id")
        title    = video.get("youtube_title", "")

        if not video_id or video_id.lower() in ("none", ""):
            print(f"  ⚠️  [{idx:03}] ID inválido, pulando.")
            continue

        if video_id in existing_ids:
            report["skipped_duplicates"].append(video_id)
            print(f"  ⏭️  [{idx:03}] Já existe : {video_id} — {title[:55]}")
            continue

        try:
            item_id = _add_video(youtube, playlist_id, video_id)
            existing_ids.add(video_id)
            report["added"].append({"video_id": video_id, "playlist_item_id": item_id})
            processed_ids.add(video_id)

            with open(progress_file, "w", encoding="utf-8") as f:
                json.dump(list(processed_ids), f)
            print(f"  ✅ [{idx:03}] Adicionado: {video_id} — {title[:55]}")

        except HttpError as ex:
            err_msg = str(ex)

            if "videoAlreadyInPlaylist" in err_msg or "duplicate" in err_msg.lower():
                report["skipped_duplicates"].append(video_id)
                existing_ids.add(video_id)
                print(f"  ⏭️  [{idx:03}] Já existe : {video_id} — {title[:55]}")
                continue

            if "quota" in err_msg.lower():
                print(f"  ⛔ Quota excedida no vídeo {idx}. Interrompendo.")
                report["errors"].append({"video_id": video_id, "error": err_msg})
                break

            report["errors"].append({"video_id": video_id, "error": err_msg})
            print(f"  ❌ [{idx:03}] Erro      : {video_id} — {err_msg[:70]}")

    report["finished_at"] = datetime.now().isoformat()

    report_file = os.path.join(
        output_dir,
        f"youtube_playlist_execution_{datetime.now():%Y%m%d_%H%M%S}.json",
    )

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)

    print(f"\n  ─────────────────────────────────────────")
    print(f"  Adicionados  : {len(report['added'])}")
    print(f"  Duplicatas   : {len(report['skipped_duplicates'])}")
    print(f"  Erros        : {len(report['errors'])}")
    print(f"  Relatório    : {report_file}")

    return report


# ── EXECUÇÃO DIRETA ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Uso direto (sem main.py):

      # usando ID da playlist:
      python step_03_execute.py --playlist-id PLzVI0b1epy9-4p7u_t81HsKVhylxbrsRg

      # usando nome da playlist:
      python step_03_execute.py --playlist-name "Past Simple"

      # tudo customizado:
      python step_03_execute.py \
        --classification .\output\youtube_playlist_classification.json \
        --playlist-id PLzVI0b1epy9-4p7u_t81HsKVhylxbrsRg \
        --output-dir .\output
    """
    import argparse

    parser = argparse.ArgumentParser(description="Insere vídeos classificados em uma playlist do YouTube.")
    parser.add_argument(
        "--classification",
        default=r".\output\youtube_playlist_classification.json",
        help="Caminho para youtube_playlist_classification.json",
    )
    parser.add_argument(
        "--playlist-id",
        default="",
        help="ID direto da playlist (ex: PLzVI0b1epy9-...)",
    )
    parser.add_argument(
        "--playlist-name",
        default="",
        help="Nome da playlist (busca ou cria se não existir)",
    )
    parser.add_argument(
        "--output-dir",
        default=r".\output",
        help="Diretório para salvar o relatório de execução",
    )
    args = parser.parse_args()

    run(
        classification_file   = args.classification,
        playlist_id_override  = args.playlist_id or None,
        playlist_name_override= args.playlist_name,
        output_dir            = args.output_dir,
    )