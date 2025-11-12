import os, requests

api_key = os.environ.get("OPENROUTER_API_KEY")

if not api_key:
    print("❌ No se encontró la variable OPENROUTER_API_KEY")
    exit()

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:5000",
    "X-Title": "Emotibot Psicología"
}

data = {
    "model": "mistralai/mistral-7b-instruct",
    "messages": [{"role": "user", "content": "Hola, ¿cómo estás?"}]
}

try:
    r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    print("Código de estado:", r.status_code)
    print("Respuesta:", r.text)
except Exception as e:
    print("❌ Error:", e)
