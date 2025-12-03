from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import random
import math
import os

# ----------------------------------------------------------
# CONFIGURAÇÕES DO VÍDEO
# ----------------------------------------------------------
VIDEO_W = 1920
VIDEO_H = 1080

BALLOON_W = 700
BALLOON_H = 220
FONT_SIZE = 48

# Movimento suave (em pixels)
AMPLITUDE = 6      # quão longe os balões se movem
SPEED = 0.4        # velocidade (quanto menor, mais lento)

OFFSET_Y = 20      # abaixar todos os balões 20px


# ----------------------------------------------------------
# CRIA BALÃO COM TEXTO
# ----------------------------------------------------------
def create_balloon(text, width=BALLOON_W, height=BALLOON_H):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 140))  # fundo translúcido
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", FONT_SIZE)
    except:
        font = ImageFont.load_default()

    # quebra automática
    words = text.split(" ")
    lines = []
    current = ""

    for w in words:
        test = (current + " " + w).strip()
        if draw.textlength(test, font=font) > width - 40:
            lines.append(current)
            current = w
        else:
            current = test
    lines.append(current)

    # centralizar verticalmente
    _, _, _, line_h = draw.textbbox((0, 0), "Ay", font=font)
    total_h = len(lines) * (line_h + 8)
    y = (height - total_h) // 2

    for line in lines:
        w_text = draw.textlength(line, font=font)
        x = (width - w_text) // 2
        draw.text((x, y), line, font=font, fill="white")
        y += line_h + 8

    return img


# ----------------------------------------------------------
# MOVIMENTO SUAVE, LENTO E NATURAL
# ----------------------------------------------------------
def smooth_motion(base_x, base_y):
    """
    Movimento suave usando seno + pequenas variações randômicas.
    """
    t_offset = random.random() * 10  # cada balão tem movimento diferente

    def anim(t):
        dx = math.sin((t + t_offset) * SPEED) * AMPLITUDE
        dy = math.cos((t + t_offset) * SPEED * 0.8) * AMPLITUDE
        return (base_x + dx, base_y + dy)

    return anim


# ----------------------------------------------------------
# MONTAGEM DO VÍDEO
# ----------------------------------------------------------
def build_video(word, images_dir, audio_dir, output_path):
    print("🎬 Montando vídeo com balões suaves...")

    audio_path = f"{audio_dir}/{word}.wav"
    bg_path = f"{images_dir}/{word}.png"

    narration = AudioFileClip(audio_path)
    duration = narration.duration

    # ----------------------------------------------------------
    # FUNDO VIA PIL
    # ----------------------------------------------------------
    pil_bg = Image.open(bg_path).convert("RGB")
    pil_bg = pil_bg.resize((VIDEO_W, VIDEO_H), Image.LANCZOS)
    bg_np = np.array(pil_bg)

    bg = ImageClip(bg_np).set_duration(duration)

    # ----------------------------------------------------------
    # CARREGA JSON
    # ----------------------------------------------------------
    import json
    json_file = f"outputs/videos/{word}.json"
    with open(json_file, "r", encoding="utf-8") as f:
        lesson_json = json.load(f)

    items = lesson_json["WORD_BANK"][0]

    balloon_texts = [
        items[0]["text"],  # palavra
        items[2]["text"],  # exemplo 1
        items[3]["text"],  # exemplo 2
        items[4]["text"],  # exemplo 3
    ]

    # ----------------------------------------------------------
    # CRIA BALÕES
    # ----------------------------------------------------------
    balloons = []
    for txt in balloon_texts:
        pil_img = create_balloon(txt)
        arr = np.array(pil_img)
        balloons.append(ImageClip(arr).set_duration(duration))

    # ----------------------------------------------------------
    # POSIÇÕES (agora com OFFSET_Y)
    # ----------------------------------------------------------
    TOP = 100 + OFFSET_Y
    SIDE = 120
    SPACING = 260

    positions = [
        (SIDE, TOP),
        (VIDEO_W - BALLOON_W - SIDE, TOP),
        (SIDE, TOP + SPACING),
        (VIDEO_W - BALLOON_W - SIDE, TOP + SPACING)
    ]

    # aplicar movimento suave
    for i in range(4):
        x, y = positions[i]
        balloons[i] = balloons[i].set_position(smooth_motion(x, y))

    # ----------------------------------------------------------
    # FINAL
    # ----------------------------------------------------------
    final = CompositeVideoClip([bg] + balloons).set_audio(narration)

    final.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac"
    )

    print("✔ Vídeo exportado:", output_path)
