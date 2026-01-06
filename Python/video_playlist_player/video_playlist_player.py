r"""
🧾 RESUMO FUNCIONAL (PARA USUÁRIOS NÃO TÉCNICOS)
▶ Modo simples (playlist normal)
set USE_MAPPING=false
set USE_RANDOM_SUBSET=false

▶ Modo inteligente (balanceamento automático)
set USE_MAPPING=true
set USE_RANDOM_SUBSET=false

▶ Modo subconjunto inteligente (recomendado)
set USE_MAPPING=true
set USE_RANDOM_SUBSET=true
set SUBSET_MAX=5

▶ Painel / estudo contínuo
set LOOP=true
set PAUSE_SECONDS=30

📁 Arquivos gerados automaticamente
Arquivo	Função
video_play_count.json	Histórico de execuções
selected_videos.json	Subconjunto fixado
Nenhum banco de dados	100% local
"""
import os
import json
import random
import subprocess
import time
import argparse
from pathlib import Path
from datetime import datetime, date

# ======================================================
# CONFIGURAÇÕES
# ======================================================

VLC_PATH = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}

MAPPING_FILE = Path("./video_play_count.json")
SUBSET_FILE = Path("./selected_videos.json")

# ======================================================
# FUNÇÕES AUXILIARES
# ======================================================

def get_videos_from_path(path: Path):
    return [
        file for file in path.iterdir()
        if file.is_file() and file.suffix.lower() in VIDEO_EXTENSIONS
    ]


# ======================================================
# MAPEAMENTO (CONTADORES)
# ======================================================

def load_or_create_mapping(videos):
    if MAPPING_FILE.exists():
        with open(MAPPING_FILE, "r", encoding="utf-8") as f:
            mapping = json.load(f)
    else:
        mapping = {}

    video_names = {v.name for v in videos}

    mapping = {k: v for k, v in mapping.items() if k in video_names}

    for video in videos:
        mapping.setdefault(video.name, 0)

    save_mapping(mapping)
    return mapping


def save_mapping(mapping):
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)


def build_playlist_with_mapping(videos, mapping, shuffle: bool):
    """
    Ordena vídeos priorizando os menos reproduzidos.
    Shuffle ocorre apenas dentro do mesmo contador.
    """
    grouped = {}

    for video in videos:
        grouped.setdefault(mapping.get(video.name, 0), []).append(video)

    playlist = []
    for count in sorted(grouped.keys()):
        group = grouped[count]
        if shuffle:
            random.shuffle(group)
        playlist.extend(group)

    return playlist


# ======================================================
# SUBSET (SELEÇÃO PARCIAL)
# ======================================================

def should_reset_subset_daily():
    if not SUBSET_FILE.exists():
        return False

    with open(SUBSET_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    generated = datetime.fromisoformat(data.get("generated_at"))
    return generated.date() != date.today()


def load_subset(videos):
    with open(SUBSET_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    video_map = {v.name: v for v in videos}
    return [video_map[name] for name in data.get("videos", []) if name in video_map]


def save_subset(videos):
    data = {
        "generated_at": datetime.now().isoformat(),
        "total_selected": len(videos),
        "videos": [v.name for v in videos]
    }

    with open(SUBSET_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def build_random_subset(
    videos,
    mapping,
    subset_max,
    shuffle,
    fixed_size=False
):
    ordered = build_playlist_with_mapping(videos, mapping, shuffle)
    max_allowed = min(len(ordered), subset_max)

    size = subset_max if fixed_size else random.randint(1, max_allowed)
    selected = ordered[:size]

    save_subset(selected)
    return selected


# ======================================================
# VÍDEO
# ======================================================

def get_video_duration_seconds(video_path: Path) -> int:
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    return int(float(result.stdout.strip())) + 1


def play_video_for_duration(video_path: Path, duration_seconds: int):
    process = subprocess.Popen(
        [
            VLC_PATH,
            "--fullscreen",
            "--no-video-title-show",
            str(video_path)
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    time.sleep(duration_seconds)
    process.terminate()
    process.wait()


# ======================================================
# MAIN
# ======================================================

def main():
    parser = argparse.ArgumentParser(description="Video Playlist Player")

    # Básico
    parser.add_argument("--path", required=True)
    parser.add_argument("--repeat-video", type=int, default=1)
    parser.add_argument("--pause", type=int, default=0)
    parser.add_argument("--shuffle", action="store_true")
    parser.add_argument("--loop", action="store_true")

    # Mapping
    parser.add_argument("--use-mapping", action="store_true")

    # Subset
    parser.add_argument("--use-random-subset", action="store_true")
    parser.add_argument("--subset-max", type=int, default=5)

    # 🔒 NOVOS RECURSOS (DESABILITADOS)
    parser.add_argument("--reuse-last-subset", action="store_true")
    parser.add_argument("--subset-fixed-size", action="store_true")
    parser.add_argument("--subset-reset-daily", action="store_true")
    parser.add_argument("--max-total-playtime", type=int, default=0)

    args = parser.parse_args()

    videos = get_videos_from_path(Path(args.path))
    if not videos:
        print("[ERRO] Nenhum vídeo encontrado.")
        return

    mapping = None
    if args.use_mapping:
        mapping = load_or_create_mapping(videos)

    subset_playlist = None
    total_playtime = 0

    # ===== SUBSET INIT =====
    if args.use_random_subset:
        if not args.use_mapping:
            print("[ERRO] random-subset requer --use-mapping")
            return

        reuse_allowed = (
            args.reuse_last_subset and
            SUBSET_FILE.exists() and
            not (args.subset_reset_daily and should_reset_subset_daily())
        )

        if reuse_allowed:
            subset_playlist = load_subset(videos)
        else:
            subset_playlist = build_random_subset(
                videos,
                mapping,
                args.subset_max,
                args.shuffle,
                fixed_size=args.subset_fixed_size
            )

    while True:
        playlist = subset_playlist if subset_playlist else (
            build_playlist_with_mapping(videos, mapping, args.shuffle)
            if args.use_mapping else
            random.sample(videos, len(videos)) if args.shuffle else videos
        )

        for video in playlist:
            duration = get_video_duration_seconds(video)

            if args.max_total_playtime > 0:
                if total_playtime + duration > args.max_total_playtime:
                    print("⏹ Tempo máximo atingido.")
                    return

            for _ in range(args.repeat_video):
                play_video_for_duration(video, duration)
                total_playtime += duration

                if args.use_mapping:
                    mapping[video.name] += 1
                    save_mapping(mapping)

                if args.pause > 0:
                    time.sleep(args.pause)

        if not args.loop:
            break


if __name__ == "__main__":
    main()
