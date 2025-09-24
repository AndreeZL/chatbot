# utils/ver_db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd

DB_PATH = os.getenv("CHATBOT_DB", "sqlite:///chatbot.db")
engine = create_engine(DB_PATH, echo=False)
Session = sessionmaker(bind=engine)
session = Session()

# Opciones para que pandas no trunque
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", None)
pd.set_option("display.width", 2000)
pd.set_option("display.expand_frame_repr", False)

def mostrar_tabla(nombre_tabla):
    df = pd.read_sql_table(nombre_tabla, con=engine)
    print(f"\n🔹 Contenido de la tabla '{nombre_tabla}':")
    # Mostrar todo sin truncar
    print(df.to_string(index=False))

if __name__ == "__main__":
    # Lista de tablas que quieres ver (ajusta si tus tablas tienen otros nombres)
    tablas = ["estudiantes", "psicologos", "conversaciones", "derivaciones"]
    for t in tablas:
        try:
            mostrar_tabla(t)
        except Exception as e:
            print(f"(omitida {t}) -> {e}")
    session.close()
