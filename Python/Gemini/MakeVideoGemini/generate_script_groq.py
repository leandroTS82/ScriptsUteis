# ============================================================
# generate_script_groq.py
# Versão ZERO CUSTO de generate_script.py usando Groq.
# Persona: Leandrinho — professor animado estilo YouTuber.
# Otimizado para:
# - Edge TTS Multilingual
# - Spoken language
# - Creator style
# - JSON resiliente
# - Naturalidade
# ============================================================

import os
import sys
import json
import re
import random
from itertools import cycle

_GROQ_LOADER_DIR = r"C:\dev\scripts\ScriptsUteis\Python"

if _GROQ_LOADER_DIR not in sys.path:
    sys.path.insert(0, _GROQ_LOADER_DIR)

from groq import Groq
from groq_keys_loader import GROQ_KEYS


# ------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------

GROQ_MODEL = "llama-3.3-70b-versatile"

MAX_RETRIES = 3
TIMEOUT_SECONDS = 30

TEMPERATURE = 1.0


# ------------------------------------------------------------------
# PERSONA
# ------------------------------------------------------------------

PERSONA = (
    "Leandrinho, charismatic Brazilian English teacher and content creator. "
    "Energetic, natural, spontaneous and engaging. "
    "Speaks like a real modern YouTube/TikTok creator. "
    "Uses conversational Brazilian Portuguese naturally mixed with simple English expressions. "
    "Teaches in a spoken and human way, never sounding robotic or academic. "
    "Always sounds motivating, casual and natural when read aloud by TTS."
)


# ------------------------------------------------------------------
# KEY ROTATION
# ------------------------------------------------------------------

_groq_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))


def _get_client():
    key_info = next(_groq_key_cycle)
    return Groq(api_key=key_info["key"]), key_info["name"]


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------

def _extract_json(text: str) -> str | None:

    match = re.search(r"\{.*\}", text, re.DOTALL)

    return match.group(0) if match else None


def _call_groq(messages: list, label: str = "") -> str:

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):

        client, key_name = _get_client()

        try:

            print(
                f"   [Groq{' ' + label if label else ''}] "
                f"tentativa {attempt} · key: {key_name}"
            )

            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=TEMPERATURE,
                timeout=TIMEOUT_SECONDS,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:

            last_error = e

            print(
                f"   ⚠️ [Groq] Falha na tentativa "
                f"{attempt}: {e}"
            )

    raise RuntimeError(
        f"[generate_script_groq] "
        f"Todas as tentativas falharam.\n"
        f"Último erro: {last_error}"
    )


def _normalize_text(text: str) -> str:

    return re.sub(
        r"\s+",
        " ",
        text.strip().lower()
    )


def _target_keywords(target: str) -> list[str]:

    stopwords = {
        "the", "a", "an",
        "he", "she", "it",
        "they", "we", "i", "you",
        "to", "of", "in", "on", "at",
        "is", "are", "am",
        "my", "your", "his", "her",
        "our", "their"
    }

    words = re.findall(
        r"\w+",
        target.lower()
    )

    return [
        w for w in words
        if w not in stopwords and len(w) > 2
    ]


# ------------------------------------------------------------------
# SEMANTIC VALIDATION FALLBACK
# ------------------------------------------------------------------

def _semantic_validation_fallback(
    validation_type: str,
    target: str,
    sentence: str,
    error_message: str
) -> bool:

    messages = [
        {
            "role": "system",
            "content": (
                "You are a strict but realistic English teacher validator.\n\n"

                "ACCEPT if:\n"
                "- the sentence sounds natural\n"
                "- the sentence teaches the target naturally\n"
                "- the target meaning/context is preserved\n"
                "- the sentence is useful for students\n\n"

                "REJECT if:\n"
                "- broken English\n"
                "- nonsense\n"
                "- unrelated sentence\n"
                "- only repetition of target\n"
                "- unnatural robotic sentence\n\n"

                "Reply ONLY with:\n"
                "VALID\n"
                "or\n"
                "INVALID"
            )
        },
        {
            "role": "user",
            "content": (
                f"Validation type: {validation_type}\n"
                f"Target: {target}\n"
                f"Sentence: {sentence}\n"
                f"Local validation error: {error_message}"
            )
        }
    ]

    try:

        result = _call_groq(
            messages,
            label="semantic-fallback"
        )

        result = result.strip().upper()

        if result.startswith("VALID"):

            print(
                f"   ⚠️ Validação local ignorada "
                f"via fallback semântico ({validation_type})"
            )

            return True

        return False

    except Exception as e:

        print(
            f"   ⚠️ Erro no fallback semântico: {e}"
        )

        return False


# ------------------------------------------------------------------
# VALIDATE EN EXAMPLES
# ------------------------------------------------------------------

def _validate_en_examples(
    lesson: dict,
    target: str,
    min_chars: int = 25,
    max_chars: int = 85
):

    target_norm = _normalize_text(target)

    keywords = _target_keywords(target)

    for group_index, group in enumerate(
        lesson.get("WORD_BANK", [])
    ):

        for item_index in [2, 3, 4]:

            try:
                item = group[item_index]

            except IndexError:
                continue

            if item.get("lang") != "en":
                continue

            text = item.get("text", "")

            text_norm = _normalize_text(text)

            # -------------------------------------------------
            # helper
            # -------------------------------------------------

            def _try_semantic(
                validation_type: str,
                error_message: str
            ):

                semantic_ok = _semantic_validation_fallback(
                    validation_type=validation_type,
                    target=target,
                    sentence=text,
                    error_message=error_message
                )

                if semantic_ok:
                    return

                raise ValueError(error_message)

            # -------------------------------------------------
            # max chars
            # -------------------------------------------------

            if len(text) > max_chars:

                _try_semantic(
                    "MAX_CHARS",
                    (
                        f"Exemplo EN excedeu "
                        f"{max_chars} caracteres: {text}"
                    )
                )

            # -------------------------------------------------
            # min chars
            # -------------------------------------------------

            if len(text) < min_chars:

                _try_semantic(
                    "MIN_CHARS",
                    (
                        f"Exemplo EN curto demais: {text}"
                    )
                )

            # -------------------------------------------------
            # only target
            # -------------------------------------------------

            if text_norm == target_norm:

                _try_semantic(
                    "ONLY_TARGET",
                    (
                        f"Exemplo contém apenas target: {text}"
                    )
                )

            # -------------------------------------------------
            # keyword validation
            # -------------------------------------------------

            matches = sum(
                1 for kw in keywords
                if kw in text_norm
            )

            required_matches = max(
                1,
                len(keywords) - 1
            )

            if matches < required_matches:

                _try_semantic(
                    "KEYWORD_MATCH",
                    (
                        f"Keywords insuficientes: {text}"
                    )
                )

            # -------------------------------------------------
            # artificial repetition
            # -------------------------------------------------

            repeated_target = (
                f"{target_norm} {target_norm}"
            )

            if repeated_target in text_norm:

                _try_semantic(
                    "REPETITION",
                    (
                        f"Exemplo repetitivo/artificial: {text}"
                    )
                )


# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------

def generate_lesson_json(word: str) -> dict:

    system_prompt = f"""
You are {PERSONA}

You are PERFORMING as a charismatic Brazilian English teacher and creator.

You are NOT writing educational material.
You are speaking naturally like a real creator recording a short lesson.

Your text must feel:
- alive
- spontaneous
- spoken
- energetic
- natural
- engaging
- human

The student should feel like they are watching a real short-form English lesson.

Output ONLY valid JSON.
No markdown.
No explanations.
No text outside JSON.
"""

    prompt = f"""
Generate a vocabulary lesson JSON for:

"{word}"

You MUST follow EXACTLY this structure:

{{
  "repeat_each": {{ "pt": 1, "en": 2 }},
  "introducao": "...",
  "nome_arquivos": "{word}",
  "WORD_BANK": [
    [
      {{ "lang": "en", "text": "{word}", "pause": 1000 }},
      {{ "lang": "pt", "text": "...", "pause": 500 }},
      {{ "lang": "en", "text": "...", "pause": 1000 }},
      {{ "lang": "en", "text": "...", "pause": 1000 }},
      {{ "lang": "en", "text": "...", "pause": 1500 }},
      {{ "lang": "pt", "text": "..." }}
    ]
  ]
}}

STYLE REFERENCE:
- modern YouTube English teachers
- TikTok educational creators
- spoken language
- short-form engaging videos
- charismatic Brazilian creators

GLOBAL STYLE:
- Write as if this will be SPOKEN OUT LOUD
- Prioritize spoken rhythm over formal writing
- Sound good for multilingual TTS
- Keep the pacing fast and engaging
- Use conversational Brazilian Portuguese
- Use natural spoken English
- The teacher may naturally mix PT-BR and EN expressions
- Avoid academic tone
- Avoid textbook explanations
- Avoid robotic phrasing
- Avoid sounding cringe or exaggerated
- Keep charisma natural
- Prefer short and medium spoken sentences
- Emojis are allowed occasionally, but use them sparingly

INTRODUCAO:
- Must sound like a real Brazilian YouTube creator opening a lesson
- Must feel spontaneous and spoken
- Greeting should vary naturally every time
- Should create curiosity immediately
- Should feel like a YouTube Shorts hook
- Should explain WHY the expression is useful
- Should make the student want to continue
- May naturally include the English expression
- The intro should often begin with:
  - a relatable situation
  - a curiosity hook
  - a common English-learning frustration
  - a real-life scenario

Examples of opening STYLE ONLY:
- "Fala, galera!"
- "E aí, pessoal!"
- "Salve, time!"
- "Hey guys!"
- "Se liga nessa!"
- "Teacher Leandrinho na área!"

DO NOT copy examples.

WORD_BANK:

1. lang=en
- ONLY the target word/expression

2. lang=pt explanation
- Explain naturally like a real teacher speaking
- Start by explaining the meaning naturally
- Then explain how natives use it
- Sound conversational and spontaneous
- May naturally include the English expression
- Should sound great for multilingual TTS
- Avoid dictionary definitions
- Avoid grammar-heavy explanations

3. lang=en
- A1 sentence
- Natural and realistic
- 25 to 85 chars

4. lang=en
- A2 sentence
- Natural and realistic
- 25 to 85 chars

5. lang=en
- B1/B2 sentence
- Natural and realistic
- 25 to 85 chars

6. lang=pt closing
- Must sound like a real teacher ending naturally
- Must feel motivating and spontaneous
- Encourage practice naturally
- May mix short EN expressions naturally
- Avoid repetitive patterns
- Should feel human and conversational

STRICT RULES:
- Output ONLY valid JSON
- No markdown
- No comments
- No explanations outside JSON
- JSON structure MUST match exactly
- PT text must be natural Brazilian Portuguese
- EN text must be natural English
- English examples must sound like real native speech
- Avoid weird or forced examples
- ALL English examples MUST contain:
  "{word}"
- Examples MUST naturally teach the target
- Examples MUST NOT be generic
- Examples MUST NOT contain Portuguese
- Examples MUST NOT be only the target
- Each EN example:
  - minimum 25 chars
  - maximum 85 chars
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    # -------------------------------------------------
    # generate
    # -------------------------------------------------

    raw = _call_groq(
        messages,
        label="generate"
    )

    json_text = _extract_json(raw)

    # -------------------------------------------------
    # fix missing json
    # -------------------------------------------------

    if not json_text:

        print(
            "   ⚠️ JSON não encontrado. "
            "Tentando corrigir..."
        )

        fix_messages = [
            {
                "role": "system",
                "content": (
                    "You are a JSON repair assistant. "
                    "Return ONLY valid JSON."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Fix this and return ONLY valid JSON:\n\n{raw}"
                )
            }
        ]

        raw_fix = _call_groq(
            fix_messages,
            label="fix"
        )

        json_text = _extract_json(raw_fix)

    if not json_text:

        raise ValueError(
            f"Não foi possível extrair JSON.\n\n{raw}"
        )

    # -------------------------------------------------
    # parse json
    # -------------------------------------------------

    try:

        lesson = json.loads(json_text)

    except json.JSONDecodeError:

        print(
            "⚠️ JSON inválido. Tentando corrigir..."
        )

        fix_messages = [
            {
                "role": "system",
                "content": (
                    "Fix ONLY the JSON syntax. "
                    "Return ONLY valid JSON."
                )
            },
            {
                "role": "user",
                "content": json_text
            }
        ]

        raw_fix = _call_groq(
            fix_messages,
            label="fix-json"
        )

        fixed_json = _extract_json(raw_fix)

        if not fixed_json:

            raise ValueError(
                "Falha ao corrigir JSON."
            )

        lesson = json.loads(fixed_json)

    # -------------------------------------------------
    # ensure pause
    # -------------------------------------------------

    for group in lesson.get("WORD_BANK", []):

        for item in group:

            if "pause" not in item:

                item["pause"] = (
                    500
                    if item.get("lang") == "pt"
                    else 1000
                )

    # -------------------------------------------------
    # validate examples
    # -------------------------------------------------

    _validate_en_examples(
        lesson,
        target=word,
        min_chars=25,
        max_chars=85
    )

    print(
        "✅ [Script/Groq] JSON gerado com sucesso.\n"
    )

    return lesson