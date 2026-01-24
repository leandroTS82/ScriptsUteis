import sys
from engine.text.groq_text_generator import generate_text
from engine.audio.gemini_audio_generator import generate_audio
from engine.image.gemini_image_generator import generate_image
from engine.image.fixed_image_provider import get_fixed_image
from engine.video.moviepy_builder import build_video
import json

word = sys.argv[1]
lesson = generate_text(word)
json.dump(lesson, open(f"media/videos/{word}.json", "w", encoding="utf-8"), indent=2)

audio = generate_audio(lesson, word)
image = generate_image(word) if generate_image else get_fixed_image()
build_video(word, image, audio)
