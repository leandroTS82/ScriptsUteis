"""
============================================================
 Script: video_slicer.py
 Autor: Leandro
 Descrição:
   - Faz slices de um vídeo por offset de tempo
   - Aceita MM:SS ou HH:MM:SS
   - 1 tempo → 2 vídeos (antes/depois)
   - CLI ou variáveis internas
============================================================
"""

import os
import subprocess
import argparse
import sys


# ============================================================
# CONFIGURAÇÃO FIXA (USO SEM CLI)
# ============================================================
USE_INTERNAL_CONFIG = True

# Pode ser PASTA ou CAMINHO COMPLETO DO VÍDEO
VIDEO_PATH = r"C:\dev\scripts\ScriptsUteis\Python\youtube_downloader\downloads"
VIDEO_NAME = "Priscilla Shirer ｜ Keep Your Eyes Fixed on Jesus.mp4"

TIMES = [
    "00:00",
    "00:33",
    "03:02",
    "05:02",
    "07:02",
    "09:02",
    "11:02",
    "13:02",
    "15:02",
    "17:02",
    "19:02",
    "21:02",
    "23:02",
    "25:02",
    "27:02",
    "29:02",
    "31:02",
    "33:02",
    "35:59"
]

# Se ffmpeg/ffprobe não estiver no PATH, informe aqui:
FFMPEG_BIN = "ffmpeg"
FFPROBE_BIN = "ffprobe"


# ============================================================
# HELPERS
# ============================================================

def parse_time_to_seconds(value: str) -> int:
    parts = value.split(":")
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60 + int(s)
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + int(s)
    raise ValueError(f"Formato inválido: {value}")


def resolve_video_file(video_path: str, video_name: str) -> str:
    """
    Aceita:
    - video_path como pasta + video_name
    - video_path como caminho completo do vídeo
    """
    video_path = os.path.abspath(video_path)

    if video_path.lower().endswith(".mp4"):
        return video_path

    return os.path.join(video_path, video_name)


def get_video_duration(video_file: str) -> float:
    try:
        cmd = [
            FFPROBE_BIN,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_file
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

        return float(result.stdout.strip())

    except FileNotFoundError:
        raise RuntimeError(
            "ffprobe não encontrado. Verifique se o FFmpeg está instalado "
            "e se ffprobe está no PATH, ou configure FFPROBE_BIN."
        )


def run_ffmpeg(input_video: str, start: float, duration: float, output_file: str):
    cmd = [
        FFMPEG_BIN,
        "-y",
        "-ss", str(start),
        "-i", input_video,
        "-t", str(duration),
        "-c", "copy",
        output_file
    ]

    subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        check=True
    )


# ============================================================
# CLI
# ============================================================

def parse_cli():
    parser = argparse.ArgumentParser(description="Video slicer por offset")
    parser.add_argument("--video-path")
    parser.add_argument("--video-name")
    parser.add_argument("--times")
    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================

def main():
    args = parse_cli()

    if args.video_path and args.video_name and args.times:
        video_path = args.video_path
        video_name = args.video_name
        times_raw = [t.strip() for t in args.times.split(",")]
        mode = "CLI"
    else:
        if not USE_INTERNAL_CONFIG:
            print("Erro: parâmetros CLI ausentes.")
            sys.exit(1)

        video_path = VIDEO_PATH
        video_name = VIDEO_NAME
        times_raw = TIMES
        mode = "INTERNAL CONFIG"

    video_file = resolve_video_file(video_path, video_name)

    if not os.path.isfile(video_file):
        raise FileNotFoundError(f"Vídeo não encontrado: {video_file}")

    times_seconds = sorted(parse_time_to_seconds(t) for t in times_raw)
    video_duration = get_video_duration(video_file)

    intervals = []

    if len(times_seconds) == 1:
        cut = times_seconds[0]
        intervals = [(0, cut), (cut, video_duration)]
    else:
        for i in range(len(times_seconds) - 1):
            intervals.append((times_seconds[i], times_seconds[i + 1]))

    intervals = [(s, e) for s, e in intervals if e > s]

    base_name, ext = os.path.splitext(os.path.basename(video_file))

    print("\n==================================================")
    print(" VIDEO SLICER")
    print("==================================================")
    print(f"Modo........: {mode}")
    print(f"Arquivo.....: {video_file}")
    print(f"Duração.....: {video_duration:.2f}s")
    print(f"Vídeos......: {len(intervals)}")
    print("Destino.....: ./")
    print("==================================================\n")

    for i, (start, end) in enumerate(intervals, 1):
        output_name = (
            f"{base_name}_{int(start//60):02d}m{int(start%60):02d}s"
            f"_to_{int(end//60):02d}m{int(end%60):02d}s{ext}"
        )

        print(f"[{i}] Gerando: {output_name}")

        run_ffmpeg(video_file, start, end - start, output_name)

    print("\nProcesso finalizado com sucesso.")


if __name__ == "__main__":
    main()
