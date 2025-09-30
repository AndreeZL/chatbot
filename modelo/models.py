# modelo/models.py
import datetime
from sqlalchemy import Boolean, Column, Date, Enum, Integer, String, DateTime, ForeignKey, Text, Time
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Estudiante(Base):
    __tablename__ = 'estudiantes'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    carrera = Column(String(100))
    correo = Column(String(100), unique=True)
    password = Column(String(255), nullable=False)

    conversaciones = relationship("Conversacion", back_populates="estudiante")
    derivaciones = relationship("Derivacion", back_populates="estudiante")
    recomendaciones = relationship("Recomendacion", back_populates="estudiante")

class Psicologo(Base):
    __tablename__ = 'psicologos'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    especialidad = Column(String(100))
    correo = Column(String(100), unique=True)

    derivaciones = relationship("Derivacion", back_populates="psicologo")

class Conversacion(Base):
    __tablename__ = 'conversaciones'
    id = Column(Integer, primary_key=True)
    estudiante_id = Column(Integer, ForeignKey('estudiantes.id'))
    fecha = Column(String(20))
    hora = Column(String(20))
    mensaje_usuario = Column(Text)
    emocion_detectada = Column(String(50))
    nivel_estres = Column(String(20))
    ansiedad = Column(Integer) 
    depresion = Column(Integer)
    respuesta_chatbot = Column(Text)

    estudiante = relationship("Estudiante", back_populates="conversaciones")
    derivaciones = relationship("Derivacion", back_populates="conversacion")

class Derivacion(Base):
    __tablename__ = 'derivaciones'
    id = Column(Integer, primary_key=True)
    conversacion_id = Column(Integer, ForeignKey('conversaciones.id'), nullable=True)
    estudiante_id = Column(Integer, ForeignKey('estudiantes.id'), nullable=True)  # Permite anonimato
    psicologo_id = Column(Integer, ForeignKey('psicologos.id'))
    fecha_derivacion = Column(DateTime)
    estado = Column(Enum('pendiente', 'atendido', 'cerrado'), default='pendiente')
    datos_anonimos = Column(Text)  # Mensaje resumido/anónimo
    mensaje_estudiante = Column(Text)  # Mensaje de confirmación/orientación

    conversacion = relationship("Conversacion", back_populates="derivaciones")
    estudiante = relationship("Estudiante", back_populates="derivaciones")
    psicologo = relationship("Psicologo", back_populates="derivaciones")

class Recomendacion(Base):
    __tablename__ = "recomendacion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    estudiante_id = Column(Integer, ForeignKey("estudiantes.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    texto = Column(String(500), nullable=False)
    tipo = Column(String(50), nullable=True)  # Ej: "taller", "ejercicio", "artículo"
    util = Column(Boolean, nullable=True)  # True = útil, False = no útil, None = no evaluada

    estudiante = relationship("Estudiante", back_populates="recomendaciones")