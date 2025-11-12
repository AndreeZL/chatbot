# control/chatbot_controller.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import datetime
import random
import firebase_admin
from firebase_admin import credentials, firestore

from modelo.chatbot import detectar_emocion
from utils.predict_stress import predecir_estres
from utils.predict_ansiedad_depresion import predecir_ansiedad_depresion
from utils.openrouter_api import obtener_respuesta_openrouter
from utils.derivar_automatico import derivar_si_riesgo
from modelo.firebase_models import (
    crear_estudiante, obtener_estudiante_por_correo,
    guardar_conversacion, guardar_recomendacion,
    guardar_derivacion, obtener_psicologos,
    obtener_conversaciones
)

# Inicializar Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("database/chatbot-78eec-firebase-adminsdk-fbsvc-b0eea0da20.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

class ChatbotController:

    # -------------------------------------------------------------------------
    # REGISTRO DE ESTUDIANTE
    # -------------------------------------------------------------------------
    def registrar_estudiante(self, nombre: str, correo: str, carrera: str) -> dict:
        estudiante = obtener_estudiante_por_correo(correo)
        if estudiante:
            return estudiante

        estudiante_id = crear_estudiante(nombre, correo, carrera)
        return {
            "id": estudiante_id,
            "nombre": nombre,
            "correo": correo,
            "carrera": carrera
        }

    # -------------------------------------------------------------------------
    # GENERADOR DE RECOMENDACIONES
    # -------------------------------------------------------------------------
    def generar_recomendacion(self, estudiante_id: str, nivel_estres: str, ansiedad: bool, depresion: bool) -> str:
        opciones = []

        # Estrés
        if nivel_estres == "alto":
            opciones += [
                "Haz ejercicios de respiración profunda durante 5 minutos.",
                "Escucha música relajante.",
                "Escribe tus pensamientos para liberar tensión."
            ]
        elif nivel_estres == "medio":
            opciones += [
                "Da una caminata corta para despejar tu mente.",
                "Prueba una breve sesión de mindfulness.",
                "Organiza tus tareas pendientes para reducir la carga mental."
            ]
        else:
            opciones += [
                "Mantén tus hábitos saludables y tu rutina positiva.",
                "Comparte tiempo con amigos o familia.",
                "Continúa con actividades que disfrutes."
            ]

        # Ansiedad y Depresión
        if ansiedad:
            opciones += [
                "Practica respiración profunda y pausada.",
                "Habla con alguien de confianza sobre cómo te sientes.",
                "Realiza ejercicios de relajación muscular progresiva."
            ]
        if depresion:
            opciones += [
                "Haz una actividad que disfrutes, aunque sea pequeña.",
                "Sal a caminar para conectar con el entorno.",
                "Busca apoyo emocional en personas cercanas."
            ]

        if not opciones:
            opciones = ["Mantén una actitud positiva y cuida tu bienestar."]

        recomendacion = random.choice(opciones)
        guardar_recomendacion(estudiante_id, recomendacion)
        return recomendacion

    # -------------------------------------------------------------------------
    # PROCESAMIENTO DE MENSAJES
    # -------------------------------------------------------------------------
    def procesar_mensaje(self, correo_estudiante: str, mensaje: str) -> dict:
        despedidas = {"chao", "adios", "adiós", "salir", "eso es todo"}
        mensaje_limpio = mensaje.lower().strip()

        estudiante = obtener_estudiante_por_correo(correo_estudiante)
        if not estudiante:
            raise ValueError("❌ Estudiante no registrado en la base de datos.")
        estudiante_id = estudiante["id"]

        # --- Si el usuario se despide ---
        if mensaje_limpio in despedidas:
            return {
                "emocion": "despedida",
                "nivel_estres": None,
                "ansiedad": None,
                "depresion": None,
                "respuesta": "👋 Nos vemos pronto, recuerda que siempre estaré aquí para escucharte.",
                "conversacion_id": None
            }

        # --- Historial de conversaciones previas ---
        conversaciones_previas = obtener_conversaciones(estudiante_id)
        historial = [
            (c.get("mensaje_usuario", ""), c.get("respuesta_chatbot", ""))
            for c in conversaciones_previas[-4:]
        ]

        # --- Detección de emociones ---
        emociones_detectadas = detectar_emocion(mensaje)
        if isinstance(emociones_detectadas, list):
            emociones_str = ",".join(emociones_detectadas)
            emociones_cod = [self.codificar_emocion(e) for e in emociones_detectadas]
        else:
            emociones_str = emociones_detectadas
            emociones_cod = [self.codificar_emocion(emociones_detectadas)]

        # --- Respuesta OpenRouter ---
        try:
            respuesta = obtener_respuesta_openrouter(mensaje, historial)
        except Exception as e:
            print(f"[ERROR] OpenRouter API falló: {e}")
            respuesta = "Lo siento, tuve un pequeño problema para responder. ¿Podrías repetirlo?"

        # --- Predicciones de estrés, ansiedad y depresión ---
        nivel_estres = predecir_estres(mensaje)
        ansiedad, depresion = predecir_ansiedad_depresion(mensaje)

        # --- Guardar conversación en Firebase ---
        conv_id = guardar_conversacion(
            estudiante_id, mensaje, emociones_str, nivel_estres, ansiedad, depresion, respuesta
        )

        # --- Generar recomendación si hay riesgo ---
        respuesta_final = respuesta
        if nivel_estres != "bajo" or ansiedad or depresion:
            recomendacion = self.generar_recomendacion(estudiante_id, nivel_estres, ansiedad, depresion)
            respuesta_final = f"{respuesta}\n\n💡 *Recomendación:* {recomendacion}"

            # Actualizar Firebase con la recomendación
            guardar_conversacion(
                estudiante_id, mensaje, emociones_str, nivel_estres, ansiedad, depresion, respuesta_final, conv_id
            )

        # --- Evaluar derivación a psicólogo ---
        derivacion_msg = derivar_si_riesgo({
            "id": conv_id,
            "mensaje": mensaje,
            "emocion": emociones_str,
            "estres": nivel_estres,
            "ansiedad": ansiedad,
            "depresion": depresion,
            "estudiante_id": estudiante_id
        }, None)

        if derivacion_msg:
            respuesta_final += f"\n⚠️ {derivacion_msg}"
            guardar_conversacion(
                estudiante_id, mensaje, emociones_str, nivel_estres, ansiedad, depresion, respuesta_final, conv_id
            )

        return {
            "emocion": emociones_str,
            "emocion_cod": emociones_cod,
            "nivel_estres": nivel_estres,
            "ansiedad": ansiedad,
            "depresion": depresion,
            "respuesta": respuesta_final,
            "conversacion_id": conv_id
        }

    # -------------------------------------------------------------------------
    # DERIVACIÓN Y CONSULTAS
    # -------------------------------------------------------------------------
    def derivar_a_psicologo(self, conversacion_id: str, psicologo_id: str) -> bool:
        return guardar_derivacion(conversacion_id, psicologo_id)

    def obtener_profesionales(self) -> list:
        return obtener_psicologos()

    def obtener_conversacion(self, correo_estudiante: str) -> list:
        estudiante = obtener_estudiante_por_correo(correo_estudiante)
        if not estudiante:
            return []

        conversaciones = obtener_conversaciones(estudiante["id"])
        conversaciones.sort(
            key=lambda c: c.get("timestamp", datetime.datetime.min.replace(tzinfo=datetime.timezone.utc))
        )

        mensajes = []
        for c in conversaciones:
            mensajes.append(("Tú", c.get("mensaje_usuario", "")))
            mensajes.append(("Bot", c.get("respuesta_chatbot", "")))

        return mensajes

    # -------------------------------------------------------------------------
    # CODIFICACIÓN NUMÉRICA DE EMOCIONES
    # -------------------------------------------------------------------------
    def codificar_emocion(self, emocion: str) -> int:
        mapping = {
            "alegria": 1,
            "tristeza": 2,
            "miedo": 3,
            "enojo": 4,
            "sorpresa": 5,
            "ansiedad": 6,
            "neutral": 0,
            "despedida": 9
        }
        return mapping.get(emocion.lower(), 99)
