r"""
=====================================================================
 Script: transcriptV2.py
 Author: Leandro
 Description:
   - Extrai áudio de vídeos
   - Transcreve PT + traduz EN via Whisper
   - Renderiza legenda DIRETO no vídeo (MoviePy + PIL)
   - Vídeo em movimento + legenda contínua (NewHistory style)
=====================================================================

python transcriptV2.py "C:\\MeusVideos"
python transcriptV2.py "C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\Communication site - ReunioesGravadas"
python transcriptV2.py "C:\Users\leand\Desktop\01-ReunioesGravadas"
"""

import whisper
import os
import glob
import sys
import shutil
import time
from datetime import datetime, timedelta

from moviepy.editor import VideoFileClip, VideoClip, AudioFileClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# ===============================================================
# ENGLISH CONTENT EXTRACTOR (OPTIONAL / DECOUPLED)
# ===============================================================

EXTRACTOR_PATH = r"C:\dev\scripts\ScriptsUteis\Python\english_extractor"

if EXTRACTOR_PATH not in sys.path:
    sys.path.append(EXTRACTOR_PATH)

try:
    from run_extract import run as extract_english_content
    EXTRACTOR_ENABLED = True
except Exception:
    EXTRACTOR_ENABLED = False

# Máximo de caracteres por envio ao extrator (rate-limit safe)
EXTRACTOR_CHUNK_SIZE = 1200

# Delay entre chamadas ao Groq (segundos)
EXTRACTOR_SLEEP = 1.2

# ===============================================================
# CONFIG
# ===============================================================

DEFAULT_VIDEO_PATH = r"./Movies"
WHISPER_MODEL = "medium"

VIDEO_W = 1920
VIDEO_H = 1080
FPS = 30

SUB_MAX_WIDTH = int(VIDEO_W * 0.80)

FONT_EN = "arial.ttf"
FONT_PT = "arial.ttf"

FONT_SIZE_EN = 42
FONT_SIZE_PT = 28

PADDING = 30
LINE_SPACING = 8
BOTTOM_MARGIN = 90
RADIUS = 25

BG_EN = (0, 0, 0, 160)
BG_PT = (20, 40, 80, 160)

# ===============================================================
# AUDIO
# ===============================================================

def extract_audio(video_path: str, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(video_path))[0]
    audio_path = os.path.join(out_dir, f"{base}.wav")

    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(audio_path, fps=24000, logger=None)
    clip.close()

    return audio_path

# ===============================================================
# TEXT WRAP + DRAW
# ===============================================================

def wrap_text(draw, text, font):
    words = text.split()
    lines = []
    current = ""

    for w in words:
        test = f"{current} {w}".strip()
        if draw.textlength(test, font=font) <= SUB_MAX_WIDTH:
            current = test
        else:
            if current:
                lines.append(current)
            current = w

    if current:
        lines.append(current)

    return lines


def draw_boxed_text(img, text, font, y_base, bg_color):
    draw = ImageDraw.Draw(img)
    lines = wrap_text(draw, text, font)

    _, _, _, line_h = draw.textbbox((0, 0), "Ay", font=font)

    box_h = len(lines) * (line_h + LINE_SPACING) + PADDING * 2
    box_w = max(draw.textlength(l, font=font) for l in lines) + PADDING * 2

    x_box = (VIDEO_W - box_w) // 2
    y_box = y_base - box_h

    draw.rounded_rectangle(
        (x_box, y_box, x_box + box_w, y_box + box_h),
        radius=RADIUS,
        fill=bg_color
    )

    y_text = y_box + PADDING
    for line in lines:
        x_text = (VIDEO_W - draw.textlength(line, font=font)) // 2
        draw.text((x_text, y_text), line, fill="white", font=font)
        y_text += line_h + LINE_SPACING

    return y_box

# ===============================================================
# VIDEO BUILDER (FIX PIL ANTIALIAS)
# ===============================================================

def build_video_with_dual_subs(video_path, audio_path, seg_en, seg_pt, output_path):
    base_clip = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path)

    font_en = ImageFont.truetype(FONT_EN, FONT_SIZE_EN)
    font_pt = ImageFont.truetype(FONT_PT, FONT_SIZE_PT)

    def frame_at(t):
        frame_np = base_clip.get_frame(t)

        frame = (
            Image.fromarray(frame_np)
            .resize(
                (VIDEO_W, VIDEO_H),
                resample=Image.Resampling.LANCZOS
            )
            .convert("RGBA")
        )

        current_en = next((s for s in seg_en if s["start"] <= t <= s["end"]), None)
        current_pt = next((s for s in seg_pt if s["start"] <= t <= s["end"]), None)

        y = VIDEO_H - BOTTOM_MARGIN

        if current_pt:
            y = draw_boxed_text(
                frame,
                current_pt["text"].strip(),
                font_pt,
                y,
                BG_PT
            ) - 10

        if current_en:
            draw_boxed_text(
                frame,
                current_en["text"].strip(),
                font_en,
                y,
                BG_EN
            )

        return np.array(frame.convert("RGB"))

    final = (
        VideoClip(frame_at, duration=audio.duration)
        .set_audio(audio)
    )

    final.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac"
    )

    base_clip.close()
    audio.close()

# ===============================================================
# ENGLISH EXTRACTOR HELPERS (CHUNKED)
# ===============================================================

def chunk_text(text: str, max_size: int):
    chunks = []
    current = ""

    for sentence in text.split(". "):
        sentence = sentence.strip()
        if not sentence:
            continue

        candidate = f"{current} {sentence}".strip()
        if len(candidate) <= max_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)

    return chunks

# ===============================================================
# PROCESS VIDEO
# ===============================================================

def process_video(video_file):
    base = os.path.splitext(os.path.basename(video_file))[0]
    base_dir = os.path.dirname(video_file)
    work_dir = os.path.join(base_dir, base)

    os.makedirs(work_dir, exist_ok=True)

    final_video = os.path.join(work_dir, f"{base}_subbed.mp4")

    original = os.path.join(work_dir, os.path.basename(video_file))
    if not os.path.exists(original):
        shutil.move(video_file, original)

    audio_dir = os.path.join(work_dir, "audio")
    audio_path = extract_audio(original, audio_dir)

    model = whisper.load_model(WHISPER_MODEL)

    print("📝 Transcrevendo PT...")
    pt = model.transcribe(audio_path, task="transcribe", language="pt")

    print("🌍 Traduzindo EN...")
    en = model.transcribe(audio_path, task="translate")

    # ===========================================================
    # ENGLISH CONTENT EXTRACTION (CHUNKED / NON-BLOCKING)
    # ===========================================================

    if EXTRACTOR_ENABLED:
        try:
            full_en_text = " ".join(
                s.get("text", "").strip()
                for s in en.get("segments", [])
                if s.get("text")
            )

            chunks = chunk_text(full_en_text, EXTRACTOR_CHUNK_SIZE)

            for idx, chunk in enumerate(chunks, start=1):
                if len(chunk.strip()) < 50:
                    continue  # evita envio de lixo muito curto

                try:
                    print(
                        f"📤 Sending extractor chunk {idx}/{len(chunks)} "
                        f"({len(chunk)} chars)"
                    )
                    extract_english_content(chunk)
                    print(f"✅ Extractor chunk {idx} processed")
                    time.sleep(EXTRACTOR_SLEEP)
                except Exception as e:
                    print(f"⚠️ Extractor chunk {idx} skipped: {e}")

        except Exception as e:
            print(f"⚠️ English extractor skipped: {e}")

    print("🎬 Renderizando vídeo...")
    build_video_with_dual_subs(
        original,
        audio_path,
        en["segments"],
        pt["segments"],
        final_video
    )

    print(f"✅ Finalizado: {final_video}")

# ===============================================================
# MAIN
# ===============================================================

if __name__ == "__main__":
    start = time.time()
    start_dt = datetime.now()

    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_VIDEO_PATH

    if os.path.isfile(path):
        videos = [path]
    else:
        videos = glob.glob(os.path.join(path, "*.mp4")) + \
                 glob.glob(os.path.join(path, "*.mkv"))

    if not videos:
        print("❌ Nenhum vídeo encontrado.")
        sys.exit(1)

    for v in videos:
        try:
            process_video(v)
        except Exception as e:
            print(f"❌ Erro em {v}: {e}")

    elapsed = timedelta(seconds=time.time() - start)

    print("\n===================================================")
    print("  transcriptV2 concluído com sucesso")
    print(f"Início: {start_dt.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Tempo total: {elapsed}")
    print("===================================================")
