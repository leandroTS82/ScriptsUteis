import os
import sys
import json
import re
import unicodedata

from generate_script import generate_lesson_json
from generate_audio_text import build_tts_text
from generate_audio import generate_audio

# IMPORTA DOIS MOTORES DE IMAGEM
from generate_image import generate_image                  # IA
from generate_image_fixed import generate_image_fixed      # IMAGEM FIXA

from generate_video import build_video


# ==============================================================
# CONFIGURAÇÃO GLOBAL
# ==============================================================

USE_FIXED_IMAGE = False  # TRUE → sempre imagem fixa
FIXED_IMAGE_PATH = r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\assets\default_bg.png"


# ------------------------------------------------------
# Sanitização do nome (FALTAVA!)
# ------------------------------------------------------
def sanitize_filename(text):
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode()
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s_-]", "", text)
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


# ------------------------------------------------------
# TESTE DE ÁUDIO — FLAG: --testAudio
# ------------------------------------------------------
def run_test_audio():
    print("🎧 MODO DE TESTE DE ÁUDIO ATIVADO — --testAudio\n")
    voiceTest = "schedar"

    test_text = f"""
    <break time="0.4s"/>
    Fala galera! {voiceTest} aqui <break time="0.5s"/>
    Hoje vamos testar a nova voz do Leandrinho!
    <break time="0.7s"/>
    
    Listen carefully... <break time="0.6s"/>

    Example sentence number one. <break time="0.8s"/>
    Example sentence number two. <break time="0.8s"/>
    Example sentence number three. <break time="1s"/>

    Obrigado por praticar comigo! <break time="0.5s"/> 
    See you in the next class! <break time="0.3s"/>
    Fui!
    """

    os.makedirs("outputs/audio", exist_ok=True)

    output_path = f"outputs/audio/{voiceTest}_test_audio.wav"
    generate_audio(test_text, output_path, voice=voiceTest)

    print("\n  Áudio de teste gerado!")
    print(f"➡ Arquivo: {output_path}")
    sys.exit(0)


# ------------------------------------------------------
# SCRIPT PRINCIPAL
# ------------------------------------------------------

# Roda somente teste de áudio
if "--testAudio" in sys.argv:
    run_test_audio()


if len(sys.argv) < 2:
    print("Uso: python main.py palavra_ou_frase  ou  python main.py --testAudio")
    exit(1)


RAW_WORD = sys.argv[1].strip()
SAFE_NAME = sanitize_filename(RAW_WORD)

if not SAFE_NAME:
    print("Erro: palavra inválida após sanitização.")
    exit(1)

print(f"📌 Gerando vídeo para: {RAW_WORD}")
print(f"➡ Nome seguro do arquivo: {SAFE_NAME}")

os.makedirs("outputs/audio", exist_ok=True)
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
# 2) Construir texto do TTS
# ----------------------------------------------------
tts_text = build_tts_text(lesson)


# ----------------------------------------------------
# 3) Gerar IMAGEM
# ----------------------------------------------------
img_path = f"outputs/images/{SAFE_NAME}.png"

if USE_FIXED_IMAGE:
    print("🖼️ Modo IMAGEM FIXA ativado!")
    generate_image_fixed(img_path, FIXED_IMAGE_PATH, mode="landscape")
else:
    print("🧠 Gerando imagem via IA Gemini...")
    generate_image(RAW_WORD, img_path, mode="landscape")


# ----------------------------------------------------
# 4) Gerar ÁUDIO
# ----------------------------------------------------
audio_path = f"outputs/audio/{SAFE_NAME}.wav"
generate_audio(tts_text, audio_path, voice="schedar")

"""
✅ Vozes disponíveis (lista oficial da API):
achernar, achird, algenib, algieba, alnilam, aoede, autonoe, 
callirrhoe, charon, despina, enceladus, erinome, fenrir, gacrux, 
iapetus, kore, laomedeia, leda, orus, puck, pulcherrima, rasalgethi, 
sadachbia, sadaltager, schedar, sulafat, umbriel, vindemiatrix, 
zephyr, zubenelgenubi

| **Voz**        | **Gênero / Timbre**        | **Energia / Estilo**                  | **Observação**               |
| -------------- | -------------------------- | ------------------------------------- | ---------------------------- |
| **algenib**    | Masculino — jovem, natural | Equilibrada, clara, educativa         | **Melhor para o Leandrinho** |
| **rasalgethi** | Masculino — grave          | Séria, firme                          | Boa para narrativas          |
| **schedar**    | Masculino — médio-grave    | Expressiva, dinâmica                  | Ótima para ensino            |
| fenrir         | Masculino — jovem          | Energia alta, mas às vezes comprimida | Pode soar “esquilo”          |
| gacrux         | Masculino — leve           | Suave, calmo                          | Bom para stories             |
| iapetus        | Masculino — neutro         | Regular                               | Genérico                     |
| puck           | Masculino — suave          | Relaxado                              | Menos impacto                |
| zephyr         | Neutro leve                | Suave, rápido                         | Não indicado para ensino     |
| aoede          | Feminino leve              | Suave                                 | Não combina com o personagem |
| laomedeia      | Feminino médio             | Expressiva                            | Não indicado                 |
| leda           | Feminino suave             | Calma                                 | Não indicado                 |
| autonoe        | Feminino neutro            | Monótona                              | Fraca para ensino            |
| pulcherrima    | Feminino jovem             | Alegre                                | Não indicado                 |
| demais vozes…  | Diversos                   | —                                     | Pouco usadas                 |


"""


# ----------------------------------------------------
# 5) Gerar VÍDEO FINAL
# ----------------------------------------------------
video_path = f"outputs/videos/{SAFE_NAME}.mp4"
build_video(SAFE_NAME, "outputs/images", "outputs/audio", video_path)

print("\n  VÍDEO FINAL GERADO:")
print(video_path)
print(f"📁 JSON correspondente: {json_path}")
