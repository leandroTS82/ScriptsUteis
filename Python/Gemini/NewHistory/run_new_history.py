r"""
AJUSTES REALIZADOS (RESUMO EXECUTIVO)

Correção de chamadas incorretas

prompts.youtube_description(text, title) → ordem correta

prompts.youtube_tags() → agora recebe text

Feedback de execução mais claro

Etapas numeradas e consistentes

Contador real de progresso

Fail-fast funcional

Para imediatamente no primeiro erro se --fail-fast

LIMIT respeitado corretamente

Nome dos arquivos

Vídeo e JSON do YouTube sempre com o mesmo nome

Código defensivo

Erros logados com stacktrace

Execução continua quando permitido

Documentação inline (clean code real)
"""

import json
import sys
import traceback

from utils.slugify import slugify
from utils.gemini_client import GeminiClient
from utils.prompt_manager import PromptManager
from utils.badge_generator import generate_badge
from utils.youtube_json_generator import generate_youtube_json

from core.audio_generator import save_wav
from core.subtitle_generator import generate_srt
from core.image_generator import save_image
from core.video_builder import build_video
from core.history_tracker import (
    load_state,
    save_state,
    is_processed,
    mark_processed
)

# ==================================================
# CLI FLAGS
# ==================================================

def get_limit():
    """
    Retorna o valor passado em --limit N
    ou None se não informado.
    """
    if "--limit" in sys.argv:
        try:
            idx = sys.argv.index("--limit")
            return int(sys.argv[idx + 1])
        except Exception:
            print("❌ Uso incorreto. Exemplo: --limit 5")
            sys.exit(1)
    return None


FAIL_FAST = "--fail-fast" in sys.argv
LIMIT = get_limit()

# ==================================================
# INIT
# ==================================================

API_KEY = open(
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Base\FilesHelper\secret_tokens_keys\google-gemini-key.txt",
    encoding="utf-8"
).read().strip()

client = GeminiClient(API_KEY)
prompts = PromptManager()

stories = json.load(
    open("history/stories.json", encoding="utf-8")
)["stories"]

state = load_state("history/history_state.json")

print(f"🚀 Iniciando NewHistory — {len(stories)} histórias")
if LIMIT:
    print(f"⚠ Limite ativo: {LIMIT}")
if FAIL_FAST:
    print("🔥 FAIL-FAST ativado (parar ao primeiro erro)")
print("")

# ==================================================
# PROCESSAMENTO
# ==================================================

processed = 0

BASE_VIDEO_PATH = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Histories\01-NewHistory"
)

BASE_AUDIO_PATH = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Audios\newHistory"
)

BASE_IMAGE_PATH = (
    r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Images"
)

for idx, story in enumerate(stories, start=1):

    if LIMIT is not None and processed >= LIMIT:
        print("\n🛑 Limite atingido. Encerrando.")
        break

    slug = slugify(story["title"])

    if is_processed(state, slug):
        print(f"[{idx}] ⏭ Ignorado (já processado): {slug}")
        continue

    print(f"\n[{idx}] ▶ Processando: {slug}")

    try:
        title = story["title"]
        text = story["text"]

        audio_path = f"{BASE_AUDIO_PATH}\\{slug}.wav"
        srt_path = f"{BASE_VIDEO_PATH}\\subtitles\\{slug}.en.srt"
        image_path = f"{BASE_IMAGE_PATH}\\{slug}.png"
        video_path = f"{BASE_VIDEO_PATH}\\{slug}.mp4"

        # -----------------------------
        # 1️⃣ ÁUDIO
        # -----------------------------
        print("   🔊 Gerando áudio...")
        save_wav(
            audio_path,
            client.generate_audio(
                text,
                prompts.audio_instruction(slow=True)
            )
        )

        # -----------------------------
        # 2️⃣ LEGENDA
        # -----------------------------
        print("   📝 Gerando legenda...")
        generate_srt(audio_path, srt_path)

        # -----------------------------
        # 3️⃣ IMAGEM (GEMINI)
        # -----------------------------
        print("   🎨 Gerando imagem (título embutido)...")
        save_image(
            image_path,
            client.generate_image(
                prompts.image_prompt(text, title)
            )
        )

        # -----------------------------
        # 4️⃣ SELO (BADGE)
        # -----------------------------
        print("   🏷️ Gerando selo...")
        badge = generate_badge(
            client,
            prompts.badge_prompt(text)
        )

        # -----------------------------
        # 5️⃣ VÍDEO
        # -----------------------------
        print("   🎬 Renderizando vídeo...")
        build_video(
            image_path=image_path,
            audio_path=audio_path,
            srt_path=srt_path,
            output_path=video_path,
            badge_img=badge,
            subtitle_style=prompts.subtitle_style()
        )

        # -----------------------------
        # 6️⃣ JSON YOUTUBE
        # -----------------------------
        print("   📺 Gerando JSON YouTube...")
        generate_youtube_json(
            output_path=video_path,
            title=title,
            description=prompts.youtube_description(title, text),
            tags=prompts.youtube_tags(text),
            playlist=prompts.youtube_playlist()
        )

        # -----------------------------
        # FINALIZAÇÃO
        # -----------------------------
        mark_processed(state, slug)
        save_state("history/history_state.json", state)

        processed += 1
        print(f"[{idx}] ✅ Finalizado ({processed}/{LIMIT or '∞'})")

    except Exception as e:
        print(f"[{idx}] ❌ ERRO ao processar {slug}")
        print(str(e))
        traceback.print_exc()

        if FAIL_FAST:
            print("🛑 FAIL-FAST ativo. Encerrando execução.")
            sys.exit(1)

        print("➡ Continuando para a próxima história...")

print("\n  NewHistory finalizado com sucesso")
