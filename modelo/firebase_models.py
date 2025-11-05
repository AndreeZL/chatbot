# modelo/firebase_models.py
import os
import datetime
from flask import json
import pytz
import firebase_admin
import json
from firebase_admin import credentials, firestore
from werkzeug.security import generate_password_hash
# ------------------------------
# 🔥 Inicialización de Firebase usando variable de entorno
# ------------------------------
cred_env = os.environ.get("FIREBASE_CREDENTIALS")

if not firebase_admin._apps:
    if cred_env:
        try:
            # Si es un JSON (Render u otro servicio en la nube)
            cred_dict = json.loads(cred_env)
            cred = credentials.Certificate(cred_dict)
        except json.JSONDecodeError as e:
            # Si no es JSON, asumimos que es la ruta al archivo local
            print("⚠️ Error cargando credenciales desde variable de entorno:", e)
            print("🔍 Intentando usar archivo local...")
            cred_path = "database/chatbot-78eec-firebase-adminsdk-fbsvc-b0eea0da20.json"
            cred = credentials.Certificate(cred_path)
        except Exception as e:
            print("❌ Error general al cargar credenciales Firebase:", e)
            raise
    else:
        print("⚠️ No se encontró FIREBASE_CREDENTIALS, usando archivo local...")
        cred_path = "database/chatbot-78eec-firebase-adminsdk-fbsvc-b0eea0da20.json"
        cred = credentials.Certificate(cred_path)

    firebase_admin.initialize_app(cred)

db = firestore.client()

# ------------------------------
# 👤 Estudiante
# ------------------------------
def crear_estudiante(nombre, correo, carrera):
    doc_ref = db.collection("estudiantes").document()
    data = {
        "nombre": nombre,
        "correo": correo,
        "carrera": carrera,
        "fecha_registro": datetime.datetime.now()
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

# ------------------------------
# 👨‍⚕️ Psicólogo
# ------------------------------
def crear_psicologo(nombre, especialidad, correo, password):
    doc_ref = db.collection("psicologos").document()
    data = {
        "nombre": nombre,
        "especialidad": especialidad,
        "correo": correo,
        "password": generate_password_hash(password)
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
# ------------------------------
# 💬 Conversación
# ------------------------------
def guardar_conversacion(estudiante_id, mensaje_usuario, emocion_detectada,
                         nivel_estres, ansiedad, depresion, respuesta_chatbot, conv_id=None):
    tz = pytz.timezone("America/Lima")
    ahora = datetime.datetime.now(tz)

    doc_ref = db.collection("conversaciones").document(conv_id) if conv_id else db.collection("conversaciones").document()
    data = {
        "estudiante_id": estudiante_id,
        "fecha": ahora.date().isoformat(),
        "hora": ahora.strftime("%H:%M:%S"),
        "timestamp": ahora,
        "mensaje_usuario": mensaje_usuario,
        "emocion_detectada": emocion_detectada,
        "nivel_estres": nivel_estres,
        "ansiedad": ansiedad,
        "depresion": depresion,
        "respuesta_chatbot": respuesta_chatbot
    }
    doc_ref.set(data)
    return doc_ref.id

def obtener_conversaciones(estudiante_id=None):
    ref = db.collection("conversaciones")
    if estudiante_id:
        ref = ref.where("estudiante_id", "==", estudiante_id)
    return [doc.to_dict() | {"id": doc.id} for doc in ref.stream()]

# ------------------------------
# 📌 Derivación
# ------------------------------
# Estados válidos de derivación
ESTADOS_DERIVACION = ("pendiente", "completada")

# Etiquetas amigables para mostrar en la UI
ESTADO_LABELS = {
    "pendiente": "Pendiente ⏳",
    "completada": "Completada ✅",
}
def guardar_derivacion(conversacion_id, psicologo_id, estudiante_id=None, mensaje_estudiante=None, estado="pendiente"):
    # Validar que el estado sea válido
    if estado not in ESTADOS_DERIVACION:
        raise ValueError(f"Estado inválido: {estado}")
    
    doc_ref = db.collection("derivaciones").document()
    data = {
        "conversacion_id": conversacion_id,
        "psicologo_id": psicologo_id,
        "estudiante_id": estudiante_id,
        "mensaje_estudiante": mensaje_estudiante,
        "fecha_derivacion": datetime.datetime.now(),
        "estado": estado
    }
    doc_ref.set(data)
    return doc_ref.id

def obtener_derivaciones():
    docs = db.collection("derivaciones").stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

# ------------------------------
# 🎯 Recomendación
# ------------------------------
def guardar_recomendacion(estudiante_id, texto, tipo=None, util=None):
    doc_ref = db.collection("recomendaciones").document()
    data = {
        "estudiante_id": estudiante_id,
        "fecha": datetime.date.today().isoformat(),
        "hora": datetime.datetime.now().strftime("%H:%M:%S"),
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
