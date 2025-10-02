# vista/webapp.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, redirect, url_for, session, flash
from control.chatbot_controller import ChatbotController
from werkzeug.security import generate_password_hash, check_password_hash
from modelo.firebase_models import db  # Firestore

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"))
app.secret_key = "emotibot-secret"  # clave para sesiones
controller = ChatbotController()

# ---------------- Landing ----------------
@app.route("/")
def index():
    return render_template("landing.html")

# ---------------- Registro ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form["nombre"]
        correo = request.form["correo"]
        carrera = request.form["carrera"]
        password = request.form["password"]

        # Buscar si ya existe
        users = db.collection("estudiantes").where("correo", "==", correo).stream()
        if any(users):
            flash("El correo ya está registrado", "error")
            return render_template("register.html")

        # Guardar con contraseña encriptada
        hashed_password = generate_password_hash(password)
        db.collection("estudiantes").add({
            "nombre": nombre,
            "correo": correo,
            "carrera": carrera,
            "password": hashed_password
        })

        flash("Registro exitoso, ahora inicia sesión", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# ---------------- Login ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"]
        password = request.form["password"]

        users = db.collection("estudiantes").where("correo", "==", correo).stream()
        user = None
        for u in users:
            user = u.to_dict()
            break

        if user and check_password_hash(user["password"], password):
            session["correo"] = user["correo"]
            session["nombre"] = user["nombre"]
            session["carrera"] = user["carrera"]
            return redirect(url_for("chat"))
        else:
            flash("Correo o contraseña incorrectos", "error")
            return render_template("login.html")

    return render_template("login.html")

# ---------------- Chat ----------------
@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "correo" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        texto = request.form.get("texto")
        if texto:
            controller.procesar_mensaje(session["correo"], texto)

    mensajes = controller.obtener_conversacion(session["correo"])
    return render_template("chat.html", nombre=session["nombre"], mensajes=mensajes)

# ---------------- Directorio ----------------
@app.route("/directorio")
def directorio():
    if "correo" not in session:
        return redirect(url_for("login"))
    
    profesionales = controller.obtener_profesionales()
    return render_template("directorio.html", profesionales=profesionales)

# ---------------- Logout ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
