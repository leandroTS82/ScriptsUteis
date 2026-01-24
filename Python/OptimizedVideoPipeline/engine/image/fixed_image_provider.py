import json
from engine.project_root import get_project_root

ROOT = get_project_root()

cfg = json.load(
    open(ROOT / "settings" / "pipeline.json", encoding="utf-8")
)

def get_fixed_image() -> str:
    return str(ROOT / cfg["fixed_image_path"])
