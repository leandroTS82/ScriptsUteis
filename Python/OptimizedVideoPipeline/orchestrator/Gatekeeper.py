import json, sys
from pathlib import Path

ROOT = Path(".")
LOCK = ROOT / "runtime/pipeline.lock"
CREATE_LATER = ROOT / "CreateLater.json"
READY = ROOT / "input/ReadyToBeCreated"

if LOCK.exists():
    sys.exit(0)

data = json.loads(CREATE_LATER.read_text()) if CREATE_LATER.exists() else {"pending": []}
if data["pending"]:
    sys.exit(0)

terms = []
for f in READY.glob("*.json"):
    j = json.loads(f.read_text())
    terms.extend(j.get("pending", []))
    f.rename(f.with_name("processing_" + f.name))

if not terms:
    sys.exit(0)

LOCK.write_text("locked")
CREATE_LATER.write_text(json.dumps({"pending": list(set(terms))}, indent=2))
sys.exit(2)
