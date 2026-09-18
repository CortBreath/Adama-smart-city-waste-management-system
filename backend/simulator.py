import json
import time

import paho.mqtt.client as mqtt


MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883

# BIN-002 and BIN-003 are simulation-only bins.
# They do NOT create operational alerts or Telegram notifications.
BINS = {
    "BIN-002": {
        "fill_levels": [
            20, 30, 40, 50, 60, 70, 80, 90, 95,
            85, 75, 65, 55, 45, 35, 25
        ],
        "index": 0,
        "temperature": 24.0,
    },

    "BIN-003": {
        "fill_levels": [
            35, 45, 55, 65, 75, 85, 92, 98,
            88, 78, 68, 58, 48, 38
        ],
        "index": 0,
        "temperature": 26.0,
    },
}

INTERVAL_SECONDS = 5


def get_system_status(fill_level):
    if fill_level >= 90:
        return "FULL"
    elif fill_level >= 60:
        return "WARNING"
    else:
        return "NORMAL"


def publish_bin(client, bin_id, config):
    fill_level = config["fill_levels"][config["index"]]

    # Move to the next filling level for the next reading.
    config["index"] = (config["index"] + 1) % len(config["fill_levels"])

    # Convert filling percentage to approximate ultrasonic distance.
    # 30 cm = empty, 5 cm = full.
    distance = 30 - ((fill_level / 100) * 25)

    payload = {
        "bin_id": bin_id,
        "fill_level": fill_level,
        "fill_level_pct": fill_level,
        "fill_distance": round(distance, 2),
        "temperature": config["temperature"],
        "smoke_status": "NORMAL",
        "lid_status": "CLOSED",
        "system_status": get_system_status(fill_level),
        "data_source": "SIMULATED",
        "timestamp": int(time.time()),
    }

    topic = f"adama-smart-city/bins/{bin_id}/telemetry"

    result = client.publish(
        topic,
        json.dumps(payload),
        qos=0,
        retain=False,
    )

    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(
            f"{bin_id} -> "
            f"{fill_level}% | "
            f"{payload['system_status']}"
        )
    else:
        print(
            f"Failed to publish {bin_id}: "
            f"MQTT error {result.rc}"
        )


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to MQTT broker: {MQTT_BROKER}")
    else:
        print(f"MQTT connection failed with code: {rc}")


# KEEP YOUR CURRENT FIXED CLIENT ID.
client = mqtt.Client(
    client_id="adama-smart-city-simulator"
)

client.on_connect = on_connect

print("Connecting to MQTT broker...")

client.connect(
    MQTT_BROKER,
    MQTT_PORT,
    60,
)

client.loop_start()

print("Simulator running...")
print("BIN-002 and BIN-003 filling levels are simulated progressively.")
print("BIN-002 and BIN-003 do not generate operational alerts.")

try:
    while True:
        for bin_id, config in BINS.items():
            publish_bin(client, bin_id, config)

        time.sleep(INTERVAL_SECONDS)

except KeyboardInterrupt:
    print("Stopping simulator...")

finally:
    client.loop_stop()
    client.disconnect()