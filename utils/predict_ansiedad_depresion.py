import joblib
import os

modelo_path = "modelo/modelo_ansiedad_depresion.pkl"
vectorizador_path = "modelo/vectorizer_ansiedad_depresion.pkl"

clf = joblib.load(modelo_path)
vectorizer = joblib.load(vectorizador_path)

def predecir_ansiedad_depresion(texto):
    X = vectorizer.transform([texto])
    pred = clf.predict(X)[0]  # Devuelve [ansiedad, depresion]
    return int(pred[0]), int(pred[1])
