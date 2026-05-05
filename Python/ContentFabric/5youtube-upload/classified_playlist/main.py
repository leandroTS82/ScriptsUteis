"""
main.py — Orquestrador do pipeline classified_playlist

Fluxo:
  0. Executa export_youtube_uploaded_inventory.py   (atualiza inventário do YouTube)
  1. Executa 01_prepare_youtube_playlist_context.py (gera contexto dos vídeos)
  2. Classifica os vídeos com Groq de acordo com a intenção
  3. Insere os vídeos classificados na playlist do YouTube
"""

import os
import sys
import json
import subprocess
from datetime import datetime

# ── path setup ────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import step_02_classify as step02
import step_03_execute  as step03

# ── CONFIG ────────────────────────────────────────────────────────────────────

# Script que exporta o inventário atualizado do YouTube
EXPORT_SCRIPT = r"C:\dev\scripts\ScriptsUteis\Python\ContentFabric\5youtube-upload\export_youtube_uploaded_inventory.py"

# Script original de preparação de contexto
PREPARE_SCRIPT = os.path.join(BASE_DIR, "01_prepare_youtube_playlist_context.py")

# Contexto gerado pelo script de preparação
CONTEXT_JSON = os.path.join(BASE_DIR, "output", "youtube_playlist_context.json")

OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# ── helpers ───────────────────────────────────────────────────────────────────

def header(title: str):
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def ask(prompt: str) -> str:
    return input(prompt).strip()


# ── STEP 0 — exportar inventário do YouTube ──────────────────────────────────

def run_export():
    """
    Executa export_youtube_uploaded_inventory.py para garantir que o
    inventário reflita todos os vídeos atualmente no canal.
    """
    if not os.path.exists(EXPORT_SCRIPT):
        print(f"  ⚠️  Script de exportação não encontrado: {EXPORT_SCRIPT}")
        print("     Pulando — o inventário existente será usado.")
        return

    print(f"  ▶ Executando: {os.path.basename(EXPORT_SCRIPT)}")

    result = subprocess.run(
        [sys.executable, EXPORT_SCRIPT],
        capture_output=False,
        text=True,
    )

    if result.returncode != 0:
        print(f"\n  ❌ Erro ao exportar inventário (código {result.returncode})")
        print("     Continuando com o inventário existente...")
    else:
        print("  ✅ Inventário atualizado.")


# ── STEP 1 — preparar contexto ───────────────────────────────────────────────

def run_prepare():
    """
    Executa o script original de preparação de contexto.
    Ele lê o inventário do YouTube e gera youtube_playlist_context.json.
    """
    if not os.path.exists(PREPARE_SCRIPT):
        print(f"  ⚠️  Script de preparação não encontrado: {PREPARE_SCRIPT}")
        print("     Verificando se o contexto já existe...")

        if os.path.exists(CONTEXT_JSON):
            print(f"  ✅ Contexto existente encontrado. Usando-o.")
            return
        else:
            print("  ❌ Nenhum contexto disponível. Abortando.")
            sys.exit(1)

    print(f"  ▶ Executando: {os.path.basename(PREPARE_SCRIPT)}")

    result = subprocess.run(
        [sys.executable, PREPARE_SCRIPT],
        capture_output=False,   # mostra output em tempo real no terminal
        text=True,
    )

    if result.returncode != 0:
        print(f"\n  ❌ Erro no script de preparação (código {result.returncode})")
        sys.exit(1)

    if not os.path.exists(CONTEXT_JSON):
        print(f"  ❌ Contexto não foi gerado em: {CONTEXT_JSON}")
        sys.exit(1)

    with open(CONTEXT_JSON, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    print(f"  ✅ Contexto gerado: {ctx.get('total_videos', '?')} vídeos")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    header("CLASSIFIED PLAYLIST — PIPELINE")

    print("\nEste pipeline irá:")
    print("  0. Atualizar o inventário de vídeos do YouTube")
    print("  1. Preparar o contexto dos vídeos")
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

    # ── STEP 0 — exportar inventário ─────────────────────────────────────────

    header("STEP 0 — Atualizando inventário do YouTube")
    run_export()

    # ── STEP 1 — preparar contexto ───────────────────────────────────────────

    header("STEP 1 — Preparando contexto de vídeos")
    run_prepare()

    with open(CONTEXT_JSON, "r", encoding="utf-8") as f:
        context = json.load(f)

    print(f"  📦 Total de vídeos no contexto: {context.get('total_videos', '?')}")

    # ── STEP 2 — classificar vídeos ──────────────────────────────────────────

    header("STEP 2 — Classificando vídeos com Groq")

    classification_result = step02.run(
        context=context,
        intention=intention,
        playlist_name_hint=playlist_input,
        output_dir=OUTPUT_DIR,
    )

    playlist_name   = classification_result["playlist_name"]
    included_videos = classification_result["videos"]
    classification_f = classification_result["output_file"]

    print(f"\n  ✅ Playlist resolvida : '{playlist_name}'")
    print(f"  ✅ Vídeos classificados: {len(included_videos)}")

    if not included_videos:
        print("\n  ⚠️  Nenhum vídeo foi classificado para inclusão. Encerrando.")
        sys.exit(0)

    # ── STEP 3 — executar no YouTube ─────────────────────────────────────────

    header("STEP 3 — Inserindo vídeos na playlist do YouTube")

    step03.run(
        classification_file   = classification_f,
        playlist_name_override= playlist_name,
        playlist_id_override  = playlist_input if playlist_input.startswith("PL") else None,
        output_dir            = OUTPUT_DIR,
    )

    header("PIPELINE CONCLUÍDO ✅")


if __name__ == "__main__":
    main()