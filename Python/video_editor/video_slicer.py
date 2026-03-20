"""
============================================================
 Script: video_slicer.py
 Autor: Leandro
 Descrição:
   - Faz slices de um vídeo por intervalos nomeados
   - Aceita MM:SS ou HH:MM:SS
   - Apenas os mapeados são mantidos
   - Não mapeados são excluídos
============================================================
"""

import os
import subprocess
import sys

# ============================================================
# CONFIGURAÇÃO INLINE
# ============================================================

USE_INTERNAL_CONFIG = True

VIDEO_FILE = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\Communication site - ReunioesGravadas\2026-03-20_10-04-38.mp4"

GLOBAL_VIDEO_NAME = ""

# 🔹 NOVA FLAG
# False → {nome_do_arquivo}_slicedFiles
# True  → 00slicedFiles (pasta compartilhada)
USE_SHARED_00_SLICED_FOLDER = False

SEGMENTS = [
    {"start": "00:00:00", "end": "00:05:00", "name": "01"},
    {"start": "00:05:01", "end": "00:10:00", "name": "02"},
    {"start": "00:10:01", "end": "00:15:00", "name": "03"},
    {"start": "00:15:01", "end": "00:20:00", "name": "04"},
    {"start": "00:20:01", "end": "00:25:00", "name": "05"},
    {"start": "00:25:01", "end": "00:30:00", "name": "06"},
    {"start": "00:30:01", "end": "00:35:00", "name": "07"},
    {"start": "00:35:01", "end": "00:39:00", "name": "08"},
    {"start": "00:40:01", "end": "00:45:00", "name": "09"},
    {"start": "00:45:01", "end": "00:50:00", "name": "10"},
    {"start": "00:50:01", "end": "00:55:00", "name": "11"},
    {"start": "00:55:01", "end": "01:00:00", "name": "12"},
    {"start": "01:00:01", "end": "01:05:00", "name": "13"},
    {"start": "01:05:01", "end": "01:10:00", "name": "14"},
    {"start": "01:10:01", "end": "01:15:00", "name": "15"},
    {"start": "01:15:01", "end": "01:20:00", "name": "16"},
    {"start": "01:20:01", "end": "01:25:00", "name": "17"},
    {"start": "01:25:01", "end": "01:30:00", "name": "18"},
    {"start": "01:30:01", "end": "01:35:00", "name": "19"},
    {"start": "01:35:01", "end": "01:40:00", "name": "20"},
    {"start": "01:40:01", "end": "01:45:00", "name": "21"},
    {"start": "01:45:01", "end": "01:50:00", "name": "22"},
    {"start": "01:50:01", "end": "01:55:00", "name": "23"},
    {"start": "01:55:01", "end": "02:00:00", "name": "24"},
    {"start": "02:00:01", "end": "02:05:00", "name": "25"},
    {"start": "02:05:01", "end": "02:10:00", "name": "26"},
    {"start": "02:10:01", "end": "02:15:00", "name": "27"},
    {"start": "02:15:01", "end": "02:20:00", "name": "28"},
    {"start": "02:20:01", "end": "02:25:00", "name": "29"},
    {"start": "02:25:01", "end": "02:30:00", "name": "30"},
    {"start": "02:30:01", "end": "02:35:00", "name": "31"},
    {"start": "02:35:01", "end": "02:40:00", "name": "32"},
    {"start": "02:40:01", "end": "02:45:00", "name": "33"},
    {"start": "02:45:01", "end": "02:50:00", "name": "34"},
    {"start": "02:50:01", "end": "02:55:00", "name": "35"},
    {"start": "02:55:01", "end": "03:00:00", "name": "36"},
    {"start": "03:00:01", "end": "03:05:00", "name": "37"},
    {"start": "03:05:01", "end": "03:10:00", "name": "38"},
    {"start": "03:10:01", "end": "03:15:00", "name": "39"},
    {"start": "03:15:01", "end": "03:20:00", "name": "40"},
    {"start": "03:20:01", "end": "03:25:00", "name": "41"},
    {"start": "03:25:01", "end": "03:30:00", "name": "42"},
    {"start": "03:30:01", "end": "03:35:00", "name": "43"},
    {"start": "03:35:01", "end": "03:40:00", "name": "44"},
    {"start": "03:40:01", "end": "03:45:00", "name": "45"},
    {"start": "03:45:01", "end": "03:50:00", "name": "46"},
    {"start": "03:50:01", "end": "03:55:00", "name": "47"}
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

    print("FFMPEG CMD:", " ".join(cmd))

    subprocess.run(
        cmd,
        check=True
    )

    # 🔎 Verificação de segurança
    if not os.path.exists(output_file):
        raise RuntimeError(f"FFmpeg não gerou o arquivo esperado: {output_file}")

# ============================================================
# MAIN
# ============================================================

def main():
    if not USE_INTERNAL_CONFIG:
        print("Este script está configurado apenas para uso inline.")
        sys.exit(1)

    video_file = os.path.abspath(VIDEO_FILE)

    if not os.path.isfile(video_file):
        raise FileNotFoundError(f"Vídeo não encontrado: {video_file}")

    video_duration = get_video_duration(video_file)

    base_dir = os.path.dirname(video_file)
    base_name = os.path.splitext(os.path.basename(video_file))[0]

    # ========================================================
    # REGRA DA PASTA
    # ========================================================

    if USE_SHARED_00_SLICED_FOLDER:
        output_dir = base_dir
    else:
        output_dir = os.path.join(base_dir, f"{base_name}_slicedFiles")
        os.makedirs(output_dir, exist_ok=True)

    # ========================================================

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
    print(" VIDEO SLICER (MAPPED ONLY)")
    print("==================================================")
    print(f"Arquivo origem.: {video_file}")
    print(f"Duração........: {video_duration:.2f}s")
    print(f"Pasta destino..: {output_dir}")
    print("==================================================\n")

    for i, (start, end, label) in enumerate(intervals, 1):

        # 🔹 Evita underscore inicial se GLOBAL_VIDEO_NAME estiver vazio
        if GLOBAL_VIDEO_NAME:
            prefix = f"{GLOBAL_VIDEO_NAME}_"
        else:
            prefix = ""

        output_name = (
            f"{prefix}{label}_"
            f"{int(start//60):02d}m{int(start%60):02d}s"
            f"_to_{int(end//60):02d}m{int(end%60):02d}s.mp4"
        )

        temp_output_path = os.path.join(base_dir, output_name)

        print(f"[{i}] Gerando: {output_name}")
        run_ffmpeg(video_file, start, end - start, temp_output_path)

        if label != "nao_mapeado":
            final_path = os.path.join(output_dir, output_name)
            os.replace(temp_output_path, final_path)
            print("    ✔ Movido para pasta de slices")
        else:
            os.remove(temp_output_path)
            print("    ✖ Não mapeado removido")

    print("\nProcesso finalizado com sucesso.")
    print("Apenas os trechos mapeados foram mantidos.")


if __name__ == "__main__":
    main()