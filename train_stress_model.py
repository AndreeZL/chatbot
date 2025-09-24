import pandas as pd
import pickle
import os
import re
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score

# Rutas
DATA_PATH = os.path.join("data", "stress_dataset.csv")
MODEL_PATH = os.path.join("utils", "modelo_estres.pkl")

def limpiar_texto(texto):
    texto = texto.lower()
    texto = re.sub(r"[^a-záéíóúñü\s]", "", texto)
    return texto

def entrenar_modelo():
    # Leer dataset
    df = pd.read_csv(DATA_PATH)
    df["mensaje"] = df["mensaje"].apply(limpiar_texto)

    # Vectorización
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(df["mensaje"])
    y = df["nivel_estres"]

    # División en train y test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Entrenamiento
    modelo = MultinomialNB()
    modelo.fit(X_train, y_train)

    # Evaluación
    y_pred = modelo.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"🎯 Precisión del modelo: {acc * 100:.2f}%")

    # Guardar modelo + vectorizer
    with open(MODEL_PATH, "wb") as f:
        pickle.dump({"modelo": modelo, "vectorizer": vectorizer}, f)

    print(f"✅ Modelo guardado en {MODEL_PATH}")

if __name__ == "__main__":
    entrenar_modelo()
