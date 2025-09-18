# control/chatbot_controller.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modelo.models import Estudiante, Conversacion, Derivacion, Psicologo, Base
from chatbot_repo.chatbot import responder_texto
import datetime
import os

DB_PATH = os.getenv("CHATBOT_DB", "sqlite:///chatbot.db")
engine = create_engine(DB_PATH, echo=False)
Session = sessionmaker(bind=engine)

class ChatbotController:
    def __init__(self):
        self.session = Session()

    def registrar_estudiante(self, nombre, correo, carrera=""):
        """Crea o devuelve un estudiante según correo"""
        estudiante = self.session.query(Estudiante).filter_by(correo=correo).first()
        if not estudiante:
            estudiante = Estudiante(nombre=nombre, correo=correo, carrera=carrera)
            self.session.add(estudiante)
            self.session.commit()
            print(f"✅ Estudiante registrado: {nombre} ({correo})")
        return estudiante

    def procesar_mensaje(self, correo_estudiante, mensaje):
        emocion, respuesta = responder_texto(mensaje)

        estudiante = self.session.query(Estudiante).filter_by(correo=correo_estudiante).first()
        if not estudiante:
            raise ValueError("El estudiante no está registrado.")

        conv = Conversacion(
            estudiante_id=estudiante.id,
            fecha=str(datetime.date.today()),
            hora=str(datetime.datetime.now().time()),
            mensaje_usuario=mensaje,
            emocion_detectada=emocion,
            respuesta_chatbot=respuesta
        )
        self.session.add(conv)
        self.session.commit()

        return {"emocion": emocion, "respuesta": respuesta, "conversacion_id": conv.id}

    def derivar_a_psicologo(self, conversacion_id, psicologo_id):
        deriv = Derivacion(
            conversacion_id=conversacion_id,
            psicologo_id=psicologo_id,
            fecha_derivacion=str(datetime.date.today()),
            estado="derivado"
        )
        self.session.add(deriv)
        self.session.commit()
        return deriv
