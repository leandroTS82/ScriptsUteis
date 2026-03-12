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

VIDEO_FILE = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - VideosBaixados\HowToWinFriends\HowToWinFriends.mp4"

GLOBAL_VIDEO_NAME = ""

# 🔹 NOVA FLAG
# False → {nome_do_arquivo}_slicedFiles
# True  → 00slicedFiles (pasta compartilhada)
USE_SHARED_00_SLICED_FOLDER = False

SEGMENTS = [
    {"start": "00:00", "end": "04:31", "name": "01_Preface_And_Revision"},
    {"start": "04:32", "end": "20:45", "name": "02_How_This_Book_Was_Written"},
    {"start": "20:46", "end": "30:50", "name": "03_Nine_Suggestions_For_Study"},
    {"start": "30:51", "end": "01:01:39", "name": "04_Part1_Fundamental_Techniques"},
    {"start": "01:01:40", "end": "01:31:49", "name": "05_Part1_Ch1_Don’t_Criticize"},
    {"start": "01:31:50", "end": "02:05:20", "name": "06_Part1_Ch2_Appreciation_Secret"},
    {"start": "02:05:21", "end": "02:45:10", "name": "07_Part1_Ch3_Arouse_An_Eager_Want"},
    {"start": "02:45:11", "end": "03:15:40", "name": "08_Part2_Ways_To_Make_People_Like_You"},
    {"start": "03:15:41", "end": "03:45:00", "name": "09_Part2_Ch1_Be_Genuinely_Interested"},
    {"start": "03:45:01", "end": "04:10:25", "name": "10_Part2_Ch2_The_Power_Of_A_Smile"},
    {"start": "04:10:26", "end": "04:40:15", "name": "11_Part2_Ch3_Remembering_Names"},
    {"start": "04:40:16", "end": "05:15:50", "name": "12_Part2_Ch4_Be_A_Good_Listener"},
    {"start": "05:15:51", "end": "06:05:30", "name": "13_Part3_Win_People_To_Your_Way_Of_Thinking"},
    {"start": "06:05:31", "end": "06:45:20", "name": "14_Part3_Ch1_Avoid_Arguments"},
    {"start": "06:45:21", "end": "07:30:10", "name": "15_Part4_Be_A_Leader_Change_People"},
    {"start": "07:30:11", "end": "08:15:00", "name": "16_Part4_Ch1_How_To_Criticize_And_Not_Be_Hated"},
    {"start": "08:15:01", "end": "08:43:15", "name": "17_Part6_Seven_Rules_For_Happy_Home"},
    {"start": "08:43:16", "end": "08:47:37", "name": "18_Epilogue_Marriage_Questionnaire"}
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