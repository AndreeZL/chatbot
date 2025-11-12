# modelo/firebase_models.py

import os
import datetime
import pytz
import json
import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.security import generate_password_hash

# ============================================================
# 🔥 Inicialización de Firebase
# ============================================================
cred_env = os.environ.get("FIREBASE_CREDENTIALS")

if not firebase_admin._apps:
    if cred_env:
        try:
            cred_dict = json.loads(cred_env)
            cred = credentials.Certificate(cred_dict)
        except json.JSONDecodeError:
            print("⚠️ FIREBASE_CREDENTIALS no es JSON, usando archivo local...")
            cred = credentials.Certificate("database/chatbot-78eec-firebase-adminsdk-fbsvc-b0eea0da20.json")
    else:
        print("⚠️ No se encontró FIREBASE_CREDENTIALS, usando archivo local...")
        cred = credentials.Certificate("database/chatbot-78eec-firebase-adminsdk-fbsvc-b0eea0da20.json")

    firebase_admin.initialize_app(cred)

db = firestore.client()
tz = pytz.timezone("America/Lima")

# ============================================================
# 👤 ESTUDIANTES
# ============================================================
def crear_estudiante(nombre, correo, carrera):
    doc_ref = db.collection("estudiantes").document()
    data = {
        "nombre": nombre,
        "correo": correo,
        "carrera": carrera,
        "fecha_registro": datetime.datetime.now(tz)
    }
    doc_ref.set(data)
    return doc_ref.id

def obtener_estudiante_por_correo(correo):
    query = db.collection("estudiantes").where("correo", "==", correo).limit(1).stream()
    for doc in query:
        return doc.to_dict() | {"id": doc.id}
    return None

def obtener_estudiante_por_id(estudiante_id):
    doc = db.collection("estudiantes").document(estudiante_id).get()
    if doc.exists:
        return doc.to_dict() | {"id": doc.id}
    return None

def obtener_estudiantes():
    return [doc.to_dict() | {"id": doc.id} for doc in db.collection("estudiantes").stream()]

# ============================================================
# 👨‍⚕️ PSICÓLOGOS
# ============================================================
def crear_psicologo(nombre, especialidad, correo, password):
    doc_ref = db.collection("psicologos").document()
    data = {
        "nombre": nombre,
        "especialidad": especialidad,
        "correo": correo,
        "password": generate_password_hash(password),
        "fecha_registro": datetime.datetime.now(tz)
    }
    doc_ref.set(data)
    return doc_ref.id

def obtener_psicologo_por_correo(correo):
    query = db.collection("psicologos").where("correo", "==", correo).limit(1).stream()
    for doc in query:
        return doc.to_dict() | {"id": doc.id}
    return None

def obtener_psicologos():
    return [doc.to_dict() | {"id": doc.id} for doc in db.collection("psicologos").stream()]

# ============================================================
# 💬 CONVERSACIONES (Chatbot ↔ Usuario)
# ============================================================
def guardar_conversacion(estudiante_id, mensaje_usuario, emocion_detectada,
                         nivel_estres, ansiedad, depresion, respuesta_chatbot,
                         conv_id=None, emocion_cod=None):
    """
    Guarda una conversación en Firestore. Si se pasa conv_id, actualiza ese documento.
    """
    ahora = datetime.datetime.now(tz)

    doc_ref = (
        db.collection("conversaciones").document(conv_id)
        if conv_id else db.collection("conversaciones").document()
    )

    data = {
        "estudiante_id": estudiante_id,
        "mensaje_usuario": mensaje_usuario,
        "respuesta_chatbot": respuesta_chatbot,
        "emocion_detectada": emocion_detectada,
        "nivel_estres": nivel_estres,
        "ansiedad": ansiedad,
        "depresion": depresion,
        "fecha": ahora.date().isoformat(),
        "hora": ahora.strftime("%H:%M:%S"),
        "timestamp": ahora,
    }

    if emocion_cod is not None:
        data["emocion_cod"] = emocion_cod

    doc_ref.set(data)
    return doc_ref.id

def obtener_conversaciones(estudiante_id=None):
    ref = db.collection("conversaciones")
    if estudiante_id:
        ref = ref.where("estudiante_id", "==", estudiante_id)
    return [doc.to_dict() | {"id": doc.id} for doc in ref.stream()]

# ============================================================
# 📌 DERIVACIONES (cuando hay riesgo emocional)
# ============================================================
ESTADOS_DERIVACION = ("pendiente", "completada")
ESTADO_LABELS = {
    "pendiente": "Pendiente ⏳",
    "completada": "Completada ✅",
}

def guardar_derivacion(conversacion_id, psicologo_id, estudiante_id=None,
                       mensaje_estudiante=None, estado="pendiente"):
    if estado not in ESTADOS_DERIVACION:
        raise ValueError(f"Estado inválido: {estado}")

    doc_ref = db.collection("derivaciones").document()
    data = {
        "conversacion_id": conversacion_id,
        "psicologo_id": psicologo_id,
        "estudiante_id": estudiante_id,
        "mensaje_estudiante": mensaje_estudiante,
        "fecha_derivacion": datetime.datetime.now(tz),
        "estado": estado,
    }
    doc_ref.set(data)
    return doc_ref.id

def obtener_derivaciones():
    docs = db.collection("derivaciones").stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

# ============================================================
# 🎯 RECOMENDACIONES
# ============================================================
def guardar_recomendacion(estudiante_id, texto, tipo=None, util=None):
    ahora = datetime.datetime.now(tz)
    doc_ref = db.collection("recomendaciones").document()
    data = {
        "estudiante_id": estudiante_id,
        "fecha": ahora.date().isoformat(),
        "hora": ahora.strftime("%H:%M:%S"),
        "timestamp": ahora,
        "texto": texto,
        "tipo": tipo,
        "util": util
    }
    doc_ref.set(data)
    return doc_ref.id

def obtener_recomendaciones(estudiante_id=None):
    ref = db.collection("recomendaciones")
    if estudiante_id:
        ref = ref.where("estudiante_id", "==", estudiante_id)
    return [doc.to_dict() | {"id": doc.id} for doc in ref.stream()]
