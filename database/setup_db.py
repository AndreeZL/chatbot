import os
from modelo.models import Base
from sqlalchemy import create_engine

# Configuración MySQL
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "andreezl13")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "chatbot_db")

# Conexión a MySQL
engine = create_engine(
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}",
    echo=True
)

# Crear todas las tablas
Base.metadata.create_all(engine)
print("✅ Tablas creadas correctamente en MySQL")
