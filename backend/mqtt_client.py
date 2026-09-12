import json
import time

import paho.mqtt.client as mqtt
from sqlalchemy import text

from database import SessionLocal


# =========================================================
# MQTT CONFIGURATION
# =========================================================

MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883

MQTT_TOPIC = "adama-smart-city/bins/+/telemetry"

MQTT_CLIENT_ID = "adama-smart-city-backend"


# =========================================================
# MQTT CONNECT
# =========================================================

def on_connect(client, userdata, flags, reason_code, properties=None):

    if reason_code == 0:
        print("Connected to MQTT broker:", MQTT_BROKER)

        client.subscribe(MQTT_TOPIC)

        print("Subscribed to:", MQTT_TOPIC)

    else:
        print("MQTT connection failed:", reason_code)


# =========================================================
# MQTT MESSAGE
# =========================================================

def on_message(client, userdata, msg):

    print()
    print("MQTT message received")
    print("Topic:", msg.topic)

    try:

        payload = json.loads(msg.payload.decode("utf-8"))

        print("Payload:", payload)

        bin_id = payload.get("bin_id")

        if not bin_id:
            print("ERROR: bin_id missing")
            return

        # -------------------------------------------------
        # Save telemetry
        # -------------------------------------------------

        db = SessionLocal()

        try:

            query = text("""
                INSERT INTO bin_readings (
                    bin_id,
                    recorded_at,
                    fill_level_pct,
                    fill_distance,
                    temperature,
                    smoke_value,
                    smoke_status,
                    human_distance,
                    lid_status,
                    system_status
                )
                VALUES (
                    :bin_id,
                    now(),
                    :fill_level_pct,
                    :fill_distance,
                    :temperature,
                    :smoke_value,
                    :smoke_status,
                    :human_distance,
                    :lid_status,
                    :system_status
                )
            """)

            db.execute(
                query,
                {
                    "bin_id": bin_id,

                    "fill_level_pct": payload.get(
    "fill_level_pct",
    payload.get("fill_level")
),
                    "fill_distance": payload.get("fill_distance"),

                    "temperature": payload.get("temperature"),

                    "smoke_value": payload.get("smoke_value"),
                    "smoke_status": payload.get("smoke_status"),

                    "human_distance": payload.get("human_distance"),

                    "lid_status": payload.get("lid_status"),
                    "system_status": payload.get("system_status"),
                }
            )

            db.commit()

            print("Telemetry saved for:", bin_id)

        except Exception as e:

            db.rollback()

            print("Database error:", e)

        finally:

            db.close()

    except json.JSONDecodeError:

        print("ERROR: MQTT payload is not valid JSON")

    except Exception as e:

        print("MQTT processing error:", e)


# =========================================================
# CREATE MQTT CLIENT
# =========================================================

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id=MQTT_CLIENT_ID
)

client.on_connect = on_connect
client.on_message = on_message


# =========================================================
# CONNECT
# =========================================================

print("Connecting to MQTT broker...")

client.connect(
    MQTT_BROKER,
    MQTT_PORT,
    60
)


# =========================================================
# START MQTT LOOP
# =========================================================

print("MQTT client running...")

client.loop_forever()