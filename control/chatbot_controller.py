# control/chatbot_controller.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modelo.models import Estudiante, Conversacion, Derivacion, Psicologo, Recomendacion, Base
from chatbot_repo.chatbot import detectar_emocion, obtener_respuesta
from utils.predict_stress import predecir_estres
from utils.predict_ansiedad_depresion import predecir_ansiedad_depresion
import datetime
import os
import random

# ----------------------------
# Configuración de la base de datos MySQL
# ----------------------------
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "andreezl13")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "chatbot_db")

engine = create_engine(
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}",
    echo=False
)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


class ChatbotController:
    def __init__(self):
        self.session = Session()

    def registrar_estudiante(self, nombre, correo, carrera):
        estudiante = self.session.query(Estudiante).filter_by(correo=correo).first()
        if not estudiante:
            estudiante = Estudiante(nombre=nombre, correo=correo, carrera=carrera)
            self.session.add(estudiante)
            self.session.commit()
            print(f"✅ Estudiante registrado: {nombre} ({correo}) {carrera}")
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

        # Guardar en BD
        rec = Recomendacion(
            estudiante_id=estudiante_id,
            fecha=datetime.date.today(),
            hora=datetime.datetime.now().time(),
            texto=recomendacion,
            tipo="automática",
            util=None
        )
        self.session.add(rec)
        self.session.commit()

        return recomendacion

    def procesar_mensaje(self, correo_estudiante, mensaje):
        despedidas = ["chao", "adios", "adiós", "salir", "eso es todo"]

        if mensaje.lower().strip() in despedidas:
            emocion = "despedida"
            respuesta = "👋 Nos vemos, recuerda que siempre estaré aquí para ti."
        else:
            emocion = detectar_emocion(mensaje)
            respuesta = obtener_respuesta(emocion)

        estudiante = self.session.query(Estudiante).filter_by(correo=correo_estudiante).first()
        if not estudiante:
            raise ValueError("El estudiante no está registrado.")

        # Predicciones automáticas
        nivel_estres = predecir_estres(mensaje)
        ansiedad, depresion = predecir_ansiedad_depresion(mensaje)

        # Guardar la conversación inicialmente
        conv = Conversacion(
            estudiante_id=estudiante.id,
            fecha=datetime.date.today(),
            hora=datetime.datetime.now().time(),
            mensaje_usuario=mensaje,
            emocion_detectada=emocion,
            nivel_estres=nivel_estres,
            ansiedad=ansiedad,
            depresion=depresion,
            respuesta_chatbot=respuesta
        )
        self.session.add(conv)
        self.session.commit()

        # Generar recomendación y actualizar respuesta
        recomendacion = self.generar_recomendacion(estudiante.id, nivel_estres, ansiedad, depresion)
        respuesta_final = f"{respuesta}\n💡 Recomendación: {recomendacion}"

        conv.respuesta_chatbot = respuesta_final
        self.session.commit()

        # Derivación automática si es de riesgo
        from utils.derivar_automatico import derivar_si_riesgo
        respuesta_derivacion = derivar_si_riesgo(conv, self.session)
        if respuesta_derivacion:
            conv.respuesta_chatbot = f"{respuesta_final}\n⚠️ {respuesta_derivacion}"
            self.session.commit()
            respuesta_final = conv.respuesta_chatbot

        return {
            "emocion": emocion,
            "nivel_estres": nivel_estres,
            "ansiedad": ansiedad,
            "depresion": depresion,
            "respuesta": respuesta_final,
            "conversacion_id": conv.id
        }

    def derivar_a_psicologo(self, conversacion_id, psicologo_id):
        deriv = Derivacion(
            conversacion_id=conversacion_id,
            psicologo_id=psicologo_id,
            fecha_derivacion=datetime.date.today(),
            estado="pendiente"
        )
        self.session.add(deriv)
        self.session.commit()
        return deriv

    def obtener_profesionales(self):
        return self.session.query(Psicologo).all()

    def obtener_conversacion(self, correo_estudiante):
        estudiante = self.session.query(Estudiante).filter_by(correo=correo_estudiante).first()
        if not estudiante:
            return []

        conversaciones = (
            self.session.query(Conversacion)
            .filter_by(estudiante_id=estudiante.id)
            .order_by(Conversacion.id.asc())
            .all()
        )

        mensajes = []
        for c in conversaciones:
            mensajes.append(("Tú", c.mensaje_usuario))
            mensajes.append(("Bot", c.respuesta_chatbot))
        return mensajes
