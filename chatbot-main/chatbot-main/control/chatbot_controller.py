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
    obtener_conversaciones, obtener_derivaciones,
    obtener_reportes_anonimos, validar_recurso,
    guardar_validacion_prediccion, obtener_validaciones_predicciones,
    calcular_metricas, evaluar_intervenciones
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

        # --- Historial limitado de conversaciones previas ---
        conversaciones_previas = obtener_conversaciones(estudiante_id, limit=4)
        historial = [
            (c.get("mensaje_usuario", ""), c.get("respuesta_chatbot", ""))
            for c in conversaciones_previas
        ]

        # --- Detección de emociones ---
        emociones_detectadas = detectar_emocion(mensaje)
        if isinstance(emociones_detectadas, list):
            emociones_str = ",".join(emociones_detectadas)
            emociones_cod = [self.codificar_emocion(e) for e in emociones_detectadas]
        else:
            emociones_str = emociones_detectadas
            emociones_cod = [self.codificar_emocion(emociones_detectadas)]

        # --- Respuesta OpenRouter con manejo seguro ---
        try:
            respuesta = obtener_respuesta_openrouter(mensaje, historial)
        except Exception as e:
            print(f"[ERROR] OpenRouter API falló: {e}")
            respuesta = "Lo siento, tuve un pequeño problema para responder. ¿Podrías repetirlo?"

        # --- Predicciones de estrés, ansiedad y depresión ---
        nivel_estres = predecir_estres(mensaje)
        ansiedad, depresion = predecir_ansiedad_depresion(mensaje)

        # --- Preparar datos para guardar una sola vez ---
        emocion_cod_to_save = emociones_cod[0] if emociones_cod else None
        conv_data = {
            "estudiante_id": estudiante_id,
            "mensaje_usuario": mensaje,
            "emocion_detectada": emociones_str,
            "nivel_estres": nivel_estres,
            "ansiedad": ansiedad,
            "depresion": depresion,
            "respuesta_chatbot": respuesta,
            "emocion_cod": emocion_cod_to_save
        }

        # --- Generar recomendación si hay riesgo ---
        if nivel_estres != "bajo" or ansiedad or depresion:
            recomendacion = self.generar_recomendacion(estudiante_id, nivel_estres, ansiedad, depresion)
            conv_data["respuesta_chatbot"] = f"{respuesta}\n\n💡 *Recomendación:* {recomendacion}"

        # --- Evaluar derivación a psicólogo ---
        derivacion_msg = derivar_si_riesgo({
            "mensaje": mensaje,
            "emocion": emociones_str,
            "estres": nivel_estres,
            "ansiedad": ansiedad,
            "depresion": depresion,
            "estudiante_id": estudiante_id
        }, None)

        if derivacion_msg:
            conv_data["respuesta_chatbot"] += f"\n⚠️ {derivacion_msg}"

        # --- Guardar conversación una sola vez ---
        conv_id = guardar_conversacion(**conv_data)

        return {
            "emocion": emociones_str,
            "emocion_cod": emociones_cod,
            "nivel_estres": nivel_estres,
            "ansiedad": ansiedad,
            "depresion": depresion,
            "respuesta": conv_data["respuesta_chatbot"],
            "conversacion_id": conv_id
        }

    # -------------------------------------------------------------------------
    # DERIVACIÓN Y CONSULTAS
    # -------------------------------------------------------------------------
    def derivar_a_psicologo(self, conversacion_id: str, psicologo_id: str) -> bool:
        return guardar_derivacion(conversacion_id, psicologo_id)

    def obtener_profesionales(self) -> list:
        return obtener_psicologos()

    def obtener_derivaciones(self) -> list:
        return obtener_derivaciones()

    def listar_reportes_anonimos(self) -> list:
        return obtener_reportes_anonimos()

    def validar_recurso(self, url: str) -> dict:
        return validar_recurso(url)

    def validar_prediccion(self, conversacion_id: str, validador_id: str = None, valido: bool = True, comentarios: str = None) -> str:
        return guardar_validacion_prediccion(conversacion_id, validador_id=validador_id, valido=valido, comentarios=comentarios)

    def obtener_validaciones_predicciones(self, conversacion_id: str = None) -> list:
        return obtener_validaciones_predicciones(conversacion_id)

    def obtener_metricas(self) -> dict:
        return calcular_metricas()

    def evaluar_intervenciones(self) -> dict:
        return evaluar_intervenciones()

    def obtener_conversacion(self, correo_estudiante: str) -> list:
        estudiante = obtener_estudiante_por_correo(correo_estudiante)
        if not estudiante:
            return []

        conversaciones = obtener_conversaciones(estudiante["id"], limit=100)
        conversaciones.sort(key=lambda c: c.get("timestamp", datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)))

        mensajes = []
        for c in conversaciones:
            mensajes.append({
                "remitente": "Tú",
                "texto": c.get("mensaje_usuario", ""),
                "ansiedad": c.get("ansiedad"),
                "depresion": c.get("depresion"),
                "emocion_detectada": c.get("emocion_detectada"),
                "conversacion_id": c.get("id")
            })
            mensajes.append({
                "remitente": "Bot",
                "texto": c.get("respuesta_chatbot", ""),
                "conversacion_id": c.get("id")
            })
        return mensajes

    # -------------------------------------------------------------------------
    # CODIFICACIÓN NUMÉRICA DE EMOCIONES
    # -------------------------------------------------------------------------
    def codificar_emocion(self, emocion: str) -> int:
        mapping = {
            "alegria": 1, "alegría": 1, "feliz": 1,
            "triste": 2, "tristeza": 2,
            "miedo": 3, "temor": 3,
            "enojo": 4, "enojado": 4,
            "sorpresa": 5,
            "ansiedad": 6, "ansioso": 6, "nervioso": 6,
            "neutral": 0,
            "despedida": 9
        }
        if not emocion:
            return 99
        e = emocion.lower().strip()
        return mapping.get(e, next((mapping[k] for k in mapping if k in e), 99))
