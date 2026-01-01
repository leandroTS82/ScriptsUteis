from moviepy.editor import (
    AudioFileClip,
    ImageClip,
    CompositeVideoClip,
    VideoClip
)
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import re

VIDEO_W = 1920
VIDEO_H = 1080
FPS = 30
BOTTOM_MARGIN = 120
BOX_PADDING = 30
BOX_ALPHA = 160  # 0–255


# ---------------------------------------------------------
# SRT PARSER
# ---------------------------------------------------------

def parse_srt(path: str):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    blocks = re.split(r"\n\s*\n", content)
    segments = []

    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3:
            continue

        time_line = lines[1]
        text = " ".join(lines[2:]).strip()

        start, end = time_line.split(" --> ")
        segments.append((
            _parse_time(start),
            _parse_time(end),
            text
        ))

    return segments


def _parse_time(t: str) -> float:
    h, m, rest = t.split(":")
    s, ms = rest.split(",")
    return (
        int(h) * 3600 +
        int(m) * 60 +
        int(s) +
        int(ms) / 1000
    )


# ---------------------------------------------------------
# IMAGE HELPERS
# ---------------------------------------------------------

def load_bg(image_path: str) -> np.ndarray:
    img = Image.open(image_path).convert("RGB")
    img = img.resize(
        (VIDEO_W, VIDEO_H),
        resample=Image.Resampling.LANCZOS
    )
    return np.array(img)


def draw_subtitle(frame: np.ndarray, text: str) -> np.ndarray:
    img = Image.fromarray(frame).convert("RGBA")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 46)
    except:
        font = ImageFont.load_default()

    max_width = VIDEO_W - 200
    words = text.split()
    lines = []
    current = ""

    for w in words:
        test = f"{current} {w}".strip()
        if draw.textlength(test, font=font) <= max_width:
            current = test
        else:
            lines.append(current)
            current = w
    lines.append(current)

    line_height = font.size + 10
    box_height = line_height * len(lines) + BOX_PADDING * 2

    y = VIDEO_H - box_height - BOTTOM_MARGIN

    overlay = Image.new(
        "RGBA",
        (VIDEO_W, box_height),
        (0, 0, 0, BOX_ALPHA)
    )

    oy = BOX_PADDING
    for line in lines:
        w = draw.textlength(line, font=font)
        x = (VIDEO_W - w) // 2
        ImageDraw.Draw(overlay).text(
            (x, oy),
            line,
            font=font,
            fill=(255, 255, 255, 255)
        )
        oy += line_height

    img.alpha_composite(overlay, (0, y))
    return np.array(img.convert("RGB"))


# ---------------------------------------------------------
# VIDEO BUILDER
# ---------------------------------------------------------

def build_video(
    image_path: str,
    audio_path: str,
    srt_path: str,
    output_path: str
) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    audio = AudioFileClip(audio_path)
    duration = audio.duration
    segments = parse_srt(srt_path)
    bg = load_bg(image_path)

    def make_frame(t):
        frame = bg.copy()

        for start, end, text in segments:
            if start <= t <= end:
                frame = draw_subtitle(frame, text)
                break

        return frame

    video = VideoClip(make_frame, duration=duration)
    video = video.set_audio(audio)

    video.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="medium"
    )

    video.close()
    audio.close()
