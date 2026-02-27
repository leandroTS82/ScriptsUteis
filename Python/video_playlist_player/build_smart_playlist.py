import os
import sys
from pathlib import Path
from datetime import datetime
import json
import requests
import random
from itertools import cycle
import re

# ======================================================
# CONFIGURAÇÕES INLINE
# ======================================================

USE_GROQ = True

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}
SRT_EXTENSIONS = {".srt"}

VIDEO_PATHS = [
    Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - LeandrinhoMovies")
]

HISTORY_VIDEO_PATHS = [
    Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - LeandrinhoMovies\Histories")
]

TERMS_PATHS = [
    Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\movies_processed"),
    Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Histories\NewHistory\subtitles"),
    Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Uploaded"),
]

PLAYLIST_OUTPUT_PATH = Path(r"C:\Playlists\01-smart_playlists")
RANDOM_STATS_JSON = Path(r"C:\Playlists\01-smart_playlists\random_playlist_stats.json")

RANDOM_PERCENT_USED = 0.30
RANDOM_PERCENT_NEW = 0.70
RANDOM_PERCENT_RECENT = 0.50
RANDOM_PERCENT_OLD = 0.50
RECENT_DAYS_THRESHOLD = 30

# ======================================================
# GROQ CONFIG
# ======================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from groq_keys_loader import GROQ_KEYS

_groq_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

# ======================================================
# UTILS
# ======================================================

def log(msg):
    print(msg, flush=True)

def ask_yes_no(msg: str) -> bool:
    return input(f"{msg} (s/n): ").strip().lower() == "s"

def ask_date(label: str) -> datetime:
    while True:
        value = input(f"{label} (dd/MM/yyyy): ").strip()
        try:
            return datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            log("❌ Data inválida.")

def normalize_date(d: datetime) -> str:
    return d.strftime("%Y%m%d")

def safe_int(prompt: str, default: int = 10, min_value: int = 1) -> int:
    raw = input(prompt).strip()
    try:
        value = int(raw)
        return value if value >= min_value else default
    except Exception:
        return default

def split_terms(raw: str):
    parts = [p.strip().lower() for p in raw.split(",")]
    return [p for p in parts if p]

# ======================================================
# RANDOM MODE
# ======================================================

def random_mode(videos, include_histories):

    qty = safe_int("Quantidade de vídeos na playlist: ", default=10, min_value=1)

    histories = get_all_videos(HISTORY_VIDEO_PATHS) if include_histories else []
    all_media = videos + histories

    if not all_media:
        log("⚠ Nenhum vídeo encontrado nas pastas configuradas.")
        return []

    state = load_random_state(all_media)
    now = datetime.now()

    recent_items = []
    old_items = []

    for k, v in state.items():
        file_date = datetime.fromisoformat(v["date"])
        path_obj = Path(k)

        if (now - file_date).days <= RECENT_DAYS_THRESHOLD:
            recent_items.append(path_obj)
        else:
            old_items.append(path_obj)

    def split_by_usage(items):
        new = []
        used = []
        for p in items:
            if state[str(p.resolve())].get("count", 0) == 0:
                new.append(p)
            else:
                used.append(p)
        return new, used

    recent_new, recent_used = split_by_usage(recent_items)
    old_new, old_used = split_by_usage(old_items)

    qty_recent = int(qty * RANDOM_PERCENT_RECENT)
    qty_old = qty - qty_recent

    def pick_group(new_list, used_list, total_qty):
        if total_qty <= 0:
            return []

        qty_new = int(total_qty * RANDOM_PERCENT_NEW)
        qty_used = total_qty - qty_new

        random.shuffle(new_list)
        selected_new = new_list[:qty_new]

        used_weights = [
            1 / (state[str(p.resolve())].get("count", 0) + 1)
            for p in used_list
        ]

        selected_used = weighted_sample(used_list, used_weights, qty_used)

        return selected_new + selected_used

    selected = []
    selected += pick_group(recent_new, recent_used, qty_recent)
    selected += pick_group(old_new, old_used, qty_old)

    random.shuffle(selected)

    for v in selected:
        key = str(v.resolve())
        state[key]["count"] = state[key].get("count", 0) + 1

    save_random_state(state)

    log("\n📊 ESTATÍSTICAS DA PLAYLIST ALEATÓRIA")
    log(f"📁 Total de itens no JSON: {len(state)}")
    log("🎯 Vídeos selecionados nesta execução:")
    for v in selected:
        log(f"   - {v.name} → contador: {state[str(v.resolve())]['count']}")

    return selected

# ======================================================
# FILE SCAN
# ======================================================

def get_all_videos(paths):
    videos = []
    for p in paths:
        if p.exists():
            videos.extend([
                f for f in p.iterdir()
                if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS
            ])
    return videos

def get_all_srts(paths):
    srts = []
    for p in paths:
        if p.exists():
            srts.extend([
                f for f in p.iterdir()
                if f.is_file() and f.suffix.lower() in SRT_EXTENSIONS
            ])
    return srts

# ======================================================
# RANDOM STATE HELPERS
# ======================================================

def load_random_state(all_files):
    if RANDOM_STATS_JSON.exists():
        with open(RANDOM_STATS_JSON, "r", encoding="utf-8") as f:
            state = json.load(f)
    else:
        state = {}

    for f in all_files:
        key = str(f.resolve())
        file_date = datetime.fromtimestamp(f.stat().st_mtime).isoformat()

        if key not in state:
            state[key] = {
                "count": 0,
                "type": "history" if f.parent in HISTORY_VIDEO_PATHS else "video",
                "date": file_date
            }
        else:
            if "date" not in state[key]:
                state[key]["date"] = file_date

    return state

def save_random_state(state):
    RANDOM_STATS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(RANDOM_STATS_JSON, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def weighted_sample(items, weights, k):
    selected = []
    pool = list(zip(items, weights))

    for _ in range(min(k, len(pool))):
        total = sum(w for _, w in pool)
        r = random.uniform(0, total)
        upto = 0
        for i, (item, weight) in enumerate(pool):
            upto += weight
            if upto >= r:
                selected.append(item)
                pool.pop(i)
                break

    return selected

# ======================================================
# PLAYLIST WRITER
# ======================================================

def write_playlist(videos, mode, meta, part_index=None, base_dir=None, custom_name=None):
    output_dir = base_dir or PLAYLIST_OUTPUT_PATH
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = custom_name
    if part_index is not None:
        filename = f"{filename}_part_{part_index}"

    path = output_dir / f"{filename}.m3u"

    with open(path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for v in videos:
            f.write(f"#EXTINF:-1,{v.stem}\n")
            f.write(str(v.resolve()) + "\n")

    log(f"📄 Playlist criada: {path.resolve().name} ({len(videos)} vídeos)")

# ======================================================
# MAIN
# ======================================================

def main():

    log("==============================================")
    log("🎬 SMART STUDY PLAYLIST")
    log("==============================================")
    log(f"⚙️  Modo ativo: {'GROQ (ONLINE)' if USE_GROQ else 'OFFLINE (Python)'}\n")

    include_histories = ask_yes_no("Adicionar histories?")
    videos = get_all_videos(VIDEO_PATHS)

    custom_name = None
    if ask_yes_no("Deseja dar um nome à playlist?"):
        custom_name = input("Insira o nome: ").strip()
        if ask_yes_no("Deseja adicionar data ao nome?"):
            custom_name = f"{datetime.now().strftime('%Y%m%d')}_{custom_name}"

    log("\nOpções:")
    log("1 - Data específica")
    log("2 - Intervalo de datas")
    log("3 - Termo ou sentido")
    log("4 - Playlist aleatória")

    option = input("Escolha (1/2/3/4): ").strip()

    selected = []
    mode = None

    if option == "1":
        d = ask_date("Informe a data")
        mode = "data"
        selected = [
            v for v in videos
            if datetime.fromtimestamp(v.stat().st_mtime).date() == d.date()
        ]

    elif option == "2":
        d1 = ask_date("Data inicial")
        d2 = ask_date("Data final")
        mode = "periodo"
        selected = [
            v for v in videos
            if d1 <= datetime.fromtimestamp(v.stat().st_mtime) <= d2
        ]

    elif option == "4":
        mode = "random"
        selected = random_mode(videos, include_histories)

    else:
        log("❌ Opção inválida")
        return

    if not selected:
        log("⚠ Nenhum vídeo encontrado")
        return

    base_dir = PLAYLIST_OUTPUT_PATH / mode / (custom_name or "default")

    write_playlist(
        selected,
        mode,
        {},
        base_dir=base_dir,
        custom_name=custom_name or mode
    )

    log("\n✅ Processo finalizado com sucesso")

# ======================================================

if __name__ == "__main__":
    main()