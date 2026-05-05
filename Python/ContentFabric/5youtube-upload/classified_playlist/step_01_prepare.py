"""
step_01_prepare.py

Responsabilidade: carregar o youtube_playlist_context.json já gerado
e devolvê-lo como dict para o pipeline.

Não re-executa a preparação — apenas valida e lê o arquivo.
"""

import os
import json


def load_context(context_json_path: str) -> dict:
    """
    Lê e valida o arquivo de contexto do YouTube.

    Args:
        context_json_path: Caminho absoluto para youtube_playlist_context.json

    Returns:
        dict com chaves: generated_at, total_videos, videos (list), ...
    """
    if not os.path.exists(context_json_path):
        raise FileNotFoundError(
            f"Contexto não encontrado: {context_json_path}\n"
            "Execute o script original 01_prepare_youtube_playlist_context.py primeiro."
        )

    with open(context_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    videos = data.get("videos", [])
    if not videos:
        raise ValueError("O contexto está vazio (nenhum vídeo encontrado).")

    # estatísticas rápidas
    with_theme    = sum(1 for v in videos if v.get("titleTheme") or v.get("descriptionTheme"))
    without_theme = len(videos) - with_theme

    print(f"  Total de vídeos no contexto : {len(videos)}")
    print(f"  Com tema extraído           : {with_theme}")
    print(f"  Sem tema (usará título YT)  : {without_theme}")

    return data


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "output/youtube_playlist_context.json"
    ctx = load_context(path)
    print(f"\nContexto OK — {ctx['total_videos']} vídeos carregados.")