# utils/derivar_automatico.py
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
from modelo.models import Derivacion, Conversacion, Psicologo

engine = create_engine("sqlite:///chatbot.db")  # Ajusta según tu DB
Session = sessionmaker(bind=engine)
session = Session()

PALABRAS_RIESGO = ["lastimarme", "suicidio", "morir", "desaparecer", "no quiero vivir"]

def derivar_si_riesgo(conversacion, psicologo_id=1):
    mensaje = conversacion.mensaje_usuario.lower()
    if any(palabra in mensaje for palabra in PALABRAS_RIESGO):
        datos_anonimos = f"Mensaje de riesgo detectado: {mensaje[:100]}..."
        mensaje_estudiante = (
            "Hemos detectado un posible riesgo. "
            "Un especialista revisará tu caso y se contactará contigo si es necesario."
        )
        derivacion = Derivacion(
            conversacion_id=conversacion.id,
            estudiante_id=conversacion.estudiante_id,  # opcional para anonimato
            psicologo_id=psicologo_id,
            fecha_derivacion=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            estado='pendiente',
            datos_anonimos=datos_anonimos,
            mensaje_estudiante=mensaje_estudiante
        )
        session.add(derivacion)
        session.commit()
        return mensaje_estudiante
    return None
