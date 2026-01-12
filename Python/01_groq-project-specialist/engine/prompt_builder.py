class PromptBuilder:
    def __init__(self, system_prompts: list, user_prompt: str):
        self.system_prompts = system_prompts
        self.user_prompt = user_prompt

    def build(self, chunk: str, project_path: str) -> list:
        messages = []

        for sp in self.system_prompts:
            messages.append({"role": "system", "content": sp})

        user_content = self.user_prompt \
            .replace("{{PROJECT_PATH}}", project_path) + \
            "\n\nPROJECT CONTENT:\n" + chunk

        messages.append({"role": "user", "content": user_content})
        return messages
