"""
============================================================
 Script: video_slicer.py
 Autor: Leandro
 Descrição:
   - Faz slices de um vídeo por intervalos nomeados
   - Aceita MM:SS ou HH:MM:SS
   - Tudo que não for mapeado vira "nao_mapeado"
   - Permite definir um NOME GLOBAL para o vídeo
   - Gera arquivos prontos para uso com video_joiner.py
============================================================

EXEMPLO DE CONFIGURAÇÃO INLINE
------------------------------------------------------------
GLOBAL_VIDEO_NAME = "Batata"

SEGMENTS = [
    {
        "start": "00:00",
        "end": "00:10",
        "name": "introducao"
    },
    {
        "start": "01:10",
        "end": "01:15",
        "name": "xxxx"
    }
]

RESULTADO:
Batata_introducao_00m00s_to_00m10s.mp4
Batata_nao_mapeado_00m10s_to_01m10s.mp4
Batata_xxxx_01m10s_to_01m15s.mp4
Batata_nao_mapeado_01m15s_to_02m00s.mp4
============================================================
"""

import os
import subprocess
import sys

# ============================================================
# CONFIGURAÇÃO INLINE
# ============================================================

USE_INTERNAL_CONFIG = True

VIDEO_PATH = r"C:\dev\scripts\ScriptsUteis\Python\youtube_downloader\downloads"
VIDEO_NAME = "Priscilla Shirer ｜ Keep Your Eyes Fixed on Jesus.mp4"

# 🔹 Nome lógico global do vídeo
GLOBAL_VIDEO_NAME = "Batata"

SEGMENTS = [
    {
        "start": "00:00",
        "end": "00:10",
        "name": "introducao"
    },
    {
        "start": "01:10",
        "end": "01:15",
        "name": "xxxx"
    }
]

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
    video_path = os.path.abspath(video_path)
    if video_path.lower().endswith(".mp4"):
        return video_path
    return os.path.join(video_path, video_name)


def get_video_duration(video_file: str) -> float:
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
# MAIN
# ============================================================

def main():
    if not USE_INTERNAL_CONFIG:
        print("Este script está configurado apenas para uso inline.")
        sys.exit(1)

    video_file = resolve_video_file(VIDEO_PATH, VIDEO_NAME)

    if not os.path.isfile(video_file):
        raise FileNotFoundError(f"Vídeo não encontrado: {video_file}")

    video_duration = get_video_duration(video_file)

    # Converte segmentos nomeados
    segments_seconds = [
        (
            parse_time_to_seconds(s["start"]),
            parse_time_to_seconds(s["end"]),
            s["name"]
        )
        for s in SEGMENTS
    ]

    segments_seconds.sort(key=lambda x: x[0])

    intervals = []
    cursor = 0

    for start, end, name in segments_seconds:
        if start > cursor:
            intervals.append((cursor, start, "nao_mapeado"))

        intervals.append((start, end, name))
        cursor = end

    if cursor < video_duration:
        intervals.append((cursor, video_duration, "nao_mapeado"))

    print("\n==================================================")
    print(" VIDEO SLICER")
    print("==================================================")
    print(f"Arquivo origem.: {video_file}")
    print(f"Nome global....: {GLOBAL_VIDEO_NAME}")
    print(f"Duração........: {video_duration:.2f}s")
    print(f"Partes.........: {len(intervals)}")
    print("==================================================\n")

    for i, (start, end, label) in enumerate(intervals, 1):
        output_name = (
            f"{GLOBAL_VIDEO_NAME}_{label}_"
            f"{int(start//60):02d}m{int(start%60):02d}s"
            f"_to_{int(end//60):02d}m{int(end%60):02d}s.mp4"
        )

        print(f"[{i}] Gerando: {output_name}")
        run_ffmpeg(video_file, start, end - start, output_name)

    print("\nProcesso finalizado com sucesso.")


if __name__ == "__main__":
    main()
