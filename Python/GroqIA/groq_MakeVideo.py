"""
python groq_MakeVideo.py
"""

import os
import json
import requests
from datetime import datetime

API_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY_FILE = "./groq_api_key.txt"
SYSTEM_PROMPT_FILE = "./systemPrompt.json"
LABEL_PROMPT_FILE = "./makevideoLabelPrompt.txt"
OUTPUT_DIR = "./output"
MODEL_NAME = "openai/gpt-oss-20b"


def load_api_key():
    if not os.path.exists(API_KEY_FILE):
        raise FileNotFoundError("groq_api_key.txt not found.")
    with open(API_KEY_FILE, "r", encoding="utf-8") as f:
        key = f.read().strip()
    if not key:
        raise ValueError("groq_api_key.txt is empty.")
    return key


def load_json_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def call_groq(system_prompt, user_prompt):
    api_key = load_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = [
        {"role": "system", "content": json.dumps(system_prompt)},
        {"role": "user", "content": json.dumps(user_prompt)}
    ]

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.2
    }

    response = requests.post(API_URL, json=payload, headers=headers)

    if response.status_code != 200:
        print("Groq API error:")
        print(response.text)
        response.raise_for_status()

    data = response.json()
    return data["choices"][0]["message"]["content"]


def save_output(text):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = os.path.join(
        OUTPUT_DIR,
        f"video_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    return filename


def main():
    system_prompt = load_json_file(SYSTEM_PROMPT_FILE)
    label_prompt = load_json_file(LABEL_PROMPT_FILE)

    print("Calling Groq for video metadata generation...")
    result = call_groq(system_prompt, label_prompt)

    output_path = save_output(result)
    print(f"Metadata saved to: {output_path}")


if __name__ == "__main__":
    main()
