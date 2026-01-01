import json
from utils.slugify import slugify
from utils.gemini_client import GeminiClient
from core.audio_generator import save_wav
from core.subtitle_generator import generate_srt
from core.image_generator import save_image
from core.video_builder import build_video
from core.history_tracker import (
    load_state,
    save_state,
    is_processed,
    mark_processed
)

API_KEY = open(
    r"C:\dev\scripts\ScriptsUteis\Python\secret_tokens_keys\google-gemini-key.txt",
    encoding="utf-8"
).read().strip()

client = GeminiClient(API_KEY)

open("history/history_state.json", "a").close()

stories = json.load(
    open("history/stories.json", encoding="utf-8")
)["stories"]

state = load_state("history/history_state.json")

for story in stories:
    slug = slugify(story["title"])

    if is_processed(state, slug):
        print(f"⏭ Ignorado: {slug}")
        continue

    print(f"▶ Processando: {slug}")

    audio_path = f"outputs/audio/{slug}.wav"
    srt_path = f"outputs/subtitles/{slug}.en.srt"
    image_path = f"outputs/images/{slug}.png"
    video_path = f"outputs/videos/{slug}.mp4"

    save_wav(audio_path, client.generate_audio(story["text"]))
    generate_srt(audio_path, srt_path)
    save_image(image_path, client.generate_image(story["text"]))
    build_video(image_path, audio_path, srt_path, video_path)

    mark_processed(state, slug)
    save_state("history/history_state.json", state)

    print(f"✔ Finalizado: {slug}\n")

print("🎉 New History gerado com sucesso")
