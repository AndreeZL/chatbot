import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.multioutput import MultiOutputClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

# Cargar dataset
df = pd.read_csv("data/dataset_ansiedad_depresion.csv")

X = df["texto"]
y = df[["ansiedad", "depresion"]]  # Multi-label

# Vectorizador
vectorizer = TfidfVectorizer()
X_vect = vectorizer.fit_transform(X)

# Modelo multi-etiqueta
clf = MultiOutputClassifier(LogisticRegression(max_iter=1000))
clf.fit(X_vect, y)

# Evaluación
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
y_pred = clf.predict(vectorizer.transform(X_test))
print(classification_report(y_test, y_pred, target_names=["ansiedad","depresion"]))

# Guardar modelos
os.makedirs("modelo", exist_ok=True)
joblib.dump(clf, "modelo/modelo_ansiedad_depresion.pkl")
joblib.dump(vectorizer, "modelo/vectorizer_ansiedad_depresion.pkl")

print("✅ Modelo multi-etiqueta entrenado y guardado.")
