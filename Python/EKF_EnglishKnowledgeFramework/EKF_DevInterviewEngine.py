"""
====================================================================================
 EKF_DevInterviewEngine.py
 Dev Interview Training Engine (Groq Only)
 Versão: V4.0 - Study Tracking + Smart Interview + Review Mode
====================================================================================
"""

import os
import sys
import json
import random
import requests
from itertools import cycle
from datetime import datetime

# =============================================================================
# BASE CONFIG
# =============================================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from groq_keys_loader import GROQ_KEYS

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

STATS_FILE = os.path.join(os.path.dirname(__file__), "interview_stats.json")
STUDY_FILE = os.path.join(os.path.dirname(__file__), "study_history.json")

# =============================================================================
# UTIL
# =============================================================================

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def wait_enter():
    input("\nPress ENTER to continue...")

# =============================================================================
# GROQ
# =============================================================================

_groq_key_cycle = cycle(random.sample(GROQ_KEYS, len(GROQ_KEYS)))

def get_next_groq_key():
    for _ in range(len(GROQ_KEYS)):
        key = next(_groq_key_cycle).get("key", "").strip()
        if key.startswith("gsk_"):
            return key
    raise RuntimeError("❌ Nenhuma GROQ API Key válida encontrada.")

def groq_json(prompt: str) -> dict:
    api_key = get_next_groq_key()

    response = requests.post(
        GROQ_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4
        },
        timeout=60
    )

    response.raise_for_status()
    raw = response.json()["choices"][0]["message"]["content"]
    raw_json = raw[raw.find("{"): raw.rfind("}") + 1]
    return json.loads(raw_json)

# =============================================================================
# FILE HANDLERS
# =============================================================================

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# =============================================================================
# PROMPTS
# =============================================================================

def build_study_prompt(area: str, level: str):
    return f"""
You are a senior backend architect teaching for interviews.

Topic: {area}
Level: {level}

Return ONLY JSON:

{{
  "overview": "...",
  "key_concepts": ["...", "..."],
  "real_world_examples": ["...", "..."],
  "common_mistakes": ["...", "..."]
}}
"""

def build_question_prompt(level: str, area: str, study_context: str):
    return f"""
You are a senior interviewer.

Area: {area}
Level: {level}

Recent study context:
{study_context}

Prioritize topics related to study context but you are not limited to them.

Return ONLY JSON:
{{
  "question": "..."
}}
"""

def build_evaluation_prompt(question: str, answer: str):
    return f"""
Evaluate this answer:

Question: "{question}"
Answer: "{answer}"

Return ONLY JSON:
{{
  "technical_score": 0,
  "clarity_score": 0,
  "architecture_score": 0,
  "english_level": "...",
  "strengths": "...",
  "improvements": "...",
  "improved_answer_example": "..."
}}
"""

# =============================================================================
# MENU HELPERS
# =============================================================================

def select_level():
    while True:
        clear_screen()
        print("=== SELECT LEVEL ===")
        print("1 - Mid")
        print("2 - Senior")
        print("3 - Architect")
        print("\nDigite número | v = voltar | s = sair")

        cmd = input("Option: ").strip().lower()

        if cmd == "s":
            sys.exit()
        if cmd == "v":
            return None

        return {"1": "mid", "2": "senior", "3": "architect"}.get(cmd)

def select_area():
    while True:
        clear_screen()
        print("=== SELECT AREA ===")
        print("1 - Microservices")
        print("2 - Event-Driven")
        print("3 - Azure")
        print("4 - AWS")
        print("5 - System Design")
        print("6 - Payments")
        print("\nDigite número | v = voltar | s = sair")

        cmd = input("Option: ").strip().lower()

        if cmd == "s":
            sys.exit()
        if cmd == "v":
            return None

        return {
            "1": "Microservices",
            "2": "Event-Driven Architecture",
            "3": "Azure",
            "4": "AWS",
            "5": "System Design",
            "6": "Payments Architecture"
        }.get(cmd)

# =============================================================================
# STUDY MODE
# =============================================================================

def run_study_mode():
    level = select_level()
    if not level:
        return

    area = select_area()
    if not area:
        return

    clear_screen()
    print("📚 Generating study material...\n")

    study_data = groq_json(build_study_prompt(area, level))

    print("=== STUDY MATERIAL ===\n")
    print(study_data["overview"])

    print("\nKey Concepts:")
    for c in study_data["key_concepts"]:
        print(f" - {c}")

    print("\nCommon Mistakes:")
    for m in study_data["common_mistakes"]:
        print(f" - {m}")

    history = load_json(STUDY_FILE, {"studies": []})

    history["studies"].append({
        "date": datetime.now().isoformat(),
        "area": area,
        "level": level,
        "overview": study_data["overview"]
    })

    save_json(STUDY_FILE, history)

    wait_enter()

# =============================================================================
# INTERVIEW MODE
# =============================================================================

def run_interview():
    level = select_level()
    if not level:
        return

    area = select_area()
    if not area:
        return

    studies = load_json(STUDY_FILE, {"studies": []})["studies"]

    study_context = ""
    if studies:
        recent = studies[-3:]
        for s in recent:
            study_context += f"{s['area']} ({s['level']}): {s['overview'][:150]}...\n"

    clear_screen()
    print("🧠 Generating question...\n")

    question_data = groq_json(build_question_prompt(level, area, study_context))
    question = question_data["question"]

    print("=== INTERVIEW QUESTION ===\n")
    print(question)
    print("\nType your answer:\n")

    answer = input("> ")

    clear_screen()
    print("📊 Evaluating...\n")

    evaluation = groq_json(build_evaluation_prompt(question, answer))

    print("=== RESULT ===\n")
    print(f"Technical: {evaluation['technical_score']}/10")
    print(f"Clarity: {evaluation['clarity_score']}/10")
    print(f"Architecture: {evaluation['architecture_score']}/10")
    print(f"English: {evaluation['english_level']}")

    print("\nStrengths:")
    print(evaluation["strengths"])

    print("\nImprovements:")
    print(evaluation["improvements"])

    wait_enter()

# =============================================================================
# REVIEW MODE
# =============================================================================

def run_review_mode():
    history = load_json(STUDY_FILE, {"studies": []})["studies"]

    if not history:
        print("No study history found.")
        wait_enter()
        return

    while True:
        clear_screen()
        print("=== STUDY HISTORY ===\n")

        for i, h in enumerate(history):
            preview = h["overview"][:60].replace("\n", " ") + "..."
            print(f"{i+1} - {h['area']} | {h['level']} - {preview}")

        print("\nDigite número | v = voltar | s = sair")

        cmd = input("Option: ").strip().lower()

        if cmd == "s":
            sys.exit()
        if cmd == "v":
            return

        if cmd.isdigit():
            index = int(cmd) - 1
            if 0 <= index < len(history):
                clear_screen()
                print("=== FULL STUDY ===\n")
                print(history[index]["overview"])
                wait_enter()

# =============================================================================
# MAIN
# =============================================================================

def main():
    while True:
        clear_screen()
        print("=== EKF DEV INTERVIEW ENGINE ===\n")
        print("1 - Interview Mode")
        print("2 - Study Mode")
        print("3 - Review Study History")
        print("\nDigite número | s = sair")

        cmd = input("Option: ").strip().lower()

        if cmd == "s":
            break
        if cmd == "1":
            run_interview()
        if cmd == "2":
            run_study_mode()
        if cmd == "3":
            run_review_mode()

if __name__ == "__main__":
    main()
