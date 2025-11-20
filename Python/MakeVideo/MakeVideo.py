r"""
===============================================================
 Script: MakeVideo.py
 Autor: Leandro
===============================================================
📌 O que este script faz?
---------------------------------------------------------------
Gera vídeos educativos (MP4) a partir de um arquivo JSON
com imagem de fundo, TTS (voz neural Google ou Gemini) e legendas.

Suporta 3 modos de voz:
1️⃣ gTTS (padrão simples)
2️⃣ Google Cloud TTS (Wavenet neural)
3️⃣ Gemini 2.5 Pro Preview TTS (AI Studio - ultra natural)

Novidades:
 - Escolha de modo de voz e fallback
 - Controle automático de pitch e velocidade por idioma
 - Fundo desfocado proporcional (sem distorção)
 - Fundo translúcido atrás do texto (parametrizável)
 - Geração inteligente (vídeo completo ou seções + completo)
 - Total compatibilidade com JSONs de treino multilíngue

Execução:
    python .\MakeVideo.py
===============================================================

# ============================================================
# MAPEAMENTO DE VOZES - GOOGLE TTS (Wavenet)
# ============================================================

VOZES DISPONÍVEIS NO GOOGLE CLOUD TTS:

Português (Brasil)
    pt-BR-Wavenet-A  (masculina)
    pt-BR-Wavenet-B  (masculina)
    pt-BR-Wavenet-C  (feminina)
    pt-BR-Wavenet-D  (feminina)
    pt-BR-Wavenet-E  (neutra)
    pt-BR-Wavenet-F  (feminina, natural)

Inglês (EUA)
    en-US-Wavenet-A  (masculina)
    en-US-Wavenet-D  (masculina, suave)
    en-US-Wavenet-F  (feminina, clara)
    en-US-Wavenet-H  (feminina, alegre)

Espanhol
    es-ES-Wavenet-B  (masculina)
    es-ES-Wavenet-C  (feminina)

Francês
    fr-FR-Wavenet-B  (masculina)
    fr-FR-Wavenet-C  (feminina)



# ============================================================
# MAPEAMENTO DE VOZES - GEMINI AI STUDIO
# ============================================================

VOZES DISPONÍVEIS NO GEMINI 2.5 PRO PREVIEW TTS:

- Zephyr → Bright, higher pitch (ideal para introduções)
- Puck   → Upbeat, middle pitch (neutra, educativa)
- Charon → Informative, lower pitch (explicações em PT)
- Kore   → Firm, middle pitch (narrações consistentes)
- Fenrir → Excitable, lower middle pitch (mistura perfeita PT/EN)

"""

import os
import json
import shutil
import base64
import requests
from datetime import datetime
from gtts import gTTS
from PIL import Image, ImageFilter
from moviepy.editor import (
    AudioFileClip, TextClip, ImageClip, ColorClip,
    CompositeVideoClip, concatenate_videoclips
)
from moviepy.config import change_settings
from google.cloud import texttospeech

# --- Corrige compatibilidade Pillow 10+ ---
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

change_settings({"IMAGEMAGICK_BINARY": "magick"})

# ============================================================
# CONFIGURAÇÕES GERAIS
# ============================================================
VIDEO_SIZE = (1280, 720)
TEXT_COLOR = "white"
FONT = "Arial-Bold"
BACKGROUND_IMAGE = "Teacher_Leandrinho.png"

TEMP_DIR = "./temp"
OUTPUT_DIR = "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\LTS SP Site - Audios para estudar inglês\\VideosGeradosPorScript\LessonsGOOGLE_TTS"
TEXT_BG_COLOR = (0, 0, 0)
TEXT_BG_OPACITY = 0.55
BLUR_AMOUNT = 18
SUBTITLE_POSITION = "bottom"

# ============================================================
# CONFIGURAÇÃO DE VOZ
# ============================================================
VOICE_MODE = "GOOGLE_TTS"   # "GTTS", "GOOGLE_TTS" ou "GEMINI"
VOICE_TYPE = "male"
ENABLE_FALLBACK = True

GOOGLE_TTS_CREDENTIALS = os.path.join(os.path.dirname(__file__), "google-tts.json")
GEMINI_KEY_PATH = os.path.join(os.path.dirname(__file__), "google-gemini-key.txt")

VOICE_MAP = {
    ("pt", "female"): "pt-BR-Wavenet-F",
    ("pt", "male"): "pt-BR-Wavenet-B",
    ("en", "female"): "en-US-Wavenet-F",
    ("en", "male"): "en-US-Wavenet-D",
    ("es", "female"): "es-ES-Wavenet-C",
    ("es", "male"): "es-ES-Wavenet-B",
    ("fr", "female"): "fr-FR-Wavenet-C",
    ("fr", "male"): "fr-FR-Wavenet-B",
}

default_voiceSpeed = {"pt": 3, "en": 1, "es": 2, "fr": 2}
default_repeat = {"pt": 1, "en": 2, "es": 1, "fr": 1}

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def ensure_dirs():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    base_dir = os.path.join(TEMP_DIR, timestamp)
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return base_dir


def generate_blurred_background(source_path, output_path):
    img = Image.open(source_path).convert("RGB")
    img_ratio = img.width / img.height
    video_ratio = VIDEO_SIZE[0] / VIDEO_SIZE[1]
    if img_ratio > video_ratio:
        new_height = VIDEO_SIZE[1]
        new_width = int(img_ratio * new_height)
    else:
        new_width = VIDEO_SIZE[0]
        new_height = int(new_width / img_ratio)
    img = img.resize((new_width, new_height), Image.LANCZOS)
    blurred = img.filter(ImageFilter.GaussianBlur(radius=BLUR_AMOUNT))
    left = (blurred.width - VIDEO_SIZE[0]) // 2
    top = (blurred.height - VIDEO_SIZE[1]) // 2
    cropped = blurred.crop((left, top, left + VIDEO_SIZE[0], top + VIDEO_SIZE[1]))
    cropped.save(output_path)
    return output_path


def cleanup_temp(base_dir):
    """Remove o diretório temporário"""
    try:
        if os.path.exists(base_dir):
            shutil.rmtree(base_dir)
            print(f"🧹 Diretório temporário removido: {base_dir}")
    except Exception as e:
        print(f"⚠️ Erro ao remover temporários: {e}")


# ============================================================
# GERAÇÃO DE TTS
# ============================================================

def generate_tts_gemini(text, lang, filename):
    """Gera voz natural usando Gemini 2.5 Pro Preview TTS via REST API"""
    try:
        if not os.path.exists(GEMINI_KEY_PATH):
            raise FileNotFoundError("Arquivo google-gemini-key.txt não encontrado.")
        with open(GEMINI_KEY_PATH) as f:
            key = f.read().strip()

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-preview-tts:generateContent?key={key}"

        if lang == "pt":
            style = "Read aloud in Brazilian Portuguese with a lively, warm, and encouraging teacher tone."
        elif lang == "en":
            style = "Read aloud in English with a clear, calm, and friendly educational tone."
        else:
            style = f"Read aloud in {lang} with a natural and instructive tone."

        payload = {
            "contents": [{"parts": [{"text": f"{style}\n\n{text}"}]}]
        }

        headers = {"Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"Erro Gemini: {response.status_code} {response.text}")

        data = response.json()
        audio_b64 = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("inline_data", {})
            .get("data")
        )
        if not audio_b64:
            raise RuntimeError("A resposta do Gemini não contém dados de áudio base64.")
        audio_bytes = base64.b64decode(audio_b64)

        with open(filename, "wb") as f:
            f.write(audio_bytes)
        return filename

    except Exception as ex:
        print(f"⚠️ Erro no Gemini TTS: {ex}")
        if ENABLE_FALLBACK:
            return generate_tts_google(text, lang, 1, filename, VOICE_TYPE)
        raise


def generate_tts_google(text, lang, velocidade, filename, voice="female"):
    """Usa Google Cloud Text-to-Speech (Wavenet neural)"""
    try:
        client = texttospeech.TextToSpeechClient.from_service_account_file(GOOGLE_TTS_CREDENTIALS)
        lang_code = lang + "-BR" if lang == "pt" else lang
        name = VOICE_MAP.get((lang, voice), f"{lang_code}-Wavenet-A")

        # Controle de entonação e velocidade natural por idioma
        if lang == "pt":
            pitch = 2.0 if voice == "female" else 0.5
            rate = 1.05  # levemente mais rápido, tom natural de instrutor
        elif lang == "en":
            pitch = -0.5  # tom mais suave
            rate = 0.85   # fala mais lenta e clara (ideal para aprendizado)
        elif lang == "es":
            pitch = 0.5
            rate = 0.95
        else:
            pitch = 0.0
            rate = 0.9

        voice_params = texttospeech.VoiceSelectionParams(
            language_code=lang_code,
            name=name,
            ssml_gender=texttospeech.SsmlVoiceGender.MALE if voice == "male" else texttospeech.SsmlVoiceGender.FEMALE
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=rate,
            pitch=pitch
        )
        response = client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=text),
            voice=voice_params,
            audio_config=audio_config
        )
        with open(filename, "wb") as out:
            out.write(response.audio_content)
        return filename
    except Exception as ex:
        print(f"⚠️ Erro no Google TTS: {ex}")
        if ENABLE_FALLBACK:
            return generate_tts_gtts(text, lang, filename)
        raise


def generate_tts_gtts(text, lang, filename):
    """Fallback simples com gTTS"""
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(filename)
    return filename


def generate_tts(text, lang, velocidade, filename, voice_type):
    """Seleciona o modo TTS configurado"""
    if VOICE_MODE == "GEMINI":
        return generate_tts_gemini(text, lang, filename)
    elif VOICE_MODE == "GOOGLE_TTS":
        return generate_tts_google(text, lang, velocidade, filename, voice_type)
    else:
        return generate_tts_gtts(text, lang, filename)


# ============================================================
# CRIAÇÃO DE CLIPES
# ============================================================

def create_text_clip(text, duration, blurred_image, sharp_image):
    if not text.strip():
        return ImageClip(sharp_image).set_duration(duration)
    bg_blurred = ImageClip(blurred_image).set_duration(duration)
    sharp_clip = ImageClip(sharp_image).resize(height=VIDEO_SIZE[1]).set_position("center").set_duration(duration)
    txt_clip = TextClip(
        text, fontsize=50, color=TEXT_COLOR, font=FONT,
        method="caption", align="center", size=(int(VIDEO_SIZE[0]*0.9), None)
    ).set_duration(duration)
    txt_bg = ColorClip(
        size=(int(VIDEO_SIZE[0]*0.9), txt_clip.h + 30),
        color=TEXT_BG_COLOR
    ).set_opacity(TEXT_BG_OPACITY).set_duration(duration)
    pos_y = VIDEO_SIZE[1] - txt_clip.h - 80 if SUBTITLE_POSITION == "bottom" else \
            50 if SUBTITLE_POSITION == "top" else (VIDEO_SIZE[1] - txt_clip.h) // 2
    return CompositeVideoClip([
        bg_blurred,
        sharp_clip,
        txt_bg.set_position(("center", pos_y)),
        txt_clip.set_position(("center", pos_y))
    ])


def create_video_segment(text, lang, velocidade, idx, base_dir, voice_type, blurred_image, sharp_image):
    temp_audio = os.path.join(base_dir, f"tmp_{idx}.mp3")
    generate_tts(text, lang, velocidade, temp_audio, voice_type)
    audio = AudioFileClip(temp_audio)
    txt_clip = create_text_clip(text, audio.duration, blurred_image, sharp_image)
    return txt_clip.set_audio(audio)


def process_block(items, base_dir, velocidades, repeat_each, voice_type, blurred_image, sharp_image):
    clips = []
    idx = 1
    for item in items:
        if isinstance(item, dict) and "text" in item and "lang" in item:
            lang = item["lang"]
            text = item["text"]
            velocidade = item.get("VoiceSpeed", velocidades.get(lang, 2))
            rep = item.get("repeat", repeat_each.get(lang, 1))
            for r in range(rep):
                clip = create_video_segment(text, lang, velocidade, f"{idx}_{r}", base_dir, voice_type, blurred_image, sharp_image)
                clips.append(clip)
            if "pause" in item:
                clips.append(ImageClip(blurred_image).set_duration(item["pause"] / 1000))
            idx += 1
    return clips


# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

def main():
    try:
        with open("textos.json", "r", encoding="utf-8") as f:
            conteudo = json.load(f)
    except Exception as e:
        print(f"Erro ao ler JSON: {e}")
        return

    velocidades = default_voiceSpeed.copy()
    repeat_each = default_repeat.copy()
    if "velocidades" in conteudo:
        velocidades.update(conteudo["velocidades"])
    if "repeat_each" in conteudo:
        repeat_each.update(conteudo["repeat_each"])

    nome_arquivos = conteudo.get("nome_arquivos", "EstudoIdiomas")
    introducao = conteudo.get("introducao")

    secoes = [k for k in conteudo.keys() if k not in ("velocidades", "repeat_each", "introducao", "nome_arquivos")]
    gerar_separados = len(secoes) > 1

    base_dir = ensure_dirs()
    blurred_path = os.path.join(base_dir, "blurred_bg.jpg")
    generate_blurred_background(BACKGROUND_IMAGE, blurred_path)

    print(f"🎬 Gerando vídeos educativos com VOICE_MODE = {VOICE_MODE}")

    all_clips = []

    if introducao:
        intro_clip = create_video_segment(introducao, "pt", velocidades.get("pt", 2), "intro", base_dir, VOICE_TYPE, blurred_path, BACKGROUND_IMAGE)
        all_clips.append(intro_clip)

    # --- gera vídeos por seção sem perda de sincronia ---
    for section in secoes:
        print(f"📖 Seção: {section}")
        clips = process_block(conteudo[section], base_dir, velocidades, repeat_each, VOICE_TYPE, blurred_path, BACKGROUND_IMAGE)
        if clips:
            section_video = concatenate_videoclips(clips, method="compose")
            section_path = os.path.join(OUTPUT_DIR, f"{nome_arquivos}_{section}.mp4")
            section_video.write_videofile(section_path, fps=24, codec="libx264", audio_codec="aac")
            print(f"✅ Vídeo salvo: {section_path}")
            all_clips.extend(clips)

    # --- gera vídeo completo unindo os mesmos clipes (sem reimportar) ---
    if all_clips:
        final_video = concatenate_videoclips(all_clips, method="compose")
        final_path = os.path.join(OUTPUT_DIR, f"{nome_arquivos}_FULL.mp4")
        final_video.write_videofile(final_path, fps=24, codec="libx264", audio_codec="aac", preset="medium")
        print(f"🎉 Vídeo completo gerado: {final_path}")

    cleanup_temp(base_dir)
    print("✅ Processo concluído!")


if __name__ == "__main__":
    main()