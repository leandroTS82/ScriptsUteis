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
from utils.known_terms_loader import load_known_terms


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
    "estilo YouTuber, focado em repetição, clareza e motivação. "
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
                temperature=0.2,   # um pouco mais criativo para o estilo YouTuber
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
    # 1) Carrega termos já estudados
    # -------------------------------------------------
    known_terms = load_known_terms(
        target_word=word,
        percentage=0.8,
        max_terms=60,
        verbose=True
    )

    known_terms_block = ""
    if known_terms:
        known_terms_block = (
            "\nKnown English vocabulary to PRIORITIZE in ENGLISH example sentences:\n"
            + ", ".join(known_terms)
            + "\n\nRules for known vocabulary:\n"
            "- At least 70% of ENGLISH example sentences MUST reuse these terms naturally\n"
            "- Max 150 characters per English example sentence\n"
            "- NEVER use known terms inside Portuguese text fields\n"
        )

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

{known_terms_block}

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
2. lang=pt → Must first give a translation and next give an clear explanation of the meaning in natural fluent Brazilian Portuguese with some usage situation. Be clear and didactic. Use examples in PT if helpful.
3. lang=en → simple A1 real sentence using "{word}"
4. lang=en → short A2 real sentence using "{word}"
5. lang=en → B1/B2 real sentence using "{word}", max 80 characters
6. lang=pt → closing message in Brazilian Portuguese only. It must motivate the student, give a simple usage tip, and encourage practice. NEVER use English words, NEVER use the target word or phrase in English. Give a sumary and say good bye, Keep it young, dynamic and natural. Max 4 sentences.

QUALITY EXAMPLES to match the tone:

introducao examples:
"E ai galera, Leandrinho aqui, Hoje tem uma dica rápida que parece pequena, mas muda muito a forma de falar. Fica comigo que isso vai deixar suas frases bem mais naturais!"
"Salve pessoal, Leandrinho na área! Bora aprender um detalhe simples que aparece direto em conversas reais? Presta atenção porque isso ajuda muito na fluência!"
"E ai alunos atentos, Olha só essa dica esperta: em poucos segundos você vai entender uma estrutura muito comum no dia a dia."

lang=pt explanation example:
"Essa estrutura é usada para confirmar uma ideia ou deixar a frase mais natural. É parecida com expressões como 'né?', 'certo?' ou 'combinado?'."

lang=pt closing example:
"Muito bem! Agora repita as frases com calma e tente criar uma situação sua. Quanto mais você pratica, mais natural fica. Bora praticar! tchaaau!"

STRICT RULES:
- Output ONLY valid JSON — absolutely no text outside the JSON object
- PT fields: natural Brazilian Portuguese only — never literal translations
- EN fields: natural English only — never Portuguese words
- The JSON structure MUST match exactly as defined
- "introducao" MUST NOT contain English words,, must start with a saldation like a young Brazilian Youttuber.
- The last WORD_BANK item with lang=pt MUST NOT contain English words
- "introducao" and the final lang=pt item MUST NOT contain the target word or phrase in English
- If any rule is broken, regenerate internally before answering
- Known vocabulary terms must appear ONLY inside EN sentence fields"""



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

    # -------------------------------------------------
    # 7) Metadata de controle
    # -------------------------------------------------
    lesson["_known_terms_context"] = {
        "source":     "english_terms.json",
        "percentage": 0.8,
        "max_terms":  60,
        "terms_used": known_terms,
        "engine":     f"groq/{GROQ_MODEL}",
    }

    print(f"✅ [Script/Groq] JSON gerado com persona Leandrinho.\n")
    return lesson