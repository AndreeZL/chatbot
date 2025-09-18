import sys
import os

# Agregamos la raíz del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modelo.models import Base
from sqlalchemy import create_engine

def crear_db_sqlite(path='sqlite:///chatbot.db'):
    engine = create_engine(path, echo=False)
    Base.metadata.create_all(engine)
    print("Base de datos SQLite creada en 'chatbot.db'")

if __name__ == "__main__":
    crear_db_sqlite('sqlite:///chatbot.db')
