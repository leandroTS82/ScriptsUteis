import re
from groq import Groq
import os
from google import genai

GEMINI_KEY = r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\google-gemini-key.txt"
GROQ_KEY = r"C:\dev\scripts\ScriptsUteis\Python\Gemini\MakeVideoGemini\groq_api_key.txt"

def _load_key(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Chave não encontrada: {path}")
    return open(path).read().strip()

def sanitize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", "_", text)
    return text[:60].strip("_")


def try_groq_theme(text):
    try:
        client = Groq(api_key=_load_key(GROQ_KEY))

        prompt = f"""
        Generate a SHORT filename-style theme (2-4 words, lowercase, underscored)
        describing the story below.

        Story:
        {text}

        Return ONLY the file name, e.g.:
        morning_surprise
        """

        response = client.chat.completions.create(
            model="llama-3.2-1b-preview",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20
        )

        theme = response.choices[0].message["content"].strip()
        return sanitize(theme)
    except:
        return None


def try_gemini_theme(text):
    try:
        client = genai.Client(api_key=_load_key(GEMINI_KEY))

        prompt = f"""
        Generate a SHORT filename-style theme:
        2–4 English words, lowercase, underscored.
        Only output the filename.

        Story: {text}
        """

        res = client.models.generate_content(
            model="gemini-2.0-flash-lite-preview",
            contents=prompt
        )

        theme = res.text.strip()
        return sanitize(theme)
    except:
        return None


def extract_story_theme(text):
    theme = try_groq_theme(text)
    if theme:
        return theme

    theme = try_gemini_theme(text)
    if theme:
        return theme

    return "my_story"
