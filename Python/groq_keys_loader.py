"""
============================================================
 groq_keys_loader.py
------------------------------------------------------------
 Utilitário reutilizável para carregamento de chaves da Groq.

 OBJETIVO
 --------
 Fornecer a variável GROQ_KEYS pronta para uso em qualquer
 script Python, com a seguinte prioridade:

   1) GroqKeys.json (externo, seguro, fora do Git)
   2) Fallback inline (compatibilidade / debug)

 FORMATO RETORNADO
 -----------------
 GROQ_KEYS = [
     {"name": "identificacao", "key": "gsk_..."},
     ...
 ]

 COMO USAR EM OUTRO .py
 ---------------------
 Basta importar:

     from groq_keys_loader import GROQ_KEYS

 Exemplo real:

     from itertools import cycle
     from groq_keys_loader import GROQ_KEYS

     key_cycle = cycle(GROQ_KEYS)

     key_info = next(key_cycle)
     print(key_info["name"])

 NENHUM COMPORTAMENTO COLATERAL
 -----------------------------
 - Não imprime logs
 - Não faz exit
 - Não lança exceções
 - Apenas retorna dados válidos

============================================================
"""

import json
import os

# ============================================================
# CONFIGURAÇÃO DO PATH DO JSON
# ============================================================

GROQ_KEYS_PATH = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\LTS SP Site - Documentos de estudo de inglês\FilesHelper\secret_tokens_keys\GroqKeys.json"

# ============================================================
# FALLBACK INLINE (SEGURANÇA / COMPATIBILIDADE)
# ============================================================

GROQ_KEYS_FALLBACK = [
    {"name": "lts@gmail.com", "key": "gsk_r***"},
    {"name": "ltsCV@gmail", "key": "gsk_4***"},
    {"name": "butterfly", "key": "gsk_n***"},
    {"name": "??", "key": "gsk_P***"},
    {"name": "MelLuz201811@gmail.com", "key": "gsk_***i"}
]

# ============================================================
# LOADER PRINCIPAL
# ============================================================

def load_groq_keys():
    """
    Carrega e retorna as chaves da Groq.

    Prioridade:
      1) Arquivo GroqKeys.json
      2) Lista GROQ_KEYS_FALLBACK

    Retorno:
      List[Dict[str, str]]
    """
    if os.path.exists(GROQ_KEYS_PATH):
        try:
            with open(GROQ_KEYS_PATH, "r", encoding="utf-8") as f:
                keys = json.load(f)

            # Validação mínima
            if isinstance(keys, list) and all(
                isinstance(k, dict) and "key" in k for k in keys
            ):
                return keys

        except Exception:
            # Falha silenciosa → fallback
            pass

    return GROQ_KEYS_FALLBACK


# ============================================================
# EXPORT PADRÃO (USO DIRETO)
# ============================================================

GROQ_KEYS = load_groq_keys()
