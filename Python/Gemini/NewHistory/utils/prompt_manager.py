import json

class PromptManager:
    def __init__(self, path="history/prompts.json"):
        with open(path, encoding="utf-8") as f:
            self.data = json.load(f)

    def badge_prompt(self, story_text: str) -> str:
        return f"{self.data['badge']['prompt']}\n\nStory:\n{story_text}"

    def image_prompt(self, story_text: str) -> str:
        return f"{self.data['image']['base_prompt']}\n\nStory:\n{story_text}"

    def title_prompt(self, story_text: str) -> str:
        return f"{self.data['title']['prompt']}\n\nStory:\n{story_text}"

    def audio_instruction(self, slow=True) -> str:
        return self.data["audio"]["slow_instruction"]

    def subtitle_style(self):
        return self.data["subtitle"]
