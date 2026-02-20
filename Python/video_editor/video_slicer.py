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

VIDEO_FILE = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\Vídeos baixados\Speak English With Tiffani\Condence.mp4"

GLOBAL_VIDEO_NAME = "Condence"

# 🔹 NOVA FLAG
# False → {nome_do_arquivo}_slicedFiles
# True  → 00slicedFiles (pasta compartilhada)
USE_SHARED_00_SLICED_FOLDER = False

SEGMENTS = [
    {
        "start": "00:00",
        "end": "01:50",
        "name": "01_Introducao_A_Gaiola_do_Ingles"
    },
    {
        "start": "01:50",
        "end": "07:13",
        "name": "02_Aplicacao_1_Parar_de_Ensaiar"
    },
    {
        "start": "07:13",
        "end": "13:47",
        "name": "03_Aplicacao_2_Permissao_Para_o_Aproximado"
    },
    {
        "start": "13:47",
        "end": "20:24",
        "name": "04_Aplicacao_3_Falar_Antes_de_Estar_Pronto"
    },
    {
        "start": "20:24",
        "end": "28:20",
        "name": "05_Aplicacao_4_Nao_Traduzir_sua_Personalidade"
    },
    {
        "start": "28:20",
        "end": "34:57",
        "name": "06_Aplicacao_5_Aceitar_a_Imperfeicao"
    },
    {
        "start": "34:57",
        "end": "42:08",
        "name": "07_Story_Time_Licao_de_Vida"
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

    video_file = os.path.abspath(VIDEO_FILE)

    if not os.path.isfile(video_file):
        raise FileNotFoundError(f"Vídeo não encontrado: {video_file}")

    video_duration = get_video_duration(video_file)

    base_dir = os.path.dirname(video_file)
    base_name = os.path.splitext(os.path.basename(video_file))[0]

    # ========================================================
    # REGRA DA PASTA (ATUALIZADA)
    # ========================================================

    if USE_SHARED_00_SLICED_FOLDER:
        # Gera diretamente no próprio diretório do vídeo
        output_dir = base_dir
    else:
        # Gera na pasta {nome_do_arquivo}_slicedFiles
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
        output_name = (
            f"{GLOBAL_VIDEO_NAME}_{label}_"
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
