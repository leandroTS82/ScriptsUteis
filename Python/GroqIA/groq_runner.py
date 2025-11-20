import os
import requests
from datetime import datetime

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY_FILE = "./groq_api_key.txt"
DEFAULT_PROMPT_FILE = "./promptDefault.txt"

# Updated working model
MODEL_NAME = "openai/gpt-oss-20b"


def load_api_key() -> str:
    if not os.path.exists(API_KEY_FILE):
        raise FileNotFoundError("groq_api_key.txt not found in current directory.")

    with open(API_KEY_FILE, "r", encoding="utf-8") as f:
        key = f.read().strip()

    if not key:
        raise ValueError("groq_api_key.txt is empty.")

    return key


def load_default_prompt() -> str:
    if not os.path.exists(DEFAULT_PROMPT_FILE):
        raise FileNotFoundError("promptDefault.txt not found in current directory.")

    with open(DEFAULT_PROMPT_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        raise ValueError("promptDefault.txt is empty.")

    return content


def call_groq(prompt: str) -> str:
    api_key = load_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    response = requests.post(GROQ_API_URL, json=payload, headers=headers)

    if response.status_code != 200:
        print("Groq API returned an error:")
        print("Status:", response.status_code)
        print("Response:", response.text)
        response.raise_for_status()

    data = response.json()
    return data["choices"][0]["message"]["content"]


def save_to_output(text: str) -> str:
    os.makedirs("./output", exist_ok=True)
    filename = f"./output/groq_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)

    return filename


def main():
    user_prompt = input("Enter your prompt (leave empty to use promptDefault.txt): ").strip()

    if user_prompt:
        prompt = user_prompt
    else:
        print("Loading promptDefault.txt...")
        prompt = load_default_prompt()

    print("Calling Groq API...")
    result = call_groq(prompt)

    path = save_to_output(result)
    print(f"Output saved to: {path}")


if __name__ == "__main__":
    main()
