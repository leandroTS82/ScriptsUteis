import os
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

# ======================================================
# FUNÇÕES
# ======================================================

def get_videos_from_path(path: Path):
    return [
        file for file in path.iterdir()
        if file.is_file() and file.suffix.lower() in VIDEO_EXTENSIONS
    ]


def get_video_duration_seconds(video_path: Path) -> int:
    """
    Obtém duração exata do vídeo em segundos usando ffprobe
    """
    try:
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

    except Exception as e:
        print(f"[ERRO] Falha ao obter duração do vídeo: {video_path.name}")
        raise e


def play_video_for_duration(video_path: Path, duration_seconds: int):
    """
    Executa o VLC e encerra após o tempo exato do vídeo
    """
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

    print(f"⏱ Duração detectada: {duration_seconds}s")
    time.sleep(duration_seconds)

    process.terminate()
    process.wait()


# ======================================================
# MAIN
# ======================================================

def main():
    parser = argparse.ArgumentParser(description="Video Playlist Player")

    parser.add_argument("--path", required=True, help="Diretório dos vídeos")
    parser.add_argument("--repeat-video", type=int, default=1, help="Quantas vezes repetir cada vídeo")
    parser.add_argument("--pause", type=int, default=0, help="Pausa em segundos entre execuções")
    parser.add_argument("--shuffle", action="store_true", help="Reprodução aleatória")
    parser.add_argument("--loop", action="store_true", help="Repetir playlist infinitamente")

    args = parser.parse_args()

    video_path = Path(args.path)

    if not video_path.exists():
        print(f"[ERRO] Caminho não existe: {video_path}")
        return

    videos = get_videos_from_path(video_path)

    if not videos:
        print("[ERRO] Nenhum vídeo encontrado.")
        return

    print(f"🎬 Vídeos encontrados: {len(videos)}")

    while True:
        playlist = videos.copy()

        if args.shuffle:
            random.shuffle(playlist)

        for video in playlist:
            duration = get_video_duration_seconds(video)

            for i in range(args.repeat_video):
                print(f"▶ Reproduzindo: {video.name} ({i+1}/{args.repeat_video})")
                play_video_for_duration(video, duration)

                if args.pause > 0:
                    print(f"⏸ Pausa: {args.pause}s")
                    time.sleep(args.pause)

        if not args.loop:
            print("✔ Playlist finalizada.")
            break


if __name__ == "__main__":
    main()
