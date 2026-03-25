import os
import sys
import random
from itertools import cycle
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from groq import Groq

# =========================
# PATH FIX
# =========================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from groq_keys_loader import GROQ_KEYS

# =========================
# CONFIG
# =========================
MAX_WORKERS = min(len(GROQ_KEYS), 5)
MAX_RETRIES = 2
TIMEOUT_SECONDS = 30

MAX_CONTEXT_CHARS = 20000
CHUNK_SIZE = 12000
CHUNK_OVERLAP = 500

# =========================
# KEY ROTATION
# =========================
groq_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))

def get_client():
    key = next(groq_key_cycle)
    return Groq(api_key=key["key"]), key["name"]

# =========================
# LOAD CONTEXT
# =========================
def load_context():
    context_dir = os.path.join(os.path.dirname(__file__), "context")
    content = ""

    for file in os.listdir(context_dir):
        path = os.path.join(context_dir, file)

        if not os.path.isfile(path):
            continue

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            file_content = f.read()
            content += f"\n\n## FILE: {file}\n{file_content}"

    print(f"📦 Raw context size: {len(content)} chars")

    return content[:MAX_CONTEXT_CHARS]

# =========================
# CHUNK CONTEXT
# =========================
def chunk_text(text):
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunks.append(text[start:end])
        start = end - CHUNK_OVERLAP

    print(f"🧩 Total chunks: {len(chunks)}")
    return chunks

# =========================
# LOAD PROMPTS
# =========================
def load_prompt(name):
    path = os.path.join(os.path.dirname(__file__), "prompts", name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

SYSTEM_TEMPLATE = load_prompt("system_prompt.txt")
USER_TEMPLATE = load_prompt("user_prompt.txt")

# =========================
# CALL LLM WITH RETRY
# =========================
def call_llm(system_prompt, user_prompt):
    tried = set()

    for _ in range(len(GROQ_KEYS)):
        client, key_name = get_client()

        if key_name in tried:
            continue

        tried.add(key_name)

        for attempt in range(MAX_RETRIES):
            try:
                print(f"[TRY] Key={key_name} Attempt={attempt+1}")

                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.1,
                    max_tokens=4000,
                    timeout=TIMEOUT_SECONDS,
                )

                print(f"[OK] Key={key_name}")
                return response.choices[0].message.content

            except Exception as e:
                print(f"[WARN] Key={key_name} failed ({attempt+1}): {str(e)}")

    return "[ERROR] All keys failed"

# =========================
# ANALYZE CHUNK
# =========================
def analyze_chunk(chunk, index, total):
    system_prompt = SYSTEM_TEMPLATE.replace("{{CODE_CONTEXT}}", chunk)
    user_prompt = USER_TEMPLATE.replace("{{CODE_CONTEXT}}", chunk)

    print(f"🔍 Processing chunk {index+1}/{total}")

    result = call_llm(system_prompt, user_prompt)

    return f"\n\n# CHUNK {index+1}\n\n{result}"

# =========================
# CONSOLIDATE RESULTS
# =========================
def consolidate_results(results):
    print("🧠 Consolidating results...")

    combined = "\n\n".join(results)

    system_prompt = "You are a senior software architect consolidating code review results."
    user_prompt = f"""
Merge and consolidate the following code review analyses.

- Remove duplicates
- Keep strongest insights
- Keep structure clean
- Prioritize critical issues

CONTENT:
{combined}
"""

    return call_llm(system_prompt, user_prompt)

# =========================
# MAIN
# =========================
def main():
    timestamp = datetime.now().strftime("%y%m%d%H%M")
    output_dir = os.path.join("files", f"{timestamp}_result")
    os.makedirs(output_dir, exist_ok=True)

    print("🧠 Running Code Review...")

    context = load_context()
    chunks = chunk_text(context)

    results = [None] * len(chunks)

    # =========================
    # PARALLEL EXECUTION
    # =========================
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(analyze_chunk, chunk, i, len(chunks)): i
            for i, chunk in enumerate(chunks)
        }

        for future in as_completed(futures):
            index = futures[future]
            results[index] = future.result()

    # =========================
    # SAVE RAW RESULTS
    # =========================
    raw_path = os.path.join(output_dir, "review_raw.md")

    with open(raw_path, "w", encoding="utf-8") as f:
        f.write("# Raw Review\n\n")
        f.write("\n\n".join(results))

    # =========================
    # FINAL CONSOLIDATION
    # =========================
    final_result = consolidate_results(results)

    final_path = os.path.join(output_dir, "review_final.md")

    with open(final_path, "w", encoding="utf-8") as f:
        f.write("# Final Code Review\n\n")
        f.write(final_result)

    print(f"\n✅ Output folder: {output_dir}")
    print("📄 Files generated:")
    print(" - review_raw.md")
    print(" - review_final.md")

# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    main()