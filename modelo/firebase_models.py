# modelo/firebase_models.py
import os
import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# ------------------------------
# 🔥 Inicialización de Firebase usando variable de entorno
# ------------------------------
# Se espera que la variable FIREBASE_CREDENTIALS contenga el JSON de credenciales
cred_json = os.environ.get("FIREBASE_CREDENTIALS")

if not firebase_admin._apps:
    if cred_json:
        cred = credentials.Certificate(eval(cred_json))  # Convertimos string a dict
        firebase_admin.initialize_app(cred)
    else:
        raise ValueError("No se encontró la variable de entorno FIREBASE_CREDENTIALS con las credenciales de Firebase.")

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

def obtener_estudiantes():
    return [doc.to_dict() | {"id": doc.id} for doc in db.collection("estudiantes").stream()]

# ------------------------------
# 👨‍⚕️ Psicólogo
# ------------------------------
def crear_psicologo(nombre, especialidad, correo):
    doc_ref = db.collection("psicologos").document()
    data = {
        "nombre": nombre,
        "especialidad": especialidad,
        "correo": correo
    }
    doc_ref.set(data)
    return doc_ref.id

def obtener_psicologos():
    return [doc.to_dict() | {"id": doc.id} for doc in db.collection("psicologos").stream()]

# ------------------------------
# 💬 Conversación
# ------------------------------
def guardar_conversacion(estudiante_id, mensaje_usuario, emocion_detectada,
                         nivel_estres, ansiedad, depresion, respuesta_chatbot, conv_id=None):
    doc_ref = db.collection("conversaciones").document(conv_id) if conv_id else db.collection("conversaciones").document()
    data = {
        "estudiante_id": estudiante_id,
        "fecha": datetime.date.today().isoformat(),
        "hora": datetime.datetime.now().strftime("%H:%M:%S"),
        "timestamp": datetime.datetime.now(),
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
def guardar_derivacion(conversacion_id, psicologo_id, estudiante_id=None, mensaje_estudiante=None, estado="pendiente"):
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
    return [doc.to_dict() | {"id": doc.id} for doc in db.collection("derivaciones").stream()]

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
