import re
import unicodedata

def normalize_text(text: str) -> str:
    """
    - Remove espaços duplicados
    - Normaliza acentuação
    - Remove caracteres invisíveis
    - Ajusta quebras de linha
    """

    if not text:
        return ""

    # Normalizar unicode
    text = unicodedata.normalize("NFC", text)

    # Remover caracteres invisíveis
    text = re.sub(r"[\u200b\u200c\u200d\uFEFF]", "", text)

    # Substituir múltiplos espaços por um só
    text = re.sub(r"\s+", " ", text).strip()

    # Se vier com \n\ n faz limpeza
    text = text.replace("\n ", "\n").replace(" \n", "\n")

    return text
