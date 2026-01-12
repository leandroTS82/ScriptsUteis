import os

class ProjectReader:
    def __init__(self, config):
        self.extensions = config["extensions"]
        self.ignore = config["ignore_folders"]

    def read(self, root_path: str) -> list:
        files = []

        for root, dirs, filenames in os.walk(root_path):
            dirs[:] = [d for d in dirs if d not in self.ignore]

            for file in filenames:
                if any(file.endswith(ext) for ext in self.extensions):
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            files.append({
                                "path": path,
                                "content": f.read()
                            })
                    except Exception:
                        continue

        return files
