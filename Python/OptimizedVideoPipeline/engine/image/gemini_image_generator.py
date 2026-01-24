import json, io
from google import genai
from PIL import Image

cfg = json.load(open("settings/gemini_image.json"))
genai.configure(api_key=open("secrets/gemini_key.txt").read())

def generate_image(word):
    prompt = json.load(open("prompts/gemini/image_prompt.json"))["template"].replace("{{word}}", word)
    model = genai.GenerativeModel(cfg["model"])
    res = model.generate_content(prompt)
    img = Image.open(io.BytesIO(res.parts[0].inline_data.data))
    path = f"media/images/{word}.png"
    img.save(path)
    return path
