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
psicologos = [
    {
        "nombre": "Lucía Mendoza",
        "especialidad": "Psicología Educativa",
        "correo": "lucia.mendoza23@gmail.com",
    },
    {
        "nombre": "Carlos Rojas",
        "especialidad": "Psicología Clínica",
        "correo": "c.rojas88@gmail.com",
    },
    {
        "nombre": "Diana Huamán",
        "especialidad": "Psicología Organizacional",
        "correo": "diana_huaman97@gmail.com",
    },
    {
        "nombre": "Jorge Quispe",
        "especialidad": "Psicología Clínica",
        "correo": "jorgeq_15@gmail.com",
    },
    {
        "nombre": "Melissa Ramos",
        "especialidad": "Psicología Educativa",
        "correo": "melissa.ramos04@gmail.com",
    },
    {
        "nombre": "Andrés Torres",
        "especialidad": "Psicología Social",
        "correo": "atorres.psico@gmail.com",
    },
    {
        "nombre": "Valeria Paredes",
        "especialidad": "Psicología Clínica",
        "correo": "valeria_paredes19@gmail.com",
    }
]

# ----------------------------
# Insertar todos en Firebase
# ----------------------------
for p in psicologos:
    data = {
        "nombre": p["nombre"],
        "especialidad": p["especialidad"],
        "correo": p["correo"],
        "password": generate_password_hash("123456")  # 🔐 puedes cambiar la contraseña si deseas
    }
    db.collection("psicologos").add(data)
    print(f"✅ Psicólogo agregado: {p['nombre']} ({p['correo']})")

print("\n🎉 Todos los psicólogos fueron agregados exitosamente a Firestore.")
