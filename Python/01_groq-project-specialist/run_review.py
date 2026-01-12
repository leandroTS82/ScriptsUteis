import json
from engine.groq_client import GroqClient
from engine.project_reader import ProjectReader
from engine.chunker import Chunker
from engine.prompt_builder import PromptBuilder
from engine.reviewer import Reviewer

PROJECT_PATH = r"C:\Dev\Outros\LTS\EtiquetaNutricional"

with open("config/settings.json") as f:
    settings = json.load(f)

with open("config/groq_keys.json") as f:
    keys = json.load(f)

with open("config/system_prompts.json") as f:
    system_prompts = json.load(f)

with open("prompts/user_prompt.txt") as f:
    user_prompt = f.read()

reader = ProjectReader(settings["reader"])
files = reader.read(PROJECT_PATH)

chunker = Chunker(settings["chunking"]["max_chars"])
chunks = chunker.chunk(files)

builder = PromptBuilder(system_prompts, user_prompt)
prompts = [builder.build(c, PROJECT_PATH) for c in chunks]

client = GroqClient(settings["groq"], keys)
reviewer = Reviewer(client)

results = reviewer.review(prompts)

with open("output/review_result.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("✔ Code review finalizado.")
