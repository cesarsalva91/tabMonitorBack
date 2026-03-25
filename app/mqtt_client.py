import os
import json
import paho.mqtt.client as mqtt

from .state import upsert_device

BROKER_HOST = os.getenv("BROKER_HOST", "mosquitto")
BROKER_PORT = int(os.getenv("BROKER_PORT", "1883"))
TOPIC = os.getenv("MQTT_TOPIC", "dispositivos/estado")

client = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Conectado con código {rc}")
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        updated = upsert_device(payload)
        print(f"[MQTT] Dispositivo actualizado: {updated['id_dispositivo']}")
    except Exception as e:
        print(f"[MQTT] Error procesando mensaje: {e}")


client.on_connect = on_connect
client.on_message = on_message


def start_mqtt():
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_start()


def stop_mqtt():
    client.loop_stop()
    client.disconnect()