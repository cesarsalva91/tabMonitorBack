from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.mqtt_client import iniciar_mqtt
from app.state import obtener_estado_dispositivos, obtener_mensajes_mqtt


app = FastAPI(
    title="Backend MQTT Dispositivos",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mqtt_client = None


@app.on_event("startup")
def startup_event():
    global mqtt_client
    mqtt_client = iniciar_mqtt()


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Backend MQTT funcionando"
    }


@app.get("/estado-dispositivos")
def estado_dispositivos():
    return obtener_estado_dispositivos()


@app.get("/mensajes-mqtt")
def mensajes_mqtt(limit: int = 100):
    return obtener_mensajes_mqtt(limit)