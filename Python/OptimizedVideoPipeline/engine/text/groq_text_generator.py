import json
import random
from itertools import cycle
from groq import Groq

# ============================================================
# IMPORT CORRETO DO LOADER (DENTRO DO PROJETO)
# ============================================================

from engine.text.groq_keys_loader import GROQ_KEYS

# ============================================================
# CONFIG FIXA (SEM settings/groq.json)
# ============================================================

GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_TEMPERATURE = 0.6

# ============================================================
# ROTATION / RANDOM KEYS (PADRÃO CONSOLIDADO SEU)
# ============================================================

_groq_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))

# ============================================================
# MAIN
# ============================================================

def generate_text(word: str) -> dict:
    """
    Gera o JSON FINAL da aula.
    Estrutura RÍGIDA — compatível com TTS e vídeo.
    """

    print(f"🧠 Gerando conteúdo para: {word}")

    key_info = next(_groq_key_cycle)
    client = Groq(api_key=key_info["key"])

    prompt = f"""
Gere um JSON seguindo exatamente esta estrutura:

{{
  "repeat_each": {{ "pt": 1, "en": 2 }},
  "introducao": "Crie uma introdução curta estilo youtuber sobre '{word}'.",
  "nome_arquivos": "Tema_{word}",
  "WORD_BANK": [
    [
      {{ "lang": "en", "text": "{word}", "pause": 1000 }},
      {{ "lang": "pt", "text": "Explique a palavra {word} em português." }},
      {{ "lang": "en", "text": "Use {word} em uma frase simples.", "pause": 1000 }},
      {{ "lang": "en", "text": "Use {word} em outra frase curta.", "pause": 1000 }},
      {{ "lang": "en", "text": "Crie uma frase mais longa com {word}.", "pause": 1000 }},
      {{ "lang": "pt", "text": "Mensagem final estilo youtuber." }}
    ]
  ]
}}

REGRAS:
- Retorne APENAS JSON válido
- Não explique nada fora do JSON
- Não altere nomes de campos
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=GROQ_TEMPERATURE,
        timeout=30
    )

    raw = response.choices[0].message.content.strip()

    try:
        return json.loads(raw)
    except Exception as e:
        raise RuntimeError(
            f"[Groq] JSON inválido retornado.\nConteúdo bruto:\n{raw}"
        ) from e
