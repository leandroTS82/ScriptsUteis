import os
import json
import random
import subprocess
import time
import argparse
from pathlib import Path
from datetime import datetime

# ======================================================
# CONFIGURAÇÕES
# ======================================================

VLC_PATH = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}

MAPPING_FILE = Path("./video_play_count.json")
SUBSET_FILE = Path("./selected_videos.json")

# ======================================================
# FUNÇÕES
# ======================================================

def get_videos_from_path(path: Path):
    return [
        file for file in path.iterdir()
        if file.is_file() and file.suffix.lower() in VIDEO_EXTENSIONS
    ]


# ---------------- MAPEAMENTO ----------------

def load_or_create_mapping(videos):
    if MAPPING_FILE.exists():
        with open(MAPPING_FILE, "r", encoding="utf-8") as f:
            mapping = json.load(f)
    else:
        mapping = {}

    video_names = {v.name for v in videos}

    mapping = {k: v for k, v in mapping.items() if k in video_names}

    for video in videos:
        if video.name not in mapping:
            mapping[video.name] = 0

    save_mapping(mapping)
    return mapping


def save_mapping(mapping):
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)


def build_playlist_with_mapping(videos, mapping, shuffle: bool):
    grouped = {}

    for video in videos:
        count = mapping.get(video.name, 0)
        grouped.setdefault(count, []).append(video)

    ordered = []
    for count in sorted(grouped.keys()):
        group = grouped[count]
        if shuffle:
            random.shuffle(group)
        ordered.extend(group)

    return ordered


# ---------------- SUBSET ----------------

def build_random_subset(videos, mapping, subset_max: int, shuffle: bool):
    ordered = build_playlist_with_mapping(videos, mapping, shuffle)
    max_allowed = min(len(ordered), subset_max)

    subset_size = random.randint(1, max_allowed)
    selected = ordered[:subset_size]

    save_subset(selected)
    return selected


def save_subset(videos):
    data = {
        "generated_at": datetime.now().isoformat(),
        "total_selected": len(videos),
        "videos": [v.name for v in videos]
    }

    with open(SUBSET_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------- VÍDEO ----------------

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

    print(f"⏱ Duração: {duration_seconds}s")
    time.sleep(duration_seconds)

    process.terminate()
    process.wait()


# ======================================================
# MAIN
# ======================================================

def main():
    parser = argparse.ArgumentParser(description="Video Playlist Player")

    parser.add_argument("--path", required=True)
    parser.add_argument("--repeat-video", type=int, default=1)
    parser.add_argument("--pause", type=int, default=0)
    parser.add_argument("--shuffle", action="store_true")
    parser.add_argument("--loop", action="store_true")

    parser.add_argument("--use-mapping", action="store_true")
    parser.add_argument("--use-random-subset", action="store_true")
    parser.add_argument("--subset-max", type=int, default=5)

    args = parser.parse_args()

    video_path = Path(args.path)
    if not video_path.exists():
        print("[ERRO] Caminho inválido.")
        return

    videos = get_videos_from_path(video_path)
    if not videos:
        print("[ERRO] Nenhum vídeo encontrado.")
        return

    mapping = None
    if args.use_mapping:
        mapping = load_or_create_mapping(videos)
        print("🗂 use-mapping ATIVADO")

    print(f"🎬 Total vídeos encontrados: {len(videos)}")

    subset_playlist = None

    # 🔒 GERA O SUBSET UMA ÚNICA VEZ
    if args.use_random_subset:
        if not args.use_mapping:
            print("[ERRO] random-subset requer --use-mapping")
            return

        subset_playlist = build_random_subset(
            videos,
            mapping,
            args.subset_max,
            args.shuffle
        )

        print(f"🎯 Subset FIXADO ({len(subset_playlist)} vídeos)")
        print(f"Arquivo: {SUBSET_FILE.resolve()}")

    while True:
        if subset_playlist is not None:
            playlist = subset_playlist
        else:
            if args.use_mapping:
                playlist = build_playlist_with_mapping(videos, mapping, args.shuffle)
            else:
                playlist = videos.copy()
                if args.shuffle:
                    random.shuffle(playlist)

        for video in playlist:
            duration = get_video_duration_seconds(video)

            for i in range(args.repeat_video):
                print(f"▶ {video.name} ({i+1}/{args.repeat_video})")
                play_video_for_duration(video, duration)

                if args.use_mapping:
                    mapping[video.name] += 1
                    save_mapping(mapping)

                if args.pause > 0:
                    time.sleep(args.pause)

        if not args.loop:
            break


if __name__ == "__main__":
    main()
