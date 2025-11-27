# vista/webapp.py
import sys
import os
import traceback
import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from modelo.firebase_models import tz

# Ajustar ruta para imports relativos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Imports internos ---
from control.chatbot_controller import ChatbotController
from modelo.firebase_models import (
    db, obtener_derivaciones, obtener_estudiante_por_correo, obtener_estudiante_por_id,
    obtener_conversaciones, obtener_estudiantes, ESTADO_LABELS,
    guardar_reporte_anonimo, obtener_reportes_anonimos, validar_recurso,
    guardar_validacion_prediccion, obtener_validaciones_predicciones,
    calcular_metricas, evaluar_intervenciones,
    guardar_recurso_sugerido, obtener_recursos_sugeridos, validar_recurso_sugerido
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
            "password": hashed_password,
            "fecha_registro": datetime.datetime.now(tz)
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

        # DEBUG: información para diagnosticar listas vacías
        try:
            print("[DEBUG PANEL] conversaciones_count:", len(conversaciones))
            print("[DEBUG PANEL] derivaciones_count:", len(derivaciones))
            print("[DEBUG PANEL] estudiantes_count:", len(estudiantes_list))
            for i, e in enumerate(estudiantes_list[:5], 1):
                print(f"[DEBUG PANEL] estudiante[{i}]:", e)
        except Exception as _:
            print("[DEBUG PANEL] error imprimiendo debug")

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

    try:
        profesionales = controller.obtener_profesionales()
        # DEBUG: imprimir información de profesionales
        try:
            print("[DEBUG DIRECTORIO] profesionales_count:", len(profesionales))
            for i, p in enumerate(profesionales[:10], 1):
                print(f"[DEBUG DIRECTORIO] profesional[{i}]:", p)
        except Exception:
            print("[DEBUG DIRECTORIO] error imprimiendo profesionales")

        return render_template("directorio.html", profesionales=profesionales)
    except Exception as e:
        print("[ERROR DIRECTORIO]:", e)
        traceback.print_exc()
        return "Error cargando directorio", 500


# --------------------------------------------------------------------
# LOGOUT
# --------------------------------------------------------------------
@app.route("/logout")
def logout():
    """Cerrar sesión actual"""
    session.clear()
    return redirect(url_for("login"))


# --------------------------------------------------------------------
# HU-9: Validación de recursos
# --------------------------------------------------------------------
@app.route("/validar_recurso", methods=["POST"])
def validar_recurso_route():
    """Valida un recurso (URL) de manera básica."""
    if session.get("rol") not in ("psicologo", "estudiante"):
        return jsonify({"success": False, "msg": "No autorizado"}), 401

    data = request.get_json() or {}
    url = data.get("url")
    if not url:
        return jsonify({"success": False, "msg": "URL requerida"}), 400

    try:
        resultado = validar_recurso(url)
        return jsonify({"success": True, "resultado": resultado})
    except Exception as e:
        print("[ERROR VALIDAR RECURSO]:", e)
        traceback.print_exc()
        return jsonify({"success": False, "msg": "Error en validación"}), 500


# --------------------------------------------------------------------
# HU-11: Reportes anónimos de estudiantes
# --------------------------------------------------------------------
@app.route("/reportes_anonimos", methods=["GET", "POST"])
def reportes_anonimos_route():
    """Permite a estudiantes enviar reportes anónimos y a psicólogos listarlos."""
    if request.method == "POST":
        # debug info
        print("[REPORTES_ANONIMOS] Content-Type:", request.content_type)
        try:
            raw = request.get_data(as_text=True)
            print("[REPORTES_ANONIMOS] Raw body:", raw)
        except Exception:
            pass

        # soportar tanto form-urlencoded como JSON
        data = None
        if request.form and len(request.form) > 0:
            data = request.form
        else:
            data = request.get_json(silent=True) or {}

        texto = data.get("texto") if data else None
        categoria = data.get("categoria") if data else None
        if not texto:
            return jsonify({"success": False, "msg": "Texto requerido"}), 400
        try:
            rid = guardar_reporte_anonimo(texto, categoria=categoria)
            return jsonify({"success": True, "id": rid})
        except Exception as e:
            print("[ERROR GUARDAR REPORTE ANÓNIMO]:", e)
            traceback.print_exc()
            return jsonify({"success": False, "msg": "Error guardando reporte"}), 500

    # GET
    rol = session.get("rol")
    if rol == "psicologo":
        try:
            reports = obtener_reportes_anonimos()
            return render_template("reportes_anonimos.html", reportes=reports)
        except Exception as e:
            print("[ERROR OBTENER REPORTES ANÓNIMOS]:", e)
            traceback.print_exc()
            return "Error obteniendo reportes anonymos", 500
    elif rol == "estudiante":
        return render_template("enviar_reporte_anonimo.html")
    else:
        return redirect(url_for("login"))


# Añadir GET para /sugerir_recurso
@app.route("/sugerir_recurso", methods=["GET", "POST"])
def sugerir_recurso_route():
    if request.method == "POST":
        # Verificar rol
        if session.get("rol") != "estudiante":
            return jsonify({"success": False, "msg": "No autorizado"}), 401

        # Leer datos del formulario
        title = request.form.get("title")
        description = request.form.get("description")
        url = request.form.get("url")

        # Validar campos obligatorios
        if not title or not url:
            return jsonify({"success": False, "msg": "title y url son requeridos"}), 400

        # Guardar recurso
        try:
            estudiante = obtener_estudiante_por_correo(session.get("correo"))
            estudiante_id = estudiante.get("id") if estudiante else None
            rid = guardar_recurso_sugerido(estudiante_id, title, description, url)
            return jsonify({"success": True, "id": rid})
        except Exception as e:
            print("[ERROR SUGERIR RECURSO]:", e)
            traceback.print_exc()
            return jsonify({"success": False, "msg": "Error guardando recurso"}), 500

    # GET
    if session.get("rol") != "estudiante":
        return redirect(url_for("login"))

    return render_template("sugerir_recurso.html")



# --------------------------------------------------------------------
# HU-12: Validación de predicciones
# --------------------------------------------------------------------
@app.route("/validar_prediccion", methods=["POST"])
def validar_prediccion_route():
    """Endpoint para que un psicólogo valide una predicción del modelo."""
    if session.get("rol") != "psicologo":
        return jsonify({"success": False, "msg": "No autorizado"}), 401

    data = request.get_json() or {}
    conversacion_id = data.get("conversacion_id")
    valido = data.get("valido", True)
    comentarios = data.get("comentarios")

    if not conversacion_id:
        return jsonify({"success": False, "msg": "conversacion_id requerido"}), 400

    try:
        vid = guardar_validacion_prediccion(
            conversacion_id,
            validador_id=session.get("correo"),
            valido=valido,
            comentarios=comentarios
        )
        return jsonify({"success": True, "id": vid})
    except Exception as e:
        print("[ERROR GUARDAR VALIDACION PREDICCIÓN]:", e)
        traceback.print_exc()
        return jsonify({"success": False, "msg": "Error guardando validación"}), 500


# NUEVA RUTA: listar validaciones
@app.route("/validaciones")
def listar_validaciones_route():
    if session.get("rol") != "psicologo":
        return redirect(url_for("login_psicologo"))
    try:
        vals = obtener_validaciones_predicciones()
        return render_template("validaciones.html", validaciones=vals)
    except Exception as e:
        print("[ERROR LISTAR VALIDACIONES]:", e)
        traceback.print_exc()
        return "Error listando validaciones", 500


# --------------------------------------------------------------------
# HU-13: Panel de métricas de bienestar estudiantil
# --------------------------------------------------------------------
@app.route("/metrics")
def metrics_route():
    """Devuelve métricas agregadas para mostrar en un panel."""
    if session.get("rol") != "psicologo":
        return redirect(url_for("login_psicologo"))
    try:
        metrics = calcular_metricas()
        # Renderizar template de métricas
        return render_template("metrics.html", metrics=metrics)
    except Exception as e:
        print("[ERROR METRICS]:", e)
        traceback.print_exc()
        return "Error calculando métricas", 500


# --------------------------------------------------------------------
# LISTADO DE DERIVACIONES (HU-10)
# --------------------------------------------------------------------
@app.route("/listado_derivaciones")
def listado_derivaciones_route():
    if session.get("rol") != "psicologo":
        return redirect(url_for("login_psicologo"))
    try:
        derivaciones = obtener_derivaciones()
        # enriquecer con estudiante si es posible
        estudiantes_list = obtener_estudiantes()
        estudiantes_dict = {e["id"]: e for e in estudiantes_list}
        return render_template("listado_derivaciones.html", derivaciones=derivaciones, estudiantes=estudiantes_dict, ESTADO_LABELS=ESTADO_LABELS)
    except Exception as e:
        print("[ERROR LISTADO DERIVACIONES]:", e)
        traceback.print_exc()
        return "Error listando derivaciones", 500


# --------------------------------------------------------------------
# HU-14: Evaluación de efectividad de intervenciones
# --------------------------------------------------------------------
@app.route("/evaluacion_intervenciones")
def evaluacion_intervenciones_route():
    """Devuelve evaluación básica de efectividad de intervenciones."""
    if session.get("rol") != "psicologo":
        return redirect(url_for("login_psicologo"))
    try:
        resultado = evaluar_intervenciones()
        estudiantes_list = obtener_estudiantes()  # Traer estudiantes
        estudiantes_dict = {e["id"]: e for e in estudiantes_list}
        return render_template(
            "evaluacion_intervenciones.html",
            resultado=resultado,
            estudiantes=estudiantes_dict
        )
    except Exception as e:
        print("[ERROR EVALUACION INTERVENCIONES]:", e)
        traceback.print_exc()
        return "Error en evaluación", 500



# --------------------------------------------------------------------
# HU-9/Extra: Estudiante sugiere recurso (libro/película) para validar por psicólogo
# --------------------------------------------------------------------
# (Ruta GET/POST ya definida anteriormente; evitar duplicados)


# --------------------------------------------------------------------
# HU-10/Extra: Psicólogo lista recursos sugeridos y valida
# --------------------------------------------------------------------
@app.route("/recursos_sugeridos")
def recursos_sugeridos_route():
    if session.get("rol") != "psicologo":
        return redirect(url_for("login_psicologo"))
    try:
        recursos = obtener_recursos_sugeridos()
        estudiantes_list = obtener_estudiantes()
        estudiantes_dict = {e["id"]: e for e in estudiantes_list}
        return render_template("recursos_sugeridos.html", recursos=recursos, estudiantes=estudiantes_dict)
    except Exception as e:
        print("[ERROR RECURSOS SUGERIDOS]:", e)
        traceback.print_exc()
        return "Error obteniendo recursos", 500


@app.route("/validar_recurso_sugerido", methods=["POST"])
def validar_recurso_sugerido_route():
    if session.get("rol") != "psicologo":
        return jsonify({"success": False, "msg": "No autorizado"}), 401
    data = request.get_json() or {}
    recurso_id = data.get("id")
    status = data.get("status")  # 'approved' or 'rejected'
    comentarios = data.get("comentarios")
    if not recurso_id or status not in ("approved", "rejected"):
        return jsonify({"success": False, "msg": "Parametros inválidos"}), 400
    try:
        validar_recurso_sugerido(recurso_id, validated_by=session.get("correo"), status=status, comentarios=comentarios)
        return jsonify({"success": True})
    except Exception as e:
        print("[ERROR VALIDAR RECURSO SUGERIDO]:", e)
        traceback.print_exc()
        return jsonify({"success": False, "msg": "Error validando recurso"}), 500


# --------------------------------------------------------------------
# MAIN APP
# --------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Emotibot ejecutándose en http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=True)
