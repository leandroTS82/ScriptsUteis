from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np

VIDEO_W = 1920
VIDEO_H = 1080


def create_text_box(text, width=VIDEO_W - 300):
    """Texto sobre fundo cinza escuro, transparente, bordas arredondadas."""

    font_size = 48
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    padding = 40
    radius = 40

    # imagem grande temporária
    img = Image.new("RGBA", (width, 2000), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # quebras
    words = text.split(" ")
    lines = []
    current = ""

    for w in words:
        test = (current + " " + w).strip()
        if draw.textlength(test, font=font) > width - (padding * 2):
            lines.append(current)
            current = w
        else:
            current = test
    lines.append(current)

    _, _, _, lh = draw.textbbox((0, 0), "Ay", font=font)
    h_total = len(lines) * (lh + 12) + padding * 2

    # fundo com borda arredondada
    box = Image.new("RGBA", (width, h_total), (0, 0, 0, 0))
    d = ImageDraw.Draw(box)
    d.rounded_rectangle(
        (0, 0, width, h_total),
        radius=radius,
        fill=(30, 30, 30, 180)
    )

    y = padding
    for line in lines:
        x = padding
        d.text((x, y), line, font=font, fill="white")
        y += lh + 12

    return box


def build_story_video(story_text, media_path, audio_path, output_path):
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    # Fundo
    pil_bg = Image.open(media_path).resize((VIDEO_W, VIDEO_H))
    bg = ImageClip(np.array(pil_bg)).set_duration(duration)

    # Texto sobreposto
    text_img = create_text_box(story_text)
    txt_clip = (
        ImageClip(np.array(text_img))
        .set_duration(duration)
        .set_position(("center", "bottom"))
        .margin(bottom=50)
    )

    final = CompositeVideoClip([bg, txt_clip]).set_audio(audio)

    final.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac"
    )

    print("✔ Vídeo exportado:", output_path)
