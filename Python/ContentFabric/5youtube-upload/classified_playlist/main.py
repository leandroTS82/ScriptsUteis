"""
main.py — Orquestrador do pipeline classified_playlist

Fluxo:
  1. Recebe intenção do usuário (ex: "Past Continuous", "família", "fé")
  2. Recebe opcionalmente um nome ou ID de playlist
  3. 01_prepare  → lê youtube_playlist_context.json (já gerado)
  4. 02_classify → Groq classifica os vídeos pela intenção
  5. 03_execute  → insere os vídeos classificados na playlist do YouTube
"""

import os
import sys
import json
from datetime import datetime

# ── path setup ────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import step_01_prepare as step01
import step_02_classify as step02
import step_03_execute  as step03

# ── CONFIG ────────────────────────────────────────────────────────────────────

# Caminho do contexto já gerado pelo antigo 01_prepare_youtube_playlist_context.py
CONTEXT_JSON = os.path.join(
    BASE_DIR, "output", "youtube_playlist_context.json"
)

OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# ── helpers ───────────────────────────────────────────────────────────────────

def header(title: str):
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def ask(prompt: str, default: str = "") -> str:
    value = input(prompt).strip()
    return value if value else default


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    header("CLASSIFIED PLAYLIST — PIPELINE")

    print("\nEste pipeline irá:")
    print("  1. Ler o contexto dos vídeos do YouTube")
    print("  2. Classificar vídeos via Groq de acordo com sua INTENÇÃO")
    print("  3. Criar/usar uma playlist no YouTube e inserir os vídeos\n")

    # ── entrada do usuário ────────────────────────────────────────────────────

    intention = ""
    while not intention:
        intention = ask(
            "🎯 Informe a INTENÇÃO da playlist\n"
            "   (ex: 'Past Continuous', 'família', 'fé', 'tecnologia'): "
        )
        if not intention:
            print("   ⚠️  A intenção é obrigatória.\n")

    playlist_input = ask(
        "\n📋 Informe o NOME ou ID da playlist no YouTube\n"
        "   (ENTER para gerar nome automaticamente com base na intenção): "
    )

    # ── STEP 01 — Preparar contexto ───────────────────────────────────────────

    header("STEP 1 — Preparando contexto de vídeos")

    if not os.path.exists(CONTEXT_JSON):
        print(f"  ❌ Arquivo de contexto não encontrado: {CONTEXT_JSON}")
        print("     Execute o script original 01_prepare_youtube_playlist_context.py primeiro.")
        sys.exit(1)

    context = step01.load_context(CONTEXT_JSON)
    print(f"  ✅ Contexto carregado: {context['total_videos']} vídeos")

    # ── STEP 02 — Classificar vídeos ──────────────────────────────────────────

    header("STEP 2 — Classificando vídeos com Groq")

    classification_result = step02.run(
        context=context,
        intention=intention,
        playlist_name_hint=playlist_input,
        output_dir=OUTPUT_DIR,
    )

    playlist_name    = classification_result["playlist_name"]
    included_videos  = classification_result["videos"]
    classification_f = classification_result["output_file"]

    print(f"\n  ✅ Playlist resolvida: '{playlist_name}'")
    print(f"  ✅ Vídeos classificados para inclusão: {len(included_videos)}")

    if not included_videos:
        print("\n  ⚠️  Nenhum vídeo foi classificado. Encerrando.")
        sys.exit(0)

    # ── STEP 03 — Executar no YouTube ─────────────────────────────────────────

    header("STEP 3 — Inserindo vídeos na playlist do YouTube")

    step03.run(
        classification_file=classification_f,
        playlist_name_override=playlist_name,
        playlist_id_override=playlist_input if playlist_input.startswith("PL") else None,
        output_dir=OUTPUT_DIR,
    )

    header("PIPELINE CONCLUÍDO ✅")


if __name__ == "__main__":
    main()