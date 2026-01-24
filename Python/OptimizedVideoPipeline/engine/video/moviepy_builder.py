from moviepy.editor import *

def build_video(word, image, audio):
    bg = ImageClip(image)
    aud = AudioFileClip(audio)
    video = bg.set_audio(aud).set_duration(aud.duration)
    video.write_videofile(f"media/videos/{word}.mp4", fps=30)
