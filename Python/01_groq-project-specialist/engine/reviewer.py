class Reviewer:
    def __init__(self, groq_client):
        self.client = groq_client

    def review(self, prompts: list) -> list:
        results = []

        for p in prompts:
            results.append(self.client.call(p))

        return results
