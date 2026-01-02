import json
import os


class PromptManager:
    """
    Responsável por:
    - Carregar prompts.json
    - Validar estrutura mínima
    - Fornecer prompts prontos para uso (image, audio, badge, youtube, etc.)
    - Garantir retrocompatibilidade (template OU base)
    """

    def __init__(self, path: str = "history/prompts.json"):
        if not os.path.exists(path):
            raise FileNotFoundError(f"❌ prompts.json não encontrado em: {path}")

        with open(path, encoding="utf-8") as f:
            self.prompts = json.load(f)

        if not isinstance(self.prompts, dict):
            raise ValueError("❌ prompts.json inválido (esperado objeto raiz)")

    # ==================================================
    # CORE SAFE ACCESS
    # ==================================================

    def _require(self, section: str, *keys: str):
        """
        Retorna o primeiro campo existente dentro da seção.

        Exemplo:
            _require("image", "template", "base")

        Isso permite compatibilidade com JSONs antigos.
        """

        section_data = self.prompts.get(section)

        if not isinstance(section_data, dict):
            raise KeyError(
                f"❌ prompts.json inválido.\n"
                f"Esperado objeto em '{section}'"
            )

        for key in keys:
            if key in section_data:
                return section_data[key]

        raise KeyError(
            f"❌ prompts.json inválido.\n"
            f"Esperado: '{section}.[{' | '.join(keys)}]'\n"
            f"Encontrado: {list(section_data.keys())}"
        )

    # ==================================================
    # AUDIO
    # ==================================================

    def audio_instruction(self, slow: bool = True) -> str:
        """
        Prompt adicional enviado ao Gemini TTS.
        """

        base = self._require("audio", "instruction", "base")

        if slow:
            return base + "\nSpeak slowly, clearly and naturally."
        return base

    # ==================================================
    # IMAGE
    # ==================================================

    def image_prompt(self, story_text: str, title: str) -> str:
        """
        Prompt para geração da imagem principal.
        O título JÁ vai embutido via Gemini.
        """

        template = self._require("image", "template", "base")

        return template.format(
            title=title,
            story=story_text
        )

    # ==================================================
    # BADGE (SELO)
    # ==================================================

    def badge_prompt(self, story_text: str) -> str:
        """
        Prompt para gerar o selo do Leandrinho.
        """

        template = self._require("badge", "template", "base")

        return template.format(
            story=story_text
        )

    # ==================================================
    # SUBTITLE STYLE
    # ==================================================

    def subtitle_style(self) -> dict:
        """
        Configuração visual da legenda.
        """
        style = self.prompts.get("subtitle", {})

        return {
            "font": style.get("font", "arial.ttf"),
            "font_size": style.get("font_size", 42)
        }

    # ==================================================
    # YOUTUBE
    # ==================================================

    def youtube_description(self, title: str, story_text: str) -> str:
        """
        Gera descrição final do YouTube.
        """

        template = self._require("youtube", "description_template")

        return template.format(
            title=title,
            story=story_text
        )

    def youtube_tags(self, story_text: str) -> list[str]:
        """
        Retorna lista de tags do YouTube.
        """
        return self._require("youtube", "tags")

    def youtube_playlist(self) -> dict:
        """
        Retorna configuração da playlist.
        """
        return self._require("youtube", "playlist")
