-- Script para MySQL (opcional)
CREATE DATABASE IF NOT EXISTS chatbot_db;
USE chatbot_db;

CREATE TABLE Estudiante (
  id_estudiante INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  carrera VARCHAR(100),
  correo VARCHAR(100) UNIQUE
);

CREATE TABLE Psicologo (
  id_psicologo INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  especialidad VARCHAR(100),
  correo VARCHAR(100) UNIQUE
);

CREATE TABLE Conversacion (
  id_conversacion INT AUTO_INCREMENT PRIMARY KEY,
  id_estudiante INT,
  fecha DATE,
  hora TIME,
  mensaje_usuario TEXT,
  emocion_detectada VARCHAR(50),
  nivel_estres VARCHAR(20),
  respuesta_chatbot TEXT,
  FOREIGN KEY (id_estudiante) REFERENCES Estudiante(id_estudiante)
);

CREATE TABLE Derivacion (
  id_derivacion INT AUTO_INCREMENT PRIMARY KEY,
  id_conversacion INT,
  id_estudiante INT,
  id_psicologo INT,
  fecha_derivacion DATE,
  estado VARCHAR(50),
  FOREIGN KEY (id_conversacion) REFERENCES Conversacion(id_conversacion),
  FOREIGN KEY (id_psicologo) REFERENCES Psicologo(id_psicologo)
);
