from pathlib import Path
from datetime import datetime
import json
import requests
import os
import sys
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
RANDOM_PERCENT_RECENT = 0.70
RANDOM_PERCENT_OLD = 0.30
RECENT_DAYS_THRESHOLD = 30

# ======================================================
# GROQ CONFIG
# ======================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from groq_keys_loader import GROQ_KEYS

# ================================================================================
# CONFIG - GROQ MULTI KEYS (ROTATION / RANDOM)
# ================================================================================
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
# GROQ
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
                timeout=20
            )

            if res.status_code == 429:
                continue

            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]

        except Exception:
            continue

    raise RuntimeError("Groq indisponível")

# ======================================================
# DATA DE ARQUIVO (FILESYSTEM)
# ======================================================

def get_modified_datetime(path: Path) -> datetime:
    """Retorna a data de última modificação do arquivo (filesystem)."""
    return datetime.fromtimestamp(os.path.getmtime(path))

def get_created_datetime(path: Path) -> datetime:
    """Retorna a data de criação do arquivo (filesystem, usa ctime no Windows)."""
    return datetime.fromtimestamp(os.path.getctime(path))

def get_best_datetime(path: Path) -> datetime:
    """
    Retorna a data mais antiga entre mtime e ctime.
    No Windows, ctime = data de criação. No Linux, ctime = última mudança de metadado.
    Usar a mais antiga evita o problema de cópias que 'resetam' a data de criação.
    """
    mtime = datetime.fromtimestamp(os.path.getmtime(path))
    ctime = datetime.fromtimestamp(os.path.getctime(path))
    return min(mtime, ctime)

# ======================================================
# EXTRAÇÃO DE TEXTO / JSON
# ======================================================

def extract_text_from_json(path: Path):
    """
    Extrai nome_arquivos e conteúdo textual de um JSON de card de vocabulário.
    Retorna (nome_arquivo, texto_concatenado).
    """
    nome_arquivo = None
    texts = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return None, ""

        nome_arquivo = data.get("nome_arquivos") or path.stem

        # introducao
        intro = data.get("introducao", "")
        if intro:
            texts.append(intro)

        # WORD_BANK: array de arrays de objetos {lang, text, pause}
        word_bank = data.get("WORD_BANK", [])
        for group in word_bank:
            if isinstance(group, list):
                for item in group:
                    if isinstance(item, dict):
                        t = item.get("text", "")
                        if t:
                            texts.append(t)
            elif isinstance(group, dict):
                t = group.get("text", "")
                if t:
                    texts.append(t)

        # _known_terms_context
        ktc = data.get("_known_terms_context", {})
        for term in ktc.get("terms_used", []):
            if term:
                texts.append(term)

        # varredura genérica em outros campos string
        for key, val in data.items():
            if key in ("nome_arquivos", "introducao", "WORD_BANK", "_known_terms_context", "repeat_each"):
                continue
            if isinstance(val, str) and val:
                texts.append(val)

    except Exception:
        return None, ""

    return nome_arquivo, " ".join(texts).lower()


def extract_main_term_from_json(path: Path) -> str:
    """
    Extrai o termo principal do JSON: primeiro item EN do primeiro grupo de WORD_BANK.
    Ex: {"WORD_BANK": [[{"lang":"en","text":"30-day threshold",...}]]} -> "30-day threshold"
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        word_bank = data.get("WORD_BANK", [])
        for group in word_bank:
            if isinstance(group, list):
                for item in group:
                    if isinstance(item, dict) and item.get("lang") == "en":
                        term = item.get("text", "").strip()
                        if term:
                            return term.lower()
    except Exception:
        pass
    return ""


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
# GROQ — ANÁLISE SEMÂNTICA EM LOTE (OPÇÃO 3)
# ======================================================

def translate_terms_to_english_if_needed(terms):
    """Traduz termos PT → EN usando Groq. Se offline, retorna os termos originais."""
    if not terms or not USE_GROQ:
        return terms

    try:
        prompt = f"""
Translate the following terms to natural English.
Rules:
- If a term is already in English, keep it unchanged.
- Preserve meaning and intent (imperatives, phrases, expressions).
- Return ONLY a valid JSON array of strings.
- No markdown, no extra text.

Terms: {json.dumps(terms, ensure_ascii=False)}
"""
        raw = groq(prompt).strip()
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1 and end > start:
            raw = raw[start:end + 1]
        translated = json.loads(raw)
        if isinstance(translated, list):
            cleaned = [t.strip().lower() for t in translated if isinstance(t, str) and t.strip()]
            return cleaned if cleaned else terms
        return terms
    except Exception:
        log("      ⚠ Falha ao traduzir termos PT→EN → usando termos originais")
        return terms


def expand_terms_with_groq(terms):
    """Expande termos base com variações gramaticais, chunks e sinônimos via Groq."""
    base_terms = [t.strip().lower() for t in terms if t.strip()]
    if not base_terms:
        return []

    if not USE_GROQ:
        expanded = set()
        for t in base_terms:
            expanded.update(_naive_variations(t))
        return sorted(expanded)

    try:
        prompt = f"""
You are helping build a study playlist search.
Given the base terms below, return ONLY a valid JSON array of strings.

Rules:
- Return grammatical variations (e.g., work, works, worked, working).
- Return common collocations / chunks (e.g., "work out", "at work", "work on").
- Return related expressions, phrasal verbs, and fixed phrases.
- Return relevant synonyms when commonly interchangeable in real usage.
- Keep items short (1 to 4 words).
- Output only JSON (no markdown, no extra text).
- Deduplicate and keep it practical for substring search.

Base terms: {json.dumps(base_terms, ensure_ascii=False)}
"""
        raw = groq(prompt).strip()
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1 and end > start:
            raw = raw[start:end + 1]
        arr = json.loads(raw)
        if isinstance(arr, list):
            merged = set(t.strip().lower() for t in arr if isinstance(t, str) and t.strip())
            for t in base_terms:
                merged.add(t)
            return sorted(merged)
    except Exception:
        log("      ⚠ Falha ao expandir termos → Fallback OFFLINE")

    expanded = set()
    for t in base_terms:
        expanded.update(_naive_variations(t))
    return sorted(expanded)


def _naive_variations(term: str):
    t = term.strip().lower()
    if not t:
        return []
    variations = {t}
    if len(t) > 2:
        variations.add(t + "s")
        variations.add(t + "ed")
        variations.add(t + "ing")
        if t.endswith("y") and len(t) > 3:
            variations.add(t[:-1] + "ies")
    return sorted(v for v in variations if v)


def groq_batch_relevance(query: str, candidates: list[dict]) -> list[str]:
    """
    Usa Groq para analisar em lote quais arquivos JSON são relevantes para a query.

    candidates: lista de dicts com keys: nome_arquivo, main_term, content_snippet
    Retorna lista de nome_arquivo considerados relevantes.
    """
    if not candidates:
        return []

    # monta sumário compacto para o prompt
    items = []
    for c in candidates:
        items.append({
            "id": c["nome_arquivo"],
            "term": c["main_term"],
            "snippet": c["content_snippet"][:300]
        })

    try:
        prompt = f"""
You are a language study playlist curator.

USER REQUEST: "{query}"

Below is a list of English vocabulary study cards. Each card has:
- "id": the file identifier (use this in your answer)
- "term": the main English term taught in that card
- "snippet": a short excerpt of the card content

Your task: identify which cards are relevant to the user's request.
Be generous — include cards that teach vocabulary in the same category, 
grammatical pattern, or semantic field as requested.

Examples:
- "irregular verbs" → include cards that teach verbs with irregular past forms (go/went, bring/brought, etc.)
- "phrasal verbs with get" → include cards that use "get" as a base verb with particles
- "feelings and emotions" → include cards about emotional states, adjectives, reactions
- "money expressions" → include cards about financial terms, payments, costs

Return ONLY a valid JSON array of "id" strings for the relevant cards.
No explanation, no markdown, just the array.

Cards:
{json.dumps(items, ensure_ascii=False)}
"""
        raw = groq(prompt).strip()
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1 and end > start:
            raw = raw[start:end + 1]
        result = json.loads(raw)
        if isinstance(result, list):
            return [r for r in result if isinstance(r, str)]
    except Exception as e:
        log(f"      ⚠ Falha no batch Groq: {e}")

    return []


# ======================================================
# RELEVÂNCIA — OPÇÃO 3
# ======================================================

GROQ_BATCH_SIZE = 30  # quantos cards por chamada ao Groq


def find_relevant_by_term(query: str, all_json_files: list[Path], srts: list[Path]) -> dict:
    """
    Busca arquivos relevantes à query usando:
    1. Expansão de termos (fallback rápido de substring)
    2. Análise semântica em lote pelo Groq

    Retorna dict {nome_arquivo: content} para os relevantes.
    """
    log("\n🌎 Verificando idioma e traduzindo termos se necessário...")
    base_terms = split_terms(query)
    translated_terms = translate_terms_to_english_if_needed(base_terms)
    log(f"📝 Termos após tradução: {', '.join(translated_terms)}")

    log("\n🧠 Expandindo termos para busca por substring...")
    expanded_terms = expand_terms_with_groq(translated_terms)
    if expanded_terms:
        preview = expanded_terms[:20]
        more = len(expanded_terms) - len(preview)
        log(f"✅ Termos base: {', '.join(base_terms)}")
        log(f"✅ Variações/chunks: {', '.join(preview)}" + (f" ... (+{more})" if more > 0 else ""))
    else:
        expanded_terms = base_terms

    # ---- FASE 1: candidatos por substring (rápido, sem custo de API) ----
    log("\n🔍 Fase 1 — Filtragem rápida por substring...")
    substring_candidates = {}  # nome_arquivo -> {main_term, content}

    for json_path in all_json_files:
        nome_arquivo, content = extract_text_from_json(json_path)
        if not nome_arquivo:
            nome_arquivo = json_path.stem
        main_term = extract_main_term_from_json(json_path)

        # match no nome do arquivo ou no conteúdo
        ref_l = nome_arquivo.lower()
        hit = any(t and (t in ref_l or t in content) for t in expanded_terms)
        if hit:
            substring_candidates[nome_arquivo] = {
                "main_term": main_term,
                "content": content,
                "path": json_path
            }

    # SRTs
    for srt in srts:
        base = srt.stem.split(".")[0]
        content = extract_text_from_srt(srt)
        hit = any(t and (t in base.lower() or t in content) for t in expanded_terms)
        if hit:
            substring_candidates[base] = {
                "main_term": base,
                "content": content,
                "path": srt
            }

    log(f"   → {len(substring_candidates)} candidatos encontrados por substring")

    # ---- FASE 2: análise semântica Groq em lote ----
    if not USE_GROQ:
        log("   📴 OFFLINE → usando apenas resultado da fase 1")
        return {k: v["content"] for k, v in substring_candidates.items()}

    log("\n🤖 Fase 2 — Análise semântica Groq em lote...")

    # prepara todos os JSONs (mesmo os não encontrados na fase 1) para análise semântica
    # limita a 150 itens por eficiência (os mais relevantes primeiro)
    all_candidates_for_groq = []

    # prioridade: os que já passaram na fase 1
    for nome, info in substring_candidates.items():
        all_candidates_for_groq.append({
            "nome_arquivo": nome,
            "main_term": info["main_term"],
            "content_snippet": info["content"]
        })

    # complementa com os demais JSONs (fase semântica pode pegar o que substring perdeu)
    already = set(substring_candidates.keys())
    for json_path in all_json_files:
        nome_arquivo, content = extract_text_from_json(json_path)
        if not nome_arquivo:
            nome_arquivo = json_path.stem
        if nome_arquivo not in already:
            main_term = extract_main_term_from_json(json_path)
            all_candidates_for_groq.append({
                "nome_arquivo": nome_arquivo,
                "main_term": main_term,
                "content_snippet": content
            })

    # limita total
    all_candidates_for_groq = all_candidates_for_groq[:200]

    # chamadas em lote
    groq_relevant = set()
    batches = [
        all_candidates_for_groq[i:i + GROQ_BATCH_SIZE]
        for i in range(0, len(all_candidates_for_groq), GROQ_BATCH_SIZE)
    ]

    log(f"   → {len(batches)} lotes de até {GROQ_BATCH_SIZE} cards cada")

    for idx, batch in enumerate(batches, 1):
        log(f"   → Lote {idx}/{len(batches)} ({len(batch)} cards)...")
        relevant_ids = groq_batch_relevance(query, batch)
        groq_relevant.update(relevant_ids)
        log(f"      ✅ {len(relevant_ids)} relevantes neste lote")

    log(f"\n✅ Total após análise semântica: {len(groq_relevant)} cards relevantes")

    # monta resultado final: nome_arquivo -> content
    # reconstrói content para os encontrados só pelo Groq (não estavam na fase 1)
    result = {}
    nome_to_content = {k: v["content"] for k, v in substring_candidates.items()}

    # para itens só encontrados pelo Groq, reextrai content
    for item in all_candidates_for_groq:
        nome = item["nome_arquivo"]
        if nome in groq_relevant:
            result[nome] = nome_to_content.get(nome, item["content_snippet"])

    return result


# ======================================================
# PRIORIDADE
# ======================================================

def priority_key(video: Path, terms, content: str):
    name = video.stem.lower()
    in_name = any(t in name for t in terms if t)
    in_content = any(t in (content or "") for t in terms if t)
    return (
        0 if in_name else 1,
        len(name),
        0 if in_content else 1
    )

# ======================================================
# RANDOM PLAYLIST HELPERS
# ======================================================

def load_random_state(all_files):
    if RANDOM_STATS_JSON.exists():
        with open(RANDOM_STATS_JSON, "r", encoding="utf-8") as f:
            state = json.load(f)
    else:
        state = {}

    for f in all_files:
        key = str(f.resolve())
        if key not in state:
            state[key] = {
                "count": 0,
                "type": "history" if f.parent in HISTORY_VIDEO_PATHS else "video"
            }

    return state

def save_random_state(state):
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

    filename = custom_name or mode
    if part_index is not None:
        filename = f"{filename}_part_{part_index}"

    path = output_dir / f"{filename}.m3u"

    with open(path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for v in videos:
            title = v.stem
            f.write(f"#EXTINF:-1,{title}\n")
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
    if include_histories:
        videos += get_all_videos(HISTORY_VIDEO_PATHS)

    srts = get_all_srts(HISTORY_VIDEO_PATHS) if include_histories else []

    custom_name = None
    if ask_yes_no("Deseja dar um nome à playlist?"):
        custom_name = input("Insira o nome: ").strip()
        if ask_yes_no("Deseja adicionar data ao nome?"):
            today = datetime.now().strftime("%Y%m%d")
            custom_name = f"{today}_{custom_name}"

    log("\nOpções:")
    log("1 - Data específica")
    log("2 - Intervalo de datas")
    log("3 - Termo ou sentido (busca inteligente)")
    log("4 - Playlist aleatória")

    option = input("Escolha (1/2/3/4): ").strip()
    selected = []
    mode = None

    # ==================================================
    # OPÇÃO 1 — DATA ESPECÍFICA
    # Busca por data de modificação/criação do arquivo
    # ==================================================
    if option == "1":
        mode = "data"
        d = ask_date("Informe a data")
        target_date = d.date()

        log(f"\n🔍 Buscando vídeos da data {d.strftime('%d/%m/%Y')}...")

        matched = []
        for v in videos:
            file_date = get_best_datetime(v).date()
            if file_date == target_date:
                matched.append(v)
                log(f"   ✅ {v.name} | {file_date}")

        selected = matched
        log(f"\n📊 {len(selected)} vídeo(s) encontrado(s)")

    # ==================================================
    # OPÇÃO 2 — INTERVALO DE DATAS
    # Busca por data de modificação/criação do arquivo
    # ==================================================
    elif option == "2":
        mode = "periodo"
        d1 = ask_date("Data inicial")
        d2 = ask_date("Data final")

        # garante que d1 <= d2
        if d1 > d2:
            d1, d2 = d2, d1

        log(f"\n🔍 Buscando vídeos entre {d1.strftime('%d/%m/%Y')} e {d2.strftime('%d/%m/%Y')}...")

        matched = []
        for v in videos:
            file_dt = get_best_datetime(v)
            if d1 <= file_dt <= d2:
                matched.append(v)
                log(f"   ✅ {v.name} | {file_dt.strftime('%d/%m/%Y')}")

        # ordena por data crescente
        matched.sort(key=lambda v: get_best_datetime(v))
        selected = matched
        log(f"\n📊 {len(selected)} vídeo(s) encontrado(s)")

    # ==================================================
    # OPÇÃO 3 — TERMO/SENTIDO COM INTELIGÊNCIA GROQ
    # Análise semântica dos JSONs em lote
    # ==================================================
    elif option == "3":
        mode = "termo"
        raw = input("Informe o termo/sentido (ex: verbos irregulares, phrasal verbs, feelings): ").strip()

        if not raw:
            log("❌ Nenhum termo informado")
            return

        # coleta todos os JSONs disponíveis
        all_json_files = []
        for tp in TERMS_PATHS:
            if tp.exists():
                all_json_files.extend([
                    f for f in tp.iterdir()
                    if f.is_file() and f.suffix.lower() == ".json"
                ])

        log(f"\n📁 {len(all_json_files)} arquivos JSON encontrados para análise")

        # busca relevante (substring + Groq semântico)
        candidates = find_relevant_by_term(raw, all_json_files, srts)

        # filtra vídeos que têm correspondência nos candidatos
        # match por stem do vídeo == nome_arquivo do JSON
        selected = [v for v in videos if v.stem in candidates]

        # ordena: termo no nome > nome curto > termo no conteúdo
        expanded_for_sort = split_terms(raw)
        selected.sort(key=lambda v: priority_key(
            v, expanded_for_sort, candidates.get(v.stem, "")
        ))

        log(f"\n📊 {len(selected)} vídeo(s) selecionado(s) para a playlist")

    # ==================================================
    # OPÇÃO 4 — PLAYLIST ALEATÓRIA
    # ==================================================
    elif option == "4":
        mode = "random"
        qty = safe_int("Quantidade de vídeos na playlist: ", default=10, min_value=1)

        all_media = videos  # já inclui histories se o usuário quis

        if not all_media:
            log("⚠ Nenhum vídeo encontrado nas pastas configuradas.")
            return

        state = load_random_state(all_media)

        now = datetime.now()
        recent_items = []
        old_items = []

        for media in all_media:
            file_date = get_best_datetime(media)
            if (now - file_date).days <= RECENT_DAYS_THRESHOLD:
                recent_items.append(media)
            else:
                old_items.append(media)

        def split_by_usage(items):
            new, used = [], []
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
        log(f"📁 Total de itens monitorados: {len(state)}")
        log(f"📅 Threshold recente: {RECENT_DAYS_THRESHOLD} dias")
        log(f"🎯 Selecionados: {len(selected)}")

        for v in selected:
            key = str(v.resolve())
            file_date = get_best_datetime(v)
            days_old = (now - file_date).days
            categoria = "RECENTE" if days_old <= RECENT_DAYS_THRESHOLD else "ANTIGO"
            log(
                f"   - {v.name} | "
                f"data: {file_date.strftime('%d/%m/%Y')} | "
                f"{categoria} ({days_old} dias) | "
                f"contador: {state[key]['count']}"
            )

    else:
        log("❌ Opção inválida")
        return

    if not selected:
        log("⚠ Nenhum vídeo encontrado com os critérios informados.")
        return

    base_dir = PLAYLIST_OUTPUT_PATH / mode / (custom_name or "default")

    if mode != "random" and len(selected) > 1:
        if ask_yes_no("Deseja particionar a playlist?"):
            size = safe_int("Quantos vídeos por playlist?: ", default=25, min_value=1)
            parts = [selected[i:i + size] for i in range(0, len(selected), size)]
            for idx, chunk in enumerate(parts, 1):
                write_playlist(
                    chunk,
                    mode,
                    {},
                    part_index=idx,
                    base_dir=base_dir,
                    custom_name=custom_name or mode
                )
            log("\n✅ Processo finalizado com sucesso")
            return

    write_playlist(selected, mode, {}, base_dir=base_dir, custom_name=custom_name or mode)
    log("\n✅ Processo finalizado com sucesso")

# ======================================================
# ENTRYPOINT
# ======================================================

if __name__ == "__main__":
    main()