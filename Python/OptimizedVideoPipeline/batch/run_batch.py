import json, subprocess, sys
from pathlib import Path

CREATE_LATER = Path("CreateLater.json")
pending = json.loads(CREATE_LATER.read_text()).get("pending", [])

for word in pending:
    subprocess.run([sys.executable, "batch/process_word.py", word], check=True)

CREATE_LATER.write_text(json.dumps({"pending": []}, indent=2))
