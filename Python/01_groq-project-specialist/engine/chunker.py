class Chunker:
    def __init__(self, max_chars: int):
        self.max_chars = max_chars

    def chunk(self, files: list) -> list:
        chunks = []
        current = ""

        for f in files:
            entry = f"\nFILE: {f['path']}\n{f['content']}\n"

            if len(current) + len(entry) > self.max_chars:
                chunks.append(current)
                current = entry
            else:
                current += entry

        if current:
            chunks.append(current)

        return chunks
