# firebase_client.py
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# =============================
# 🔥 Inicializar Firebase SOLO UNA VEZ
# =============================
if not firebase_admin._apps:  # evita inicializar repetidamente en debug
    cred_env = os.environ.get("FIREBASE_CREDENTIALS")

    if cred_env:
        try:
            # Caso: FIREBASE_CREDENTIALS contiene JSON completo
            cred_dict = json.loads(cred_env)
            cred = credentials.Certificate(cred_dict)
        except json.JSONDecodeError:
            # Caso: FIREBASE_CREDENTIALS es una ruta
            cred = credentials.Certificate(cred_env)
    else:
        # Ruta absoluta basada en este archivo
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        cred_path = os.path.join(BASE_DIR, "chatbot-78eec-firebase-adminsdk-fbsvc-09d157af1f.json")
        
        if not os.path.exists(cred_path):
            raise FileNotFoundError(f"❌ Archivo de credenciales no encontrado: {cred_path}")

        cred = credentials.Certificate(cred_path)

    firebase_admin.initialize_app(cred)

# Cliente Firestore global (rápido, no se reinicia)
db = firestore.client()
