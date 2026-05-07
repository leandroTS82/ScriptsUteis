# ============================================================
# generate_script_groq.py
# Versão ZERO CUSTO de generate_script.py usando Groq.
# Persona: Leandrinho — professor animado estilo YouTuber.
# Contrato de retorno IDÊNTICO ao generate_script.py.
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
# CONFIGURAÇÃO
# ------------------------------------------------------------------

GROQ_MODEL      = "llama-3.3-70b-versatile"
MAX_RETRIES     = 3
TIMEOUT_SECONDS = 30

# ------------------------------------------------------------------
# PERSONA DO LEANDRINHO
# ------------------------------------------------------------------

PERSONA = (
    "Leandrinho, professor brasileiro animado, didático, moderno, "
    "estilo criador de conteúdo jovem, focado em repetição, clareza e motivação. "
    "Sempre fala com energia alta, usa linguagem jovem e natural do Brasil, "
    "com variação de abertura, sem repetir sempre a mesma frase. "
    "Explica de forma simples, envolvente e prática, incentivando o aluno a repetir e praticar."
)

# ------------------------------------------------------------------
# ROTAÇÃO DE KEYS
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
            print(f"   [Groq{' ' + label if label else ''}] tentativa {attempt} · key: {key_name}")
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=0.7,   # um pouco mais criativo para o estilo YouTuber
                timeout=TIMEOUT_SECONDS,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            last_error = e
            print(f"   ⚠️  [Groq] Falha na tentativa {attempt}: {e}")

    raise RuntimeError(f"[generate_script_groq] Todas as tentativas falharam. Último erro: {last_error}")


# ------------------------------------------------------------------
# FUNÇÃO PRINCIPAL
# ------------------------------------------------------------------

def generate_lesson_json(word: str) -> dict:
    """
    Gera o JSON da aula com a persona do Leandrinho usando Groq.
    Contrato de retorno idêntico ao generate_script.py.
    """   

    # -------------------------------------------------
    # 2) System prompt — define a persona
    # -------------------------------------------------
    system_prompt = f"""You are {PERSONA}

    Your job is to create engaging English vocabulary lessons for Brazilian students.
    Your tone is ALWAYS energetic, fun, motivating — like a young Brazilian YouTuber teacher.
    You speak Portuguese naturally and fluently when writing PT fields.
    You write clear, natural English when writing EN fields.
    You NEVER mix languages inside the same text field.
    You output ONLY valid JSON — no markdown, no backticks, no explanations outside the JSON."""

    # -------------------------------------------------
    # 3) User prompt — estrutura + exemplos de qualidade
    # -------------------------------------------------
    prompt = f"""Generate a vocabulary lesson JSON for the word or phrase: "{word}"

    You MUST follow EXACTLY this JSON structure.
    DO NOT:
    - add fields
    - remove fields
    - rename fields
    - change structure

    The output MUST be a single valid JSON object.

    NO explanations
    NO comments
    NO markdown
    NO text outside JSON

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

    RULES FOR EACH FIELD:

    "introducao":
    - Write ONLY in Brazilian Portuguese
    - NEVER use English words
    - NEVER use the target word or phrase in English
    - Must be a presentation of what is coming, not a translation
    - Must be light, young, fun and curiosity-driven
    - Vary the opening naturally; do NOT always start with the same phrase
    - Use variation of impact phrases.
    - Max 3 sentences

    WORD_BANK items:
    1. lang=en → the word/phrase itself: "{word}"
    2. lang=pt → MUST follow this exact structure:
    - Start with: "Significa ..." followed by a clear and correct translation in Brazilian Portuguese
    - Then give a natural, simple explanation in Brazilian Portuguese explaining how and when the expression is used
    - Include at least one short usage context or situation in Portuguese
    - The explanation must be clear, didactic and sound like a real teacher speaking naturally
    - Do NOT use English words or the target expression in English
    - The translation must be the first sentence
    - The explanation must be the second sentence
    - Keep it concise (max 2–3 sentences total)
    3. lang=en → simple A1 real sentence using "{word}"
    4. lang=en → short A2 real sentence using "{word}"
    5. lang=en → B1/B2 real sentence using "{word}", max 80 characters
    6. lang=pt → closing message in strict Brazilian Portuguese only. Briefly summarize the Portuguese meaning again in a natural way, motivate the student, give one simple usage tip, and say goodbye. NEVER use English words, English expressions, or the target word/phrase in English. Keep it young, dynamic, didactic and natural. Max 4 sentences.

    QUALITY EXAMPLES to match the tone:

    introducao examples (style reference only — DO NOT copy):
    - "E ai galera, Leandrinho aqui! Hoje tem uma dica rápida que muda muito a forma de falar. Fica comigo!"
    - "Salve! Bora destravar um detalhe que aparece direto no inglês do dia a dia?"
    - "Olha só essa dica: em poucos segundos você vai entender algo que muita gente usa sem perceber."

    Rules:
    - DO NOT reuse these sentences
    - Vary tone, rhythm and structure
    - Avoid always starting with the same expression

    lang=pt explanation examples (style reference only):
    - "Quer dizer ..., e é usada pra ..., tipo ..., ... ou ..."
    - "É uma forma de dizer ... de um jeito mais natural, como no português quando falamos ..."
    - "Usamos isso quando queremos ..., por exemplo ..."

    Rules:
    - Be clear and natural
    - Avoid robotic or dictionary-like explanations
    - Sound like you are explaining to a real student

    lang=pt closing rules:
    - Sound natural, spontaneous and human
    - Vary the structure every time
    - Avoid fixed patterns like "Agora repita com calma"
    - Keep it short, motivating and fluid
    - Encourage practice in a natural way
    - End like a friendly Brazilian teacher creating a short online lesson

    Examples of good closings (DO NOT copy):
    - "Boa! Agora tenta usar isso no seu dia a dia que vai ficar muito mais natural."
    - "Mandou bem! Testa isso em uma frase sua e você já começa a sentir a diferença."
    - "Perfeito, agora manda ver e tenta usar isso em situações reais."

    STRICT RULES:
    - Output ONLY valid JSON — absolutely no text outside the JSON object
    - PT fields: natural Brazilian Portuguese only — never literal translations
    - EN fields: natural English only — never Portuguese words
    - EN examples must be realistic, useful, and something a native speaker would actually say
    - Do NOT create weird, forced, random, or unnatural sentences
    - The target word or phrase MUST appear naturally in all 3 EN example sentences
    - The JSON structure MUST match exactly as defined
    - "introducao" MUST NOT contain English words
    - "introducao" must start with a natural greeting like a young Brazilian YouTuber
    - The last WORD_BANK item with lang=pt MUST NOT contain English words
    - "introducao" and the final lang=pt item MUST NOT contain the target word or phrase in English
    - If any rule is broken, regenerate internally before answering
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": prompt},
    ]

    # -------------------------------------------------
    # 4) Chamada principal
    # -------------------------------------------------
    raw = _call_groq(messages, label="generate")
    json_text = _extract_json(raw)

    # -------------------------------------------------
    # 5) Fallback de correção
    # -------------------------------------------------
    if not json_text:
        print("   ⚠️  JSON não encontrado — tentando autocorreção...")
        fix_messages = [
            {"role": "system", "content": "You are a JSON repair assistant. Return ONLY valid JSON, nothing else."},
            {"role": "user",   "content": f"Fix this and return ONLY valid JSON, no backticks:\n\n{raw}"}
        ]
        raw_fix   = _call_groq(fix_messages, label="fix")
        json_text = _extract_json(raw_fix)

    if not json_text:
        raise ValueError(
            f"[generate_script_groq] Não foi possível extrair JSON para '{word}'.\n"
            f"Última resposta:\n{raw}"
        )

    try:
        lesson = json.loads(json_text)

    except json.JSONDecodeError as e:
        print("⚠️ JSON inválido, tentando corrigir...")

        fix_messages = [
            {
                "role": "system",
                "content": "You are a strict JSON fixer. Fix syntax only. Return ONLY valid JSON."
            },
            {
                "role": "user",
                "content": f"Fix this JSON:\n\n{json_text}"
            }
        ]

        raw_fix = _call_groq(fix_messages, label="fix-json")
        fixed_json = _extract_json(raw_fix)

        if not fixed_json:
            print("❌ Falha ao corrigir JSON:")
            print(json_text)
            raise e

        lesson = json.loads(fixed_json)

    # -------------------------------------------------
    # 6) Garante que pause existe nos itens PT sem pause
    # -------------------------------------------------
    for group in lesson.get("WORD_BANK", []):
        for item in group:
            if "pause" not in item:
                item["pause"] = 500 if item.get("lang") == "pt" else 1000    

    print(f"✅ [Script/Groq] JSON gerado com persona Leandrinho.\n")
    return lesson