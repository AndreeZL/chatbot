<<<<<<< HEAD
import joblib
import os

# Rutas a tus archivos de modelo y vectorizador
modelo_path = "modelo/modelo_ansiedad_depresion.pkl"
vectorizador_path = "modelo/vectorizer_ansiedad_depresion.pkl"

# Cargar modelo y vectorizador
clf = joblib.load(modelo_path)
vectorizer = joblib.load(vectorizador_path)

# Función principal que devuelve ambos valores
def predecir_ansiedad_depresion(texto):
    X = vectorizer.transform([texto])
    pred = clf.predict(X)[0]  # Devuelve [ansiedad, depresion]
    return int(pred[0]), int(pred[1])

# Funciones individuales para importación separada
=======
# utils/predict_ansiedad_depresion.py

import joblib
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
modelo_path = os.path.join(BASE_DIR, "modelo", "modelo_ansiedad_depresion.pkl")
vectorizador_path = os.path.join(BASE_DIR, "modelo", "vectorizer_ansiedad_depresion.pkl")

clf = joblib.load(modelo_path)
vectorizer = joblib.load(vectorizador_path)

def predecir_ansiedad_depresion(texto):
    """
    Devuelve dos valores: ansiedad (0 o 1) y depresión (0 o 1)
    """
    X = vectorizer.transform([texto])
    pred = clf.predict(X)[0]
    return int(pred[0]), int(pred[1])

>>>>>>> 2dde462 (UML AGREGADO)
def predecir_ansiedad(texto):
    return predecir_ansiedad_depresion(texto)[0]

def predecir_depresion(texto):
    return predecir_ansiedad_depresion(texto)[1]
