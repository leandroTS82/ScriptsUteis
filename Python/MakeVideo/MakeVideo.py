r"""
===============================================================
 Script: MakeVideo.py
 Autor: Leandro
===============================================================
📌 O que este script faz?
---------------------------------------------------------------
Gera vídeos educativos (MP4) a partir de um arquivo JSON
com imagem de fundo, TTS (Google Cloud ou gTTS), legendas
e música de fundo suave com volume reduzido.

💡 Características principais:
---------------------------------------------------------------
 - Suporte a múltiplos backgrounds (imagem, GIF, vídeo)
 - Fundo desfocado proporcional (sem distorção)
 - Fundo translúcido atrás do texto
 - Controle global de pausa (PAUSE_MULTIPLIER)
 - Ajuste de velocidade por idioma (VOICE_SPEED_ADJUST)
 - Feedback em tempo real
 - Música de fundo contínua com fade in/out
 - Verificação de arquivo existente (evita recriação)
 - Geração de vídeo único (_FULL)
===============================================================
"""

import os
import json
import glob
import shutil
from datetime import datetime
from gtts import gTTS
from PIL import Image, ImageFilter
from moviepy.editor import (
    AudioFileClip, TextClip, ImageClip, ColorClip, VideoFileClip,
    CompositeVideoClip, concatenate_videoclips, CompositeAudioClip
)
from moviepy.config import change_settings
from google.cloud import texttospeech

# ------------------------------------------------------------
# Compatibilidade com Pillow 10+
# ------------------------------------------------------------
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
OUTPUT_DIR = "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\LTS SP Site - Audios para estudar inglês\\VideosGeradosPorScript\\GOOGLE_TTS\\WordBank"
TEXT_BG_COLOR = (0, 0, 0)
TEXT_BG_OPACITY = 0.55
BLUR_AMOUNT = 18
SUBTITLE_POSITION = "bottom"

# ------------------------------------------------------------
# CONTROLES DE PAUSA E VELOCIDADE
# ------------------------------------------------------------
PAUSE_MULTIPLIER = 1.2
VOICE_SPEED_ADJUST = {
    "pt": 1.0,
    "en": 0.75,
    "es": 1.0,
    "fr": 1.0
}

# ============================================================
# CONFIGURAÇÃO DE VOZ
# ============================================================
VOICE_MODE = "GOOGLE_TTS"  # "GTTS" ou "GOOGLE_TTS"
VOICE_TYPE = "male"
ENABLE_FALLBACK = True
GOOGLE_TTS_CREDENTIALS = os.path.join(os.path.dirname(__file__), "google-tts.json")

default_voiceSpeed = {"pt": 3, "en": 1, "es": 2, "fr": 2}
default_repeat = {"pt": 1, "en": 2, "es": 1, "fr": 1}

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

# ============================================================
# MÚSICA DE FUNDO
# ============================================================
# BACKGROUND_MUSIC = "C:\\dev\\scripts\\ScriptsUteis\\Python\\MakeVideo\\MediaContent\\music\\gorila-315977.mp3"
BACKGROUND_MUSIC = ""
MUSIC_VOLUME = 0.10
VOICE_VOLUME = 1.0
MUSIC_FADE_DURATION = 2.0
MUSIC_LOOP = False
MUSIC_START_AT = 10
MUSIC_STOP_AT = 60

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
    """Cria versão desfocada da imagem mantendo proporção e centralização."""
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
    """Remove o diretório temporário após conclusão."""
    try:
        if os.path.exists(base_dir):
            shutil.rmtree(base_dir)
            print(f"🧹 Diretório temporário removido: {base_dir}")
    except Exception as e:
        print(f"⚠️ Erro ao remover temporários: {e}")

# ============================================================
# TTS
# ============================================================
def generate_tts_google(text, lang, velocidade, filename, voice="female"):
    try:
        client = texttospeech.TextToSpeechClient.from_service_account_file(GOOGLE_TTS_CREDENTIALS)
        lang_code = lang + "-BR" if lang == "pt" else lang
        name = VOICE_MAP.get((lang, voice), f"{lang_code}-Wavenet-A")
        rate = (1.0 + ((velocidade - 1) * 0.1)) * VOICE_SPEED_ADJUST.get(lang, 1.0)
        pitch = 0.5 if voice == "female" else -1.0

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
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(filename)
    return filename


def generate_tts(text, lang, velocidade, filename, voice_type):
    if VOICE_MODE == "GOOGLE_TTS":
        return generate_tts_google(text, lang, velocidade, filename, voice_type)
    else:
        return generate_tts_gtts(text, lang, filename)

# ============================================================
# CLIPES DE VÍDEO
# ============================================================
def get_background_clip(path, duration):
    """Retorna clip de fundo (imagem, GIF ou vídeo)."""
    ext = path.lower()
    if ext.endswith((".gif", ".mp4", ".mov", ".avi", ".mkv")):
        clip = VideoFileClip(path).loop(duration=duration)
        clip = clip.resize(height=VIDEO_SIZE[1]).set_position("center")
    else:
        clip = ImageClip(path).resize(height=VIDEO_SIZE[1]).set_position("center")
    return clip.set_duration(duration)


def create_text_clip(text, duration, blurred_image, sharp_image):
    """Cria texto com fundo borrado e imagem nítida centralizada."""
    bg_blurred = get_background_clip(blurred_image, duration)
    sharp_clip = get_background_clip(sharp_image, duration).resize(height=int(VIDEO_SIZE[1] * 0.9)).set_position("center")

    txt_clip = TextClip(
        text, fontsize=50, color=TEXT_COLOR, font=FONT,
        method="caption", align="center", size=(int(VIDEO_SIZE[0]*0.9), None)
    ).set_duration(duration)

    txt_bg = ColorClip(size=(int(VIDEO_SIZE[0]*0.9), txt_clip.h + 30), color=TEXT_BG_COLOR)
    txt_bg = txt_bg.set_opacity(TEXT_BG_OPACITY).set_duration(duration)

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
    return txt_clip.set_audio(audio.volumex(VOICE_VOLUME))


def process_block(items, base_dir, velocidades, repeat_each, voice_type):
    clips = []
    idx = 1
    current_bg = BACKGROUND_IMAGE
    for item in items:
        sub_items = item if isinstance(item, list) else [item]
        if "background" in sub_items[0]:
            current_bg = sub_items[0]["background"]
        blurred_path = os.path.join(base_dir, f"blurred_{idx}.jpg")
        generate_blurred_background(current_bg, blurred_path)
        print(f"🖼️ Fundo atual: {current_bg}")
        for sub in sub_items:
            if "text" not in sub or "lang" not in sub:
                continue
            lang = sub["lang"]
            text = sub["text"]
            velocidade = sub.get("VoiceSpeed", velocidades.get(lang, 2))
            rep = sub.get("repeat", repeat_each.get(lang, 1))
            for r in range(rep):
                print(f"🎙️ [{lang}] {text[:60]}...")
                clip = create_video_segment(text, lang, velocidade, f"{idx}_{r}", base_dir, voice_type, blurred_path, current_bg)
                clips.append(clip)
            if "pause" in sub:
                pause_dur = (sub["pause"] / 1000) * PAUSE_MULTIPLIER
                clips.append(get_background_clip(current_bg, pause_dur))
                print(f"⏸️ Pausa ajustada: {pause_dur:.2f}s")
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
    velocidades.update(conteudo.get("velocidades", {}))
    repeat_each.update(conteudo.get("repeat_each", {}))
    nome_arquivos = conteudo.get("nome_arquivos", "EstudoIdiomas")

    final_path = os.path.join(OUTPUT_DIR, f"{nome_arquivos}_FULL.mp4")

    introducao = conteudo.get("introducao")
    base_dir = ensure_dirs()
    print(f"🎬 Iniciando geração de vídeo ({VOICE_MODE})...")

    all_clips = []
    if introducao:
        blurred_path = os.path.join(base_dir, "blurred_intro.jpg")
        generate_blurred_background(BACKGROUND_IMAGE, blurred_path)
        intro_clip = create_video_segment(introducao, "pt", velocidades.get("pt", 2), "intro", base_dir, VOICE_TYPE, blurred_path, BACKGROUND_IMAGE)
        all_clips.append(intro_clip)

    secoes = [v for k, v in conteudo.items() if k not in ("velocidades", "repeat_each", "introducao", "nome_arquivos")]
    for section in secoes:
        if isinstance(section, list) and len(section) > 0:
            if isinstance(section[0], list):
                for bloco in section:
                    all_clips.extend(process_block(bloco, base_dir, velocidades, repeat_each, VOICE_TYPE))
            else:
                all_clips.extend(process_block(section, base_dir, velocidades, repeat_each, VOICE_TYPE))

    if all_clips:
        print("🧩 Montando vídeo final...")
        final_video = concatenate_videoclips(all_clips, method="compose")
        final_audio = final_video.audio

        if BACKGROUND_MUSIC and os.path.exists(BACKGROUND_MUSIC):
            bg_music = AudioFileClip(BACKGROUND_MUSIC).subclip(MUSIC_START_AT, MUSIC_STOP_AT)
            bg_music = bg_music.volumex(MUSIC_VOLUME)
            bg_music = bg_music.audio_fadein(MUSIC_FADE_DURATION).audio_fadeout(MUSIC_FADE_DURATION)
            if MUSIC_LOOP:
                bg_music = bg_music.audio_loop(duration=final_video.duration)
            bg_music = bg_music.set_duration(final_video.duration)
            final_audio = CompositeAudioClip([final_audio, bg_music])
            print(f"🎶 Música adicionada de {MUSIC_START_AT}s a {MUSIC_STOP_AT}s")

        final_video = final_video.set_audio(final_audio)
        final_video.write_videofile(final_path, fps=24, codec="libx264", audio_codec="aac", preset="medium")
        print(f"✅ Vídeo completo gerado: {final_path}")

    cleanup_temp(base_dir)
    print("  Processo finalizado com sucesso!")


if __name__ == "__main__":
    main()
