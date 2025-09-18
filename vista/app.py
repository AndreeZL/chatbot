# vista/app.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from control.chatbot_controller import ChatbotController

def main():
    controller = ChatbotController()
    print("=== EMOTIBOT — Chat de apoyo emocional ===")

    # Registro del estudiante
    correo = input("Ingrese su correo institucional: ").strip()
    nombre = input("Ingrese su nombre completo: ").strip()
    controller.registrar_estudiante(nombre, correo)

    print(f"\n👋 Hola {nombre}, puedes empezar a conversar conmigo. (Escribe 'salir' para terminar)\n")

    while True:
        texto = input("Tú: ").strip()
        if texto.lower() in ["salir", "adios", "chao"]:
            print("Chatbot: Cuídate mucho 👋")
            break
        resultado = controller.procesar_mensaje(correo, texto)
        print("Chatbot:", resultado["respuesta"])

if __name__ == "__main__":
    main()
