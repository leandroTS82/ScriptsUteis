from utils.gemini_client import GeminiClient

def generate_title(client: GeminiClient, story_text: str, prompt: str) -> str:
    response = client.generate_text(
        f"{prompt}\n\nStory:\n{story_text}"
    )
    return response.strip().replace('"', '')
