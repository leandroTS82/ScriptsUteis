import json
import random
import requests

class GroqClient:
    def __init__(self, settings, keys):
        self.settings = settings
        self.keys = keys

    def call(self, messages: list) -> dict:
        key = random.choice(self.keys)

        headers = {
            "Authorization": f"Bearer {key['key']}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.settings["model"],
            "messages": messages,
            "temperature": self.settings["temperature"]
        }

        res = requests.post(
            self.settings["url"],
            headers=headers,
            json=payload,
            timeout=self.settings["timeout"]
        )

        res.raise_for_status()

        content = res.json()["choices"][0]["message"]["content"]
        json_text = content[content.find("{"):content.rfind("}") + 1]

        data = json.loads(json_text)
        data["_key_used"] = key["name"]
        return data
