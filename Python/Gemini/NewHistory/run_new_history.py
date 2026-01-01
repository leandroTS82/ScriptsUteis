import json
from utils.slugify import slugify
from utils.gemini_client import GeminiClient
from utils.prompt_manager import PromptManager
from utils.title_generator import generate_title
from utils.badge_generator import generate_badge
from core.audio_generator import save_wav
from core.subtitle_generator import generate_srt
from core.image_generator import save_image
from core.video_builder import build_video
from core.history_tracker import load_state, save_state, is_processed, mark_processed

API_KEY = open(
    r"C:\dev\scripts\ScriptsUteis\Python\secret_tokens_keys\google-gemini-key.txt"
).read().strip()

client = GeminiClient(API_KEY)
prompts = PromptManager()

stories = json.load(open("history/stories.json", encoding="utf-8"))["stories"]
state = load_state("history/history_state.json")

for story in stories:
    slug = slugify(story["title"])

    if is_processed(state, slug):
        continue

    story_text = story["text"]

    title = generate_title(client, story_text, prompts.title_prompt(story_text))
    badge = generate_badge(client, prompts.badge_prompt(story_text))

    audio_path = f"outputs/audio/{slug}.wav"
    srt_path = f"outputs/subtitles/{slug}.en.srt"
    image_path = f"outputs/images/{slug}.png"
    video_path = f"outputs/videos/{slug}.mp4"

    save_wav(
        audio_path,
        client.generate_audio(story_text, prompts.audio_instruction(slow=True))
    )

    generate_srt(audio_path, srt_path)
    save_image(image_path, client.generate_image(prompts.image_prompt(story_text)))

    build_video(
        image_path=image_path,
        audio_path=audio_path,
        srt_path=srt_path,
        output_path=video_path,
        title_text=title,
        badge_img=badge,
        subtitle_style=prompts.subtitle_style()
    )

    mark_processed(state, slug)
    save_state("history/history_state.json", state)

print("🎉 New History com prompts desacoplados gerado com sucesso")
