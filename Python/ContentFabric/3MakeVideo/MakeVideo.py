r"""
===============================================================
 Script: MakeVideo.py
 Autor: Leandro
 Versão: Ajustada com ContentCreated + agrupamento de 10 itens
         + movimentação de vídeos + prefixo no JSON movido
===============================================================
📌 O que este script faz?
---------------------------------------------------------------
Gera vídeos educativos (MP4) a partir de um arquivo JSON
com imagem de fundo, TTS (Google Cloud ou gTTS), legendas,
e música de fundo suave com volume reduzido.

NOVO:
 • Estrutura automática em OUTPUT_DIR/ContentCreated/Lists
 • Para cada categoria (pasta dentro de ContentToCreate/Lists)
      → cria pastas equivalentes em lotes de 10 itens
      → FolderA, FolderA_2, FolderA_3 etc.
 • Move JSON processado para a pasta correta
 • Move VÍDEO FINAL para a mesma pasta
 • Aplica prefixo em JSON antes de mover
===============================================================
"""

r"""
===============================================================
 Script: MakeVideo.py
 Autor: Leandro
 Versão: TOTALMENTE CONFIGURÁVEL via makevideo.config.json
         + ContentCreated + agrupamento + prefixo + TTS
===============================================================
"""

import os
import json
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
# COMPATIBILIDADE PILLOW 10+
# ------------------------------------------------------------
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

change_settings({"IMAGEMAGICK_BINARY": "magick"})


# ============================================================
# 1) CARREGAR ARQUIVO DE CONFIGURAÇÃO
# ============================================================

CONFIG_FILE = "makevideo.config.json"

if not os.path.exists(CONFIG_FILE):
    raise FileNotFoundError(
        f"Arquivo de configuração '{CONFIG_FILE}' não encontrado."
    )

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)


# ============================================================
# 2) FUNÇÃO PARA NORMALIZAR PATHS
# ============================================================

def normalize_path(path_value):
    """
    Se o path começar com "./" → converte para caminho relativo real
    Se for um path simples (ex: "Videos") → também trata como relativo
    Se for absoluto (C:/... ou /home...) → mantém como está
    """
    if not path_value:
        return None

    path_value = path_value.replace("\\", "/")

    # Se começa com "./" ou não contém ":", tratar como relativo
    if path_value.startswith("./") or ":" not in path_value:
        base = os.path.dirname(os.path.abspath(__file__))
        fixed = os.path.abspath(os.path.join(base, path_value))
        return fixed

    # Caso contrário é absoluto
    return path_value


# ============================================================
# 3) CARREGAR TODAS AS CONFIGS COM TRATAMENTO
# ============================================================

# ----- PATHS -----
TEMP_DIR = normalize_path(CONFIG["paths"]["TEMP_DIR"])
OUTPUT_DIR = normalize_path(CONFIG["paths"]["OUTPUT_DIR"])
BACKGROUND_IMAGE = normalize_path(CONFIG["paths"]["BACKGROUND_IMAGE"])
GOOGLE_TTS_CREDENTIALS = normalize_path(CONFIG["paths"]["GOOGLE_TTS_CREDENTIALS"])

# ----- VÍDEO -----
VIDEO_SIZE = tuple(CONFIG["video"]["VIDEO_SIZE"])
FPS = CONFIG["video"]["FPS"]
TEXT_COLOR = CONFIG["video"]["TEXT_COLOR"]
FONT = CONFIG["video"]["FONT"]
TEXT_BG_COLOR = tuple(CONFIG["video"]["TEXT_BG_COLOR"])
TEXT_BG_OPACITY = CONFIG["video"]["TEXT_BG_OPACITY"]
BLUR_AMOUNT = CONFIG["video"]["BLUR_AMOUNT"]
SUBTITLE_POSITION = CONFIG["video"]["SUBTITLE_POSITION"]

BACKGROUND_MUSIC = normalize_path(CONFIG["video"]["BACKGROUND_MUSIC"])
MUSIC_VOLUME = CONFIG["video"]["MUSIC_VOLUME"]
VOICE_VOLUME = CONFIG["video"]["VOICE_VOLUME"]
MUSIC_FADE_DURATION = CONFIG["video"]["MUSIC_FADE_DURATION"]
MUSIC_LOOP = CONFIG["video"]["MUSIC_LOOP"]
MUSIC_START_AT = CONFIG["video"]["MUSIC_START_AT"]
MUSIC_STOP_AT = CONFIG["video"]["MUSIC_STOP_AT"]

# ----- PROCESSAMENTO -----
PAUSE_MULTIPLIER = CONFIG["processing"]["PAUSE_MULTIPLIER"]
JSON_PREFIX = CONFIG["processing"]["JSON_PREFIX"]
MAX_ITEMS_PER_FOLDER = CONFIG["processing"]["MAX_ITEMS_PER_FOLDER"]

# ----- TTS -----
VOICE_MODE = CONFIG["tts"]["VOICE_MODE"]
VOICE_TYPE = CONFIG["tts"]["VOICE_TYPE"]
ENABLE_FALLBACK = CONFIG["tts"]["ENABLE_FALLBACK"]

VOICE_SPEED_ADJUST = CONFIG["tts"]["VOICE_SPEED_ADJUST"]
default_voiceSpeed = CONFIG["tts"]["default_voiceSpeed"]
default_repeat = CONFIG["tts"]["default_repeat"]

# VOICE MAP expandido
VOICE_MAP = {}
for key, value in CONFIG["tts"]["VOICE_MAP"].items():
    lang, gender = key.split("_")
    VOICE_MAP[(lang, gender)] = value


# ============================================================
# 4) FUNÇÕES DA ÁREA “ContentCreated”
# ============================================================

def ensure_content_created_structure(output_dir):
    """
    Garante:
    OUTPUT_DIR/ContentCreated/Lists
    """
    base = os.path.join(output_dir, "ContentCreated", "Lists")
    os.makedirs(base, exist_ok=True)
    return base


def get_target_folder(base_lists_dir, category_name):
    """
    Cada pasta pode ter até MAX_ITEMS_PER_FOLDER itens.
    Se ultrapassar → cria category, category_2, category_3...
    """
    index = 1

    while True:
        folder_name = category_name if index == 1 else f"{category_name}_{index}"
        full_path = os.path.join(base_lists_dir, folder_name)

        if not os.path.exists(full_path):
            os.makedirs(full_path)
            return full_path

        items = [
            f for f in os.listdir(full_path)
            if f.lower().endswith(".json") or f.lower().endswith(".mp4")
        ]

        if len(items) < MAX_ITEMS_PER_FOLDER:
            return full_path

        index += 1


def move_json_to_contentcreated(json_path):
    """
    Move json → ContentCreated/Lists/<categoria>/
    Adiciona prefixo JSON_PREFIX.
    """
    base_lists_dir = ensure_content_created_structure(OUTPUT_DIR)

    filename = os.path.basename(json_path)
    final_name = JSON_PREFIX + filename

    # Determinar categoria
    parts = json_path.replace("\\", "/").split("/")
    try:
        idx = parts.index("Lists")
        category = parts[idx + 1]
    except ValueError:
        category = "Misc"

    target_folder = get_target_folder(base_lists_dir, category)
    dest = os.path.join(target_folder, final_name)

    print(f"📦 Movendo JSON para: {dest}")
    shutil.move(json_path, dest)

    return dest


def move_video_to_contentcreated(video_path, json_path):
    """
    Move vídeo final → mesma pasta do JSON movido.
    """
    base_lists_dir = ensure_content_created_structure(OUTPUT_DIR)

    filename = os.path.basename(video_path)

    parts = json_path.replace("\\", "/").split("/")
    try:
        idx = parts.index("Lists")
        category = parts[idx + 1]
    except ValueError:
        category = "Misc"

    target_folder = get_target_folder(base_lists_dir, category)
    dest = os.path.join(target_folder, filename)

    print(f"🎞 Movendo VÍDEO para: {dest}")
    shutil.move(video_path, dest)

    return dest


# ============================================================
# 5) FUNÇÕES AUXILIARES DE ARQUIVOS E DIRETÓRIOS
# ============================================================

def ensure_dirs():
    """
    Cria diretórios temporários e de saída, se necessário.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    base_dir = os.path.join(TEMP_DIR, timestamp)

    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    return base_dir


def cleanup_temp(base_dir):
    """
    Remove arquivos temporários usados durante a geração do vídeo.
    """
    try:
        if os.path.exists(base_dir):
            shutil.rmtree(base_dir)
            print(f"🧹 Diretório temporário removido: {base_dir}")
    except Exception as e:
        print(f"⚠ Erro ao remover temporários: {e}")


# ============================================================
# 6) FUNÇÕES DE FUNDO DESFOCADO
# ============================================================

def generate_blurred_background(source_path, output_path):
    """
    Cria uma versão desfocada do fundo, mantendo proporção da imagem.
    """
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


# ============================================================
# 7) FUNÇÕES DE TTS
# ============================================================

def generate_tts_google(text, lang, velocidade, filename, voice_gender):
    """
    Geração de áudio usando Google Cloud Text-To-Speech.
    """
    try:
        client = texttospeech.TextToSpeechClient.from_service_account_file(
            GOOGLE_TTS_CREDENTIALS
        )

        lang_code = lang + "-BR" if lang == "pt" else lang
        voice_name = VOICE_MAP.get((lang, voice_gender), f"{lang_code}-Wavenet-A")

        rate = (
            1.0 + ((velocidade - 1) * 0.1)
        ) * VOICE_SPEED_ADJUST.get(lang, 1.0)

        pitch = 0.5 if voice_gender == "female" else -1.0

        voice_params = texttospeech.VoiceSelectionParams(
            language_code=lang_code,
            name=voice_name,
            ssml_gender=(
                texttospeech.SsmlVoiceGender.FEMALE
                if voice_gender == "female"
                else texttospeech.SsmlVoiceGender.MALE
            )
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
        print(f"⚠ Erro no Google TTS: {ex}")
        if ENABLE_FALLBACK:
            return generate_tts_gtts(text, lang, filename)
        raise


def generate_tts_gtts(text, lang, filename):
    """
    Geração via gTTS (fallback).
    """
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(filename)
    return filename


def generate_tts(text, lang, velocidade, filename, voice_gender):
    """
    Decide qual sistema TTS usar.
    """
    if VOICE_MODE == "GOOGLE_TTS":
        return generate_tts_google(text, lang, velocidade, filename, voice_gender)

    return generate_tts_gtts(text, lang, filename)


# ============================================================
# 8) FUNÇÕES DE FUNDO / TEXTO
# ============================================================

def get_background_clip(path, duration):
    """
    Retorna o clip de fundo — imagem, GIF ou vídeo.
    """
    lower = path.lower()

    if lower.endswith((".gif", ".mp4", ".mov", ".avi", ".mkv")):
        clip = VideoFileClip(path).loop(duration=duration)
        clip = clip.resize(height=VIDEO_SIZE[1]).set_position("center")
    else:
        clip = ImageClip(path).resize(height=VIDEO_SIZE[1]).set_position("center")

    return clip.set_duration(duration)


def create_text_clip(text, duration, blurred_image, sharp_image):
    """
    Cria o clipe com:
      - fundo desfocado
      - imagem nítida (sharp)
      - fundo translúcido atrás do texto
      - texto centralizado
    """
    bg_blurred = get_background_clip(blurred_image, duration)

    sharp_clip = (
        get_background_clip(sharp_image, duration)
        .resize(height=int(VIDEO_SIZE[1] * 0.9))
        .set_position("center")
    )

    txt_clip = TextClip(
        text,
        fontsize=50,
        color=TEXT_COLOR,
        font=FONT,
        method="caption",
        align="center",
        size=(int(VIDEO_SIZE[0] * 0.9), None)
    ).set_duration(duration)

    txt_bg = (
        ColorClip(
            size=(int(VIDEO_SIZE[0] * 0.9), txt_clip.h + 30),
            color=TEXT_BG_COLOR
        )
        .set_opacity(TEXT_BG_OPACITY)
        .set_duration(duration)
    )

    if SUBTITLE_POSITION == "bottom":
        pos_y = VIDEO_SIZE[1] - txt_clip.h - 80
    elif SUBTITLE_POSITION == "top":
        pos_y = 50
    else:
        pos_y = (VIDEO_SIZE[1] - txt_clip.h) // 2

    return CompositeVideoClip([
        bg_blurred,
        sharp_clip,
        txt_bg.set_position(("center", pos_y)),
        txt_clip.set_position(("center", pos_y))
    ])


# ============================================================
# 9) SEGMENTOS DE VÍDEO
# ============================================================

def create_video_segment(
    text, lang, velocidade, idx, base_dir, voice_gender,
    blurred_image, sharp_image
):
    """
    Gera TTS → gera clipe de texto → retorna clipe completo.
    """
    temp_audio = os.path.join(base_dir, f"tmp_{idx}.mp3")

    generate_tts(text, lang, velocidade, temp_audio, voice_gender)

    audio = AudioFileClip(temp_audio)
    clip = create_text_clip(text, audio.duration, blurred_image, sharp_image)

    return clip.set_audio(audio.volumex(VOICE_VOLUME))


# ============================================================
# 10) PROCESSAMENTO DE BLOCOS DO JSON
# ============================================================

def process_block(items, base_dir, velocidades, repeat_each, voice_gender):
    """
    Recebe um bloco de frases e devolve os clipes prontos para montagem.
    """
    clips = []
    idx = 1
    current_bg = BACKGROUND_IMAGE

    for item in items:
        sub_items = item if isinstance(item, list) else [item]

        # Troca de background opcional
        if "background" in sub_items[0]:
            current_bg = normalize_path(sub_items[0]["background"])

        blurred_path = os.path.join(base_dir, f"blurred_{idx}.jpg")
        generate_blurred_background(current_bg, blurred_path)

        print(f"🖼️ Fundo atual: {current_bg}")

        for sub in sub_items:
            if "text" not in sub or "lang" not in sub:
                continue

            text = sub["text"]
            lang = sub["lang"]

            velocidade = sub.get("VoiceSpeed", velocidades.get(lang, 2))
            repeat = sub.get("repeat", repeat_each.get(lang, 1))

            # TTS e clipe
            for r in range(repeat):
                print(f"🎙️ [{lang}] {text[:60]}...")
                clip = create_video_segment(
                    text, lang, velocidade,
                    f"{idx}_{r}", base_dir, voice_gender,
                    blurred_path, current_bg
                )
                clips.append(clip)

            # Pausa opcional
            if "pause" in sub:
                pausa = (sub["pause"] / 1000) * PAUSE_MULTIPLIER
                clips.append(get_background_clip(current_bg, pausa))
                print(f"⏸️ Pausa de {pausa:.2f}s")

            idx += 1

    return clips


# ============================================================
# 11) LEITURA DO JSON ATUAL (BatchMakeVideos escreve aqui)
# ============================================================

CURRENT_JSON_SOURCE_PATH = None

if os.path.exists("CURRENT_JSON_PATH.txt"):
    with open("CURRENT_JSON_PATH.txt", "r", encoding="utf-8") as f:
        CURRENT_JSON_SOURCE_PATH = f.read().strip()


# ============================================================
# 12) MÚSICA DE FUNDO
# ============================================================

def apply_background_music(final_video):
    """
    Aplica música de fundo com volume reduzido e fade, caso configurado.
    """
    if not BACKGROUND_MUSIC:
        return final_video

    if not os.path.exists(BACKGROUND_MUSIC):
        print(f"⚠ Música não encontrada: {BACKGROUND_MUSIC}")
        return final_video

    try:
        music = AudioFileClip(BACKGROUND_MUSIC)

        if MUSIC_START_AT:
            music = music.subclip(MUSIC_START_AT)

        if MUSIC_STOP_AT:
            music = music.subclip(0, MUSIC_STOP_AT)

        if MUSIC_LOOP:
            music = music.loop(duration=final_video.duration)

        music = music.volumex(MUSIC_VOLUME)

        music = music.audio_fadein(MUSIC_FADE_DURATION)
        music = music.audio_fadeout(MUSIC_FADE_DURATION)

        new_audio = CompositeAudioClip([final_video.audio.volumex(VOICE_VOLUME), music])

        return final_video.set_audio(new_audio)

    except Exception as e:
        print(f"⚠ Erro ao aplicar música de fundo: {e}")
        return final_video


# ============================================================
# 13) FUNÇÃO PRINCIPAL
# ============================================================

def main():
    if not os.path.exists("textos.json"):
        print("❌ Arquivo textos.json não encontrado.")
        return

    try:
        with open("textos.json", "r", encoding="utf-8") as f:
            conteudo = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao ler JSON: {e}")
        return

    velocidades = default_voiceSpeed.copy()
    repeat_each = default_repeat.copy()

    velocidades.update(conteudo.get("velocidades", {}))
    repeat_each.update(conteudo.get("repeat_each", {}))

    nome_arquivos = conteudo.get("nome_arquivos", "VideoGerado")

    # Caminho do vídeo final
    final_output = os.path.join(OUTPUT_DIR, f"{nome_arquivos}_FULL.mp4")

    introducao = conteudo.get("introducao")
    base_dir = ensure_dirs()

    print("=====================================================")
    print("🎬 Iniciando geração de vídeo")
    print("=====================================================")

    all_clips = []

    # ------------------------------------------------------
    # INTRODUÇÃO
    # ------------------------------------------------------
    if introducao:
        blurred_path = os.path.join(base_dir, "blurred_intro.jpg")
        generate_blurred_background(BACKGROUND_IMAGE, blurred_path)

        intro_clip = create_video_segment(
            introducao, "pt",
            velocidades.get("pt", 2),
            "intro", base_dir,
            VOICE_TYPE, blurred_path,
            BACKGROUND_IMAGE
        )
        all_clips.append(intro_clip)

    # ------------------------------------------------------
    # SEÇÕES DO JSON (WORD_BANK e outras)
    # ------------------------------------------------------
    secoes = [
        v for k, v in conteudo.items()
        if k not in ("velocidades", "repeat_each", "introducao", "nome_arquivos")
    ]

    for section in secoes:
        if isinstance(section, list) and len(section) > 0:
            if isinstance(section[0], list):
                for bloco in section:
                    all_clips.extend(
                        process_block(bloco, base_dir, velocidades, repeat_each, VOICE_TYPE)
                    )
            else:
                all_clips.extend(
                    process_block(section, base_dir, velocidades, repeat_each, VOICE_TYPE)
                )

    # ======================================================
    # 14) MONTAR VÍDEO FINAL
    # ======================================================
    if not all_clips:
        print("⚠ Nada para montar. JSON vazio?")
        return

    print("🧩 Montando vídeo final...")

    final_video = concatenate_videoclips(all_clips, method="compose")

    # Adicionar música de fundo (opcional)
    final_video = apply_background_music(final_video)

    # Exportar vídeo
    final_video.write_videofile(
        final_output,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="medium"
    )

    print(f"✅ Vídeo gerado: {final_output}")

    # ======================================================
    # 15) MOVER JSON PARA ContentCreated
    # ======================================================
    dest_json = None

    if CURRENT_JSON_SOURCE_PATH and os.path.exists(CURRENT_JSON_SOURCE_PATH):
        try:
            dest_json = move_json_to_contentcreated(CURRENT_JSON_SOURCE_PATH)
        except Exception as e:
            print(f"⚠ Erro ao mover JSON: {e}")

    # ======================================================
    # 16) MOVER VÍDEO PARA MESMA PASTA DO JSON
    # ======================================================
    if dest_json:
        try:
            move_video_to_contentcreated(final_output, dest_json)
        except Exception as e:
            print(f"⚠ Erro ao mover vídeo: {e}")

    # Remover temporários
    cleanup_temp(base_dir)

    print("🎉 Processo finalizado com sucesso!")


# ============================================================
# 17) EXECUTAR
# ============================================================

if __name__ == "__main__":
    main()
