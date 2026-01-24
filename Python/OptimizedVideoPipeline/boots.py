"""
=========================================================
 Script: bootstrap_pipeline.py
 Objetivo:
   - Criar a estrutura COMPLETA do OptimizedVideoPipeline
   - Criar arquivos somente se NÃO existirem
   - Inicializar JSONs com conteúdo padrão válido
=========================================================
"""

import json
from pathlib import Path

ROOT = Path("OptimizedVideoPipeline")

# --------------------------------------------------
# Helpers
# --------------------------------------------------

def ensure_dir(path: Path):
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"📁 Criado diretório: {path}")

def ensure_file(path: Path, content: str = ""):
    if not path.exists():
        path.write_text(content, encoding="utf-8")
        print(f"📄 Criado arquivo: {path}")

def ensure_json(path: Path, data: dict):
    if not path.exists():
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"🧾 Criado JSON: {path}")

# --------------------------------------------------
# Diretórios
# --------------------------------------------------

DIRS = [
    "orchestrator",
    "runtime/logs",
    "runtime/temp",
    "input/ReadyToBeCreated",
    "batch",
    "engine/text",
    "engine/image",
    "engine/audio",
    "engine/video",
    "settings",
    "prompts/shared",
    "prompts/groq",
    "prompts/gemini",
    "media/audio",
    "media/images",
    "media/videos"
]

# --------------------------------------------------
# Arquivos vazios (placeholders)
# --------------------------------------------------

FILES = [
    "orchestrator/CreateRightNow.bat",
    "orchestrator/Gatekeeper.py",

    "batch/run_batch.py",
    "batch/process_word.py",

    "engine/text/groq_text_generator.py",
    "engine/image/gemini_image_generator.py",
    "engine/image/fixed_image_provider.py",
    "engine/audio/gemini_audio_generator.py",
    "engine/video/moviepy_builder.py",

    "README.md"
]

# --------------------------------------------------
# JSONs de configuração
# --------------------------------------------------

JSON_FILES = {
    "CreateLater.json": {
        "pending": []
    },

    "settings/pipeline.json": {
        "enable_image_ai": True,
        "fixed_image_path": "./assets/default.gif",
        "lock_enabled": True
    },

    "settings/groq.json": {
        "model": "openai/gpt-oss-20b",
        "temperature": 0.6,
        "keys_file": "./secrets/groq_keys.txt"
    },

    "settings/gemini_audio.json": {
        "model": "gemini-2.5-flash-preview-tts",
        "voice": "schedar",
        "sample_rate": 24000
    },

    "settings/gemini_image.json": {
        "model": "gemini-2.5-flash-image",
        "aspect_ratio": "16:9",
        "width": 1344,
        "height": 768
    },

    "settings/moviepy.json": {
        "fps": 30,
        "codec": "libx264",
        "audio_codec": "aac"
    },

    "prompts/shared/personality.json": {
        "persona": (
            "Leandrinho, professor brasileiro animado, didático, moderno, "
            "estilo YouTuber, focado em repetição, clareza e motivação."
        )
    },

    "prompts/groq/lesson_prompt.json": {
        "template": (
            "You are {{persona}}.\n"
            "Generate ONLY valid JSON for the word '{{word}}', following "
            "the predefined WORD_BANK structure, using repetition and "
            "simple progressive examples (A1 → B2)."
        )
    },

    "prompts/gemini/image_prompt.json": {
        "template": (
            "Create a vibrant educational thumbnail for '{{word}}' featuring "
            "Leandrinho teaching English in a friendly, modern YouTube style."
        )
    }
}

# --------------------------------------------------
# Execução
# --------------------------------------------------

def main():
    print("\n🚀 Inicializando estrutura do OptimizedVideoPipeline...\n")

    ensure_dir(ROOT)

    # Criar diretórios
    for d in DIRS:
        ensure_dir(ROOT / d)

    # Criar arquivos vazios
    for f in FILES:
        ensure_file(ROOT / f)

    # Criar JSONs
    for path, data in JSON_FILES.items():
        ensure_json(ROOT / path, data)

    print("\n✅ Estrutura criada com sucesso (ou já existente).")
    print("🔁 Script idempotente — seguro para reexecução.\n")

if __name__ == "__main__":
    main()
