import json
cfg = json.load(open("settings/pipeline.json"))

def get_fixed_image():
    return cfg["fixed_image_path"]
