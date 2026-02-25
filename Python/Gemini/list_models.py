import google.generativeai as genai

key_path = "C:\\Users\\leand\\LTS - CONSULTORIA E DESENVOLVtIMENTO DE SISTEMAS\\EKF - English Knowledge Framework - Base\\FilesHelper\\secret_tokens_keys\\google-gemini-key.txt"
api_key = open(key_path).read().strip()

genai.configure(api_key=api_key)

print("📌 MODELOS DISPONÍVEIS PARA SUA KEY:\n")

for m in genai.list_models():
    print("➡", m.name, " | métodos:", m.supported_generation_methods)
    
    # Python list_models.py
