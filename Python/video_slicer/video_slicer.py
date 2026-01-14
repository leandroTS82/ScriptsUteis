"""
============================================================
 Script: video_slicer.py
 Autor: Leandro
 Descrição:
   - Recebe path + nome do vídeo
   - Recebe um array de horários no formato HH:mm
   - Faz slices consecutivos do vídeo
   - Salva os cortes na pasta atual (./)
============================================================

Exemplo de uso:
python video_slicer.py \
  --video-path "C:\\Videos" \
  --video-name "aula.mp4" \
  --times "00:00,02:30,05:00,07:15"
"""

import os
import subprocess
import argparse
from datetime import datetime


# ============================================================
# HELPERS
# ============================================================

def hhmm_to_seconds(hhmm: str) -> int:
    """Converte HH:mm para segundos"""
    try:
        t = datetime.strptime(hhmm, "%H:%M")
        return t.hour * 3600 + t.minute * 60
    except ValueError:
        raise ValueError(f"Formato inválido: {hhmm}. Use HH:mm")


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
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Video slicer por HH:mm")
    parser.add_argument("--video-path", required=True, help="Diretório do vídeo")
    parser.add_argument("--video-name", required=True, help="Nome do arquivo de vídeo")
    parser.add_argument(
        "--times",
        required=True,
        help="Lista de horários HH:mm separados por vírgula"
    )

    args = parser.parse_args()

    video_path = os.path.abspath(args.video_path)
    video_file = os.path.join(video_path, args.video_name)

    if not os.path.isfile(video_file):
        raise FileNotFoundError(f"Vídeo não encontrado: {video_file}")

    # Parse e ordena os tempos
    times_raw = [t.strip() for t in args.times.split(",")]
    times_seconds = sorted(hhmm_to_seconds(t) for t in times_raw)

    if len(times_seconds) < 2:
        raise ValueError("Informe pelo menos dois horários para gerar slices.")

    base_name, ext = os.path.splitext(args.video_name)

    print("\nIniciando cortes do vídeo")
    print(f"Arquivo: {video_file}")
    print(f"Slices: {len(times_seconds) - 1}\n")

    for i in range(len(times_seconds) - 1):
        start = times_seconds[i]
        end = times_seconds[i + 1]
        duration = end - start

        start_label = times_raw[i].replace(":", "h")
        end_label = times_raw[i + 1].replace(":", "h")

        output_name = f"{base_name}_{start_label}_to_{end_label}{ext}"
        output_path = os.path.join(os.getcwd(), output_name)

        print(f"[{i+1}] {output_name}")

        run_ffmpeg(
            input_video=video_file,
            start=start,
            duration=duration,
            output_file=output_path
        )

    print("\nProcesso finalizado com sucesso.")


if __name__ == "__main__":
    main()
