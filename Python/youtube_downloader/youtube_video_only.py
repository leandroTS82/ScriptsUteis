"""
============================================================
 Script: youtube_video_only.py
 Autor: Leandro
 Descrição:
   - Baixa APENAS o vídeo do YouTube
   - MP4 até 1080p (estável)
   - Cria uma pasta com o nome do vídeo
   - Nome de pasta e arquivo Windows-safe
   - Sem impersonation
============================================================
"""

import subprocess
import sys
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

BASE_OUTPUT_DIR = Path("./videos")
BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VIDEO_FORMAT = (
    "bv*[ext=mp4][height<=1080]+ba[ext=m4a]/"
    "bv*[height<=1080]+ba/b"
)

MERGE_FORMAT = "mp4"

# ==========================================================
# HELPERS
# ==========================================================

def clean_youtube_url(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    video_id = query.get("v", [None])[0]
    return f"https://www.youtube.com/watch?v={video_id}" if video_id else url


def sanitize_filename(name: str) -> str:
    """Remove caracteres inválidos para Windows"""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name[:200]


def get_video_title(url: str) -> str:
    """Obtém o título do vídeo sem baixar"""
    result = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "--get-title", url],
        capture_output=True,
        text=True,
        check=True
    )
    return sanitize_filename(result.stdout.strip())

# ==========================================================
# CORE
# ==========================================================

def download_video_only(url: str):
    clean_url = clean_youtube_url(url)

    title = get_video_title(clean_url)
    video_dir = BASE_OUTPUT_DIR / title
    video_dir.mkdir(parents=True, exist_ok=True)

    output_template = video_dir / f"{title}.%(ext)s"

    command = [
        sys.executable, "-m", "yt_dlp",

        # Vídeo estável
        "-f", VIDEO_FORMAT,
        "--merge-output-format", MERGE_FORMAT,

        # Não baixar legendas aqui
        "--no-write-subs",

        # Output
        "-o", str(output_template),

        clean_url
    ]

    print("=================================================")
    print("▶ Baixando APENAS vídeo")
    print(f"▶ Vídeo: {title}")
    print(f"▶ Pasta: {video_dir.resolve()}")
    print("=================================================")

    subprocess.run(command, check=True)

    print("=================================================")
    print("✔ Vídeo baixado com sucesso")
    print("=================================================")

# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":
    url = input("Cole o link do YouTube: ").strip()

    if not url.startswith("http"):
        print("❌ URL inválida")
        sys.exit(1)

    download_video_only(url)
