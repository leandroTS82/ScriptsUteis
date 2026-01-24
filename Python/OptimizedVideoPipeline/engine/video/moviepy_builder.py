import json
from moviepy.editor import ImageClip, AudioFileClip
from engine.project_root import get_project_root

ROOT = get_project_root()

cfg = json.load(
    open(ROOT / "settings" / "moviepy.json", encoding="utf-8")
)

def build_video(word: str, image: str, audio: str):
    bg = ImageClip(image)
    aud = AudioFileClip(audio)

    video = bg.set_audio(aud).set_duration(aud.duration)

    output = ROOT / "media" / "videos" / f"{word}.mp4"

    video.write_videofile(
        str(output),
        fps=cfg["fps"],
        codec=cfg["codec"],
        audio_codec=cfg["audio_codec"]
    )
