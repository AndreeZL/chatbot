# utils/recomendador.py
def generar_recomendaciones(nivel_estres: str, ansiedad: int, depresion: int, historial=None):
    """
    Devuelve una lista de recomendaciones (strings) ordenadas por prioridad.
    nivel_estres: "bajo", "medio", "alto"
    ansiedad, depresion: 0 o 1
    historial: opcional (puedes pasar historial de accesos para personalizar)
    """
    recomendaciones = []

    # Reglas para estrés alto
    if nivel_estres == "alto":
        if ansiedad and depresion:
            recomendaciones.append("Haz una pausa ahora: 5 minutos de respiración guiada (4-4-4). Si persiste, contacta con un profesional del directorio.")
            recomendaciones.append("Realiza una actividad breve (5–10 min) que te guste. Si tienes pensamientos de autolesión, busca ayuda inmediatamente.")
        elif ansiedad:
            recomendaciones.append("Prueba la técnica 4-7-8 de respiración y grounding. Escucha un audio corto de respiración.")
            recomendaciones.append("Si la ansiedad es recurrente, considera agendar una sesión con un especialista.")
        elif depresion:
            recomendaciones.append("Intenta una tarea pequeña y concreta (5-10 min). Si la apatía persiste, busca apoyo profesional.")
            recomendaciones.append("Actividades programadas (salir a caminar 10 min) pueden ayudar a romper el ciclo.")
        else:
            recomendaciones.append("Haz una pausa y realiza respiraciones profundas durante 5 minutos. Si no mejora, busca apoyo.")

    # Reglas para estrés medio
    elif nivel_estres == "medio":
        if ansiedad:
            recomendaciones.append("Pausa breve + técnica de respiración. Prueba un ejercicio de mindfulness de 5 minutos.")
        elif depresion:
            recomendaciones.append("Organiza una micro-tarea que te guste; rompe actividades grandes en pasos pequeños.")
        else:
            recomendaciones.append("Tómate una pausa activa y escucha música relajante durante 10 minutos.")

    # Reglas para estrés bajo
    else:  # 'bajo'
        if ansiedad or depresion:
            recomendaciones.append("Mantén rutinas saludables: sueño, ejercicio ligero y contacto social. Haz ejercicios de autocuidado.")
        else:
            recomendaciones.append("¡Vas bien! Mantén tus hábitos saludables. Aquí tienes recursos para continuar.")

    # Añadir sugerencias complementarias generales
    recomendaciones.append("Revisa el directorio de profesionales si quieres hablar con alguien. (Directorio → Recursos)")

    # Si tienes historial, podrías filtrar recomendaciones ya ofrecidas; por ahora devolvemos todas
    # elimina duplicados manteniendo orden
    seen = set()
    dedup = []
    for r in recomendaciones:
        if r not in seen:
            dedup.append(r)
            seen.add(r)
    return dedup
