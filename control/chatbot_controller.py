# control/chatbot_controller.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot_repo.chatbot import detectar_emocion, obtener_respuesta
from utils.predict_stress import predecir_estres
from utils.predict_ansiedad_depresion import predecir_ansiedad_depresion
from modelo.firebase_models import (
    crear_estudiante, obtener_estudiante_por_correo,
    guardar_conversacion, guardar_recomendacion,
    guardar_derivacion, obtener_psicologos,
    obtener_conversaciones
)
import datetime
import random
import firebase_admin
from firebase_admin import credentials, firestore

# Inicializar Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("database/chatbot-78eec-firebase-adminsdk-fbsvc-b0eea0da20.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

class ChatbotController:
    def registrar_estudiante(self, nombre, correo, carrera):
        estudiante = obtener_estudiante_por_correo(correo)
        if not estudiante:
            estudiante_id = crear_estudiante(nombre, correo, carrera)
            print(f"✅ Estudiante registrado en Firestore: {nombre} ({correo}) {carrera}")
            return {"id": estudiante_id, "nombre": nombre, "correo": correo, "carrera": carrera}
        return estudiante

    def generar_recomendacion(self, estudiante_id, nivel_estres, ansiedad, depresion):
        opciones = []

        # Estrés
        if nivel_estres == "alto":
            opciones.extend([
                "Intenta hacer ejercicios de respiración profunda durante 5 minutos.",
                "Tómate un descanso corto y escucha música relajante.",
                "Escribe tus pensamientos en un diario para liberar tensión."
            ])
        elif nivel_estres == "medio":
            opciones.extend([
                "Realiza una caminata corta para despejar tu mente.",
                "Prueba técnicas de mindfulness por unos minutos.",
                "Organiza tus tareas para reducir la presión."
            ])
        else:  # bajo
            opciones.extend([
                "Mantén tu rutina positiva y aprovecha el momento.",
                "Comparte tu tiempo libre con amigos o familia.",
                "Continúa con tus actividades que te hagan sentir bien."
            ])

        # Ansiedad
        if ansiedad:
            opciones.extend([
                "Respira profundamente y cuenta hasta 10.",
                "Habla con alguien de confianza sobre lo que sientes.",
                "Realiza un ejercicio de relajación muscular progresiva."
            ])

        # Depresión
        if depresion:
            opciones.extend([
                "Intenta realizar una actividad que normalmente disfrutes.",
                "Sal a dar un paseo al aire libre, aunque sea corto.",
                "Busca apoyo de un amigo o familiar cercano."
            ])

        if not opciones:
            opciones.append("Mantén una actitud positiva y cuida tu bienestar diario.")

        recomendacion = random.choice(opciones)

        # Guardar en Firestore
        guardar_recomendacion(estudiante_id, recomendacion)

        return recomendacion

    def procesar_mensaje(self, correo_estudiante, mensaje):
        despedidas = ["chao", "adios", "adiós", "salir", "eso es todo"]

        if mensaje.lower().strip() in despedidas:
            emocion = "despedida"
            respuesta = "👋 Nos vemos, recuerda que siempre estaré aquí para ti."
        else:
            emocion = detectar_emocion(mensaje)
            respuesta = obtener_respuesta(emocion)

        estudiante = obtener_estudiante_por_correo(correo_estudiante)
        if not estudiante:
            raise ValueError("El estudiante no está registrado.")

        estudiante_id = estudiante["id"]

        # Predicciones automáticas
        nivel_estres = predecir_estres(mensaje)
        ansiedad, depresion = predecir_ansiedad_depresion(mensaje)

        # Verificar cuántas conversaciones previas tiene el estudiante
        conversaciones_previas = obtener_conversaciones(estudiante_id)

        # Guardar conversación inicial
        conv_id = guardar_conversacion(
            estudiante_id, mensaje, emocion, nivel_estres, ansiedad, depresion, respuesta
        )

        respuesta_final = respuesta

        # 🔹 Solo generar recomendación si NO es el primer mensaje
        if len(conversaciones_previas) > 0:
            recomendacion = self.generar_recomendacion(estudiante_id, nivel_estres, ansiedad, depresion)
            respuesta_final = f"{respuesta}\n💡 Recomendación: {recomendacion}"

            # Actualizar conversación con recomendación
            guardar_conversacion(
                estudiante_id, mensaje, emocion, nivel_estres, ansiedad, depresion, respuesta_final, conv_id
            )

        # Derivación automática
        from utils.derivar_automatico import derivar_si_riesgo
        respuesta_derivacion = derivar_si_riesgo(
            {"id": conv_id, "mensaje": mensaje, "emocion": emocion,
             "estres": nivel_estres, "ansiedad": ansiedad, "depresion": depresion},
            None
        )

        if respuesta_derivacion:
            respuesta_final = f"{respuesta_final}\n⚠️ {respuesta_derivacion}"
            guardar_conversacion(
                estudiante_id, mensaje, emocion, nivel_estres, ansiedad, depresion, respuesta_final, conv_id
            )

        return {
            "emocion": emocion,
            "nivel_estres": nivel_estres,
            "ansiedad": ansiedad,
            "depresion": depresion,
            "respuesta": respuesta_final,
            "conversacion_id": conv_id
        }

    def derivar_a_psicologo(self, conversacion_id, psicologo_id):
        return guardar_derivacion(conversacion_id, psicologo_id)

    def obtener_profesionales(self):
        return obtener_psicologos()

    def obtener_conversacion(self, correo_estudiante):
        estudiante = obtener_estudiante_por_correo(correo_estudiante)
        if not estudiante:
            return []

        conversaciones = db.collection("conversaciones") \
            .where("estudiante_id", "==", estudiante["id"]) \
            .stream()

        conversaciones_list = [doc.to_dict() for doc in conversaciones]
        conversaciones_list.sort(
            key=lambda x: x.get(
                "timestamp",
                datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
            )
        )

        mensajes = []
        for c in conversaciones_list:
            mensajes.append(("Tú", c.get("mensaje_usuario", "")))
            mensajes.append(("Bot", c.get("respuesta_chatbot", "")))

        return mensajes
