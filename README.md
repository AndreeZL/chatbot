# EMOTIBOT - Chatbot de Apoyo Emocional (prototipo)
- Chaupis Leguia Piero Pool
- Riveros Sumalabe Fredy
- Yarasca Batalla Jairo Ronald
- Zacarias Lopez Lenning Andree

## Pasos rápidos
1. Crear entorno virtual:
   - `python -m venv venv`
   - `venv\Scripts\activate` 
2. Instalar dependencias:
   - `pip install -r requirements.txt`
3. Crear la base de datos SQLite:
   - `python database\setup_db.py`
4. Insertar psicologo al directorio (ejecutar uno de los dos):
   - `python -m database.insert_psicologo`
   - `python database/insert_psicologo.py`
5. Ejecutar la app:
   - `python -m vista.webapp`
6. Ver la base de datos en VSC:
   - `python utils/ver_db.py`