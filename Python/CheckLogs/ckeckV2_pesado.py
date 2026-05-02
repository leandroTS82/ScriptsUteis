import subprocess
import os
import sys
import random
from itertools import cycle
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# =========================
# PATH FIX (IMPORT SHARED)
# =========================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from groq_keys_loader import GROQ_KEYS
from groq import Groq

# =========================
# CONFIG
# =========================
NAMESPACE = "my-theft"
DEPLOYMENTS = [
    "allsetraplatform-be-eventhandlers",
    "allsetraplatform-be-handlers",
    "allsetraplatform-be-servicebushandlers",
]

MAX_RETRIES_PER_KEY = 2
MAX_WORKERS = min(len(GROQ_KEYS), 5)

# =========================
# KEY ROTATION
# =========================
groq_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))


def get_next_client():
    key = next(groq_key_cycle)
    return Groq(api_key=key["key"]), key["name"]


# =========================
# LOAD CONTEXT FILES
# =========================
def load_context():
    context_dir = os.path.join(os.path.dirname(__file__), "context")
    if not os.path.exists(context_dir):
        return ""

    content = ""
    for file in os.listdir(context_dir):
        path = os.path.join(context_dir, file)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content += f"\n\n## FILE: {file}\n{f.read()[:10000]}"
    return content


# =========================
# LOAD PROMPTS
# =========================
def load_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "system.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    return "You are a senior distributed systems architect."


CODE_CONTEXT = load_context()
SYSTEM_PROMPT = load_prompt() + "\n\n" + CODE_CONTEXT


# =========================
# LOG FETCH
# =========================
def get_logs(deployment: str, tail: int = 500) -> str:
    result = subprocess.run(
        ["kubectl", "logs", f"deployment/{deployment}", "-n", NAMESPACE, f"--tail={tail}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    return result.stdout


# =========================
# CHUNKING
# =========================
def chunk_logs(text: str, chunk_size: int = 20000, overlap: int = 500):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


# =========================
# AI CALL WITH FAILOVER
# =========================
def call_groq_with_retry(messages):
    tried_keys = set()

    for _ in range(len(GROQ_KEYS)):
        client, key_name = get_next_client()

        if key_name in tried_keys:
            continue

        tried_keys.add(key_name)

        for attempt in range(MAX_RETRIES_PER_KEY):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    max_tokens=4000,
                    temperature=0.1,
                )
                return response.choices[0].message.content

            except Exception as e:
                print(f"[WARN] Key {key_name} failed (attempt {attempt+1}): {str(e)}")

    return "[ERROR] All keys failed."


# =========================
# ANALYZE SINGLE CHUNK
# =========================
def analyze_chunk(chunk_text, index, total):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"""
Analyze logs (part {index+1}/{total})

### Required:
- Errors
- Idempotency issues
- Persistence failures
- Cross-deployment correlation
- Root cause ranked
- Concrete fixes with code diff

LOGS:
{chunk_text}
""",
        },
    ]

    return call_groq_with_retry(messages)


# =========================
# PARALLEL ANALYSIS
# =========================
def analyze_all_chunks(all_logs):
    combined = ""
    for dep, log in all_logs.items():
        combined += f"\n\n=== {dep} ===\n{log}"

    chunks = chunk_logs(combined)
    total = len(chunks)

    results = [None] * total

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(analyze_chunk, chunk, i, total): i
            for i, chunk in enumerate(chunks)
        }

        for future in as_completed(futures):
            index = futures[future]
            results[index] = future.result()

    return "\n\n".join(results)


# =========================
# MAIN
# =========================
def main():
    timestamp = datetime.now().strftime("%y%m%d%H%M")
    output_dir = os.path.join("files", f"{timestamp}_result")
    os.makedirs(output_dir, exist_ok=True)

    print("🔄 Collecting logs...")

    all_logs = {dep: get_logs(dep) for dep in DEPLOYMENTS}

    # Save raw logs
    for dep, logs in all_logs.items():
        with open(os.path.join(output_dir, f"logs_{dep}.txt"), "w", encoding="utf-8") as f:
            f.write(logs)

    print("🧠 Analyzing logs with AI (multi-key + parallel)...")

    analysis = analyze_all_chunks(all_logs)

    md_path = os.path.join(output_dir, "analysis.md")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Log Analysis\nGenerated: {timestamp}\n\n")
        f.write(analysis)

    print(f"\n✅ Output folder: {output_dir}")


if __name__ == "__main__":
    main()