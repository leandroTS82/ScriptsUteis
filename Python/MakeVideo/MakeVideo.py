r"""
===============================================================
 Script: MakeVideo.py
 Autor: Leandro
===============================================================
📌 O que este script faz?
---------------------------------------------------------------
Gera vídeos educativos (MP4) a partir de um arquivo JSON
com imagem de fundo, TTS e legendas animadas.

Novidades:
 - Fundo desfocado proporcional (sem distorção)
 - Imagem nítida sobre o fundo borrado
 - Fundo translúcido atrás do texto (parametrizável)
 - Legenda posicionável (centro, topo ou parte inferior)
 - Controle real de velocidade de voz com pitch natural
 - Limpeza automática parametrizável (temp_*, .pdf, etc.)
 - Processamento isolado em ./temp e saída final em OUTPUT_DIR
 - Geração inteligente (vídeo completo ou seções + completo)

Execução:
    python .\MakeVideo.py
===============================================================
"""

import os
import json
import glob
import shutil
from datetime import datetime
from gtts import gTTS
from pydub import AudioSegment
from PIL import Image, ImageFilter

# --- Correção Pillow 10+ ---
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

from moviepy.editor import (
    AudioFileClip, TextClip, ImageClip, ColorClip,
    CompositeVideoClip, concatenate_videoclips
)
from moviepy.config import change_settings

# ------------------------------------------------------------
# Configuração do executável do ImageMagick
# ------------------------------------------------------------
change_settings({"IMAGEMAGICK_BINARY": "magick"})

# =========================================================
# CONFIGURAÇÕES PADRÃO
# =========================================================
VIDEO_SIZE = (1280, 720)
TEXT_COLOR = "white"
FONT = "Arial-Bold"

BACKGROUND_IMAGE = "Teacher_Leandrinho.png"
VOICE_TYPE = "male"  # 'male' ou 'female'

# Fundo translúcido da legenda
TEXT_BG_COLOR = (0, 0, 0)
TEXT_BG_OPACITY = 0.55

# Desfoque
BLUR_AMOUNT = 18

# Controle de velocidade e repetição
default_voiceSpeed = {"pt": 3, "en": 1, "es": 2, "fr": 2}
default_repeat = {"pt": 1, "en": 2, "es": 1, "fr": 1}

# Legenda (posição: "center", "bottom" ou "top")
SUBTITLE_POSITION = "bottom"

# Diretórios
TEMP_DIR = "./temp"
# OUTPUT_DIR = "videos"
OUTPUT_DIR = "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\LTS SP Site - Audios para estudar inglês\\VideosGeradosPorScript\\Lessons"

# Arquivos a remover antes de mover o resultado final
CLEANUP_PATTERNS = ["tmp_*", "blurred_bg.jpg"]

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================

def ensure_dirs():
    """Cria pasta temporária com timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    base_dir = os.path.join(TEMP_DIR, timestamp)
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return base_dir


def generate_blurred_background(source_path, output_path):
    """Cria uma versão desfocada proporcional da imagem."""
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
    right = left + VIDEO_SIZE[0]
    bottom = top + VIDEO_SIZE[1]
    cropped = blurred.crop((left, top, right, bottom))
    cropped.save(output_path)
    return output_path


def generate_tts(text, lang, velocidade, filename, voice="female"):
    """Gera TTS e ajusta velocidade/pitch mantendo naturalidade."""
    if not text.strip():
        return None

    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(filename)

    sound = AudioSegment.from_file(filename, format="mp3")

    # Aceleração com compensação de pitch para manter naturalidade
    if velocidade > 1:
        rate = 1.0 + ((velocidade - 1) * 0.15)
        new_frame_rate = int(sound.frame_rate * rate)
        sound = sound._spawn(sound.raw_data, overrides={"frame_rate": new_frame_rate})
        sound = sound.set_frame_rate(44100)

        # Reduz ligeiramente o pitch se português, para evitar "voz de esquilo"
        if lang == "pt" and velocidade >= 3:
            sound = sound._spawn(sound.raw_data, overrides={"frame_rate": int(sound.frame_rate * 0.9)})
            sound = sound.set_frame_rate(44100)

    # Voz masculina = pitch mais grave
    if voice == "male":
        sound = sound._spawn(sound.raw_data, overrides={"frame_rate": int(sound.frame_rate * 0.85)})
        sound = sound.set_frame_rate(44100)

    sound.export(filename, format="mp3")
    return filename


def create_text_clip(text, duration, blurred_image, sharp_image):
    """Cria clipe com imagem nítida sobre fundo desfocado."""
    if not text.strip():
        return ImageClip(sharp_image).set_duration(duration)

    bg_blurred = ImageClip(blurred_image).set_duration(duration)
    sharp_clip = ImageClip(sharp_image).resize(height=VIDEO_SIZE[1]).set_position("center").set_duration(duration)

    txt_clip = TextClip(
        text,
        fontsize=50,
        color=TEXT_COLOR,
        font=FONT,
        method="caption",
        align="center",
        size=(int(VIDEO_SIZE[0]*0.9), None)
    ).set_duration(duration)

    txt_bg = ColorClip(
        size=(int(VIDEO_SIZE[0]*0.9), txt_clip.h + 30),
        color=TEXT_BG_COLOR
    ).set_opacity(TEXT_BG_OPACITY).set_duration(duration)

    if SUBTITLE_POSITION == "bottom":
        pos_y = VIDEO_SIZE[1] - txt_clip.h - 80
    elif SUBTITLE_POSITION == "top":
        pos_y = 50
    else:
        pos_y = (VIDEO_SIZE[1] - txt_clip.h) // 2

    txt_bg = txt_bg.set_position(("center", pos_y))
    txt_clip = txt_clip.set_position(("center", pos_y))

    return CompositeVideoClip([bg_blurred, sharp_clip, txt_bg, txt_clip])


def create_video_segment(text, lang, velocidade, idx, base_dir, voice_type, blurred_image, sharp_image):
    """Cria o clipe final com TTS e legenda."""
    temp_audio = os.path.join(base_dir, f"tmp_{idx}.mp3")
    generate_tts(text, lang, velocidade, temp_audio, voice_type)
    audio = AudioFileClip(temp_audio)
    txt_clip = create_text_clip(text, audio.duration, blurred_image, sharp_image)
    return txt_clip.set_audio(audio)


def process_block(items, base_dir, velocidades, repeat_each, voice_type, blurred_image, sharp_image):
    """Processa blocos de frases e gera clipes."""
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


def cleanup_files(base_dir, patterns):
    """Remove arquivos específicos com base nos padrões informados."""
    for pattern in patterns:
        if pattern.startswith("."):
            files = glob.glob(os.path.join(base_dir, f"*{pattern}"))
        else:
            files = glob.glob(os.path.join(base_dir, pattern))
        for file in files:
            try:
                os.remove(file)
            except Exception:
                pass


# =========================================================
# EXECUÇÃO PRINCIPAL
# =========================================================
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

    # Determina se há mais de uma seção
    seções = [k for k in conteudo.keys() if k not in ("velocidades", "repeat_each", "introducao", "nome_arquivos")]
    gerar_separados = len(seções) > 1

    base_dir = ensure_dirs()
    blurred_path = os.path.join(base_dir, "blurred_bg.jpg")
    generate_blurred_background(BACKGROUND_IMAGE, blurred_path)

    print("🎬 Gerando vídeos educativos...")

    all_clips = []

    if introducao:
        intro_clip = create_video_segment(introducao, "pt", velocidades.get("pt", 2), "intro", base_dir, VOICE_TYPE, blurred_path, BACKGROUND_IMAGE)
        all_clips.append(intro_clip)

    for section in seções:
        print(f"📖 Seção: {section}")
        clips = process_block(conteudo[section], base_dir, velocidades, repeat_each, VOICE_TYPE, blurred_path, BACKGROUND_IMAGE)
        if clips:
            section_video = concatenate_videoclips(clips, method="compose")
            if gerar_separados:
                section_path = os.path.join(base_dir, f"{nome_arquivos}_{section}.mp4")
                section_video.write_videofile(section_path, fps=24, codec="libx264", audio_codec="aac")
                print(f"✅ Vídeo salvo: {section_path}")
            all_clips.append(section_video)

    if all_clips:
        final_video = concatenate_videoclips(all_clips, method="compose")
        final_path = os.path.join(base_dir, f"{nome_arquivos}_FULL.mp4")
        final_video.write_videofile(final_path, fps=24, codec="libx264", audio_codec="aac", preset="medium")
        print(f"🎉 Vídeo completo gerado: {final_path}")

        cleanup_files(base_dir, CLEANUP_PATTERNS)
        dest_folder = os.path.join(OUTPUT_DIR, os.path.basename(base_dir))
        if os.path.exists(dest_folder):
            shutil.rmtree(dest_folder)
        shutil.move(base_dir, dest_folder)
        print(f"📦 Pasta final movida para: {dest_folder}")

    print("✅ Processo concluído!")


if __name__ == "__main__":
    main()
