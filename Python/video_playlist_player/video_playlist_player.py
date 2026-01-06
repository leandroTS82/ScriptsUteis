import os
import json
import random
import subprocess
import time
import argparse
from pathlib import Path

# ======================================================
# CONFIGURAÇÕES
# ======================================================

VLC_PATH = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}

MAPPING_FILE = Path("./video_play_count.json")

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

    # Remove vídeos inexistentes
    mapping = {k: v for k, v in mapping.items() if k in video_names}

    # Adiciona vídeos novos
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

    ordered_playlist = []

    for count in sorted(grouped.keys()):
        group = grouped[count]
        if shuffle:
            random.shuffle(group)
        ordered_playlist.extend(group)

    return ordered_playlist


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

    duration = float(result.stdout.strip())
    return int(duration) + 1


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

    parser.add_argument("--path", required=True, help="Diretório dos vídeos")
    parser.add_argument("--repeat-video", type=int, default=1, help="Repetições por vídeo")
    parser.add_argument("--pause", type=int, default=0, help="Pausa em segundos")
    parser.add_argument("--shuffle", action="store_true", help="Shuffle")
    parser.add_argument("--loop", action="store_true", help="Loop infinito")

    # 🔥 NOVA FLAG
    parser.add_argument(
        "--use-mapping",
        action="store_true",
        help="Habilita controle por JSON e priorização por contador"
    )

    args = parser.parse_args()

    video_path = Path(args.path)

    if not video_path.exists():
        print(f"[ERRO] Caminho não existe: {video_path}")
        return

    videos = get_videos_from_path(video_path)

    if not videos:
        print("[ERRO] Nenhum vídeo encontrado.")
        return

    # ===== MODO COM MAPEAMENTO =====
    if args.use_mapping:
        mapping = load_or_create_mapping(videos)
        print("🗂 Controle por mapeamento ATIVADO")
        print(f"Arquivo: {MAPPING_FILE.resolve()}")
    else:
        mapping = None
        print("▶ Modo simples (sem mapeamento)")

    print(f"🎬 Vídeos encontrados: {len(videos)}")

    while True:
        if args.use_mapping:
            playlist = build_playlist_with_mapping(videos, mapping, args.shuffle)
        else:
            playlist = videos.copy()
            if args.shuffle:
                random.shuffle(playlist)

        for video in playlist:
            duration = get_video_duration_seconds(video)

            for i in range(args.repeat_video):
                if args.use_mapping:
                    print(
                        f"▶ {video.name} "
                        f"({i+1}/{args.repeat_video}) "
                        f"| contador: {mapping[video.name]}"
                    )
                else:
                    print(f"▶ {video.name} ({i+1}/{args.repeat_video})")

                play_video_for_duration(video, duration)

                if args.use_mapping:
                    mapping[video.name] += 1
                    save_mapping(mapping)

                if args.pause > 0:
                    print(f"⏸ Pausa: {args.pause}s")
                    time.sleep(args.pause)

        if not args.loop:
            print("✔ Playlist finalizada.")
            break


if __name__ == "__main__":
    main()
