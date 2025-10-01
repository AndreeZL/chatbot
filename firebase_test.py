import firebase_admin
from firebase_admin import credentials, firestore

# Cargar credenciales
cred = credentials.Certificate("database/chatbot-78eec-firebase-adminsdk-fbsvc-b0eea0da20.json")
firebase_admin.initialize_app(cred)

# Cliente Firestore
db = firestore.client()

# Insertar un estudiante
db.collection("estudiantes").add({
    "nombre": "Juan Pérez",
    "correo": "juan@example.com",
    "carrera": "Ingeniería de Sistemas"
})

print("✅ Estudiante agregado")

# Leer estudiantes
print("📌 Estudiantes en la BD:")
docs = db.collection("estudiantes").stream()
for doc in docs:
    print(f"{doc.id} => {doc.to_dict()}")
