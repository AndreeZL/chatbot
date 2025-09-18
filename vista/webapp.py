# vista/webapp.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, redirect, url_for, session
from control.chatbot_controller import ChatbotController

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"))
app.secret_key = "emotibot-secret"  # clave para sesiones
controller = ChatbotController()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("correo")
        nombre = request.form.get("nombre")

        if correo and nombre:
            controller.registrar_estudiante(nombre, correo)
            session["correo"] = correo
            session["nombre"] = nombre
            return redirect(url_for("chat"))

    return render_template("login.html")

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "correo" not in session:
        return redirect(url_for("login"))

    mensajes = session.get("mensajes", [])

    if request.method == "POST":
        texto = request.form.get("texto")
        if texto:
            resultado = controller.procesar_mensaje(session["correo"], texto)
            mensajes.append(("Tú", texto))
            mensajes.append(("Bot", resultado["respuesta"]))
            session["mensajes"] = mensajes

    return render_template("chat.html", nombre=session["nombre"], mensajes=mensajes)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
