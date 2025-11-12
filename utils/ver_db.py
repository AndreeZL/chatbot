# utils/ver_db.py

from firebase_client import db
from datetime import datetime
import pandas as pd

# ----------------------------
# Opciones de pandas
# ----------------------------
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", None)
pd.set_option("display.width", 2000)
pd.set_option("display.expand_frame_repr", False)

# ----------------------------
# Guardar conversación en Firestore
# ----------------------------
def guardar_conversacion_firestore(usuario_msg, bot_msg, emociones=None, estres='bajo', ansiedad=0, depresion=0):
    """
    Guarda la conversación en Firestore.
    """
    coleccion = db.collection('conversaciones')
    doc_data = {
        "usuario_msg": usuario_msg,
        "bot_msg": bot_msg,
        "emociones": emociones,
        "estres": estres,
        "ansiedad": ansiedad,
        "depresion": depresion,
        "fecha": datetime.utcnow()
    }
    doc_ref = coleccion.add(doc_data)
    print(f"Conversación guardada en Firestore con ID: {doc_ref[1].id}")
    return doc_ref[1].id  # Retorna ID del documento

# ----------------------------
# Mostrar tabla/conversaciones
# ----------------------------
def mostrar_tabla_firestore():
    """
    Muestra todas las conversaciones de Firestore como DataFrame.
    """
    coleccion = db.collection('conversaciones')
    docs = coleccion.stream()

    lista = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        lista.append(data)

    if lista:
        df = pd.DataFrame(lista)
        print("\n🔹 Contenido de Firestore 'conversaciones':")
        print(df.to_string(index=False))
    else:
        print("\n🔹 No hay conversaciones guardadas.")

# ----------------------------
# Ejemplo de uso
# ----------------------------
if __name__ == "__main__":
    # Guardar ejemplo
    guardar_conversacion_firestore("Hola", "¡Hola! ¿Cómo estás?", emociones="feliz", estres="bajo")
    
    # Mostrar todas
    mostrar_tabla_firestore()
