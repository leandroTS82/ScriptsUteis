import subprocess
import sys
from pathlib import Path

# ======================================================
# CONFIGURAÇÕES
# ======================================================
OUTPUT_DIR = Path("./downloads")
OUTPUT_DIR.mkdir(exist_ok=True)

YTDLP_FORMAT = "bv*+ba/b"
MERGE_FORMAT = "mp4"

# ======================================================
# CORE
# ======================================================
def download_youtube_mp4(url: str):
    command = [
        sys.executable, "-m", "yt_dlp",
        "-f", YTDLP_FORMAT,
        "--merge-output-format", MERGE_FORMAT,
        "-o", str(OUTPUT_DIR / "%(title)s.%(ext)s"),
        url
    ]

    print("==============================================")
    print("▶ Iniciando download do YouTube")
    print(f"▶ URL: {url}")
    print(f"▶ Saída: {OUTPUT_DIR.resolve()}")
    print("==============================================")

    subprocess.run(command, check=True)

    print("==============================================")
    print("✔ Download concluído com sucesso")
    print("==============================================")

# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":
    youtube_url = input("Cole o link do vídeo do YouTube: ").strip()

    if not youtube_url.startswith("http"):
        print("❌ URL inválida.")
        sys.exit(1)

    download_youtube_mp4(youtube_url)
