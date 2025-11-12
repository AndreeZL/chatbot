# vista/webapp.py
import sys
import os
import traceback
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

# Ajustar ruta para imports relativos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Imports internos ---
from control.chatbot_controller import ChatbotController
from modelo.firebase_models import (
    db, obtener_derivaciones, obtener_estudiante_por_correo, obtener_estudiante_por_id,
    obtener_conversaciones, obtener_estudiantes, ESTADO_LABELS
)

# --- Configuración base de la app ---
app = Flask(__name__, template_folder="templates")
app.secret_key = "emotibot-secret"
controller = ChatbotController()


# --------------------------------------------------------------------
# LANDING PAGE
# --------------------------------------------------------------------
@app.route("/")
def index():
    """Página de inicio"""
    return render_template("landing.html")


# --------------------------------------------------------------------
# REGISTRO DE ESTUDIANTE
# --------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    """Registro de nuevos estudiantes"""
    if request.method == "POST":
        nombre = request.form.get("nombre")
        correo = request.form.get("correo")
        carrera = request.form.get("carrera")
        password = request.form.get("password")

        if not (nombre and correo and password):
            flash("Por favor completa todos los campos.", "error")
            return render_template("register.html")

        users = db.collection("estudiantes").where("correo", "==", correo).stream()
        if any(users):
            flash("El correo ya está registrado.", "error")
            return render_template("register.html")

        hashed_password = generate_password_hash(password)
        db.collection("estudiantes").add({
            "nombre": nombre,
            "correo": correo,
            "carrera": carrera,
            "password": hashed_password
        })

        flash("✅ Registro exitoso. Ahora inicia sesión.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# --------------------------------------------------------------------
# LOGIN ESTUDIANTE
# --------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    """Inicio de sesión del estudiante"""
    if request.method == "POST":
        correo = request.form.get("correo")
        password = request.form.get("password")

        users = db.collection("estudiantes").where("correo", "==", correo).stream()
        user = next((u.to_dict() for u in users), None)

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["rol"] = "estudiante"
            session["correo"] = user["correo"]
            session["nombre"] = user["nombre"]
            session["carrera"] = user["carrera"]
            return redirect(url_for("chat"))
        else:
            flash("Correo o contraseña incorrectos.", "error")

    return render_template("login.html")


# --------------------------------------------------------------------
# LOGIN PSICÓLOGO
# --------------------------------------------------------------------
@app.route("/login_psicologo", methods=["GET", "POST"])
def login_psicologo():
    """Inicio de sesión para psicólogos"""
    if request.method == "POST":
        correo = request.form.get("correo")
        password = request.form.get("password")

        users = db.collection("psicologos").where("correo", "==", correo).stream()
        user = next((u.to_dict() for u in users), None)

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["rol"] = "psicologo"
            session["correo"] = user["correo"]
            session["nombre"] = user["nombre"]
            return redirect(url_for("panel_psicologo"))
        else:
            flash("Correo o contraseña incorrectos.", "error")

    return render_template("login_psicologo.html")


# --------------------------------------------------------------------
# PANEL DEL PSICÓLOGO
# --------------------------------------------------------------------
@app.route("/panel_psicologo")
def panel_psicologo():
    """Panel principal donde el psicólogo ve las derivaciones"""
    if session.get("rol") != "psicologo":
        return redirect(url_for("login_psicologo"))

    try:
        conversaciones = obtener_conversaciones()
        derivaciones = obtener_derivaciones()
        deriv_map = {d["conversacion_id"]: d for d in derivaciones}

        estudiantes_list = obtener_estudiantes()
        estudiantes_dict = {e["id"]: e for e in estudiantes_list}

        # Filtrar solo conversaciones derivadas
        conversaciones = [c for c in conversaciones if c["id"] in deriv_map]

        # Enriquecer datos
        for conv in conversaciones:
            est = estudiantes_dict.get(conv["estudiante_id"], {})
            conv["estudiante_nombre"] = est.get("nombre", "Desconocido")
            conv["estado"] = deriv_map[conv["id"]].get("estado", "pendiente")

        return render_template(
            "panel_psicologo.html",
            conversaciones=conversaciones,
            deriv_map=deriv_map,
            ESTADO_LABELS=ESTADO_LABELS,
            estudiantes=estudiantes_dict
        )
    except Exception as e:
        print("[ERROR PANEL PSICÓLOGO]:", e)
        traceback.print_exc()
        return "Error cargando el panel del psicólogo.", 500


# --------------------------------------------------------------------
# ACTUALIZAR ESTADO DE DERIVACIÓN
# --------------------------------------------------------------------
@app.route("/actualizar_estado_derivacion", methods=["POST"])
def actualizar_estado_derivacion():
    """Permite actualizar el estado de una derivación"""
    if session.get("rol") != "psicologo":
        return jsonify({"success": False, "msg": "No autorizado"}), 401

    data = request.get_json()
    derivacion_id = data.get("id")
    nuevo_estado = data.get("estado")

    if nuevo_estado not in ESTADO_LABELS:
        return jsonify({"success": False, "msg": "Estado inválido"}), 400

    try:
        db.collection("derivaciones").document(derivacion_id).update({"estado": nuevo_estado})
        return jsonify({"success": True, "label": ESTADO_LABELS[nuevo_estado]})
    except Exception as e:
        print("[ERROR ESTADO DERIVACIÓN]:", e)
        return jsonify({"success": False, "msg": "Error al actualizar"}), 500


# --------------------------------------------------------------------
# CHAT PRINCIPAL (ESTUDIANTE)
# --------------------------------------------------------------------
@app.route("/chat", methods=["GET", "POST"])
def chat():
    """Página principal del chat para estudiantes"""
    if session.get("rol") != "estudiante":
        return redirect(url_for("login"))

    ultima_respuesta = None

    if request.method == "POST":
        texto = request.form.get("texto")
        if texto:
            try:
                respuesta = controller.procesar_mensaje(session["correo"], texto)
                ultima_respuesta = respuesta["respuesta"]
            except Exception as e:
                print("[ERROR CHATBOT]:", e)
                traceback.print_exc()
                ultima_respuesta = "⚠️ Hubo un error al procesar tu mensaje. Intenta nuevamente."

    mensajes = controller.obtener_conversacion(session["correo"])
    return render_template(
        "chat.html",
        nombre=session["nombre"],
        mensajes=mensajes,
        ultima_respuesta=ultima_respuesta
    )


# --------------------------------------------------------------------
# ENDPOINT API (para AJAX / JS)
# --------------------------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def chat_api():
    """Versión API para interacción AJAX"""
    try:
        data = request.get_json()
        texto = data.get("mensaje")
        correo = session.get("correo")

        if not correo or not texto:
            return jsonify({"error": "Datos inválidos"}), 400

        respuesta = controller.procesar_mensaje(correo, texto)
        return jsonify(respuesta)
    except Exception as e:
        print("[ERROR API CHAT]:", e)
        traceback.print_exc()
        return jsonify({"error": "Error interno del servidor"}), 500


# --------------------------------------------------------------------
# HISTORIAL DEL ESTUDIANTE (vista psicólogo)
# --------------------------------------------------------------------
@app.route("/historial/<estudiante_id>")
def historial_chat(estudiante_id):
    """Historial de conversaciones visible solo para psicólogo"""
    if session.get("rol") != "psicologo":
        return redirect(url_for("login_psicologo"))

    estudiante = obtener_estudiante_por_id(estudiante_id)
    if not estudiante:
        return "Estudiante no encontrado", 404

    conversaciones = obtener_conversaciones(estudiante_id=estudiante_id)
    conversaciones.sort(key=lambda x: x.get("timestamp", None))

    return render_template("historial_chat.html", estudiante=estudiante, conversaciones=conversaciones)


# --------------------------------------------------------------------
# DIRECTORIO DE PSICÓLOGOS
# --------------------------------------------------------------------
@app.route("/directorio")
def directorio():
    """Directorio público de psicólogos"""
    if session.get("rol") != "estudiante":
        return redirect(url_for("login"))

    profesionales = controller.obtener_profesionales()
    return render_template("directorio.html", profesionales=profesionales)


# --------------------------------------------------------------------
# LOGOUT
# --------------------------------------------------------------------
@app.route("/logout")
def logout():
    """Cerrar sesión actual"""
    session.clear()
    return redirect(url_for("login"))


# --------------------------------------------------------------------
# MAIN APP
# --------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Emotibot ejecutándose en http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=True)
