import json, os
from google import genai

cfg = json.load(open("settings/gemini_audio.json"))
genai.configure(api_key=open("secrets/gemini_key.txt").read())

def generate_audio(lesson, word):
    text = " ".join(i["text"] for i in lesson["WORD_BANK"][0])
    model = genai.GenerativeModel(cfg["model"])
    res = model.generate_content(text)
    path = f"media/audio/{word}.wav"
    open(path, "wb").write(res.candidates[0].content.parts[0].inline_data.data)
    return path
