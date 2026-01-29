"""
============================================================
 Script: youtube_downloader_with_subtitles.py
 Autor: Leandro
 Descrição:
   - Baixa vídeo do YouTube em MP4 (até 1080p)
   - Baixa legendas oficiais e automáticas
   - Converte legendas para SRT
   - Compatível com Windows sem impersonation
============================================================
"""

import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

OUTPUT_DIR = Path("./downloads")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Força MP4 até 1080p (mais estável)
VIDEO_FORMAT = (
    "bv*[ext=mp4][height<=1080]+ba[ext=m4a]/"
    "bv*[height<=1080]+ba/b"
)

MERGE_FORMAT = "mp4"

SUB_LANGS = "en,pt,pt-BR"
SUB_FORMAT = "srt"

# ==========================================================
# HELPERS
# ==========================================================

def clean_youtube_url(url: str) -> str:
    """Remove parâmetros como &t= para evitar problemas"""
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    video_id = query.get("v", [None])[0]
    if not video_id:
        return url

    return f"https://www.youtube.com/watch?v={video_id}"

# ==========================================================
# CORE
# ==========================================================

def download_video_with_subs(url: str):
    clean_url = clean_youtube_url(url)

    command = [
        sys.executable, "-m", "yt_dlp",

        # Vídeo (estável)
        "-f", VIDEO_FORMAT,
        "--merge-output-format", MERGE_FORMAT,

        # Legendas
        "--write-subs",
        "--write-auto-subs",
        "--sub-lang", SUB_LANGS,
        "--sub-format", SUB_FORMAT,

        # Output
        "-o", str(OUTPUT_DIR / "%(title)s.%(ext)s"),

        clean_url
    ]

    print("=================================================")
    print("▶ Iniciando download do YouTube")
    print(f"▶ URL limpa: {clean_url}")
    print(f"▶ Legendas: {SUB_LANGS}")
    print(f"▶ Saída: {OUTPUT_DIR.resolve()}")
    print("=================================================")

    subprocess.run(command, check=True)

    print("=================================================")
    print("✔ Vídeo e legendas baixados com sucesso")
    print("=================================================")

# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":
    url = input("Cole o link do YouTube: ").strip()

    if not url.startswith("http"):
        print("❌ URL inválida")
        sys.exit(1)

    download_video_with_subs(url)
