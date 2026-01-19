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
    Path(r"./01-Vídeos Inglês Leandrinho/wordbank")
]

HISTORY_VIDEO_PATHS = [
    Path(r"./01-Vídeos Inglês Leandrinho/Histories")
]

TERMS_PATHS = [
    Path("./Json_files")
]

PLAYLIST_OUTPUT_PATH = Path("./01-smart_playlists")

# ======================================================
# RANDOM PLAYLIST CONFIG (ISOLADO)
# ======================================================

RANDOM_STATS_JSON = Path("./random_playlist_stats.json")
RANDOM_PERCENT_USED = 0.30   # 30% itens já usados
RANDOM_PERCENT_NEW  = 0.70   # 70% itens novos

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
    # Ex: "work, play  ,  study" -> ["work", "play", "study"]
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
                timeout=10
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
# TERM EXPANSION (INTELIGÊNCIA EXTRA)
# ======================================================

def _naive_variations(term: str):
    """
    Fallback OFFLINE simples (não muda o CORE; apenas garante usabilidade se o Groq falhar).
    """
    t = term.strip().lower()
    if not t:
        return []
    variations = {t}

    # heurísticas leves
    if len(t) > 2:
        variations.add(t + "s")
        variations.add(t + "ed")
        variations.add(t + "ing")
        # tentativa de "y" -> "ies"
        if t.endswith("y") and len(t) > 3:
            variations.add(t[:-1] + "ies")

    # sem espaços duplicados
    return sorted(v for v in variations if v)

def translate_terms_to_english_if_needed(terms):
    """
    Recebe lista de termos (podem estar em PT ou EN).
    Se USE_GROQ=True, traduz PT → EN mantendo frases.
    Retorna lista em inglês.
    """
    if not terms:
        return terms

    if not USE_GROQ:
        return terms  # OFFLINE: não traduz, mantém como está

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
            cleaned = []
            for t in translated:
                if isinstance(t, str) and t.strip():
                    cleaned.append(t.strip().lower())
            return cleaned if cleaned else terms

        return terms

    except Exception:
        log("      ⚠ Falha ao traduzir termos PT→EN → usando termos originais")
        return terms

def expand_terms_with_groq(terms):
    """
    Recebe lista base (ex: ["work", "play"]) e retorna lista expandida com:
    variações gramaticais, expressões, chunks e usos relacionados.
    """
    base_terms = [t.strip().lower() for t in terms if t.strip()]
    if not base_terms:
        return []

    # OFFLINE
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
    - Return common collocations / chunks (e.g., "work out", "at work", "work on", "work hard").
    - Return useful related expressions/usages (phrasal verbs, fixed phrases).
    - Return relevant synonyms when they are commonly interchangeable in real usage (e.g., "job", "task", "duty" for "work"; "stand up" ↔ "get up").
    - Keep items short (1 to 4 words).
    - Output only JSON (no markdown, no extra text).
    - Deduplicate and keep it practical for substring search in subtitles and JSON content.

Base terms: {json.dumps(base_terms, ensure_ascii=False)}
"""
        raw = groq(prompt).strip()

        # tenta extrair JSON array mesmo se vier algum lixo ao redor
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1 and end > start:
            raw = raw[start:end + 1]

        arr = json.loads(raw)
        if isinstance(arr, list):
            cleaned = []
            for x in arr:
                if isinstance(x, str):
                    s = x.strip().lower()
                    if s:
                        cleaned.append(s)

            # garante que os termos originais estejam presentes
            merged = set(cleaned)
            for t in base_terms:
                merged.add(t)

            return sorted(merged)

        # fallback se não for lista
        expanded = set()
        for t in base_terms:
            expanded.update(_naive_variations(t))
        return sorted(expanded)

    except Exception:
        log("      ⚠ Falha ao expandir termos com Groq → Fallback OFFLINE aplicado")
        expanded = set()
        for t in base_terms:
            expanded.update(_naive_variations(t))
        return sorted(expanded)

# ======================================================
# RELEVÂNCIA
# ======================================================

def is_relevant_any(terms, content: str, filename: str) -> bool:
    """
    Mantém o CORE: primeiro tenta nome, depois conteúdo;
    se USE_GROQ, valida 'utilidade de estudo' (true/false).
    """
    if not terms:
        return False

    filename_l = (filename or "").lower()
    content_l = (content or "").lower()

    # 1) match direto no nome do arquivo (rápido)
    for t in terms:
        if t and t in filename_l:
            log("      ✅ Termo no nome do arquivo")
            return True

    # 2) se nenhum termo aparecer no conteúdo, descartamos
    found_in_content = any(t and t in content_l for t in terms)
    if not found_in_content:
        log("      ❌ Termo não encontrado no conteúdo")
        return False

    # 3) OFFLINE: se apareceu no conteúdo, vale
    if not USE_GROQ:
        log("      📴 OFFLINE → termo encontrado no conteúdo")
        return True

    # 4) ONLINE: pergunta ao Groq se é útil para estudo
    try:
        prompt = f"""
Terms: {json.dumps(terms[:60], ensure_ascii=False)}

Content:
\"\"\"
{content_l[:3000]}
\"\"\"

Is this content useful for studying ANY of these terms?
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

def priority_key(video: Path, terms, content: str):
    name = video.stem.lower()
    # prioridade: termo no nome (qualquer) -> nome menor -> termo no conteúdo (qualquer)
    in_name = any(t in name for t in terms if t)
    in_content = any(t in (content or "") for t in terms if t)
    return (
        0 if in_name else 1,
        len(name),
        0 if in_content else 1
    )

# ======================================================
# RANDOM PLAYLIST HELPERS (ISOLADO)
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
    """
    Seleção aleatória ponderada sem reposição.
    """
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
# PLAYLIST
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
            title = v.stem  # 👈 título amigável (nome do vídeo)
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
    log("3 - Termo ou sentido")
    log("4 - Playlist aleatória")

    option = input("Escolha (1/2/3/4): ").strip()
    selected = []
    mode = None

    # ==================================================
    # OPÇÃO 1 — DATA ESPECÍFICA
    # ==================================================
    if option == "1":
        d = ask_date("Informe a data")
        mode = "data"
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
        mode = "periodo"
        selected = [
            v for v in videos
            if d1 <= datetime.fromtimestamp(v.stat().st_mtime) <= d2
        ]

    # ==================================================
    # OPÇÃO 3 — TERMO (COM INTELIGÊNCIA EXTRA + MULTI-TERM)
    # ==================================================
    elif option == "3":
        raw = input("Informe o termo/sentido: ").strip()
        base_terms = split_terms(raw)

        if not base_terms:
            log("❌ Nenhum termo informado")
            return

        mode = "termo"

        log("\n🌎 Verificando idioma e traduzindo termos se necessário...")
        translated_terms = translate_terms_to_english_if_needed(base_terms)

        log(f"📝 Termos após tradução: {', '.join(translated_terms)}")

        log("\n🧠 Expandindo termos para tornar a busca mais eficiente...")
        expanded_terms = expand_terms_with_groq(translated_terms)

        # feedback amigável (sem poluir demais)
        if expanded_terms:
            preview = expanded_terms[:20]
            more = len(expanded_terms) - len(preview)
            log(f"✅ Termos base: {', '.join(base_terms)}")
            log(f"✅ Variações/chunks detectados: {', '.join(preview)}" + (f" ... (+{more})" if more > 0 else ""))
        else:
            expanded_terms = base_terms
            log("⚠ Não foi possível expandir termos; usando termos base.")

        candidates = {}

        # JSON terms
        for f in TERMS_PATHS[0].glob("*.json"):
            nome_arquivo, content = extract_text_from_json(f)
            ref = nome_arquivo or f.stem
            if content and is_relevant_any(expanded_terms, content, ref):
                candidates[ref] = content

        # SRT histories
        for srt in srts:
            base = srt.stem.split(".")[0]
            content = extract_text_from_srt(srt)
            if content and is_relevant_any(expanded_terms, content, base):
                candidates[base] = content

        selected = [v for v in videos if v.stem in candidates]
        selected.sort(key=lambda v: priority_key(v, expanded_terms, candidates.get(v.stem, "")))

    # ==================================================
    # OPÇÃO 4 — PLAYLIST ALEATÓRIA
    # ==================================================
    elif option == "4":
        mode = "random"
        qty = safe_int("Quantidade de vídeos na playlist: ", default=10, min_value=1)

        histories = get_all_videos(HISTORY_VIDEO_PATHS) if include_histories else []
        all_media = videos + histories

        if not all_media:
            log("⚠ Nenhum vídeo encontrado nas pastas configuradas.")
            return

        state = load_random_state(all_media)

        new_items = [Path(k) for k, v in state.items() if v.get("count", 0) == 0]
        used_items = [Path(k) for k, v in state.items() if v.get("count", 0) > 0]

        random.shuffle(new_items)

        qty_new = int(qty * RANDOM_PERCENT_NEW)
        qty_used = qty - qty_new

        selected_new = new_items[:qty_new]

        # 🔥 Seleção ponderada por menor contagem (mais justo)
        used_weights = [
            1 / (state[str(p.resolve())].get("count", 0) + 1)
            for p in used_items
        ]

        selected_used = weighted_sample(used_items, used_weights, qty_used)

        selected = selected_new + selected_used
        random.shuffle(selected)

        for v in selected:
            state[str(v.resolve())]["count"] = state[str(v.resolve())].get("count", 0) + 1

        save_random_state(state)

        # ========= FEEDBACK FINAL =========
        log("\n📊 ESTATÍSTICAS DA PLAYLIST ALEATÓRIA")
        log(f"📁 Total de itens no JSON: {len(state)}")
        log("🎯 Vídeos selecionados nesta execução:")
        for v in selected:
            log(f"   - {v.name} → contador: {state[str(v.resolve())]['count']}")

    else:
        log("❌ Opção inválida")
        return

    if not selected:
        log("⚠ Nenhum vídeo encontrado")
        return

    base_dir = PLAYLIST_OUTPUT_PATH / mode / (custom_name or "default")

    # Mantém o CORE: no modo 1/2/3, pergunta de particionamento
    # No modo random, gera direto (mais simples e consistente com seu 01PlayRandom.py)
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
