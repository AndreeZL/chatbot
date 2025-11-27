# utils/openrouter_api.py
import os
import requests

def obtener_respuesta_openrouter(mensaje, historial=None):
    """
    Envía un mensaje a OpenRouter y devuelve la respuesta del chatbot.
    
    Args:
        mensaje (str): Mensaje del usuario.
        historial (list, opcional): Lista de tuplas [(mensaje_usuario, respuesta_chatbot), ...]
    
    Returns:
        str: Respuesta generada por el modelo.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ No se encontró la variable OPENROUTER_API_KEY")
        return "No tengo conexión con el modelo, por favor intenta más tarde."

    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",  # ⚠️ Requerido por OpenRouter
        "X-Title": "Emotibot Psicología"           # Nombre de tu app
    }

    # Mensaje inicial del sistema
    mensajes = [
        {
            "role": "system",
            "content": "Eres un psicólogo empático que escucha y ofrece orientación emocional breve en español."
        }
    ]

    # Agregar historial previo
    if historial:
        for user_msg, bot_msg in historial:
            mensajes.append({"role": "user", "content": user_msg})
            mensajes.append({"role": "assistant", "content": bot_msg})

    # Agregar el mensaje actual del usuario
    mensajes.append({"role": "user", "content": mensaje})

    payload = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": mensajes,
        "max_tokens": 250,
        "temperature": 0.8
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        # Extraer la respuesta del asistente
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"❌ Error al conectar con OpenRouter: {e}")
        return "Lo siento, tuve un problema para responder. ¿Podrías repetirlo?"
