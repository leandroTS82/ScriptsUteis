"""
====================================================================================
Classificador de Vídeos por História — EXTRAÇÃO DIRETA DAS LEGENDAS
====================================================================================

REGRAS:
- Termos são extraídos diretamente das legendas (.en.srt)
- Não depende de IA (Groq NÃO é usado)
- Vídeos MakeMovie podem estar em múltiplas pastas
- Podem existir com ou sem prefixo 'uploaded_'
- Apenas histórias COM termos são classificadas
- Story + termos ficam na MESMA pasta
- Arquivos são SEMPRE COPIADOS

====================================================================================
"""

import os
import json
import shutil
import re
import argparse
from typing import Dict, List, Set, Optional

# =========================================================
# CONFIGURAÇÕES (PATHS MANTIDOS)
# =========================================================

MAKEMOVIE_VIDEO_PATHS = [
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Videos",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Uploaded",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\EnableToYoutubeUpload",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Youtube_Upload_Faulty_File",
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\20251211_Som com qualidade ruim"
]

STORIES_VIDEO_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Histories\NewHistory"
STORIES_SUBTITLE_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - VideosGeradosPorScript\Histories\NewHistory\subtitles"

OUTPUT_BASE = "./output"
CLASSIFIED_BASE = os.path.join(OUTPUT_BASE, "ClassifiedsHistories")

VIDEO_EXTENSIONS = (".mp4", ".mkv", ".avi")

# =========================================================
# UTILIDADES
# =========================================================

def log(msg: str):
    print(msg)

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def normalize_video_name(filename: str) -> str:
    base = os.path.splitext(filename)[0]
    if base.startswith("uploaded_"):
        base = base[len("uploaded_"):]
    return base.lower()

def extract_story_id_from_subtitle(filename: str) -> Optional[str]:
    name = filename.lower()
    if ".en." in name:
        return name.split(".en.")[0]
    if name.endswith(".en"):
        return name[:-3]
    return None

# =========================================================
# FASE 0 — INDEXAÇÃO DOS VÍDEOS MAKEMOVIE
# =========================================================

def build_video_index(paths: List[str]) -> Dict[str, str]:
    log("\n🔹 FASE 0 — Indexando vídeos MakeMovie")
    index: Dict[str, str] = {}

    for base_path in paths:
        if not os.path.isdir(base_path):
            continue

        for root, _, files in os.walk(base_path):
            for f in files:
                if not f.lower().endswith(VIDEO_EXTENSIONS):
                    continue

                key = normalize_video_name(f)
                index.setdefault(key, os.path.join(root, f))

    log(f"✅ Vídeos indexados: {len(index)}")
    return index

# =========================================================
# FASE 1 — EXTRAÇÃO DE TERMOS DA LEGENDA
# =========================================================

def extract_terms_from_subtitle(path: str) -> Set[str]:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # remove timestamps e números
    content = re.sub(r"\d+\n\d{2}:\d{2}:\d{2},\d{3} --> .*", " ", content)
    content = normalize(content)

    words = content.split()
    terms: Set[str] = set()

    # unigrams
    terms.update(words)

    # bigrams
    terms.update(
        f"{a} {b}"
        for a, b in zip(words, words[1:])
    )

    return terms

# =========================================================
# FASE 2 — INDEXAÇÃO DAS HISTÓRIAS
# =========================================================

def build_stories(limit: Optional[int]) -> List[Dict]:
    log("\n🔹 FASE 1 — Indexando histórias")
    stories = []

    subtitles = {}
    for f in os.listdir(STORIES_SUBTITLE_PATH):
        sid = extract_story_id_from_subtitle(f)
        if sid:
            subtitles[sid] = os.path.join(STORIES_SUBTITLE_PATH, f)

    for file in os.listdir(STORIES_VIDEO_PATH):
        if not file.lower().endswith(VIDEO_EXTENSIONS):
            continue

        sid = os.path.splitext(file)[0]
        subtitle = subtitles.get(sid)

        if not subtitle:
            continue

        stories.append({
            "story_id": sid,
            "video_path": os.path.join(STORIES_VIDEO_PATH, file),
            "subtitle_path": subtitle
        })

        if limit and len(stories) >= limit:
            break

    log(f"✅ Histórias encontradas: {len(stories)}")
    return stories

# =========================================================
# FASE 3 — MATCHING TERMOS ↔ VÍDEOS
# =========================================================

def match_terms_to_videos(stories: List[Dict], video_index: Dict[str, str]) -> List[Dict]:
    log("\n🔹 FASE 2 — Relacionando termos aos vídeos")
    result = []

    for story in stories:
        extracted_terms = extract_terms_from_subtitle(story["subtitle_path"])

        matched_videos = {
            base for base in video_index
            if base in extracted_terms
        }

        if not matched_videos:
            continue

        log(f"📖 {story['story_id']} → {len(matched_videos)} termo(s)")

        result.append({
            "story_id": story["story_id"],
            "story_video_path": story["video_path"],
            "terms_video_bases": sorted(matched_videos)
        })

    log(f"✅ Histórias com termos: {len(result)}")
    return result

# =========================================================
# FASE 4 — MATERIALIZAÇÃO
# =========================================================

def materialize(mapping: List[Dict], video_index: Dict[str, str]):
    log("\n🔹 FASE 3 — Copiando arquivos")
    ensure_dir(CLASSIFIED_BASE)

    for item in mapping:
        story_dir = os.path.join(CLASSIFIED_BASE, item["story_id"])
        ensure_dir(story_dir)

        shutil.copy2(
            item["story_video_path"],
            os.path.join(story_dir, os.path.basename(item["story_video_path"]))
        )

        for base in item["terms_video_bases"]:
            src = video_index.get(base)
            if not src:
                continue

            dest = os.path.join(story_dir, os.path.basename(src))
            if not os.path.exists(dest):
                shutil.copy2(src, dest)

    log("✅ Classificação concluída")

# =========================================================
# MAIN
# =========================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-limit", type=int)
    args = parser.parse_args()

    ensure_dir(OUTPUT_BASE)

    video_index = build_video_index(MAKEMOVIE_VIDEO_PATHS)
    stories = build_stories(args.limit)
    mapping = match_terms_to_videos(stories, video_index)

    with open(os.path.join(OUTPUT_BASE, "stories_terms_map.json"), "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    materialize(mapping, video_index)

    log("\n  PROCESSO FINALIZADO COM SUCESSO")

if __name__ == "__main__":
    main()
