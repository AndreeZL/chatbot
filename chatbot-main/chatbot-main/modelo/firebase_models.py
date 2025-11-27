# modelo/firebase_models.py

import os
import datetime
import pytz
import json
import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.security import generate_password_hash
from google.api_core import exceptions as api_exceptions

# ============================================================
# 🔥 Configuración general
# ============================================================

EMOTION_LABELS = [
    "alegría", "tristeza", "enojo", "miedo", "sorpresa", "asco", "neutral"
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Inicialización de Firebase
cred_env = os.environ.get("FIREBASE_CREDENTIALS")

if not firebase_admin._apps:
    if cred_env:
        try:
            cred_dict = json.loads(cred_env)
            cred = credentials.Certificate(cred_dict)
        except json.JSONDecodeError:
            if os.path.isfile(cred_env):
                cred = credentials.Certificate(cred_env)
            else:
                print("⚠️ FIREBASE_CREDENTIALS no válido, usando archivo local...")
                json_path = os.path.join(BASE_DIR, "chatbot-78eec-firebase-adminsdk-fbsvc-b0eea0da20.json")
                cred = credentials.Certificate(json_path)
    else:
        print("⚠️ No se encontró FIREBASE_CREDENTIALS, usando archivo local...")
        json_path = os.path.join(BASE_DIR, "chatbot-78eec-firebase-adminsdk-fbsvc-b0eea0da20.json")
        cred = credentials.Certificate(json_path)

    firebase_admin.initialize_app(cred)

db = firestore.client()
tz = pytz.timezone("America/Lima")


def _to_datetime(v):
    """Normaliza distintos tipos de timestamp a datetime.datetime. Si no se puede, devuelve datetime.datetime.min"""
    if v is None:
        return datetime.datetime.min
    if isinstance(v, datetime.datetime):
        return v
    if isinstance(v, str):
        try:
            # soportar ISO formats
            return datetime.datetime.fromisoformat(v)
        except Exception:
            pass
    # Firestore/Protobuf timestamp objects suelen tener ToDatetime()
    try:
        if hasattr(v, 'ToDatetime'):
            return v.ToDatetime()
        if hasattr(v, 'to_datetime'):
            return v.to_datetime()
    except Exception:
        pass
    return datetime.datetime.min

# ============================================================
# 👤 ESTUDIANTES
# ============================================================

def crear_estudiante(nombre, correo, carrera):
    doc_ref = db.collection("estudiantes").document()
    data = {
        "nombre": nombre,
        "correo": correo,
        "carrera": carrera,
        "fecha_registro": datetime.datetime.now(tz)
    }
    doc_ref.set(data)
    return doc_ref.id

def obtener_estudiante_por_correo(correo):
    query = db.collection("estudiantes").where("correo", "==", correo).limit(1).stream()
    for doc in query:
        return doc.to_dict() | {"id": doc.id}
    return None

def obtener_estudiante_por_id(estudiante_id):
    doc = db.collection("estudiantes").document(estudiante_id).get()
    if doc.exists:
        return doc.to_dict() | {"id": doc.id}
    return None

def obtener_estudiantes(limit=50, start_after=None):
    try:
        # Tomamos los documentos sin order_by
        docs = [d for d in db.collection("estudiantes").stream()]
        items = [doc.to_dict() | {"id": doc.id} for doc in docs]

        # Fallback de paginación manual usando start_after como índice
        if start_after:
            try:
                start_index = next(i for i, e in enumerate(items) if e["id"] == start_after)
                items = items[start_index + 1:]
            except StopIteration:
                pass

        return items[:limit]
    except Exception as e:
        print("[ERROR obtener_estudiantes]:", e)
        return []


# ============================================================
# 👨‍⚕️ PSICÓLOGOS
# ============================================================

def crear_psicologo(nombre, especialidad, correo, password):
    doc_ref = db.collection("psicologos").document()
    data = {
        "nombre": nombre,
        "especialidad": especialidad,
        "correo": correo,
        "password": generate_password_hash(password),
        "fecha_registro": datetime.datetime.now(tz)
    }
    doc_ref.set(data)
    return doc_ref.id

def obtener_psicologo_por_correo(correo):
    query = db.collection("psicologos").where("correo", "==", correo).limit(1).stream()
    for doc in query:
        return doc.to_dict() | {"id": doc.id}
    return None

def obtener_psicologos(limit=50, start_after=None):
    try:
        docs = [d for d in db.collection("psicologos").stream()]
        items = [doc.to_dict() | {"id": doc.id} for doc in docs]
        print("[DEBUG fallback obtener_psicologos] count:", len(items))
        return items[:limit]
    except Exception as e:
        print("[ERROR obtener_psicologos fallback]:", e)
        return []

# ============================================================
# 💬 CONVERSACIONES
# ============================================================

def guardar_conversacion(estudiante_id, mensaje_usuario, emocion_detectada,
                         nivel_estres, ansiedad, depresion, respuesta_chatbot,
                         conv_id=None, emocion_cod=None):
    ahora = datetime.datetime.now(tz)
    doc_ref = db.collection("conversaciones").document(conv_id) if conv_id else db.collection("conversaciones").document()
    data = {
        "estudiante_id": estudiante_id,
        "mensaje_usuario": mensaje_usuario,
        "respuesta_chatbot": respuesta_chatbot,
        "emocion_detectada": emocion_detectada,
        "nivel_estres": nivel_estres,
        "ansiedad": ansiedad,
        "depresion": depresion,
        "fecha": ahora.date().isoformat(),
        "hora": ahora.strftime("%H:%M:%S"),
        "timestamp": ahora
    }
    if emocion_cod is not None:
        data["emocion_cod"] = emocion_cod
    doc_ref.set(data)
    return doc_ref.id

def obtener_conversaciones(estudiante_id=None, limit=50, start_after=None):
    ref = db.collection("conversaciones")
    if estudiante_id:
        ref = ref.where("estudiante_id", "==", estudiante_id)
    ref = ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
    if start_after:
        try:
            sa = start_after if isinstance(start_after, datetime.datetime) else _to_datetime(start_after)
            ref = ref.start_after({"timestamp": sa})
        except Exception:
            pass
    try:
        return [doc.to_dict() | {"id": doc.id} for doc in ref.stream()]
    except api_exceptions.FailedPrecondition:
        # Fallback: Firestore requiere índice -> obtenemos sin order_by y ordenamos en memoria
        ref2 = db.collection("conversaciones")
        if estudiante_id:
            ref2 = ref2.where("estudiante_id", "==", estudiante_id)
        docs = [doc for doc in ref2.stream()]
        items = []
        for doc in docs:
            d = doc.to_dict()
            d = d | {"id": doc.id}
            items.append(d)

        # Emular start_after para paginación: si se entregó start_after, filtramos
        if start_after:
            sa = start_after if isinstance(start_after, datetime.datetime) else _to_datetime(start_after)
            items = [i for i in items if i.get("timestamp") and _to_datetime(i.get("timestamp")) < sa]

        # Orden descendente por timestamp y limitar
        items.sort(key=lambda x: _to_datetime(x.get("timestamp")), reverse=True)
        return items[:limit]

# ============================================================
# 📌 DERIVACIONES
# ============================================================

ESTADOS_DERIVACION = ("pendiente", "completada")
ESTADO_LABELS = {"pendiente": "Pendiente ⏳", "completada": "Completada ✅"}

def guardar_derivacion(conversacion_id, psicologo_id, estudiante_id=None,
                       mensaje_estudiante=None, estado="pendiente"):
    if estado not in ESTADOS_DERIVACION:
        raise ValueError(f"Estado inválido: {estado}")
    doc_ref = db.collection("derivaciones").document()
    data = {
        "conversacion_id": conversacion_id,
        "psicologo_id": psicologo_id,
        "estudiante_id": estudiante_id,
        "mensaje_estudiante": mensaje_estudiante,
        "fecha_derivacion": datetime.datetime.now(tz),
        "estado": estado
    }
    doc_ref.set(data)
    return doc_ref.id

def obtener_derivaciones(limit=50, start_after=None):
    ref = db.collection("derivaciones").order_by("fecha_derivacion", direction=firestore.Query.DESCENDING).limit(limit)
    if start_after:
        try:
            sa = start_after if isinstance(start_after, datetime.datetime) else _to_datetime(start_after)
            ref = ref.start_after({"fecha_derivacion": sa})
        except Exception:
            pass
    try:
        return [{"id": d.id, **d.to_dict()} for d in ref.stream()]
    except api_exceptions.FailedPrecondition:
        docs = [d for d in db.collection("derivaciones").stream()]
        items = [{"id": d.id, **d.to_dict()} for d in docs]
        items.sort(key=lambda x: _to_datetime(x.get("fecha_derivacion")), reverse=True)
        if start_after:
            sa = start_after if isinstance(start_after, datetime.datetime) else _to_datetime(start_after)
            items = [i for i in items if _to_datetime(i.get("fecha_derivacion")) and _to_datetime(i.get("fecha_derivacion")) < sa]
        return items[:limit]

# ============================================================
# 🎯 RECOMENDACIONES
# ============================================================

def guardar_recomendacion(estudiante_id, texto, tipo=None, util=None):
    ahora = datetime.datetime.now(tz)
    doc_ref = db.collection("recomendaciones").document()
    data = {
        "estudiante_id": estudiante_id,
        "fecha": ahora.date().isoformat(),
        "hora": ahora.strftime("%H:%M:%S"),
        "timestamp": ahora,
        "texto": texto,
        "tipo": tipo,
        "util": util
    }
    doc_ref.set(data)
    return doc_ref.id

def obtener_recomendaciones(estudiante_id=None, limit=50, start_after=None):
    ref = db.collection("recomendaciones")
    if estudiante_id:
        ref = ref.where("estudiante_id", "==", estudiante_id)
    ref = ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
    if start_after:
        try:
            sa = start_after if isinstance(start_after, datetime.datetime) else _to_datetime(start_after)
            ref = ref.start_after({"timestamp": sa})
        except Exception:
            pass
    try:
        return [doc.to_dict() | {"id": doc.id} for doc in ref.stream()]
    except api_exceptions.FailedPrecondition:
        ref2 = db.collection("recomendaciones")
        if estudiante_id:
            ref2 = ref2.where("estudiante_id", "==", estudiante_id)
        docs = [d for d in ref2.stream()]
        items = [doc.to_dict() | {"id": doc.id} for doc in docs]
        items.sort(key=lambda x: _to_datetime(x.get("timestamp")), reverse=True)
        if start_after:
            sa = start_after if isinstance(start_after, datetime.datetime) else _to_datetime(start_after)
            items = [i for i in items if _to_datetime(i.get("timestamp")) and _to_datetime(i.get("timestamp")) < sa]
        return items[:limit]

# ============================================================
# 📄 REPORTES ANÓNIMOS
# ============================================================

def guardar_reporte_anonimo(texto, categoria=None):
    ahora = datetime.datetime.now(tz)
    doc_ref = db.collection("reportes_anonimos").document()
    data = {
        "texto": texto,
        "categoria": categoria,
        "fecha": ahora.date().isoformat(),
        "hora": ahora.strftime("%H:%M:%S"),
        "timestamp": ahora
    }
    doc_ref.set(data)
    return doc_ref.id

def obtener_reportes_anonimos(limit=50, start_after=None):
    ref = db.collection("reportes_anonimos").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
    if start_after:
        try:
            sa = start_after if isinstance(start_after, datetime.datetime) else _to_datetime(start_after)
            ref = ref.start_after({"timestamp": sa})
        except Exception:
            pass
    try:
        return [doc.to_dict() | {"id": doc.id} for doc in ref.stream()]
    except api_exceptions.FailedPrecondition:
        docs = [d for d in db.collection("reportes_anonimos").stream()]
        items = [doc.to_dict() | {"id": doc.id} for doc in docs]
        items.sort(key=lambda x: _to_datetime(x.get("timestamp")), reverse=True)
        if start_after:
            sa = start_after if isinstance(start_after, datetime.datetime) else _to_datetime(start_after)
            items = [i for i in items if _to_datetime(i.get("timestamp")) and _to_datetime(i.get("timestamp")) < sa]
        return items[:limit]

# ============================================================
# 📝 VALIDACIÓN DE RECURSOS
# ============================================================

def validar_recurso(url):
    valido = isinstance(url, str) and url.startswith(("http://", "https://")) and len(url) > 10
    return {"url": url, "valido": bool(valido)}

def guardar_validacion_prediccion(conversacion_id, validador_id=None, valido=True, comentarios=None):
    ahora = datetime.datetime.now(tz)
    doc_ref = db.collection("validaciones_predicciones").document()
    data = {
        "conversacion_id": conversacion_id,
        "validador_id": validador_id,
        "valido": bool(valido),
        "comentarios": comentarios,
        "fecha": ahora.date().isoformat(),
        "hora": ahora.strftime("%H:%M:%S"),
        "timestamp": ahora
    }
    doc_ref.set(data)
    return doc_ref.id

def obtener_validaciones_predicciones(conversacion_id=None, limit=50, start_after=None):
    ref = db.collection("validaciones_predicciones")
    if conversacion_id:
        ref = ref.where("conversacion_id", "==", conversacion_id)
    ref = ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
    if start_after:
        try:
            sa = start_after if isinstance(start_after, datetime.datetime) else _to_datetime(start_after)
            ref = ref.start_after({"timestamp": sa})
        except Exception:
            pass
    try:
        return [doc.to_dict() | {"id": doc.id} for doc in ref.stream()]
    except api_exceptions.FailedPrecondition:
        ref2 = db.collection("validaciones_predicciones")
        if conversacion_id:
            ref2 = ref2.where("conversacion_id", "==", conversacion_id)
        docs = [d for d in ref2.stream()]
        items = [doc.to_dict() | {"id": doc.id} for doc in docs]
        items.sort(key=lambda x: _to_datetime(x.get("timestamp")), reverse=True)
        if start_after:
            sa = start_after if isinstance(start_after, datetime.datetime) else _to_datetime(start_after)
            items = [i for i in items if _to_datetime(i.get("timestamp")) and _to_datetime(i.get("timestamp")) < sa]
        return items[:limit]

# ============================================================
# 🎓 MÉTRICAS Y EVALUACIONES
# ============================================================

def calcular_metricas():
    conversaciones = obtener_conversaciones(limit=500)  # límite de seguridad
    n = len(conversaciones)
    total_ans = sum((c.get("ansiedad") or 0) for c in conversaciones)
    total_dep = sum((c.get("depresion") or 0) for c in conversaciones)
    avg_ans = (total_ans / n) if n else 0
    avg_dep = (total_dep / n) if n else 0
    derivaciones = obtener_derivaciones(limit=500)
    return {
        "total_conversaciones": n,
        "promedio_ansiedad": avg_ans,
        "promedio_depresion": avg_dep,
        "total_derivaciones": len(derivaciones)
    }

def evaluar_intervenciones():
    recomendaciones = obtener_recomendaciones(limit=500)
    estudiantes_con_recomendaciones = set(r["estudiante_id"] for r in recomendaciones if r.get("estudiante_id"))
    resultado = {}

    for estudiante_id in estudiantes_con_recomendaciones:
        convs = obtener_conversaciones(estudiante_id=estudiante_id, limit=500)
        if not convs:
            continue
        convs = sorted(convs, key=lambda x: x.get("timestamp") or datetime.datetime.min)
        recs_est = [r for r in recomendaciones if r.get("estudiante_id") == estudiante_id and r.get("timestamp")]
        if not recs_est:
            continue
        primera_rec_ts = min(r["timestamp"] for r in recs_est)

        antes = [c for c in convs if c.get("timestamp") and c.get("timestamp") < primera_rec_ts]
        despues = [c for c in convs if c.get("timestamp") and c.get("timestamp") >= primera_rec_ts]

        def prom(lista, campo):
            if not lista:
                return None
            vals = [c.get(campo) or 0 for c in lista]
            return sum(vals) / len(vals)

        resultado[estudiante_id] = {
            "antes": {"ansiedad": prom(antes, "ansiedad"), "depresion": prom(antes, "depresion")},
            "despues": {"ansiedad": prom(despues, "ansiedad"), "depresion": prom(despues, "depresion")}
        }

    return resultado

# ============================================================
# 🔗 RECURSOS SUGERIDOS Y NOTIFICACIONES
# ============================================================

def guardar_recurso_sugerido(created_by, title, description, url):
    ahora = datetime.datetime.now(tz)
    doc_ref = db.collection("recursos_sugeridos").document()
    data = {
        "created_at": ahora,
        "created_by": created_by,
        "title": title,
        "description": description,
        "url": url,
        "status": "pending"
    }
    doc_ref.set(data)
    return doc_ref.id

def obtener_recursos_sugeridos(status=None, limit=50, start_after=None):
    ref = db.collection("recursos_sugeridos").order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)
    if status:
        ref = ref.where("status", "==", status)
        if start_after:
            try:
                sa = start_after if isinstance(start_after, datetime.datetime) else _to_datetime(start_after)
                ref = ref.start_after({"created_at": sa})
            except Exception:
                pass
    try:
        return [doc.to_dict() | {"id": doc.id} for doc in ref.stream()]
    except api_exceptions.FailedPrecondition:
        ref2 = db.collection("recursos_sugeridos")
        if status:
            ref2 = ref2.where("status", "==", status)
        docs = [d for d in ref2.stream()]
        items = [doc.to_dict() | {"id": doc.id} for doc in docs]
        items.sort(key=lambda x: _to_datetime(x.get("created_at")), reverse=True)
        if start_after:
            sa = start_after if isinstance(start_after, datetime.datetime) else _to_datetime(start_after)
            items = [i for i in items if _to_datetime(i.get("created_at")) and _to_datetime(i.get("created_at")) < sa]
        return items[:limit]

def guardar_notificacion(user_id, mensaje, extra=None):
    ahora = datetime.datetime.now(tz)
    doc_ref = db.collection("notificaciones").document()
    data = {
        "user_id": user_id,
        "mensaje": mensaje,
        "extra": extra,
        "leida": False,
        "created_at": ahora
    }
    doc_ref.set(data)
    return doc_ref.id

def obtener_notificaciones_por_usuario(user_id, limit=50, start_after=None):
    ref = db.collection("notificaciones").where("user_id", "==", user_id).order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)
    if start_after:
        try:
            sa = start_after if isinstance(start_after, datetime.datetime) else _to_datetime(start_after)
            ref = ref.start_after({"created_at": sa})
        except Exception:
            pass
    try:
        return [doc.to_dict() | {"id": doc.id} for doc in ref.stream()]
    except api_exceptions.FailedPrecondition:
        ref2 = db.collection("notificaciones")
        ref2 = ref2.where("user_id", "==", user_id)
        docs = [d for d in ref2.stream()]
        items = [doc.to_dict() | {"id": doc.id} for doc in docs]
        items.sort(key=lambda x: _to_datetime(x.get("created_at")), reverse=True)
        if start_after:
            sa = start_after if isinstance(start_after, datetime.datetime) else _to_datetime(start_after)
            items = [i for i in items if _to_datetime(i.get("created_at")) and _to_datetime(i.get("created_at")) < sa]
        return items[:limit]

def validar_recurso_sugerido(recurso_id, validated_by=None, status="approved", comentarios=None):
    if status not in ("approved", "rejected", "pending"):
        raise ValueError("Estado inválido para recurso")
    data = {
        "status": status,
        "validated_by": validated_by,
        "comentarios": comentarios,
        "validated_at": datetime.datetime.now(tz)
    }
    db.collection("recursos_sugeridos").document(recurso_id).update(data)

    try:
        doc = db.collection("recursos_sugeridos").document(recurso_id).get()
        if doc.exists:
            recurso = doc.to_dict()
            creador = recurso.get("created_by")
            titulo = recurso.get("title", "tu recurso")
            if creador:
                mensaje = f"Tu recurso '{titulo}' fue {status}."
                extra = {"recurso_id": recurso_id, "status": status}
                guardar_notificacion(creador, mensaje, extra=extra)
    except Exception as e:
        print("[ERROR NOTIFICACION VALIDACION RECURSO]:", e)

    return recurso_id
