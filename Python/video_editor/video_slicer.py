"""
============================================================
 Script: video_slicer.py
 Autor: Leandro
 Descrição:
   - Faz slices de um vídeo por intervalos nomeados
   - Aceita MM:SS ou HH:MM:SS
   - Apenas os mapeados são mantidos
   - Não mapeados são excluídos

 NOVO: SLICE_DURATION_MINUTES
   - Quando preenchido (> 0), sobrepõe o SEGMENTS manual
   - Divide o vídeo automaticamente em partes iguais
   - Ex: SLICE_DURATION_MINUTES = 5 → partes de 5 minutos
============================================================
"""

import os
import subprocess
import sys
import math

# ============================================================
# CONFIGURAÇÃO INLINE
# ============================================================

USE_INTERNAL_CONFIG = True

VIDEO_FILE = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos\Documentos pessoais\Leandro CV\Entrevistas Testes\(Evertec) - 2026-04-13_16-04-26.mp4"

GLOBAL_VIDEO_NAME = ""

# 🔹 False → {nome_do_arquivo}_slicedFiles
#    True  → 00slicedFiles (pasta compartilhada)
USE_SHARED_00_SLICED_FOLDER = False

# ============================================================
# 🔸 NOVO: SLICE_DURATION_MINUTES
#   - 0 ou None → usa o SEGMENTS manual abaixo
#   - Qualquer valor > 0 → divide o vídeo em partes iguais
#     com esse número de minutos cada
#     Ex: 5  → partes de 5 minutos
#         10 → partes de 10 minutos
# ============================================================

SLICE_DURATION_MINUTES = 0  # Defina o tempo de cada parte em minutos (0 para usar SEGMENTS manual)

# ============================================================
# SEGMENTS MANUAL (usado apenas se SLICE_DURATION_MINUTES = 0)
# ============================================================

SEGMENTS = [
    {"start": "00:00:00", "end": "00:01:00", "name": "01"}
    
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

    if not os.path.exists(output_file):
        raise RuntimeError(f"FFmpeg não gerou o arquivo esperado: {output_file}")


def generate_auto_segments(video_duration: float, slice_minutes: float) -> list:
    """
    Gera segmentos automaticamente com base na duração do vídeo
    e no tempo de cada parte em minutos.
    A última parte recebe o restante do vídeo (pode ser menor).
    """
    slice_seconds = slice_minutes * 60
    total_parts = math.ceil(video_duration / slice_seconds)

    segments = []
    for i in range(total_parts):
        start = i * slice_seconds
        end = min(start + slice_seconds, video_duration)
        name = f"{i + 1:02d}"
        segments.append((start, end, name))

    return segments


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
    # MODO: AUTO vs MANUAL
    # ========================================================

    if SLICE_DURATION_MINUTES and SLICE_DURATION_MINUTES > 0:
        # 🔸 MODO AUTOMÁTICO: gera segmentos pela duração informada
        print(f"\n[MODO AUTO] Dividindo em partes de {SLICE_DURATION_MINUTES} minuto(s)...")
        intervals = generate_auto_segments(video_duration, SLICE_DURATION_MINUTES)

    else:
        # 🔹 MODO MANUAL: usa o SEGMENTS definido acima
        print("\n[MODO MANUAL] Usando SEGMENTS configurado...")

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

    # ========================================================

    print("\n==================================================")
    print(" VIDEO SLICER (MAPPED ONLY)")
    print("==================================================")
    print(f"Arquivo origem.: {video_file}")
    print(f"Duração........: {video_duration:.2f}s")
    print(f"Partes.........: {len(intervals)}")
    print(f"Pasta destino..: {output_dir}")
    print("==================================================\n")

    for i, (start, end, label) in enumerate(intervals, 1):

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

    # ========================================================
    # FULL: copia o vídeo inteiro (00:00 até 1s antes do fim)
    # ========================================================

    full_output_name = f"FULL_{os.path.basename(video_file)}"
    full_output_path = os.path.join(output_dir, full_output_name)
    full_duration = max(video_duration - 1, 1)

    print(f"\n[FULL] Gerando cópia completa: {full_output_name}")
    run_ffmpeg(video_file, 0, full_duration, full_output_path)
    print(f"    ✔ FULL salvo em: {full_output_path}")

    # ========================================================
    # Remove o vídeo original
    # ========================================================

    os.remove(video_file)
    print(f"\n    🗑 Original removido: {video_file}")

    print("\nProcesso finalizado com sucesso.")
    print("Apenas os trechos mapeados foram mantidos.")


if __name__ == "__main__":
    main()