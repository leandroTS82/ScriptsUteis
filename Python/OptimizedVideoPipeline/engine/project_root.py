import os
from pathlib import Path

def get_project_root() -> Path:
    """
    Retorna o diretório raiz do projeto OptimizedVideoPipeline,
    independente de onde o script foi executado.
    """
    return Path(__file__).resolve().parents[1]
