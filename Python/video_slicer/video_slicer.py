"""
============================================================
 Script: video_slicer.py
 Autor: Leandro
 Descrição:
   - Faz slices de um vídeo por offset de tempo
   - Formatos aceitos:
       * MM:SS
       * HH:MM:SS
   - 1 tempo:
       * meio → 2 vídeos
       * início ou fim → 1 vídeo
   - N tempos → slices consecutivos
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

VIDEO_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\Communication site - ReunioesGravadas"
VIDEO_NAME = "2026-01-14_09-29-51.mp4"

# Offsets do vídeo (MM:SS ou HH:MM:SS)
TIMES = [
    "00:00",
    "01:03",
    "02:05",
    "03:13",
    "03:27"
]


# ============================================================
# HELPERS
# ============================================================

def parse_time_to_seconds(value: str) -> int:
    parts = value.split(":")

    if len(parts) == 2:  # MM:SS
        m, s = parts
        return int(m) * 60 + int(s)

    if len(parts) == 3:  # HH:MM:SS
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + int(s)

    raise ValueError(f"Formato inválido: {value}. Use MM:SS ou HH:MM:SS")


def get_video_duration(video_file: str) -> int:
    cmd = [
        "ffprobe",
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

    return int(float(result.stdout.strip()))


def run_ffmpeg(input_video: str, start: int, duration: int, output_file: str):
    cmd = [
        "ffmpeg",
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
    parser.add_argument("--times", help="Offsets MM:SS ou HH:MM:SS separados por vírgula")

    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================

def main():
    args = parse_cli()

    # --------------------------------------------
    # CLI vs CONFIG
    # --------------------------------------------
    if args.video_path and args.video_name and args.times:
        video_path = args.video_path
        video_name = args.video_name
        times_raw = [t.strip() for t in args.times.split(",")]
        mode = "CLI"
    else:
        if not USE_INTERNAL_CONFIG:
            print("Erro: parâmetros CLI ausentes e USE_INTERNAL_CONFIG = False")
            sys.exit(1)

        video_path = VIDEO_PATH
        video_name = VIDEO_NAME
        times_raw = TIMES
        mode = "INTERNAL CONFIG"

    if not times_raw:
        raise ValueError("Informe pelo menos um tempo de corte.")

    video_file = os.path.join(os.path.abspath(video_path), video_name)

    if not os.path.isfile(video_file):
        raise FileNotFoundError(f"Vídeo não encontrado: {video_file}")

    times_seconds = sorted(parse_time_to_seconds(t) for t in times_raw)
    video_duration = get_video_duration(video_file)

    # --------------------------------------------
    # GERAR INTERVALOS (ROBUSTO)
    # --------------------------------------------
    intervals = []

    if len(times_seconds) == 1:
        cut = times_seconds[0]

        if cut > video_duration:
            raise ValueError(
                f"Corte {cut}s maior que duração do vídeo ({video_duration}s)"
            )

        candidates = [
            (0, cut),
            (cut, video_duration)
        ]

        intervals = [(s, e) for s, e in candidates if e > s]

    else:
        for i in range(len(times_seconds) - 1):
            s, e = times_seconds[i], times_seconds[i + 1]
            if e > s:
                intervals.append((s, e))

    if not intervals:
        print("Nenhum intervalo válido para gerar vídeos.")
        return

    base_name, ext = os.path.splitext(video_name)

    # --------------------------------------------
    # PROCESSAMENTO
    # --------------------------------------------
    print("\n==================================================")
    print(" VIDEO SLICER")
    print("==================================================")
    print(f"Modo........: {mode}")
    print(f"Arquivo.....: {video_file}")
    print(f"Duração.....: {video_duration}s")
    print(f"Vídeos......: {len(intervals)}")
    print("Destino.....: ./")
    print("==================================================\n")

    for idx, (start, end) in enumerate(intervals, start=1):
        duration = end - start

        start_label = f"{start//60:02d}m{start%60:02d}s"
        end_label = f"{end//60:02d}m{end%60:02d}s"

        output_name = f"{base_name}_{start_label}_to_{end_label}{ext}"

        print(f"[{idx}] Gerando: {output_name}")

        run_ffmpeg(video_file, start, duration, output_name)

    print("\nProcesso finalizado com sucesso.")


if __name__ == "__main__":
    main()
