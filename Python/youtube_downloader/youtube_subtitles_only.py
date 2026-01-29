"""
============================================================
 Script: youtube_subtitles_only.py
 Autor: Leandro
 Descrição:
   - Baixa APENAS legendas do YouTube
   - Legendas oficiais + automáticas
   - Converte para SRT
   - Cria pasta com nome do vídeo (Windows-safe)
   - Não falha se um idioma der erro (429, inexistente, etc.)
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

BASE_OUTPUT_DIR = Path("./subtitles")
BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

#SUB_LANGS = ["en", "pt", "pt-BR"]
SUB_LANGS = ["en"]
SUB_FORMAT = "srt"

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
    return name[:200]  # evita path longo demais


def get_video_title(url: str) -> str:
    """Obtém o título do vídeo sem baixar nada"""
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

def download_subtitles_only(url: str):
    clean_url = clean_youtube_url(url)

    title = get_video_title(clean_url)
    video_dir = BASE_OUTPUT_DIR / title
    video_dir.mkdir(parents=True, exist_ok=True)

    print("=================================================")
    print("▶ Baixando APENAS legendas")
    print(f"▶ Vídeo: {title}")
    print(f"▶ Pasta: {video_dir.resolve()}")
    print("=================================================")

    for lang in SUB_LANGS:
        command = [
            sys.executable, "-m", "yt_dlp",
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--sub-lang", lang,
            "--sub-format", SUB_FORMAT,
            "--no-abort-on-error",
            "-o", str(video_dir / f"{title}.%(ext)s"),
            clean_url
        ]

        print(f"▶ Tentando legenda: {lang}")
        subprocess.run(command)

    print("=================================================")
    print("✔ Processo finalizado (idiomas disponíveis baixados)")
    print("=================================================")

# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":
    url = input("Cole o link do YouTube: ").strip()

    if not url.startswith("http"):
        print("❌ URL inválida")
        sys.exit(1)

    download_subtitles_only(url)
