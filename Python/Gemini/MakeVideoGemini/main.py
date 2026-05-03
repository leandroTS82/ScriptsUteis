import os
import sys
import json
import re
import unicodedata

from generate_audio_text import build_tts_text
from generate_video import build_video


# ==============================================================
# ██████████████████████████████████████████████████████████████
#  CONFIGURAÇÃO DE CUSTO — ajuste aqui antes de rodar
# ==============================================================

# ── Script (JSON da aula) ─────────────────────────────────────
# False → gera via Gemini (gera custo de API)
# True  → gera via Groq/llama (zero custo)
USE_ZERO_COST_SCRIPT = True

# ── Imagem ────────────────────────────────────────────────────
# False → gera imagem via IA Gemini (gera custo de API)
# True  → usa imagem fixa de assets/ (zero custo)
USE_ZERO_COST_IMAGE = True

FIXED_IMAGE_PATH = os.path.join(
    os.path.dirname(__file__), "assets", "default_bg.png"
)

# ── Áudio ─────────────────────────────────────────────────────
# "gemini"  → Gemini TTS        (gera custo de API)
# "gcloud"  → Google Cloud TTS  (requer service account)
# "edge"    → Edge TTS Microsoft (gratuito, sem key, recomendado)
AUDIO_ENGINE = "edge"

# ██████████████████████████████████████████████████████████████


# ------------------------------------------------------------------
# Validação da config de áudio
# ------------------------------------------------------------------
_VALID_AUDIO_ENGINES = ("gemini", "gcloud", "edge")
if AUDIO_ENGINE not in _VALID_AUDIO_ENGINES:
    raise ValueError(
        f"AUDIO_ENGINE inválido: '{AUDIO_ENGINE}'. "
        f"Use um de: {_VALID_AUDIO_ENGINES}"
    )


# ------------------------------------------------------------------
# Imports condicionais — carregados apenas quando necessário
# ------------------------------------------------------------------

if USE_ZERO_COST_SCRIPT:
    from generate_script_groq import generate_lesson_json
else:
    from generate_script import generate_lesson_json

if USE_ZERO_COST_IMAGE:
    from generate_image_zero_cost import generate_image_zero_cost
else:
    from generate_image import generate_image
    from generate_image_fixed import generate_image_fixed   # fallback legacy

if AUDIO_ENGINE == "gcloud":
    from generate_audio_gcloud import generate_audio_gcloud
elif AUDIO_ENGINE == "edge":
    from generate_audio_edge import generate_audio_edge
else:
    from generate_audio import generate_audio


# ------------------------------------------------------------------
# Sanitização do nome de arquivo
# ------------------------------------------------------------------

def sanitize_filename(text):
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode()
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s_-]", "", text)
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


# ------------------------------------------------------------------
# Label legível para o log
# ------------------------------------------------------------------

_AUDIO_LABELS = {
    "gemini": "Gemini TTS",
    "gcloud": "Google Cloud TTS",
    "edge":   "Edge TTS (Microsoft Neural)",
}


# ------------------------------------------------------------------
# TESTE DE ÁUDIO — FLAG: --testAudio
# ------------------------------------------------------------------

def run_test_audio():
    print("🎧 MODO DE TESTE DE ÁUDIO ATIVADO — --testAudio\n")
    print(f"   Motor: {_AUDIO_LABELS[AUDIO_ENGINE]}\n")

    os.makedirs("outputs/audio", exist_ok=True)

    test_lesson = {
        "repeat_each": {"pt": 1, "en": 2},
        "introducao": "Hey everyone! Leandrinho here. Let's test the new voice!",
        "nome_arquivos": "test",
        "WORD_BANK": [
            [
                {"lang": "en", "text": "test",                              "pause": 800},
                {"lang": "pt", "text": "Teste de voz do Leandrinho."},
                {"lang": "en", "text": "Example sentence number one.",      "pause": 800},
                {"lang": "en", "text": "Example sentence number two.",      "pause": 800},
                {"lang": "en", "text": "Thank you for practicing with me!", "pause": 1000},
                {"lang": "pt", "text": "Até a próxima aula!"},
            ]
        ]
    }

    if AUDIO_ENGINE == "gcloud":
        output_path = "outputs/audio/gcloud_test_audio.wav"
        generate_audio_gcloud(test_lesson, output_path)
    elif AUDIO_ENGINE == "edge":
        output_path = "outputs/audio/edge_test_audio.wav"
        generate_audio_edge(test_lesson, output_path)
    else:
        voice = "schedar"
        test_text = (
            '<break time="0.4s"/>'
            f'Fala galera! {voice} aqui <break time="0.5s"/>'
            'Hoje vamos testar a nova voz do Leandrinho!'
            '<break time="0.7s"/>'
            'Listen carefully... <break time="0.6s"/>'
            'Example sentence number one. <break time="0.8s"/>'
            'Example sentence number two. <break time="0.8s"/>'
            'Example sentence number three. <break time="1s"/>'
            'Obrigado por praticar comigo! <break time="0.5s"/>'
            'See you in the next class! <break time="0.3s"/>Fui!'
        )
        output_path = f"outputs/audio/{voice}_test_audio.wav"
        generate_audio(test_text, output_path, voice=voice)

    print(f"\n✔  Áudio de teste gerado!")
    print(f"➡ Arquivo: {output_path}")
    sys.exit(0)


# ------------------------------------------------------------------
# SCRIPT PRINCIPAL
# ------------------------------------------------------------------

if "--testAudio" in sys.argv:
    run_test_audio()

if len(sys.argv) < 2:
    print("Uso: python main.py palavra_ou_frase  ou  python main.py --testAudio")
    exit(1)

RAW_WORD  = sys.argv[1].strip()
SAFE_NAME = sanitize_filename(RAW_WORD)

if not SAFE_NAME:
    print("Erro: palavra inválida após sanitização.")
    exit(1)

print(f"📌 Gerando vídeo para: {RAW_WORD}")
print(f"➡ Nome seguro do arquivo: {SAFE_NAME}")
print(f"   Script : {'Groq/llama (zero custo)'    if USE_ZERO_COST_SCRIPT else 'Gemini IA'}")
print(f"   Imagem : {'Zero-cost (fixa)'           if USE_ZERO_COST_IMAGE  else 'Gemini IA'}")
print(f"   Áudio  : {_AUDIO_LABELS[AUDIO_ENGINE]}")

os.makedirs("outputs/audio",  exist_ok=True)
os.makedirs("outputs/images", exist_ok=True)
os.makedirs("outputs/videos", exist_ok=True)


# ----------------------------------------------------
# 1) Gerar JSON da aula
# ----------------------------------------------------
try:
    lesson = generate_lesson_json(RAW_WORD)
except Exception as e:
    print("❌ Erro crítico ao gerar JSON:")
    print(e)
    sys.exit(1)

lesson["nome_arquivos"] = SAFE_NAME

json_path = f"outputs/videos/{SAFE_NAME}.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(lesson, f, ensure_ascii=False, indent=2)

print(f"✔ JSON salvo em: {json_path}")


# ----------------------------------------------------
# 2) Construir texto do TTS  (usado apenas pelo Gemini TTS)
# ----------------------------------------------------
tts_text = build_tts_text(lesson)


# ----------------------------------------------------
# 3) Gerar IMAGEM
# ----------------------------------------------------
img_path = f"outputs/images/{SAFE_NAME}.png"

if USE_ZERO_COST_IMAGE:
    print("🖼️  Modo ZERO COST: usando imagem fixa.")
    generate_image_zero_cost(img_path, FIXED_IMAGE_PATH, mode="landscape")
else:
    print("🧠 Gerando imagem via IA Gemini...")
    generate_image(RAW_WORD, img_path, mode="landscape")


# ----------------------------------------------------
# 4) Gerar ÁUDIO
# ----------------------------------------------------
audio_path = f"outputs/audio/{SAFE_NAME}.wav"

if AUDIO_ENGINE == "gcloud":
    print("🎤 Gerando áudio via Google Cloud TTS...")
    generate_audio_gcloud(lesson, audio_path)
elif AUDIO_ENGINE == "edge":
    print("🎤 Gerando áudio via Edge TTS (Microsoft Neural)...")
    generate_audio_edge(lesson, audio_path)
else:
    print("🎤 Gerando áudio via Gemini TTS...")
    generate_audio(tts_text, audio_path, voice="schedar")


# ----------------------------------------------------
# 5) Gerar VÍDEO FINAL
# ----------------------------------------------------
video_path = f"outputs/videos/{SAFE_NAME}.mp4"
build_video(SAFE_NAME, "outputs/images", "outputs/audio", video_path)

print("\n✅ VÍDEO FINAL GERADO:")
print(video_path)
print(f"📄 JSON correspondente: {json_path}")