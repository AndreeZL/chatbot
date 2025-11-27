# chatbot_repo/chatbot.py
import random

def detectar_emocion(texto):
    texto = texto.lower()
    if any(palabra in texto for palabra in ["triste", "mal", "deprimido", "bajón", "desanimado"]):
        return "triste"
    elif any(palabra in texto for palabra in ["ansioso", "nervioso", "preocupado", "estresado"]):
        return "ansioso"
    elif any(palabra in texto for palabra in ["feliz", "bien", "contento", "alegre", "genial"]):
        return "feliz"
    elif any(palabra in texto for palabra in ["enojado", "molesto", "frustrado", "irritado"]):
        return "enojado"
    elif "ayuda" in texto:
        return "ayuda"
    else:
        return "desconocido"

def obtener_respuesta(emocion):
    respuestas = {
        "triste": [
            "Lo siento que te sientas así 😔. ¿Quieres contarme qué te preocupa?",
            "Es normal sentirse triste a veces 😢. Estoy aquí para escucharte.",
            "Lamento que estés pasando por un momento difícil 💙. ¿Quieres hablar más sobre ello?"
        ],
        "ansioso": [
            "La ansiedad puede ser muy difícil 😟. Respira profundo, estoy aquí contigo.",
            "Entiendo que te sientas ansioso 😰. ¿Quieres intentar relajarte juntos?",
            "A veces ayuda hablar de lo que nos preocupa 🧘. ¿Quieres intentarlo?"
        ],
        "feliz": [
            "¡Qué bueno que te sientas feliz 😄! ¿Qué te ha hecho sentir así?",
            "Me alegra mucho escuchar eso 🎉. ¡Disfruta ese momento!",
            "La felicidad es contagiosa 😃, gracias por compartirla conmigo."
        ],
        "enojado": [
            "Está bien sentirse enojado a veces 😠. ¿Quieres contarme qué pasó?",
            "La ira puede ser fuerte 🔥, pero hablar ayuda a calmarla.",
            "¿Quieres que te escuche? A veces expresar lo que sentimos ayuda 🤗."
        ],
        "ayuda": [
            "Estoy aquí para apoyarte 🤝. ¿Qué te gustaría compartir?",
            "Cuéntame más, estoy para escucharte 👂.",
            "No estás solo 🧑‍🤝‍🧑, dime cómo puedo ayudarte."
        ],
        "desconocido": [
            "Entiendo 🤔. Cuéntame más, por favor.",
            "Estoy aquí para escucharte, sigue hablando 🗣️.",
            "Gracias por compartir conmigo 🙏. ¿Quieres contarme más?"
        ]
    }
    return random.choice(respuestas.get(emocion, respuestas["desconocido"]))

def responder_texto(texto):
    emocion = detectar_emocion(texto)
    respuesta = obtener_respuesta(emocion)
    return emocion, respuesta

# Si ejecutas este archivo directamente, permite chat interactivo
if __name__ == "__main__":
    print("Hola, soy EMOTIBOT. Escribe 'salir' para terminar.")
    while True:
        user = input("Tú: ").strip()
        if user.lower() in ["salir", "adios", "chao"]:
            print("Chatbot: Cuídate 👋")
            break
        emocion, respuesta = responder_texto(user)
        print("Chatbot:", respuesta)
