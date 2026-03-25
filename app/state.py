import json
from pathlib import Path
from threading import Lock

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "dispositivos.json"

_lock = Lock()


def ensure_data_file():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("{}", encoding="utf-8")


def read_data() -> dict:
    ensure_data_file()
    with _lock:
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}


def write_data(data: dict) -> None:
    ensure_data_file()
    temp_file = DATA_FILE.with_suffix(".tmp")

    with _lock:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_file.replace(DATA_FILE)


def fase_ok(value) -> bool:
    try:
        return float(value) > 180
    except (TypeError, ValueError):
        return False


def build_phase_flags(device: dict) -> dict:
    device["fase1_activa"] = fase_ok(device.get("fase1"))
    device["fase2_activa"] = fase_ok(device.get("fase2"))
    device["fase3_activa"] = fase_ok(device.get("fase3"))
    return device


def upsert_device(payload: dict) -> dict:
    device_id = payload.get("id_dispositivo")
    if not device_id:
        raise ValueError("Falta 'id_dispositivo' en el payload.")

    with _lock:
        ensure_data_file()

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {}

        existing = data.get(device_id)

        if existing is None:
            if "coordenadas" not in payload:
                raise ValueError("Falta 'coordenadas' para un dispositivo nuevo.")

            existing = {
                "id_dispositivo": device_id,
                "coordenadas": payload["coordenadas"],
                "fase1": payload.get("fase1", 0),
                "fase2": payload.get("fase2", 0),
                "fase3": payload.get("fase3", 0),
            }
        else:
            if "coordenadas" in payload:
                existing["coordenadas"] = payload["coordenadas"]
            if "fase1" in payload:
                existing["fase1"] = payload["fase1"]
            if "fase2" in payload:
                existing["fase2"] = payload["fase2"]
            if "fase3" in payload:
                existing["fase3"] = payload["fase3"]

        existing = build_phase_flags(existing)
        data[device_id] = existing

        temp_file = DATA_FILE.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_file.replace(DATA_FILE)

        return existing