from gemini_config import GeminiConfig

def generate_audio(text, output_path):
    config = GeminiConfig()
    model = config.get_audio()

    response = model.generate_content(
        text,
        generation_config={"response_mime_type": "audio/wav"}
    )

    audio_bytes = response.candidates[0].content.parts[0].data

    with open(output_path, "wb") as f:
        f.write(audio_bytes)
