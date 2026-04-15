import os
import sys
import json
import random
import re
from pathlib import Path
from datetime import datetime
from itertools import cycle
import requests

# =========================
# PATH FIX
# =========================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from groq_keys_loader import GROQ_KEYS

# =========================
# CONFIG
# =========================
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov"}

VIDEO_PATHS = [
    Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - LeandrinhoMovies")
]

TERMS_PATH = Path(
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\movies_processed"
)

PLAYLIST_OUTPUT_PATH = Path(r"C:\Playlists\01-smart_playlists")
RANDOM_STATS_JSON = PLAYLIST_OUTPUT_PATH / "random_playlist_stats.json"

# =========================
# GROQ CONFIG
# =========================
_groq_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

# =========================
# UTILS
# =========================
def log(msg):
    print(msg, flush=True)


def ask_date(label):
    while True:
        try:
            return datetime.strptime(input(f"{label} (dd/MM/yyyy): "), "%d/%m/%Y")
        except:
            log("❌ Data inválida")


def ask_int(msg, default=10):
    try:
        return max(1, int(input(msg)))
    except:
        return default


def get_modified_datetime(path: Path):
    return datetime.fromtimestamp(os.path.getmtime(path))


def get_all_videos():
    videos = []
    for p in VIDEO_PATHS:
        if p.exists():
            videos.extend([
                f for f in p.iterdir()
                if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS
            ])
    return videos


# =========================
# GROQ
# =========================
def get_next_groq_key():
    key_obj = next(_groq_key_cycle)
    key = key_obj.get("key")
    name = key_obj.get("name", "unknown")

    log(f"🔑 GROQ KEY: {name}")
    return key


def groq(prompt: str):
    for _ in range(len(GROQ_KEYS)):
        try:
            key = get_next_groq_key()

            res = requests.post(
                GROQ_URL,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2
                },
                timeout=10
            )

            if res.status_code == 429:
                continue

            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]

        except:
            continue

    return ""


# =========================
# METADATA
# =========================
def load_metadata_dates():
    metadata = {}

    if RANDOM_STATS_JSON.exists():
        with open(RANDOM_STATS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data.get("files", []):
            if "name" in item:
                dt = item.get("modified_at") or item.get("created_at")
                if dt:
                    metadata[item["name"].lower()] = datetime.fromisoformat(dt)

    return metadata


# =========================
# OPTION 1 & 2
# =========================
def filter_by_date(videos, start_date, end_date=None):
    metadata = load_metadata_dates()
    selected = []

    for v in videos:
        name = v.name.lower()
        file_date = metadata.get(name) or get_modified_datetime(v)

        if end_date:
            if start_date <= file_date <= end_date:
                selected.append(v)
        else:
            if file_date.date() == start_date.date():
                selected.append(v)

    return selected


# =========================
# JSON CONTEXT
# =========================
def extract_json_context(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        nome = data.get("nome_arquivos", "").lower()

        main_term = ""
        context = []

        for item in data.get("WORD_BANK", [[]])[0]:
            if item.get("lang") == "en" and not main_term:
                main_term = item.get("text", "").lower()

            if "text" in item:
                context.append(item["text"].lower())

        if "introducao" in data:
            context.append(data["introducao"].lower())

        return nome, main_term, " ".join(context)

    except:
        return None, None, ""


# =========================
# OPTION 3 (AI SEARCH)
# =========================
def local_pre_filter(json_files, user_input, limit=200):
    results = []

    for f in json_files:
        nome, term, context = extract_json_context(f)

        if not nome:
            continue

        text = f"{term} {context}"

        if user_input.lower() in text:
            results.append((f, 2))
        elif any(word in text for word in user_input.split()):
            results.append((f, 1))

    results.sort(key=lambda x: x[1], reverse=True)

    return [r[0] for r in results[:limit]]


def score_with_groq(user_input, term, context):
    prompt = f"""
User intent: "{user_input}"
Term: "{term}"
Context:
{context[:1500]}

Return ONLY a number from 0 to 100.
"""

    try:
        result = groq(prompt)
        return int(re.findall(r"\d+", result)[0])
    except:
        return 0


def ai_search(videos, user_input, desired_count):
    json_files = list(TERMS_PATH.glob("*.json"))

    log("⚡ Pré-filtrando candidatos...")
    candidates = local_pre_filter(json_files, user_input, limit=300)

    log(f"📊 Candidatos após pré-filtro: {len(candidates)}")

    scored = []

    for f in candidates:
        nome, term, context = extract_json_context(f)

        score = score_with_groq(user_input, term, context)

        if score > 50:
            log(f"🎯 {nome} | score={score}")
            scored.append((nome, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    top_names = [s[0] for s in scored[:desired_count]]

    return [v for v in videos if v.stem.lower() in top_names]


# =========================
# PLAYLIST
# =========================
def write_playlist(videos, name):
    PLAYLIST_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    path = PLAYLIST_OUTPUT_PATH / f"{name}.m3u"

    with open(path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for v in videos:
            f.write(f"#EXTINF:-1,{v.stem}\n")
            f.write(str(v.resolve()) + "\n")

    log(f"\n📄 Playlist criada: {path}")


# =========================
# MAIN
# =========================
def main():
    videos = get_all_videos()

    log("1 - Data específica")
    log("2 - Intervalo de datas")
    log("3 - Termo ou sentido (IA)")
    log("4 - Playlist aleatória")

    option = input("Escolha: ").strip()

    if option == "1":
        d = ask_date("Data")
        selected = filter_by_date(videos, d)

    elif option == "2":
        d1 = ask_date("Data inicial")
        d2 = ask_date("Data final")
        selected = filter_by_date(videos, d1, d2)

    elif option == "3":
        term = input("Digite o termo: ")
        qty = ask_int("Quantos vídeos deseja? ", 10)
        selected = ai_search(videos, term, qty)

    elif option == "4":
        selected = random.sample(videos, min(10, len(videos)))

    else:
        log("❌ inválido")
        return

    if not selected:
        log("⚠ Nenhum vídeo encontrado")
        return

    write_playlist(selected, f"playlist_{option}")


if __name__ == "__main__":
    main()