"""
============================================================
 Script: video_joiner.py
 Autor: Leandro
 Descrição:
   - Junta vídeos na ORDEM definida em um array
   - Usa FFmpeg concat (sem re-encode)
   - Gera um único arquivo final
============================================================

Requisitos:
- ffmpeg instalado e disponível no PATH
"""

import os
import subprocess
import sys
from tempfile import NamedTemporaryFile


# ============================================================
# CONFIGURAÇÃO
# ============================================================

VIDEO_PATH = r"C:\Users\leand\Desktop\GijsDemonstration"

VIDEO_ARRAY_NAME = [
    "01_CreatedTR_00m00s_to_00m18s.mp4",
    "02_ChangeInZoho_00m00s_to_00m15s.mp4",
    "03_Updated_In_TR_00m00s_to_00m16s.mp4",
    "04_ShowDataBAse01_00m00s_to_00m18s.mp4",
    "04_ShowDataBAse02_00m00s_to_00m30s.mp4",
    "05_Confitmation_00m00s_to_00m27s.mp4",
]

OUTPUT_NAME = "FINAL_JOINED_VIDEO.mp4"

FFMPEG_BIN = "ffmpeg"


# ============================================================
# HELPERS
# ============================================================

def validate_files(video_path: str, files: list[str]) -> list[str]:
    resolved = []

    for name in files:
        full = os.path.join(video_path, name)

        if not os.path.isfile(full):
            raise FileNotFoundError(f"Arquivo não encontrado: {full}")

        resolved.append(os.path.abspath(full))

    return resolved


def create_concat_file(video_files: list[str]) -> str:
    """
    Cria arquivo temporário no formato aceito pelo ffmpeg concat
    """
    temp = NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8")

    for vf in video_files:
        # ffmpeg exige path com aspas simples
        temp.write(f"file '{vf}'\n")

    temp.close()
    return temp.name


def run_ffmpeg_concat(concat_file: str, output_file: str):
    cmd = [
        FFMPEG_BIN,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
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
    print("\n==================================================")
    print(" VIDEO JOINER")
    print("==================================================")

    video_files = validate_files(VIDEO_PATH, VIDEO_ARRAY_NAME)

    print(f"Arquivos....: {len(video_files)}")
    for i, vf in enumerate(video_files, 1):
        print(f"  {i:02d} - {os.path.basename(vf)}")

    concat_file = create_concat_file(video_files)
    output_file = os.path.join(VIDEO_PATH, OUTPUT_NAME)

    print("\nGerando vídeo final...")
    run_ffmpeg_concat(concat_file, output_file)

    os.unlink(concat_file)

    print("\n==================================================")
    print(" PROCESSO FINALIZADO")
    print(f" Arquivo gerado: {output_file}")
    print("==================================================\n")


if __name__ == "__main__":
    main()
