# control/chatbot_controller.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modelo.models import Estudiante, Conversacion, Derivacion, Psicologo, Base
from chatbot_repo.chatbot import responder_texto
from utils.predict_stress import predecir_estres
from utils.predict_ansiedad_depresion import predecir_ansiedad_depresion
import datetime
import os

# Importar función de derivación automática
from utils.derivar_automatico import derivar_si_riesgo

# ----------------------------
# Configuración de la base de datos MySQL
# ----------------------------
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "andreezl13")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "chatbot_db")

# Engine MySQL + SQLAlchemy
engine = create_engine(
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}",
    echo=False
)
Session = sessionmaker(bind=engine)

# Crear las tablas si no existen
Base.metadata.create_all(engine)


class ChatbotController:
    def __init__(self):
        self.session = Session()

    def registrar_estudiante(self, nombre, correo, carrera):
        """Crea o devuelve un estudiante según correo"""
        estudiante = self.session.query(Estudiante).filter_by(correo=correo).first()
        if not estudiante:
            estudiante = Estudiante(nombre=nombre, correo=correo, carrera=carrera)
            self.session.add(estudiante)
            self.session.commit()
            print(f"✅ Estudiante registrado: {nombre} ({correo}) {carrera}")
        return estudiante

    def procesar_mensaje(self, correo_estudiante, mensaje):
        """Procesa un mensaje del estudiante, detecta emoción, predice estrés y ansiedad/depresión,
        guarda en BD, deriva si es de riesgo y devuelve respuesta"""

        despedidas = ["chao", "adios", "adiós", "salir", "eso es todo"]

        if mensaje.lower().strip() in despedidas:
            emocion = "despedida"
            respuesta = "👋 Nos vemos, recuerda que siempre estaré aquí para ti."
        else:
            # Detectar emoción con el chatbot
            emocion, respuesta = responder_texto(mensaje)

        estudiante = self.session.query(Estudiante).filter_by(correo=correo_estudiante).first()
        if not estudiante:
            raise ValueError("El estudiante no está registrado.")

        # 🔹 Predicciones automáticas
        nivel_estres = predecir_estres(mensaje)
        ansiedad, depresion = predecir_ansiedad_depresion(mensaje)  # ansiedad y depresión separados

        # Guardar la conversación con tipos compatibles para MySQL
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

        # Derivación automática si el mensaje es de riesgo
        respuesta_derivacion = derivar_si_riesgo(conv, self.session)
        if respuesta_derivacion:
            conv.respuesta_chatbot = respuesta_derivacion
            self.session.commit()
            respuesta = respuesta_derivacion

        return {
            "emocion": emocion,
            "nivel_estres": nivel_estres,
            "respuesta": respuesta,
            "conversacion_id": conv.id
        }

    def derivar_a_psicologo(self, conversacion_id, psicologo_id):
        """Registra manualmente una derivación de conversación a un psicólogo"""
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
        """Devuelve la lista completa de psicólogos registrados"""
        return self.session.query(Psicologo).all()

    def obtener_conversacion(self, correo_estudiante):
        """Devuelve la lista de mensajes (usuario y bot) de un estudiante"""
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
