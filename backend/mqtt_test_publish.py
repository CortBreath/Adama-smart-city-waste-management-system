import json
import time
import paho.mqtt.client as mqtt


MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883

TOPIC = "adama-smart-city/bins/BIN-001/telemetry"


payload = {
    "bin_id": "BIN-001",
    "fill_level_pct": 0,
    "fill_distance": 403.47,
    "temperature": 14.30,
    "smoke_value": 0,
    "smoke_status": "NORMAL",
    "human_distance": 93.81,
    "lid_status": "CLOSED",
    "system_status": "NORMAL"
}


client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="adama-smart-city-test-publisher"
)


print("Connecting to MQTT broker...")

client.connect(
    MQTT_BROKER,
    MQTT_PORT,
    60
)

client.loop_start()

time.sleep(1)

message = json.dumps(payload)

result = client.publish(
    TOPIC,
    message
)

result.wait_for_publish()

print("Telemetry published!")
print("Topic:", TOPIC)
print("Payload:", message)

client.loop_stop()
client.disconnect()