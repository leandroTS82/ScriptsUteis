import google.generativeai as genai
import os

# Caminho da sua chave
key_path = "./google-gemini-key.txt"

# Ler a chave
with open(key_path, "r") as f:
    api_key = f.read().strip()

# Configurar Gemini
genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel("gemini-3-pro-preview")
    response = model.generate_content("Say hello!")
    print("✅ Chave funcionando!")
    print("Resposta:", response.text)

except Exception as e:
    print("❌ Erro na chave!")
    print(e)
