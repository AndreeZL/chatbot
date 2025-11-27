import pickle
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer

# Ruta del modelo entrenado
MODEL_PATH = os.path.join(os.path.dirname(__file__), "modelo_estres.pkl")

# Cargar el modelo y el vectorizador
with open(MODEL_PATH, "rb") as f:
    modelo_data = pickle.load(f)
    modelo = modelo_data["modelo"]
    vectorizer = modelo_data["vectorizer"]

def limpiar_texto(texto):
    """Preprocesa el texto eliminando símbolos y pasándolo a minúsculas"""
    texto = texto.lower()
    texto = re.sub(r"[^a-záéíóúñü\s]", "", texto)
    return texto

def predecir_estres(texto):
    """Predice el nivel de estrés a partir de un mensaje"""
    texto = limpiar_texto(texto)
    vector = vectorizer.transform([texto])
    pred = modelo.predict(vector)[0]
    return pred
