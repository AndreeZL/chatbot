import os
import sys
import json
import datetime
import pytz
import firebase_admin
from firebase_admin import credentials, firestore

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRED_PATH = os.path.join(BASE_DIR, "modelo", "chatbot-78eec-firebase-adminsdk-fbsvc-b0eea0da20.json")

if not firebase_admin._apps:
    if os.path.isfile(CRED_PATH):
        cred = credentials.Certificate(CRED_PATH)
    else:
        cred = credentials.Certificate(os.path.join(BASE_DIR, "chatbot-78eec-firebase-adminsdk-fbsvc-b0eea0da20.json"))
    firebase_admin.initialize_app(cred)

db = firestore.client()

def print_collection_sample(coll_name, limit=20):
    docs = list(db.collection(coll_name).limit(limit).stream())
    print(f"==> {coll_name} count sample: {len(docs)}")
    for i, d in enumerate(docs, 1):
        data = d.to_dict()
        # stringify datetime-like values
        for k, v in data.items():
            if isinstance(v, datetime.datetime):
                data[k] = v.isoformat()
            try:
                # Firestore Timestamp
                if hasattr(v, 'ToDatetime'):
                    data[k] = v.ToDatetime().isoformat()
            except Exception:
                pass
        print(f"  {i}) id={d.id} -> {json.dumps(data, ensure_ascii=False)}")

if __name__ == '__main__':
    print_collection_sample('psicologos', limit=50)
    print_collection_sample('estudiantes', limit=50)
    print_collection_sample('conversaciones', limit=10)
    print('\nSi los psicólogos aparecen aquí pero no en /directorio, pega la salida y los logs de la app (líneas [DEBUG DIRECTORIO]).')
