import json
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

DISPOSITIVOS_FILE = DATA_DIR / "dispositivos.json"
ESTADO_FILE = DATA_DIR / "estado_dispositivos.json"
MENSAJES_FILE = DATA_DIR / "mensajes_mqtt.jsonl"

TIEMPO_OFFLINE_MINUTOS = 15


def cargar_json(path: Path, default):
    if not path.exists():
        return default

    try:
        with open(path, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except json.JSONDecodeError:
        return default


def guardar_json(path: Path, data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as archivo:
        json.dump(data, archivo, indent=4, ensure_ascii=False)


def cargar_dispositivos():
    return cargar_json(DISPOSITIVOS_FILE, {})


def fecha_actual():
    return datetime.now().isoformat(timespec="seconds")


def normalizar_payload_estado(payload: dict):
    return {
        "fase1": payload.get("f1", 0),
        "fase2": payload.get("f2", 0),
        "fase3": payload.get("f3", 0)
    }


def enriquecer_mensaje(payload: dict, topic: str):
    dispositivos = cargar_dispositivos()

    id_dispositivo = payload.get("id_dispositivo")
    info_dispositivo = dispositivos.get(id_dispositivo, {})

    return {
        "timestamp_recepcion": fecha_actual(),
        "topic": topic,
        "id_dispositivo": id_dispositivo,
        "nombre": info_dispositivo.get("nombre", "Dispositivo desconocido"),
        "coordenadas": info_dispositivo.get("coordenadas"),
        "payload": payload
    }


def persistir_mensaje(mensaje: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(MENSAJES_FILE, "a", encoding="utf-8") as archivo:
        archivo.write(json.dumps(mensaje, ensure_ascii=False) + "\n")


def actualizar_estado_dispositivo(mensaje: dict):
    estados = cargar_json(ESTADO_FILE, {})

    id_dispositivo = mensaje.get("id_dispositivo")
    if not id_dispositivo:
        return

    estado_actual = estados.get(id_dispositivo, {})

    estado_actual["id_dispositivo"] = id_dispositivo
    estado_actual["nombre"] = mensaje.get("nombre")
    estado_actual["coordenadas"] = mensaje.get("coordenadas")
    estado_actual["ultimo_mensaje"] = mensaje.get("timestamp_recepcion")
    estado_actual["ultimo_topic"] = mensaje.get("topic")

    topic = mensaje.get("topic")
    payload = mensaje.get("payload", {})

    if topic == "dispositivos/estado":
        estado_actual["ultimo_estado_fases"] = normalizar_payload_estado(payload)
        estado_actual["ultimo_estado_recibido"] = mensaje.get("timestamp_recepcion")

    elif topic == "dispositivos/online":
        estado_actual["ultimo_online"] = mensaje.get("timestamp_recepcion")
        estado_actual["hora_dispositivo"] = payload.get("hora")

    elif topic == "dispositivos/hora":
        estado_actual["ultima_hora_reportada"] = payload.get("hora")
        estado_actual["ultima_hora_recibida"] = mensaje.get("timestamp_recepcion")

    estados[id_dispositivo] = estado_actual
    guardar_json(ESTADO_FILE, estados)


def calcular_estado_conexion(ultimo_online: str | None, ultimo_estado_recibido: str | None):
    fechas_validas = []

    for fecha_texto in [ultimo_online, ultimo_estado_recibido]:
        if not fecha_texto:
            continue

        try:
            fechas_validas.append(datetime.fromisoformat(fecha_texto))
        except ValueError:
            continue

    if not fechas_validas:
        return "offline"

    ultima_comunicacion = max(fechas_validas)
    diferencia = datetime.now() - ultima_comunicacion

    if diferencia > timedelta(minutes=TIEMPO_OFFLINE_MINUTOS):
        return "offline"

    return "online"


def procesar_mensaje_mqtt(topic: str, payload: dict):
    mensaje_enriquecido = enriquecer_mensaje(payload, topic)

    persistir_mensaje(mensaje_enriquecido)

    if topic in [
        "dispositivos/estado",
        "dispositivos/online",
        "dispositivos/hora"
    ]:
        actualizar_estado_dispositivo(mensaje_enriquecido)

    return mensaje_enriquecido


def obtener_estado_dispositivos():
    estados = cargar_json(ESTADO_FILE, {})

    for id_dispositivo, estado in estados.items():
        ultimo_online = estado.get("ultimo_online")
        ultimo_estado_recibido = estado.get("ultimo_estado_recibido")

        estado["estado_conexion"] = calcular_estado_conexion(
            ultimo_online,
            ultimo_estado_recibido
        )

        if estado["estado_conexion"] == "offline":
            estado["ultimo_estado_fases"] = {
                "fase1": 0,
                "fase2": 0,
                "fase3": 0
            }

        estado["offline_despues_minutos"] = TIEMPO_OFFLINE_MINUTOS

    return estados


def obtener_mensajes_mqtt(limit: int = 100):
    if not MENSAJES_FILE.exists():
        return []

    with open(MENSAJES_FILE, "r", encoding="utf-8") as archivo:
        lineas = archivo.readlines()

    mensajes = []
    for linea in lineas[-limit:]:
        try:
            mensajes.append(json.loads(linea))
        except json.JSONDecodeError:
            continue

    return mensajes