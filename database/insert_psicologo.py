import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modelo.models import Psicologo, Base

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Conexión a la base de datos (ajústala si usas MySQL en lugar de SQLite)
engine = create_engine("sqlite:///chatbot.db")  
Session = sessionmaker(bind=engine)
session = Session()

# Crear registro
psicologa = Psicologo(
    nombre="Karolai Alania",
    especialidad="Psicología Clínica",
    correo="karolai.alania@continental.edu.pe"
)

session.add(psicologa)
session.commit()

print("✅ Psicóloga Karolai Alania agregada al directorio")
