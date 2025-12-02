from moviepy.editor import *

def build_video(word, images_dir, audio_dir, output_path):
    audio_path = f"{audio_dir}/{word}.wav"
    img_path = f"{images_dir}/{word}.png"

    narration = AudioFileClip(audio_path)
    bg = ImageClip(img_path).set_duration(narration.duration)

    final = bg.set_audio(narration)
    final.write_videofile(output_path, fps=30)
