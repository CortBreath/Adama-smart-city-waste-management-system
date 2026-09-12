import json
import random
import time

import paho.mqtt.client as mqtt


# =========================================================
# MQTT CONFIGURATION
# =========================================================

MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883

BINS = [
    "BIN-002",
    "BIN-003",
]

INTERVAL_SECONDS = 10


# =========================================================
# CREATE MQTT CLIENT
# =========================================================

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="adama-smart-city-simulator"
)


# =========================================================
# CONNECT
# =========================================================

print("Connecting to MQTT broker...")

client.connect(
    MQTT_BROKER,
    MQTT_PORT,
    60
)

client.loop_start()

print("Connected to:", MQTT_BROKER)
print("Simulating:", ", ".join(BINS))
print("Publishing every", INTERVAL_SECONDS, "seconds")
print()


# =========================================================
# SIMULATION
# =========================================================

try:

    while True:

        for bin_id in BINS:

            # -------------------------------------------------
            # Simulated fill level
            # -------------------------------------------------

            fill_level = random.uniform(10, 95)

            # Distance decreases as bin becomes full.
            fill_distance = 450 - (fill_level * 3.5)

            # -------------------------------------------------
            # Simulated temperature
            # -------------------------------------------------

            temperature = random.uniform(18, 30)

            # -------------------------------------------------
            # Simulated smoke
            # -------------------------------------------------

            smoke_value = random.uniform(0, 10)

            if smoke_value > 7:
                smoke_status = "WARNING"
            else:
                smoke_status = "NORMAL"

            # -------------------------------------------------
            # Simulated human proximity
            # -------------------------------------------------

            human_distance = random.uniform(50, 200)

            # -------------------------------------------------
            # Simulated lid
            # -------------------------------------------------

            lid_status = random.choice([
                "OPEN",
                "CLOSED"
            ])

            # -------------------------------------------------
            # System status
            # -------------------------------------------------

            if smoke_status == "WARNING":
                system_status = "WARNING"
            elif fill_level >= 90:
                system_status = "FULL"
            else:
                system_status = "NORMAL"

            # -------------------------------------------------
            # MQTT payload
            # -------------------------------------------------

            payload = {
                "bin_id": bin_id,

                "fill_level_pct": round(fill_level, 2),
                "fill_distance": round(fill_distance, 2),

                "temperature": round(temperature, 2),

                "smoke_value": round(smoke_value, 2),
                "smoke_status": smoke_status,

                "human_distance": round(human_distance, 2),

                "lid_status": lid_status,

                "system_status": system_status,
            }

            topic = (
                f"adama-smart-city/"
                f"bins/{bin_id}/telemetry"
            )

            message = json.dumps(payload)

            result = client.publish(
                topic,
                message
            )

            result.wait_for_publish()

            print(
                f"{bin_id} → "
                f"fill={payload['fill_level_pct']}% | "
                f"temp={payload['temperature']}°C | "
                f"smoke={payload['smoke_status']} | "
                f"lid={payload['lid_status']}"
            )

        print()

        time.sleep(INTERVAL_SECONDS)


except KeyboardInterrupt:

    print()
    print("Simulator stopped.")


finally:

    client.loop_stop()
    client.disconnect()