import json
import time
import paho.mqtt.client as mqtt


MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
TOPIC = "adama-smart-city/bins/BIN-001/telemetry"


payload = {
    "bin_id": "BIN-001",
    "fill_level_pct": 90,
    "fill_distance": 250.00,
    "temperature": 14.30,
    "smoke_value": 0,
    "smoke_status": "NORMAL",
    "human_distance": 93.81,
    "lid_status": "CLOSED",
    "system_status": "NORMAL"
}


connected = False


def on_connect(client, userdata, flags, reason_code, properties=None):
    global connected

    if reason_code == 0:
        connected = True
        print("Connected to MQTT broker:", MQTT_BROKER)
    else:
        print("MQTT connection failed:", reason_code)


client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="adama-smart-city-test-publisher"
)

client.on_connect = on_connect

print("Connecting to MQTT broker...")

client.connect(
    MQTT_BROKER,
    MQTT_PORT,
    60
)

client.loop_start()

# Give Paho time to establish the connection
for _ in range(20):
    if connected:
        break
    time.sleep(0.5)

if not connected:
    print("ERROR: MQTT connection was not established.")
    client.loop_stop()
    client.disconnect()
    raise SystemExit(1)


message = json.dumps(payload)

result = client.publish(
    TOPIC,
    message,
    qos=0
)

result.wait_for_publish()

print("Telemetry published!")
print("Topic:", TOPIC)
print("Payload:", message)

client.loop_stop()
client.disconnect()