# vista/webapp.py
import sys, os
import mysql.connector
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, redirect, url_for, session, flash
from control.chatbot_controller import ChatbotController
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"))
app.secret_key = "emotibot-secret"  # clave para sesiones
controller = ChatbotController()

# Conexión a MySQL
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="andreezl13",
    database="chatbot_db"
)
cursor = db.cursor(dictionary=True)

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

        cursor.execute("SELECT * FROM estudiantes WHERE correo=%s", (correo,))
        user = cursor.fetchone()
        if user:
            flash("El correo ya está registrado", "error")
            return render_template("register.html")

        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO estudiantes (nombre, correo, carrera, password) VALUES (%s, %s, %s, %s)",
            (nombre, correo, carrera, hashed_password)
        )
        db.commit()

        flash("Registro exitoso, ahora inicia sesión", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# ---------------- Login ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"]
        password = request.form["password"]

        cursor.execute("SELECT * FROM estudiantes WHERE correo=%s", (correo,))
        user = cursor.fetchone()
        if user and check_password_hash(user["password"], password):
            session["correo"] = user["correo"]
            session["nombre"] = user["nombre"]
            session["carrera"] = user["carrera"]
            return redirect(url_for("chat"))
        else:
            flash("Correo o contraseña incorrectos", "error")
            return render_template("login.html")

    return render_template("login.html")

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

@app.route("/directorio")
def directorio():
    if "correo" not in session:
        return redirect(url_for("login"))
    
    profesionales = controller.obtener_profesionales()
    return render_template("directorio.html", profesionales=profesionales)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
