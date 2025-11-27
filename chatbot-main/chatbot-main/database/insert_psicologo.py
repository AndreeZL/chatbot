import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.security import generate_password_hash
import datetime
import pytz

# Agregar ruta del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Usar la misma ruta de credenciales que el módulo modelo
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRED_PATH = os.path.join(BASE_DIR, "modelo", "chatbot-78eec-firebase-adminsdk-fbsvc-b0eea0da20.json")

# ----------------------------
# Inicializar Firebase
# ----------------------------
if not firebase_admin._apps:
    if os.path.isfile(CRED_PATH):
        cred = credentials.Certificate(CRED_PATH)
    else:
        # fallback a la ruta relativa antigua
        cred = credentials.Certificate(os.path.join(BASE_DIR, "chatbot-78eec-firebase-adminsdk-fbsvc-b0eea0da20.json"))
    firebase_admin.initialize_app(cred)

db = firestore.client()

tz = pytz.timezone("America/Lima")

# ----------------------------
# Lista de Psicólogos a insertar
# ----------------------------
psicologos = [
    {"nombre": "Lucía Mendoza", "especialidad": "Psicología Educativa", "correo": "lucia.mendoza23@gmail.com"},
    {"nombre": "Carlos Rojas", "especialidad": "Psicología Clínica", "correo": "c.rojas88@gmail.com"},
    {"nombre": "Diana Huamán", "especialidad": "Psicología Organizacional", "correo": "diana_huaman97@gmail.com"},
    {"nombre": "Jorge Quispe", "especialidad": "Psicología Clínica", "correo": "jorgeq_15@gmail.com"},
    {"nombre": "Melissa Ramos", "especialidad": "Psicología Educativa", "correo": "melissa.ramos04@gmail.com"},
    {"nombre": "Andrés Torres", "especialidad": "Psicología Social", "correo": "atorres.psico@gmail.com"},
    {"nombre": "Valeria Paredes", "especialidad": "Psicología Clínica", "correo": "valeria_paredes19@gmail.com"}
]

# ----------------------------
# Insertar todos en Firebase (idempotente)
# ----------------------------
for p in psicologos:
    # evitar duplicados por correo
    exists = list(db.collection("psicologos").where("correo", "==", p["correo"]).limit(1).stream())
    if exists:
        print(f"⚠️ Psicólogo ya existe, omitiendo: {p['nombre']} ({p['correo']})")
        continue

    data = {
        "nombre": p["nombre"],
        "especialidad": p["especialidad"],
        "correo": p["correo"],
        "password": generate_password_hash("123456"),  # Contraseña inicial
        "fecha_registro": datetime.datetime.now(tz)
    }
    db.collection("psicologos").add(data)
    print(f"✅ Psicólogo agregado: {p['nombre']} ({p['correo']})")

print("\n🎉 Script terminado. Revisa el panel/directorio en la app.")
