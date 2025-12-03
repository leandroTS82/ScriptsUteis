import re

def build_tts_text(lesson_json):
    """
    Constrói o texto final para o TTS do Gemini,
    respeitando:
    - repeat_each
    - pause
    - introducao (1 vez)
    - frases EN repetidas 2x
    - frases PT repetidas 1x
    """

    repeat_pt = lesson_json["repeat_each"]["pt"]
    repeat_en = lesson_json["repeat_each"]["en"]

    final_output = []

    # ----------------------------------------------------
    # 1. INTRODUÇÃO (somente 1 vez)
    # ----------------------------------------------------
    intro = lesson_json.get("introducao", "").strip()
    if intro:
        final_output.append(intro)
        final_output.append("<break time=\"1s\"/>")

    # ----------------------------------------------------
    # 2. WORD_BANK
    # ----------------------------------------------------
    groups = lesson_json["WORD_BANK"]

    for group in groups:

        for item in group:
            text = item["text"].strip()
            lang = item["lang"]
            pause = item.get("pause", 1000)  # valor default = 1 segundo

            # ------------------------
            # Repetições
            # ------------------------
            if lang == "en":
                repeat = repeat_en
            else:
                repeat = repeat_pt

            # Adiciona repetições
            for _ in range(repeat):
                final_output.append(text)

            # Converte pausa em segundos
            seconds = pause / 1000.0
            final_output.append(f"<break time=\"{seconds}s\"/>")

    # ----------------------------------------------------
    # 3. Retorno final
    # ----------------------------------------------------
    return "\n".join(final_output)
