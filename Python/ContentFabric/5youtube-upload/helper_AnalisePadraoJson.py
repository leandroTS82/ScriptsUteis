import json, os

path = r"C:\Users\leand\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\EKF - English Knowledge Framework - Videos\Videos\flavored_antacid.json"

print("EXISTE? ", os.path.exists(path))

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("CHAVES DO JSON: ", list(data.keys()))