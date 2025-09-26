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
def predecir_ansiedad(texto):
    return predecir_ansiedad_depresion(texto)[0]

def predecir_depresion(texto):
    return predecir_ansiedad_depresion(texto)[1]
