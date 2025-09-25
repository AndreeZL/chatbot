# utils/ver_db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd

# ----------------------------
# Configuración MySQL
# ----------------------------
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "andreezl13")  # cambia tu_pass por tu contraseña
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "chatbot_db")

# Engine MySQL + SQLAlchemy
engine = create_engine(
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4",
    echo=False
)
Session = sessionmaker(bind=engine)
session = Session()

# Opciones para que pandas no trunque
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", None)
pd.set_option("display.width", 2000)
pd.set_option("display.expand_frame_repr", False)

def mostrar_tabla(nombre_tabla):
    """
    Muestra el contenido completo de una tabla en MySQL usando pandas.
    """
    try:
        df = pd.read_sql_table(nombre_tabla, con=engine)
        print(f"\n🔹 Contenido de la tabla '{nombre_tabla}':")
        print(df.to_string(index=False))
    except Exception as e:
        print(f"(omitida {nombre_tabla}) -> {e}")

if __name__ == "__main__":
    # Lista de tablas que quieres ver (ajusta según tus nombres reales)
    tablas = ["estudiantes", "psicologos", "conversaciones", "derivaciones"]
    for t in tablas:
        mostrar_tabla(t)

    session.close()
