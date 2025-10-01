# utils/derivar_automatico.py
from datetime import datetime
from modelo.firebase_models import guardar_derivacion

# Palabras clave que indican riesgo
PALABRAS_RIESGO = ["lastimarme", "suicidio", "morir", "desaparecer", "no quiero vivir"]

def derivar_si_riesgo(conversacion, session=None, psicologo_id="default_psicologo"):
    """
    Revisa el mensaje de la conversación y deriva a psicólogo si detecta palabras de riesgo.

    :param conversacion: diccionario con los datos de la conversación (Firestore)
    :param session: parámetro no usado (solo para compatibilidad con versiones anteriores)
    :param psicologo_id: ID del psicólogo al que derivar (string o int)
    :return: mensaje para el estudiante si es de riesgo, o None
    """
    mensaje = conversacion.get("mensaje_usuario", "").lower()

    if any(palabra in mensaje for palabra in PALABRAS_RIESGO):
        datos_anonimos = f"Mensaje de riesgo detectado: {mensaje[:100]}..."
        mensaje_estudiante = (
            "⚠️ Hemos detectado un posible riesgo. "
            "Un especialista revisará tu caso y se contactará contigo si es necesario."
        )

        # Guardar la derivación en Firestore
        guardar_derivacion(
            conversacion_id=conversacion["id"],
            psicologo_id=psicologo_id,
            estudiante_id=conversacion.get("estudiante_id"),
            mensaje_estudiante=mensaje_estudiante,
            estado="pendiente"
        )

        return mensaje_estudiante

    return None
