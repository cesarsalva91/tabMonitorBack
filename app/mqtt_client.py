import json
import paho.mqtt.client as mqtt

from app.state import procesar_mensaje_mqtt


MQTT_BROKER = "host.docker.internal"
MQTT_PORT = 1883
MQTT_TOPIC = "dispositivos/#"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT conectado correctamente")
        client.subscribe(MQTT_TOPIC)
        print(f"Suscripto a: {MQTT_TOPIC}")
    else:
        print(f"Error conectando a MQTT. Código: {rc}")


def on_message(client, userdata, msg):
    topic = msg.topic

    try:
        payload_texto = msg.payload.decode("utf-8")
        payload_json = json.loads(payload_texto)

        mensaje = procesar_mensaje_mqtt(topic, payload_json)

        print("Mensaje MQTT recibido:")
        print(json.dumps(mensaje, indent=4, ensure_ascii=False))

    except json.JSONDecodeError:
        print(f"Mensaje no JSON recibido en {topic}: {msg.payload.decode('utf-8', errors='ignore')}")

    except Exception as e:
        print(f"Error procesando mensaje MQTT: {e}")


def iniciar_mqtt():
    client = mqtt.Client(client_id="backend-mqtt-listener")

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    return client