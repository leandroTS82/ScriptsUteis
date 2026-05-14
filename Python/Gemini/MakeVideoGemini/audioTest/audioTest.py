# ============================================================
# audioTest.py
#
# Runner de teste para generate_audio_edge.py
# ============================================================

import os
import sys
import json

# ============================================================
# PATHS
# ============================================================

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

ROOT_DIR = os.path.abspath(
    os.path.join(CURRENT_DIR, "..")
)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ============================================================
# IMPORT
# ============================================================

from generate_audio_edge import (
    generate_audio_edge
)

# ============================================================
# FILES
# ============================================================

JSON_PATH = os.path.join(
    CURRENT_DIR,
    "audioTest.json"
)

OUTPUT_DIR = os.path.join(
    CURRENT_DIR,
    "outputs"
)

OUTPUT_AUDIO = os.path.join(
    OUTPUT_DIR,
    "audioTest.wav"
)

# ============================================================
# LOAD JSON
# ============================================================

with open(
    JSON_PATH,
    "r",
    encoding="utf-8"
) as f:

    lesson_json = json.load(f)

# ============================================================
# EXECUTE
# ============================================================

print("===================================")
print("🎧 AUDIO TEST STARTED")
print("===================================")

generate_audio_edge(
    lesson_json,
    OUTPUT_AUDIO
)

print("===================================")
print("✅ AUDIO TEST FINISHED")
print(f"📁 Output: {OUTPUT_AUDIO}")
print("===================================")