"""
============================================================
 Script: smart_video_compressor.py
 Autor: Leandro
 Descrição:
   - Comprime vídeos usando FFmpeg
   - Mantém qualidade visual usando CRF
   - Redução grande de tamanho usando H265
   - Entrada: caminho do vídeo
   - Saída: vídeo comprimido na mesma pasta
============================================================

python smart_video_compressor.py "C:\videos\meu_video.mp4"
"""

import subprocess
from pathlib import Path
import sys

# ==========================================================
# CONFIG
# ==========================================================

CRF_VALUE = 24          # menor = mais qualidade (18-28 recomendado)
PRESET = "slow"         # slow = melhor compressão
AUDIO_BITRATE = "128k"  # mantém boa qualidade de áudio

# ==========================================================
# FUNCTIONS
# ==========================================================

def check_ffmpeg():
    """Verifica se FFmpeg está instalado"""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("❌ FFmpeg não encontrado. Instale: https://ffmpeg.org/")
        sys.exit(1)


def build_output_path(input_path: Path) -> Path:
    """Gera nome do arquivo de saída"""
    return input_path.with_name(f"{input_path.stem}_compressed.mp4")


def compress_video(input_path: Path, output_path: Path):
    """Executa compressão usando FFmpeg"""

    command = [
        "ffmpeg",
        "-i", str(input_path),
        "-vcodec", "libx265",
        "-crf", str(CRF_VALUE),
        "-preset", PRESET,
        "-acodec", "aac",
        "-b:a", AUDIO_BITRATE,
        str(output_path)
    ]

    print("\n🎬 Comprimindo vídeo...")
    print(f"📥 Entrada : {input_path}")
    print(f"📤 Saída   : {output_path}\n")

    subprocess.run(command)

    print("\n✅ Compressão finalizada.")


# ==========================================================
# MAIN
# ==========================================================

def main():

    if len(sys.argv) < 2:
        print("\nUso:")
        print("python smart_video_compressor.py <caminho_do_video>\n")
        return

    input_path = Path(sys.argv[1])

    if not input_path.exists():
        print("❌ Arquivo não encontrado.")
        return

    check_ffmpeg()

    output_path = build_output_path(input_path)

    compress_video(input_path, output_path)


if __name__ == "__main__":
    main()