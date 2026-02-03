from pathlib import Path
import random

# ======================================================
# CONFIGURAÇÕES
# ======================================================

AUDIO_PATH = Path("./audios")
PLAYLIST_OUTPUT_PATH = Path("./audio_playlists")

AUDIO_EXTENSIONS = {
    ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"
}

# ======================================================
# UTILS
# ======================================================

def log(msg):
    print(msg, flush=True)

def safe_int(prompt: str, default: int = 10, min_value: int = 1) -> int:
    raw = input(prompt).strip()
    try:
        value = int(raw)
        return value if value >= min_value else default
    except Exception:
        return default

# ======================================================
# FILE SCAN
# ======================================================

def get_all_audios(path: Path):
    if not path.exists():
        return []

    return [
        f for f in path.iterdir()
        if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS
    ]

# ======================================================
# PLAYLIST
# ======================================================

def write_playlist(audios, name):
    PLAYLIST_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    playlist_path = PLAYLIST_OUTPUT_PATH / f"{name}.m3u"

    with open(playlist_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for audio in audios:
            title = audio.stem
            f.write(f"#EXTINF:-1,{title}\n")
            f.write(str(audio.resolve()) + "\n")

    log(f"\n🎧 Playlist criada com sucesso!")
    log(f"📄 Arquivo: {playlist_path.resolve()}")
    log(f"🔢 Total de áudios: {len(audios)}")

# ======================================================
# MAIN
# ======================================================

def main():
    log("==============================================")
    log("🎵 AUDIO RANDOM PLAYLIST")
    log("==============================================\n")

    audios = get_all_audios(AUDIO_PATH)

    if not audios:
        log("❌ Nenhum arquivo de áudio encontrado em ./audios")
        return

    playlist_name = input("Informe o nome da playlist: ").strip()
    if not playlist_name:
        log("❌ Nome da playlist inválido")
        return

    qty = safe_int(
        "Quantidade de itens na playlist: ",
        default=10,
        min_value=1
    )

    if qty > len(audios):
        log(f"⚠ Quantidade solicitada maior que o total disponível ({len(audios)}). Ajustando.")
        qty = len(audios)

    random.shuffle(audios)
    selected = audios[:qty]

    write_playlist(selected, playlist_name)

    log("\n✅ Processo finalizado com sucesso")

# ======================================================
# ENTRYPOINT
# ======================================================

if __name__ == "__main__":
    main()