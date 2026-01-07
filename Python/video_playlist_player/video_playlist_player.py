import json
import random
import subprocess
import time
import argparse
from pathlib import Path
from datetime import datetime, date

# ======================================================
# CONFIGURAÇÕES
# ======================================================

VLC_PATH = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}

MAPPING_FILE = Path("./video_play_count.json")
SUBSET_FILE = Path("./selected_videos.json")

# ======================================================
# UTIL
# ======================================================

def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}")

def get_videos_from_path(path: Path):
    return [f for f in path.iterdir() if f.suffix.lower() in VIDEO_EXTENSIONS]

# ======================================================
# MAPEAMENTO
# ======================================================

def load_or_create_mapping(videos):
    mapping = json.load(open(MAPPING_FILE)) if MAPPING_FILE.exists() else {}
    names = {v.name for v in videos}
    mapping = {k: v for k, v in mapping.items() if k in names}
    for v in videos:
        mapping.setdefault(v.name, 0)
    save_mapping(mapping)
    return mapping

def save_mapping(mapping):
    json.dump(mapping, open(MAPPING_FILE, "w"), indent=2)

def build_playlist_with_mapping(videos, mapping, shuffle):
    grouped = {}
    for v in videos:
        grouped.setdefault(mapping[v.name], []).append(v)
    playlist = []
    for k in sorted(grouped):
        if shuffle:
            random.shuffle(grouped[k])
        playlist.extend(grouped[k])
    return playlist

# ======================================================
# SUBSET
# ======================================================

def should_reset_subset_daily():
    if not SUBSET_FILE.exists():
        return False
    data = json.load(open(SUBSET_FILE))
    return datetime.fromisoformat(data["generated_at"]).date() != date.today()

def save_subset(videos):
    json.dump({
        "generated_at": datetime.now().isoformat(),
        "total_selected": len(videos),
        "videos": [v.name for v in videos]
    }, open(SUBSET_FILE, "w"), indent=2)

def load_subset(videos):
    data = json.load(open(SUBSET_FILE))
    lookup = {v.name: v for v in videos}
    return [lookup[n] for n in data["videos"] if n in lookup]

def build_random_subset(videos, mapping, max_size, shuffle, fixed):
    ordered = build_playlist_with_mapping(videos, mapping, shuffle)
    size = max_size if fixed else random.randint(1, min(len(ordered), max_size))
    subset = ordered[:size]
    save_subset(subset)
    return subset

# ======================================================
# VIDEO
# ======================================================

def get_video_duration(video):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nokey=1:noprint_wrappers=1", str(video)],
        capture_output=True, text=True
    )
    return int(float(r.stdout.strip())) + 1

def play_video(video, duration):
    log(f"▶ Reproduzindo: {video.name}")
    p = subprocess.Popen([VLC_PATH, "--fullscreen", str(video)])
    time.sleep(duration)
    p.terminate()
    p.wait()

# ======================================================
# MAIN
# ======================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True)
    ap.add_argument("--repeat-video", type=int, default=1)
    ap.add_argument("--pause", type=int, default=0)
    ap.add_argument("--shuffle", action="store_true")
    ap.add_argument("--loop", action="store_true")

    ap.add_argument("--use-mapping", action="store_true")
    ap.add_argument("--use-random-subset", action="store_true")
    ap.add_argument("--subset-max", type=int, default=5)
    ap.add_argument("--reuse-last-subset", action="store_true")
    ap.add_argument("--subset-fixed-size", action="store_true")
    ap.add_argument("--subset-reset-daily", action="store_true")

    ap.add_argument("--enable-max-total-playtime", action="store_true")
    ap.add_argument("--max-total-playtime-minutes", type=int, default=0)

    args = ap.parse_args()

    videos = get_videos_from_path(Path(args.path))
    if not videos:
        log("❌ Nenhum vídeo encontrado.")
        return

    log(f"🎬 {len(videos)} vídeos encontrados")

    mapping = load_or_create_mapping(videos) if args.use_mapping else None
    subset = None

    if args.use_random_subset:
        log("🎯 Modo SUBSET ativado")

        if args.reuse_last_subset and SUBSET_FILE.exists():
            if not (args.subset_reset_daily and should_reset_subset_daily()):
                subset = load_subset(videos)
                log(f"♻ Reutilizando subset ({len(subset)} vídeos)")

        if subset is None:
            subset = build_random_subset(
                videos, mapping, args.subset_max,
                args.shuffle, args.subset_fixed_size
            )
            log(f"🆕 Subset gerado ({len(subset)} vídeos)")

    playlist = subset if subset else (
        build_playlist_with_mapping(videos, mapping, args.shuffle)
        if args.use_mapping else random.sample(videos, len(videos))
    )

    max_seconds = args.max_total_playtime_minutes * 60
    played_seconds = 0

    while True:
        for v in playlist:
            duration = get_video_duration(v)

            if args.enable_max_total_playtime and played_seconds + duration > max_seconds:
                log("⏹ Tempo máximo atingido. Encerrando.")
                return

            for i in range(args.repeat_video):
                play_video(v, duration)
                played_seconds += duration

                if mapping:
                    mapping[v.name] += 1
                    save_mapping(mapping)

                if args.pause:
                    log(f"⏸ Pausa {args.pause}s")
                    time.sleep(args.pause)

        if not args.loop:
            break

if __name__ == "__main__":
    main()
