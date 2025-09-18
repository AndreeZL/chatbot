# utils/ver_db.py
import sqlite3
import pandas as pd

def mostrar_tablas(db_path="chatbot.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Mostrar todas las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = cursor.fetchall()
    print("📌 Tablas encontradas en la BD:\n", [t[0] for t in tablas], "\n")

    # Mostrar contenido de cada tabla
    for (tabla,) in tablas:
        print(f"🔹 Contenido de la tabla '{tabla}':")
        try:
            df = pd.read_sql_query(f"SELECT * FROM {tabla}", conn)
            if df.empty:
                print("(vacía)\n")
            else:
                print(df, "\n")
        except Exception as e:
            print(f"Error leyendo la tabla {tabla}: {e}\n")

    conn.close()

if __name__ == "__main__":
    mostrar_tablas("chatbot.db")
