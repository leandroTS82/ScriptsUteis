import argparse
from pathlib import Path
from datetime import datetime
import sys

# ======================================================
# CONFIGURAÇÕES
# ======================================================

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}
DEFAULT_VIDEO_PATH = Path(r"C:\Users\leand\Desktop\wordbank")

# ======================================================
# UTIL
# ======================================================

def log(msg):
    print(msg)

def parse_date(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str, "%d/%m/%Y")
    except ValueError:
        log(f"❌ Data inválida: {date_str} (use dd/MM/yyyy)")
        sys.exit(1)

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
    ap = argparse.ArgumentParser(description="Gera playlist por intervalo de data")
    ap.add_argument("--from-date", required=True, help="Data inicial dd/MM/yyyy")
    ap.add_argument("--to-date", required=True, help="Data final dd/MM/yyyy")

    ap.add_argument(
        "--output-path",
        default=None,
        help="Diretório de saída do .m3u (default: pasta do script)"
    )

    args = ap.parse_args()

    from_date = parse_date(args.from_date)
    to_date = parse_date(args.to_date)

    if from_date > to_date:
        log("❌ Data inicial maior que data final")
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
    # NOME DO ARQUIVO .m3u BASEADO NO PY + PARÂMETROS
    # ======================================================

    script_name = Path(sys.argv[0]).stem

    from_str = normalize_date_for_filename(from_date)
    to_str = normalize_date_for_filename(to_date)

    playlist_filename = f"{script_name}_{from_str}_to_{to_str}.m3u"

    output_dir = (
        Path(args.output_path)
        if args.output_path
        else Path(sys.argv[0]).parent
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    playlist_path = output_dir / playlist_filename

    # ======================================================
    # GRAVA PLAYLIST
    # ======================================================

    with open(playlist_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for _, video in filtered:
            f.write(str(video.resolve()) + "\n")

    log("✅ Playlist gerada com sucesso")
    log(f"📄 Arquivo: {playlist_path.resolve()}")
    log(f"🎬 Total de vídeos: {len(filtered)}")

if __name__ == "__main__":
    main()
