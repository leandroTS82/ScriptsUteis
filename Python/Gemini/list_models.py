import google.generativeai as genai

key_path = "./google-gemini-key.txt"
api_key = open(key_path).read().strip()

genai.configure(api_key=api_key)

print("📌 MODELOS DISPONÍVEIS PARA SUA KEY:\n")

for m in genai.list_models():
    print("➡", m.name, " | métodos:", m.supported_generation_methods)
