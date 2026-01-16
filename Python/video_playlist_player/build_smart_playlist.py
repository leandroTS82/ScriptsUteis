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

USE_GROQ = True  # 🔥 True = usa Groq | False = 100% OFFLINE

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}
SRT_EXTENSIONS = {".srt"}

VIDEO_PATHS = [
    Path(r"C:\Users\leand\Desktop\wordbank")
]

HISTORY_VIDEO_PATHS = [
    Path(r"C:\Users\leand\Desktop\wordbank\Histories")
]

TERMS_PATHS = [
    Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\movies_processed"),
    Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Histories\NewHistory\subtitles"),
    Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Uploaded"),
]

PLAYLIST_OUTPUT_PATH = Path(r"C:\Users\leand\Desktop\wordbank\01-smart_playlists")
# ======================================================
# GROQ CONFIG (APENAS SE USE_GROQ = True)
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
# GROQ (OPCIONAL)
# ======================================================

def get_next_groq_key():
    for _ in range(len(GROQ_KEYS)):
        key = next(_groq_key_cycle).get("key", "")
        if key.startswith("gsk_"):
            return key
    raise RuntimeError("Nenhuma GROQ key válida.")

def groq(prompt: str) -> str:
    for _ in range(len(GROQ_KEYS)):
        try:
            key = get_next_groq_key()
            log("      🤖 Consultando Groq...")
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
                timeout=8
            )

            if res.status_code == 429:
                continue

            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]

        except Exception:
            continue

    raise RuntimeError("Groq indisponível")

# ======================================================
# EXTRAÇÃO DE TEXTO
# ======================================================

def extract_text_from_json(path: Path):
    texts = []
    nome_arquivo = None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            nome_arquivo = data.get("nome_arquivos")

            for v in data.values():
                if isinstance(v, str):
                    texts.append(v)
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            for val in item.values():
                                if isinstance(val, str):
                                    texts.append(val)

    except Exception:
        pass

    return nome_arquivo, " ".join(texts).lower()

def extract_text_from_srt(path: Path) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        return " ".join(
            line.strip()
            for line in lines
            if not re.match(r"^\d+$", line.strip())
            and "-->" not in line
        ).lower()

    except Exception:
        return ""

# ======================================================
# RELEVÂNCIA
# ======================================================

def is_relevant(term: str, content: str, filename: str) -> bool:
    term = term.lower()

    if term in filename.lower():
        log("      ✅ Termo no nome do arquivo")
        return True

    if term not in content:
        log("      ❌ Termo não encontrado no conteúdo")
        return False

    if not USE_GROQ:
        log("      📴 OFFLINE → termo encontrado no conteúdo")
        return True

    try:
        prompt = f"""
Term: "{term}"

Content:
\"\"\"
{content[:3000]}
\"\"\"

Is this content useful for studying the term?
Answer ONLY true or false.
"""
        result = groq(prompt).strip().lower()
        return "true" in result

    except Exception:
        log("      ⚠ Fallback OFFLINE aplicado")
        return True

# ======================================================
# PRIORIDADE
# ======================================================

def priority_key(video: Path, term: str, content: str):
    name = video.stem.lower()
    return (
        0 if term in name else 1,
        len(name),
        0 if term in content else 1
    )

# ======================================================
# PLAYLIST
# ======================================================

def write_playlist(videos, mode, meta, part_index=None, base_dir=None):
    output_dir = base_dir or PLAYLIST_OUTPUT_PATH
    output_dir.mkdir(parents=True, exist_ok=True)

    parts = ["play", mode]

    if "term" in meta:
        parts.append(f"term_{meta['term']}")

    if "from" in meta:
        parts.append(f"from_{meta['from']}")

    if "to" in meta:
        parts.append(f"to_{meta['to']}")

    if meta.get("histories"):
        parts.append("with_histories")

    if part_index is not None:
        parts.append(f"part_{part_index}")

    name = "_".join(parts)
    path = output_dir / f"{name}.m3u"

    with open(path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for v in videos:
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
    srts = get_all_srts(HISTORY_VIDEO_PATHS) if include_histories else []

    log("\nOpções:")
    log("1 - Data específica")
    log("2 - Intervalo de datas")
    log("3 - Termo ou sentido")

    option = input("Escolha (1/2/3): ").strip()
    selected = []
    meta = {"histories": include_histories}
    mode = None

    # ==================================================
    # OPÇÃO 1 — DATA ESPECÍFICA
    # ==================================================
    if option == "1":
        d = ask_date("Informe a data")
        mode = "date"
        meta["from"] = normalize_date(d)

        selected = [
            v for v in videos
            if datetime.fromtimestamp(v.stat().st_mtime).date() == d.date()
        ]

    # ==================================================
    # OPÇÃO 2 — INTERVALO
    # ==================================================
    elif option == "2":
        d1 = ask_date("Data inicial")
        d2 = ask_date("Data final")
        mode = "range"
        meta["from"] = normalize_date(d1)
        meta["to"] = normalize_date(d2)

        selected = [
            v for v in videos
            if d1 <= datetime.fromtimestamp(v.stat().st_mtime) <= d2
        ]

    # ==================================================
    # OPÇÃO 3 — TERMO / SENTIDO
    # ==================================================
    elif option == "3":
        term = input("Informe o termo/sentido: ").strip().lower()
        mode = "term"
        meta["term"] = term
        candidates = {}

        log("\n📄 Analisando JSONs...\n")
        for f in TERMS_PATHS[0].glob("*.json"):
            log(f"   ▶ {f.name}")
            nome_arquivo, content = extract_text_from_json(f)
            ref = nome_arquivo or f.stem

            if content and is_relevant(term, content, ref):
                candidates[ref] = content

        log("\n📜 Analisando SRTs...\n")
        for srt in srts:
            base = srt.stem.split(".")[0]
            log(f"   ▶ {srt.name}")
            content = extract_text_from_srt(srt)

            if content and is_relevant(term, content, base):
                candidates[base] = content

        selected = [
            v for v in videos
            if v.stem in candidates
        ]

        selected.sort(
            key=lambda v: priority_key(v, term, candidates.get(v.stem, ""))
        )

    else:
        log("❌ Opção inválida")
        return

    if not selected:
        log("⚠ Nenhum vídeo encontrado")
        return

    # ==================================================
    # PARTICIONAMENTO DA PLAYLIST
    # ==================================================

    # Se for busca por termo, preparar pasta do termo
    term_output_dir = None
    if mode == "term":
        term_output_dir = PLAYLIST_OUTPUT_PATH / meta["term"]

    # Se só houver 1 vídeo, NÃO perguntar
    if len(selected) == 1:
        write_playlist(selected, mode, meta, base_dir=term_output_dir)
        log("\n✅ Processo finalizado com sucesso")
        return

    if ask_yes_no("Deseja particionar a playlist?"):
        size = int(input("Quantos vídeos por playlist?: ").strip())
        parts = [
            selected[i:i + size]
            for i in range(0, len(selected), size)
        ]

        for idx, chunk in enumerate(parts, 1):
            write_playlist(
                chunk,
                mode,
                meta,
                part_index=idx,
                base_dir=term_output_dir
            )
    else:
        write_playlist(selected, mode, meta, base_dir=term_output_dir)

    log("\n✅ Processo finalizado com sucesso")

# ======================================================
# ENTRYPOINT
# ======================================================

if __name__ == "__main__":
    main()
