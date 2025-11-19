r"""
===============================================================
 Script: Extract audio from video and generate transcription/translation
 Author: Leandro (enhanced version)
===============================================================

What this script does
---------------------------------------------------------------
Automates audio extraction, transcription, and translation of one or several
videos, organizing everything into per-video folders.

Flow:
1. Finds videos (.mp4 or .mkv) in a target directory.
   - Can be passed via command line:
       python transcript.py "C:/Videos"
   - Or defined directly in DEFAULT_VIDEO_PATH.
2. For each video found:
   - Creates a folder with the same name as the video.
   - Moves the video into its folder.
   - Extracts audio (.mp3) with FFmpeg.
   - Transcribes audio based on --lang:
       --lang pt    → Portuguese only
       --lang en    → English (translated) only
       --lang both  → Both languages
       No --lang    → Default: both
   - Generates TXT, SRT, VTT files inside ./transcripts.
3. Keeps each project clean and organized.

Requirements
---------------------------------------------------------------
- Python 3.9+
- Install dependencies:
    pip install "numpy<=2.2.0"
    pip install openai-whisper
    pip install torch openai-whisper
    *Se tiver algum problema e precisar reinstalar:
    pip install --force-reinstall openai-whisper
- FFmpeg instalado:
    Windows:
        winget install Gyan.FFmpeg
    Linux:
        sudo apt install ffmpeg
    macOS:
        brew install ffmpeg

Folder structure produced
---------------------------------------------------------------
./Videos/
    └── aula/
        ├── aula.mp4
        ├── mp3/
        │   └── aula.mp3
        └── transcripts/
            ├── aula.pt.txt
            ├── aula.pt.srt
            ├── aula.pt.vtt
            ├── aula.en.txt
            ├── aula.en.srt
            └── aula.en.vtt

How to run
---------------------------------------------------------------
1. Default path:
    python transcript.py

2. Manual path:
    python transcript.py "C:/MeusVideos"

3. Path + language:
    python transcript.py "C:/Videos" --lang pt
    python transcript.py "C:/Videos" --lang en
    python transcript.py "C:/Videos" --lang both

Most used example:
    python transcript.py "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVIMENTO DE SISTEMAS\\Communication site - ReunioesGravadas"

Use cases
---------------------------------------------------------------
- Creating multilingual subtitles
- Transcribing meetings, classes, interviews
- Building clean datasets of audio + text
===============================================================
"""

import whisper
import os
import glob
import subprocess
import time
import sys
import shutil
from datetime import datetime, timedelta

# ===============================================================
# DEFAULT CONFIGURATION
# ===============================================================

DEFAULT_VIDEO_PATH = r"./Movies"


# ===============================================================
# AUXILIARY FUNCTIONS
# ===============================================================

def format_time_srt(secs: float) -> str:
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = int(secs % 60)
    ms = int((secs % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def format_time_vtt(secs: float) -> str:
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = int(secs % 60)
    ms = int((secs % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02}.{ms:03}"


def save_txt(segments, file_path: str):
    with open(file_path, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(seg["text"].strip() + " ")


def save_srt(segments, file_path: str):
    with open(file_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            f.write(f"{i}\n")
            f.write(f"{format_time_srt(seg['start'])} --> {format_time_srt(seg['end'])}\n")
            f.write(f"{seg['text'].strip()}\n\n")


def save_vtt(segments, file_path: str):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for seg in segments:
            f.write(f"{format_time_vtt(seg['start'])} --> {format_time_vtt(seg['end'])}\n")
            f.write(f"{seg['text'].strip()}\n\n")


def extract_audio(video_path: str, output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    audio_path = os.path.join(output_dir, f"{base_name}.mp3")

    command = [
        "ffmpeg",
        "-i", video_path,
        "-map", "0:a:0",
        "-vn",
        "-acodec", "libmp3lame",
        "-q:a", "0",
        audio_path,
        "-y"
    ]

    subprocess.run(command, check=True)
    print(f"Audio extracted: {audio_path}")
    return audio_path


def transcribe_and_translate(file_path: str, output_dir: str, lang_option: str):
    model = whisper.load_model("medium")
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    os.makedirs(output_dir, exist_ok=True)

    if lang_option in ["pt", "both"]:
        print("Transcribing (Portuguese)...")
        result_pt = model.transcribe(file_path, task="transcribe", language="pt")
        save_txt(result_pt["segments"], os.path.join(output_dir, f"{base_name}.pt.txt"))
        save_srt(result_pt["segments"], os.path.join(output_dir, f"{base_name}.pt.srt"))
        save_vtt(result_pt["segments"], os.path.join(output_dir, f"{base_name}.pt.vtt"))

    if lang_option in ["en", "both"]:
        print("Translating (English)...")
        result_en = model.transcribe(file_path, task="translate")
        save_txt(result_en["segments"], os.path.join(output_dir, f"{base_name}.en.txt"))
        save_srt(result_en["segments"], os.path.join(output_dir, f"{base_name}.en.srt"))
        save_vtt(result_en["segments"], os.path.join(output_dir, f"{base_name}.en.vtt"))

    print(f"Files generated in: {output_dir}")


def process_video(video_file: str, lang_option: str):
    base_name = os.path.splitext(os.path.basename(video_file))[0]
    video_dir = os.path.join(os.path.dirname(video_file), base_name)

    os.makedirs(video_dir, exist_ok=True)

    new_video_path = os.path.join(video_dir, os.path.basename(video_file))
    if os.path.abspath(video_file) != os.path.abspath(new_video_path):
        shutil.move(video_file, new_video_path)

    print(f"\nProcessing: {base_name}")
    print(f"Folder created: {video_dir}")

    mp3_dir = os.path.join(video_dir, "mp3")
    audio_file = extract_audio(new_video_path, mp3_dir)

    transcript_dir = os.path.join(video_dir, "transcripts")
    transcribe_and_translate(audio_file, transcript_dir, lang_option)


# ===============================================================
# MAIN EXECUTION
# ===============================================================

if __name__ == "__main__":
    start_time = time.time()
    start_dt = datetime.now()

    print("\n===================================================")
    print("Starting...")
    print(f"Start: {start_dt.strftime('%d/%m/%Y %H:%M:%S')}")
    print("===================================================\n")

    lang_option = "both"
    input_path = None

    # New robust argument parser
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]

        if arg.startswith("--lang"):
            if "=" in arg:
                lang_option = arg.split("=")[1].lower()
            else:
                if i + 1 < len(args):
                    lang_option = args[i + 1].lower()
                    i += 1
        else:
            input_path = arg

        i += 1

    if lang_option not in ["pt", "en", "both"]:
        print(f"Invalid --lang option: {lang_option}. Expected: pt | en | both")
        exit(1)

    if input_path is None:
        input_path = DEFAULT_VIDEO_PATH

    if os.path.isfile(input_path):
        files_to_process = [input_path]
    else:
        files_to_process = glob.glob(os.path.join(input_path, "*.mp4")) + \
                           glob.glob(os.path.join(input_path, "*.mkv"))

    if not files_to_process:
        print(f"No video found in {input_path}")
        exit(1)

    for video in files_to_process:
        try:
            process_video(video, lang_option)
        except Exception as e:
            print(f"Error processing {video}: {e}")

    end_time = time.time()
    end_dt = datetime.now()
    elapsed = timedelta(seconds=end_time - start_time)

    print("\n===================================================")
    print("Done!")
    print(f"Start: {start_dt.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"End:   {end_dt.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Total: {elapsed}")
    print("===================================================\n")
