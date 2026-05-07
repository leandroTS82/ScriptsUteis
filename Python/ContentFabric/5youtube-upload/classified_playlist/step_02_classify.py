"""
step_02_classify.py

Responsabilidades:
  1. Receber a INTENÇÃO do usuário (ex: "Past Continuous", "família", "fé")
  2. Se não houver nome/ID de playlist, pedir ao Groq para gerar um nome criativo
  3. Classificar os vídeos do contexto em batches via Groq
  4. Salvar e retornar o resultado
"""

import os
import sys
import json
import re
import random
from datetime import datetime
from itertools import cycle
import config

# ── Groq loader ───────────────────────────────────────────────────────────────
GROQ_LOADER_DIR = r"C:\dev\scripts\ScriptsUteis\Python"
if os.path.isdir(GROQ_LOADER_DIR) and GROQ_LOADER_DIR not in sys.path:
    sys.path.insert(0, GROQ_LOADER_DIR)

try:
    from groq_keys_loader import GROQ_KEYS
except ImportError:
    # fallback para desenvolvimento: define GROQ_API_KEY no ambiente
    _api_key = os.environ.get("GROQ_API_KEY", "")
    if not _api_key:
        raise RuntimeError(
            "groq_keys_loader não encontrado e GROQ_API_KEY não definida.\n"
            "Defina a variável de ambiente GROQ_API_KEY ou ajuste GROQ_LOADER_DIR."
        )
    GROQ_KEYS = [{"key": _api_key, "name": "env"}]

from groq import Groq  # pip install groq

# ── CONFIG ────────────────────────────────────────────────────────────────────

GROQ_MODEL      = config.GROQ_MODEL
MAX_RETRIES     = config.MAX_RETRIES
TIMEOUT_SECONDS = config.TIMEOUT_SECONDS
BATCH_SIZE      = config.BATCH_SIZE

# ── Groq key rotation ─────────────────────────────────────────────────────────

_groq_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))


def _get_client():
    key_info = next(_groq_key_cycle)
    return Groq(api_key=key_info["key"]), key_info["name"]


def _call_groq(messages: list[dict], label: str = "groq") -> str:
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        client, key_name = _get_client()
        try:
            print(f"    [Groq/{label}] tentativa {attempt} · key: {key_name}")
            resp = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=0.2,
                timeout=TIMEOUT_SECONDS,
            )
            return resp.choices[0].message.content.strip()
        except Exception as ex:
            last_error = ex
            print(f"    ⚠️  Falha tentativa {attempt}: {ex}")
    raise RuntimeError(f"Todas as tentativas Groq falharam. Último erro: {last_error}")


def _extract_json_array(text: str) -> str | None:
    match = re.search(r"\[.*\]", text, re.DOTALL)
    return match.group(0) if match else None


def _extract_json_object(text: str) -> str | None:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else None


# ── 1. Geração do nome da playlist ────────────────────────────────────────────

def generate_playlist_name(intention: str) -> str:
    """
    Pede ao Groq para gerar um nome criativo e conciso para a playlist,
    baseado na intenção fornecida pelo usuário.
    """
    print(f"\n  🤖 Gerando nome de playlist para intenção: '{intention}'...")

    messages = [
        {
            "role": "system",
            "content": (
                "You are a creative naming specialist for YouTube playlists focused on "
                "English learning content. "
                "Return ONLY a valid JSON object, no markdown, no explanation."
            ),
        },
        {
            "role": "user",
            "content": f"""
Generate a creative, concise, and attractive YouTube playlist name based on this intention:

Intention: "{intention}"

Rules:
- The name must clearly communicate the topic to English learners
- If the intention is a grammar topic (Past Simple, Past Continuous, etc.), keep it clear and direct
- If the intention is a theme (family, faith, technology), make it engaging and slightly poetic
- The name should be in English, but may include the Portuguese term in parentheses if it adds clarity
- Maximum 60 characters
- Do NOT use generic terms like "Playlist" or "Collection"

Return ONLY this JSON object:
{{
  "playlist_name": "...",
  "reason": "short explanation"
}}
""",
        },
    ]

    raw = _call_groq(messages, label="name-gen")
    json_text = _extract_json_object(raw)
    if not json_text:
        raise ValueError(f"Groq não retornou JSON para nome:\n{raw}")

    parsed = json.loads(json_text)
    name = parsed.get("playlist_name", "").strip()

    if not name:
        raise ValueError("Groq retornou nome vazio.")

    print(f"  ✅ Nome gerado: '{name}' — {parsed.get('reason', '')}")
    return name


# ── 2. Classificação em batch ─────────────────────────────────────────────────

def _build_classification_prompt(videos, intention, playlist_name):
    compact = [
        {
            "youtube_video_id": v.get("youtube_video_id"),
            "youtube_title": v.get("youtube_title"),
            "youtube_description": v.get("youtube_description"),
            "titleTheme": v.get("titleTheme"),
            "descriptionTheme": v.get("descriptionTheme"),
            "tags": v.get("tags", []),
            "playlists": v.get("playlists", []),
        }
        for v in videos
    ]

    return f"""
You are classifying existing YouTube videos from an English learning channel.

User intention:
"{intention}"

The intention can be:
- a grammar rule, e.g. Past Continuous, Present Perfect, modal verbs
- a semantic topic, e.g. family, work, health, faith, technology
- a learning goal, e.g. phrases for meetings, restaurant English, emotional vocabulary

Tasks:
1. Refine the user's intention into a clear playlist concept.
2. Generate a concise YouTube playlist title in English.
3. Classify each video.

Primary signals:
- titleTheme
- descriptionTheme
- youtube_title
- youtube_description
- tags

Rules:
- Include only videos clearly related to the intention.
- Be conservative.
- Do not include weak or indirect matches.
- Prefer semantic relevance over exact keyword matching.
- Confidence must be from 0.0 to 1.0.

Target playlist name:
"{playlist_name}"
Do not generate a different playlist name.
Use this exact playlist_name in the JSON response.

Return ONLY valid JSON:

{{
  "refined_intention": "...",
  "playlist_name": "...",
  "playlist_description": "...",
  "videos": [
    {{
      "youtube_video_id": "...",
      "include": true,
      "confidence": 0.92,
      "reason": "...",
      "matched_signals": ["titleTheme", "youtube_description"]
    }}
  ]
}}

Videos:
{json.dumps(compact, ensure_ascii=False)}
"""


def _classify_batch(videos: list[dict], intention: str, playlist_name: str) -> dict:
    messages = [
        {
            "role": "system",
            "content": "You return only valid JSON objects. You are strict and conservative.",
        },
        {
            "role": "user",
            "content": _build_classification_prompt(videos, intention, playlist_name),
        },
    ]

    raw = _call_groq(messages, label="classify")
    json_text = _extract_json_object(raw)

    if not json_text:
        raise ValueError(f"Groq não retornou JSON object:\n{raw}")

    return json.loads(json_text)


# ── 3. Entry-point do step ────────────────────────────────────────────────────

def run(
    context: dict,
    intention: str,
    playlist_name_hint: str = "",
    output_dir: str = "./output",
) -> dict:
    """
    Executa a classificação completa.

    Args:
        context:           dict do youtube_playlist_context.json
        intention:         intenção informada pelo usuário
        playlist_name_hint: nome/ID fornecido pelo usuário (pode ser vazio)
        output_dir:        onde salvar o JSON de classificação

    Returns:
        dict com:
          - playlist_name  (str)
          - videos         (list de vídeos a incluir)
          - output_file    (str, caminho do JSON gerado)
          - classification (list com todos os resultados Groq)
    """
    os.makedirs(output_dir, exist_ok=True)

    # ── resolver nome da playlist ──────────────────────────────────────────────
    if playlist_name_hint and not playlist_name_hint.startswith("PL"):
        # usuário informou um nome (não um ID)
        playlist_name = playlist_name_hint
        print(f"\n  📋 Usando nome de playlist informado: '{playlist_name}'")
    elif playlist_name_hint.startswith("PL"):
        # usuário informou um ID — o nome será o da intenção para logs
        playlist_name = intention
        print(f"\n  🆔 Usando ID de playlist: '{playlist_name_hint}'")
    else:
        # nenhuma entrada — gerar via Groq
        playlist_name = generate_playlist_name(intention)

    # ── candidatos (vídeos com algum sinal de tema) ────────────────────────────
    videos = context.get("videos", [])
    candidates = [
        v for v in videos
        if v.get("youtube_video_id") and (
            v.get("titleTheme") or v.get("descriptionTheme") or v.get("youtube_title")
        )
    ]

    print(f"\n  📦 Total de candidatos a classificar: {len(candidates)}")

    all_results: list[dict] = []
    total_batches = (len(candidates) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(candidates), BATCH_SIZE):
        batch      = candidates[i : i + BATCH_SIZE]
        batch_num  = i // BATCH_SIZE + 1
        print(f"\n  ── Batch {batch_num}/{total_batches} ({len(batch)} vídeos) ──")

        try:
            batch_result = _classify_batch(batch, intention, playlist_name)
            results = batch_result.get("videos", [])

            all_results.extend(results)

            included = sum(1 for r in results if r.get("include"))
            print(f"     Incluídos neste batch: {included}/{len(batch)}")
        except Exception as ex:
            print(f"     ❌ Erro no batch {batch_num}: {ex}")

    # ── montar lista de vídeos incluídos ──────────────────────────────────────
    included_ids = {
        r["youtube_video_id"]
        for r in all_results
        if r.get("include") is True
    }

    included_videos = [
        v for v in videos
        if v.get("youtube_video_id") in included_ids
    ]

    # ── salvar resultado ──────────────────────────────────────────────────────
    output_file = os.path.join(output_dir, "youtube_playlist_classification.json")

    output = {
        "generated_at"    : datetime.now().isoformat(),
        "intention"       : intention,
        "target_playlist" : playlist_name,
        "total_candidates": len(candidates),
        "total_included"  : len(included_videos),
        "classification"  : all_results,
        "videos"          : included_videos,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print(f"\n  💾 Classificação salva em: {output_file}")

    return {
        "playlist_name" : playlist_name,
        "videos"        : included_videos,
        "classification": all_results,
        "output_file"   : output_file,
    }