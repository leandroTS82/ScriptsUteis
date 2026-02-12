"""
====================================================================================
 EKF_DevInterviewEngine.py
 Dev Interview Training Engine (Groq Only)
 Versão: V3.0 - Navegação com voltar + limpar tela
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

# =============================================================================
# UTIL
# =============================================================================

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def wait_enter():
    input("\nPress ENTER to continue...")

# =============================================================================
# GROQ ROTATION
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
# PROMPTS
# =============================================================================

def build_study_prompt(area: str, level: str) -> str:
    return f"""
You are a senior backend architect teaching a developer preparing for interviews.

Topic: {area}
Target level: {level}

Return ONLY JSON:

{{
  "overview": "clear explanation",
  "key_concepts": ["...", "...", "..."],
  "real_world_examples": ["...", "..."],
  "common_mistakes": ["...", "..."],
  "interview_questions": ["...", "...", "..."]
}}
"""

def build_question_prompt(level: str, area: str) -> str:
    return f"""
You are a senior technical interviewer.

Generate ONE technical interview question.

Area focus: {area}
Level: {level}

Return ONLY JSON:

{{
  "question": "...",
  "area": "{area}",
  "difficulty": "{level}"
}}
"""

def build_evaluation_prompt(question: str, answer: str) -> str:
    return f"""
Evaluate this Senior Backend Engineer answer.

Question:
"{question}"

Answer:
"{answer}"

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
# STATS
# =============================================================================

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {"sessions": [], "total_xp": 0}

    with open(STATS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_stats(data):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def calculate_xp(result: dict) -> int:
    total = (
        result["technical_score"] +
        result["clarity_score"] +
        result["architecture_score"]
    )
    return int(total * 2)

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

        level_map = {"1": "mid", "2": "senior", "3": "architect"}
        if cmd in level_map:
            return level_map[cmd]

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

        area_map = {
            "1": "Microservices",
            "2": "Event-Driven Architecture",
            "3": "Azure",
            "4": "AWS",
            "5": "System Design",
            "6": "Payments Architecture"
        }

        if cmd in area_map:
            return area_map[cmd]

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

    print("\nReal World Examples:")
    for e in study_data["real_world_examples"]:
        print(f" - {e}")

    print("\nCommon Mistakes:")
    for m in study_data["common_mistakes"]:
        print(f" - {m}")

    print("\nInterview Questions:")
    for q in study_data["interview_questions"]:
        print(f" - {q}")

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

    clear_screen()
    print("🧠 Generating question...\n")

    question_data = groq_json(build_question_prompt(level, area))
    question = question_data["question"]

    print("=== INTERVIEW QUESTION ===\n")
    print(question)
    print("\nType your answer below:\n")

    answer = input("> ")

    clear_screen()
    print("📊 Evaluating...\n")

    evaluation = groq_json(build_evaluation_prompt(question, answer))
    xp = calculate_xp(evaluation)

    print("=== RESULT ===\n")
    print(f"Technical: {evaluation['technical_score']}/10")
    print(f"Clarity: {evaluation['clarity_score']}/10")
    print(f"Architecture: {evaluation['architecture_score']}/10")
    print(f"English: {evaluation['english_level']}")
    print(f"\nXP Gained: {xp}")

    print("\nStrengths:")
    print(evaluation["strengths"])

    print("\nImprovements:")
    print(evaluation["improvements"])

    print("\nImproved Example:")
    print(evaluation["improved_answer_example"])

    stats = load_stats()
    stats["sessions"].append({
        "date": datetime.now().isoformat(),
        "area": area,
        "level": level,
        "xp": xp
    })
    stats["total_xp"] += xp
    save_stats(stats)

    print(f"\n🔥 Total XP: {stats['total_xp']}")

    wait_enter()

# =============================================================================
# MAIN MENU
# =============================================================================

def main():
    while True:
        clear_screen()
        print("=== EKF DEV INTERVIEW ENGINE ===\n")
        print("1 - Interview Mode")
        print("2 - Study Mode")
        print("\nDigite número | s = sair")

        cmd = input("Option: ").strip().lower()

        if cmd == "s":
            break
        if cmd == "1":
            run_interview()
        if cmd == "2":
            run_study_mode()

if __name__ == "__main__":
    main()
