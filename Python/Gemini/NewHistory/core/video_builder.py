from moviepy.editor import VideoClip, AudioFileClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import re

VIDEO_W = 1920
VIDEO_H = 1080
FPS = 30

SUBTITLE_MAX_WIDTH = int(VIDEO_W * 0.80)
SUBTITLE_BOTTOM_MARGIN = 90
SUBTITLE_PADDING = 30
SUBTITLE_BG_ALPHA = 160
SUBTITLE_RADIUS = 25


# --------------------------------------------------
# SRT PARSER
# --------------------------------------------------

def parse_srt(path: str):
    with open(path, encoding="utf-8") as f:
        blocks = re.split(r"\n\s*\n", f.read().strip())

    def parse_time(t):
        h, m, rest = t.split(":")
        s, ms = rest.split(",")
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

    segments = []
    for b in blocks:
        lines = b.splitlines()
        if len(lines) >= 3:
            start, end = lines[1].split(" --> ")
            segments.append(
                (parse_time(start), parse_time(end), " ".join(lines[2:]))
            )
    return segments


# --------------------------------------------------
# SUBTITLE RENDER
# --------------------------------------------------

def draw_subtitle(frame: Image.Image, text: str, font: ImageFont.FreeTypeFont):
    img = frame.copy().convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Quebra de linhas baseada na largura real do texto
    words = text.split()
    lines = []
    current = ""

    for w in words:
        test = f"{current} {w}".strip()
        if draw.textlength(test, font=font) <= SUBTITLE_MAX_WIDTH:
            current = test
        else:
            lines.append(current)
            current = w

    if current:
        lines.append(current)

    # Métricas
    _, _, _, line_height = draw.textbbox((0, 0), "Ay", font=font)

    box_height = (
        len(lines) * (line_height + 8)
        + SUBTITLE_PADDING * 2
    )

    box_width = (
        max(draw.textlength(line, font=font) for line in lines)
        + SUBTITLE_PADDING * 2
    )

    x_box = (VIDEO_W - box_width) // 2
    y_box = VIDEO_H - box_height - SUBTITLE_BOTTOM_MARGIN

    # Fundo arredondado (CORRETO)
    draw.rounded_rectangle(
        (x_box, y_box, x_box + box_width, y_box + box_height),
        radius=SUBTITLE_RADIUS,
        fill=(0, 0, 0, SUBTITLE_BG_ALPHA)
    )

    # Texto
    y_text = y_box + SUBTITLE_PADDING
    for line in lines:
        text_w = draw.textlength(line, font=font)
        x_text = (VIDEO_W - text_w) // 2
        draw.text(
            (x_text, y_text),
            line,
            fill="white",
            font=font
        )
        y_text += line_height + 8

    return img.convert("RGB")


# --------------------------------------------------
# VIDEO BUILDER
# --------------------------------------------------

def build_video(
    image_path: str,
    audio_path: str,
    srt_path: str,
    output_path: str,
    badge_img: Image.Image,
    subtitle_style: dict
):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    audio = AudioFileClip(audio_path)
    segments = parse_srt(srt_path)

    bg = (
        Image.open(image_path)
        .convert("RGB")
        .resize((VIDEO_W, VIDEO_H))
    )

    badge = badge_img.resize((220, 220))

    font = ImageFont.truetype(
        subtitle_style["font"],
        subtitle_style["font_size"]
    )

    def make_frame(t):
        frame = bg.copy().convert("RGBA")

        # SELO (topo direito)
        frame.alpha_composite(
            badge,
            (VIDEO_W - badge.width - 30, 30)
        )

        # LEGENDA
        for s, e, text in segments:
            if s <= t <= e:
                frame = draw_subtitle(frame, text, font)
                break

        return np.array(frame)

    video = (
        VideoClip(make_frame, duration=audio.duration)
        .set_audio(audio)
    )

    video.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac"
    )
