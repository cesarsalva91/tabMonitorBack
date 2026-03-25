from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .mqtt_client import start_mqtt, stop_mqtt
from .state import ensure_data_file, read_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_data_file()
    start_mqtt()
    yield
    stop_mqtt()


app = FastAPI(title="Monitoreo de Dispositivos", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/dispositivos")
def get_dispositivos():
    return read_data()


@app.get("/dispositivos/{device_id}")
def get_dispositivo(device_id: str):
    data = read_data()
    device = data.get(device_id)

    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")

    return device