# utils/derivar_automatico.py
from datetime import datetime
from modelo.models import Derivacion

PALABRAS_RIESGO = ["lastimarme", "suicidio", "morir", "desaparecer", "no quiero vivir"]

def derivar_si_riesgo(conversacion, session, psicologo_id=1):
    """
    Revisa el mensaje de la conversación y deriva a psicólogo si detecta palabras de riesgo.

    :param conversacion: objeto Conversacion
    :param session: sesión SQLAlchemy (ya creada en el controller)
    :param psicologo_id: ID del psicólogo al que derivar
    :return: mensaje para el estudiante si es de riesgo, o None
    """
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
            fecha_derivacion=datetime.now(),
            estado='pendiente',
            datos_anonimos=datos_anonimos,
            mensaje_estudiante=mensaje_estudiante
        )
        session.add(derivacion)
        session.commit()
        return mensaje_estudiante
    return None
