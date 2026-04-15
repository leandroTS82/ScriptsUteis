import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import json
import re

# ======================================================
# CONFIGURAÇÕES
# ======================================================

BASE_VIDEO_DIR = Path(r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - LeandrinhoMovies")
METADATA_PATH = BASE_VIDEO_DIR / "metadata.json"
OUTPUT_ROOT = Path(r"C:\Users\leand\Desktop\01-smart_playlists")

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}

# ======================================================
# LOG
# ======================================================

def log(msg: str) -> None:
    print(msg, flush=True)

# ======================================================
# METADATA (NOVO - SEM QUEBRAR SUA LÓGICA)
# ======================================================

def collect_video_metadata(source_dir: Path) -> dict:
    files_metadata = []

    for root, _, files in os.walk(source_dir):
        for file in files:
            if os.path.splitext(file)[1].lower() not in VIDEO_EXTENSIONS:
                continue

            full_path = os.path.join(root, file)
            stat = os.stat(full_path)

            files_metadata.append({
                "name": file,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

    return {"files": files_metadata}


def merge_metadata(existing: dict, new: dict) -> dict:
    existing_map = {f["name"].lower(): f for f in existing.get("files", [])}

    updated = 0
    added = 0

    for item in new.get("files", []):
        key = item["name"].lower()

        if key in existing_map:
            existing_map[key].update(item)
            updated += 1
        else:
            existing_map[key] = item
            added += 1

    log(f"🔄 Metadata atualizado: {updated} atualizados, {added} novos")

    return {"files": list(existing_map.values())}


def load_or_update_metadata(path: Path, base_dir: Path) -> dict:
    log("🔍 Indexando vídeos...")

    new_metadata = collect_video_metadata(base_dir)

    if not path.exists():
        log(f"⚠ metadata.json não encontrado em: {path.resolve()}")
        log("🔄 Criando metadata...")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(new_metadata, f, indent=2, ensure_ascii=False)

        log(f"✅ metadata.json criado ({len(new_metadata['files'])} arquivos)\n")
        return new_metadata

    with open(path, "r", encoding="utf-8") as f:
        existing = json.load(f)

    merged = merge_metadata(existing, new_metadata)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    log(f"✅ metadata.json atualizado ({len(merged['files'])} arquivos)\n")
    return merged

# ======================================================
# UTILS (INALTERADO)
# ======================================================

def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]+', "_", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name or "playlist"

def parse_flexible_date(value: str) -> datetime:
    value = value.strip()

    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", value):
        return datetime.strptime(value, "%d/%m/%Y")

    if re.fullmatch(r"\d{2}/\d{2}/\d{2}", value):
        return datetime.strptime(value, "%d/%m/%y")

    if re.fullmatch(r"\d{2}/\d{2}", value):
        day, month = map(int, value.split("/"))
        return datetime(datetime.now().year, month, day)

    raise ValueError("Data inválida")

def ask_date(prompt: str, allow_empty: bool = False):
    while True:
        raw = input(prompt).strip()

        # 🔥 PROTEÇÃO contra comando colado
        if raw.startswith("&") or "python.exe" in raw.lower():
            log("⚠ Entrada ignorada (comando detectado). Digite apenas a data.")
            continue

        if allow_empty and not raw:
            return None

        try:
            return parse_flexible_date(raw)
        except ValueError as ex:
            log(f"❌ {ex}")

def parse_iso_datetime(value):
    try:
        return datetime.fromisoformat(value)
    except:
        return None

def get_video_files(base_dir: Path):
    files = {}
    for f in base_dir.iterdir():
        if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
            files[f.name.lower()] = f
    return files

def extract_reference_date(item):
    m = parse_iso_datetime(item.get("modified_at"))
    if m:
        return m, "modified_at"

    c = parse_iso_datetime(item.get("created_at"))
    if c:
        return c, "created_at"

    return None, None

def is_in_period(target, start, end):
    return start.date() <= target.date() <= end.date()

def build_playlist_name(start, end):
    if start.date() == end.date():
        return f"playlist_{start.strftime('%Y%m%d')}"
    return f"playlist_{start.strftime('%Y%m%d')}_a_{end.strftime('%Y%m%d')}"

def write_m3u(videos, output):
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for v in videos:
            f.write(f"#EXTINF:-1,{v.stem}\n")
            f.write(str(v.resolve()) + "\n")

# ======================================================
# MAIN (APENAS 1 LINHA ALTERADA)
# ======================================================

def main():
    log("====================================")
    log("📅 DATE M3U GENERATOR")
    log("====================================\n")

    try:
        # 🔥 AQUI ESTÁ A MUDANÇA
        metadata = load_or_update_metadata(METADATA_PATH, BASE_VIDEO_DIR)

        available_videos = get_video_files(BASE_VIDEO_DIR)

        if not available_videos:
            log(f"⚠ Nenhum vídeo encontrado em: {BASE_VIDEO_DIR.resolve()}")
            return

        while True:
            start = ask_date("Data inicial: ")
            end = ask_date("Data final (Enter = mesma): ", True) or start

            selected = []

            for item in metadata.get("files", []):
                name = item.get("name")
                if not name:
                    continue

                file = available_videos.get(name.lower())
                if not file:
                    continue

                ref, source = extract_reference_date(item)
                if not ref:
                    continue

                if is_in_period(ref, start, end):
                    selected.append(file)

            if not selected:
                log("⚠ Nenhum vídeo encontrado")
                continue

            name = build_playlist_name(start, end)
            output = OUTPUT_ROOT / sanitize_filename(name) / "playlist.m3u"

            write_m3u(selected, output)

            log(f"\n✅ Playlist criada: {output}")
            log(f"🎯 Total: {len(selected)} vídeos")
            return

    except KeyboardInterrupt:
        log("\n⚠ Cancelado pelo usuário")
    except Exception as ex:
        log(f"❌ Erro: {ex}")

# ======================================================
# ENTRYPOINT
# ======================================================

if __name__ == "__main__":
    main()