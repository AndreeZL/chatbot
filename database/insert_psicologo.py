import os
import sys
import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.security import generate_password_hash
# Agregar ruta del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ----------------------------
# Inicializar Firebase
# ----------------------------
if not firebase_admin._apps:  # evitar inicializar más de una vez
    cred = credentials.Certificate("database/chatbot-78eec-firebase-adminsdk-fbsvc-b0eea0da20.json")  
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ----------------------------
# Insertar Psicólogo
# ----------------------------
psicologa = {
    "nombre": "Karolai Alania",
    "especialidad": "Psicología Clínica",
    "correo": "71696163@continental.edu.pe",
    "password": generate_password_hash("71696163")

}

db.collection("psicologos").add(psicologa)

print("✅ Psicóloga Karolai Alania agregada al directorio en Firebase")
