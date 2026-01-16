from pathlib import Path
from datetime import datetime
import sys

# ======================================================
# CONFIGURAÇÕES
# ======================================================

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}

DEFAULT_VIDEO_PATH = Path(r"C:\Users\leand\Desktop\wordbank")
PLAYLISTS_PATH = DEFAULT_VIDEO_PATH / "playlists"

# ======================================================
# UTIL
# ======================================================

def log(msg):
    print(msg)

def ask_date(label: str) -> datetime:
    while True:
        value = input(f"{label} (dd/MM/yyyy): ").strip()
        try:
            return datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            log("❌ Data inválida. Use dd/MM/yyyy.")

def normalize_date_for_filename(d: datetime) -> str:
    return d.strftime("%Y%m%d")

def get_videos_root(path: Path):
    return [
        f for f in path.iterdir()
        if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS
    ]

# ======================================================
# MAIN
# ======================================================

def main():
    log("==============================================")
    log("🎬 GERADOR DE PLAYLIST POR INTERVALO DE DATA")
    log("==============================================")

    from_date = ask_date("Informe a data INICIAL")
    to_date = ask_date("Informe a data FINAL")

    if from_date > to_date:
        log("❌ Data inicial maior que data final")
        return

    if not DEFAULT_VIDEO_PATH.exists():
        log(f"❌ Pasta não encontrada: {DEFAULT_VIDEO_PATH}")
        return

    videos = get_videos_root(DEFAULT_VIDEO_PATH)

    if not videos:
        log("❌ Nenhum vídeo encontrado")
        return

    filtered = []

    for v in videos:
        modified = datetime.fromtimestamp(v.stat().st_mtime)
        if from_date <= modified <= to_date:
            filtered.append((modified, v))

    if not filtered:
        log("⚠ Nenhum vídeo encontrado no intervalo informado")
        return

    # Ordena por data de modificação
    filtered.sort(key=lambda x: x[0])

    # ======================================================
    # NOME DO ARQUIVO .m3u
    # ======================================================

    script_name = Path(sys.argv[0]).stem
    from_str = normalize_date_for_filename(from_date)
    to_str = normalize_date_for_filename(to_date)

    playlist_filename = f"{script_name}_{from_str}_to_{to_str}.m3u"

    PLAYLISTS_PATH.mkdir(parents=True, exist_ok=True)
    playlist_path = PLAYLISTS_PATH / playlist_filename

    # ======================================================
    # GRAVA PLAYLIST
    # ======================================================

    with open(playlist_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for _, video in filtered:
            f.write(str(video.resolve()) + "\n")

    log("✅ Playlist gerada com sucesso")
    log(f"📄 Arquivo: {playlist_path}")
    log(f"🎬 Total de vídeos: {len(filtered)}")

# ======================================================
# ENTRYPOINT
# ======================================================

if __name__ == "__main__":
    main()
