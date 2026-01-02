import json

class PromptManager:
    def __init__(self, path="history/prompts.json"):
        with open(path, encoding="utf-8") as f:
            self.prompts = json.load(f)

    # ---------------------------
    # AUDIO
    # ---------------------------
    def audio_instruction(self, slow=True):
        base = self.prompts["audio"]["base"]
        return base + (
            "\nSpeak slowly and clearly for English learners."
            if slow else ""
        )

    # ---------------------------
    # IMAGE (COM TÍTULO)
    # ---------------------------
    def image_prompt(self, story_text: str, title: str) -> str:
        template = self.prompts["image"]["base"]

        return template.format(
            title=title,
            story=story_text
        )

    # ---------------------------
    # BADGE
    # ---------------------------
    def badge_prompt(self, story_text: str) -> str:
        return self.prompts["badge"]["base"].format(story=story_text)

    # ---------------------------
    # SUBTITLE STYLE
    # ---------------------------
    def subtitle_style(self):
        return self.prompts["subtitle_style"]
