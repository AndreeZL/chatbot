import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modelo.models import Psicologo, Base

# Agregar ruta del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ----------------------------
# Configuración MySQL
# ----------------------------
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "andreezl13")  # cambia por tu contraseña
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "chatbot_db")

# Crear engine MySQL
engine = create_engine(
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}",
    echo=False
)

# Crear sesión
Session = sessionmaker(bind=engine)
session = Session()

# Crear las tablas si no existen
Base.metadata.create_all(engine)

# Crear registro de psicólogo
psicologa = Psicologo(
    nombre="Karolai Alania",
    especialidad="Psicología Clínica",
    correo="karolai.alania@continental.edu.pe"
)

session.add(psicologa)
session.commit()

print("✅ Psicóloga Karolai Alania agregada al directorio")
