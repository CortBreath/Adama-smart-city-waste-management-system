import json

import paho.mqtt.client as mqtt
from sqlalchemy import text

from database import SessionLocal
from decision_engine import evaluate_bin
from telegram import send_telegram_message


# ============================================================
# MQTT CONFIGURATION
# ============================================================

MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883

MQTT_TOPIC = "adama-smart-city/bins/+/telemetry"


# ============================================================
# OPERATIONAL BIN CONFIGURATION
# ============================================================

# Only this bin is connected to the operational
# collection/Telegram workflow.
OPERATIONAL_BIN_ID = "BIN-001"


# ============================================================
# ENVIRONMENTAL ALERT HELPERS
# ============================================================

def find_active_environmental_alert(db, bin_id: str):
    """
    Find the current unresolved environmental alert
    for the operational bin.
    """

    return db.execute(
        text(
            """
            SELECT
                id,
                alert_type,
                severity,
                assigned_janitor_id,
                cleanup_notification_sent
            FROM alerts
            WHERE bin_id = :bin_id
              AND alert_type IN (
                  'SMOKE_DETECTED',
                  'HIGH_TEMPERATURE',
                  'SMOKE_AND_HIGH_TEMPERATURE'
              )
              AND resolved_at IS NULL
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        {
            "bin_id": bin_id
        }
    ).mappings().first()


def get_janitor_by_id(db, janitor_id):
    """
    Get janitor information by ID.
    """

    if janitor_id is None:
        return None

    return db.execute(
        text(
            """
            SELECT
                id,
                name,
                telegram_chat_id
            FROM janitors
            WHERE id = :janitor_id
            """
        ),
        {
            "janitor_id": janitor_id
        }
    ).mappings().first()


def find_environmental_janitor(db, collection_decision=None):
    """
    Find a janitor for an environmental alert.

    If a collection decision already assigned a janitor,
    use that same janitor so one physical bin does not
    unnecessarily involve two different people.
    """

    # --------------------------------------------------------
    # First preference:
    # Use the janitor already assigned to the collection alert.
    # --------------------------------------------------------

    if collection_decision:
        collection_janitor = collection_decision.get("janitor")

        if collection_janitor:
            return collection_janitor

        active_alert = collection_decision.get("active_alert")

        if active_alert:
            assigned_janitor_id = active_alert.get(
                "assigned_janitor_id"
            )

            if assigned_janitor_id:
                janitor = get_janitor_by_id(
                    db,
                    assigned_janitor_id
                )

                if janitor:
                    return janitor

    # --------------------------------------------------------
    # Second preference:
    # Find another available janitor.
    # --------------------------------------------------------

    return db.execute(
        text(
            """
            SELECT
                id,
                name,
                telegram_chat_id
            FROM janitors
            WHERE status = 'AVAILABLE'
              AND telegram_chat_id IS NOT NULL
            ORDER BY id
            LIMIT 1
            """
        )
    ).mappings().first()


def process_environmental_alert(
    db,
    bin_id: str,
    temperature: float | None,
    smoke_value: float | None,
    smoke_status: str | None,
    collection_decision=None,
):
    """
    Process environmental conditions using ONLY:
        - temperature
        - smoke value
        - smoke status

    Environmental alerts are independent from
    FULL_BIN collection alerts.
    """

    # --------------------------------------------------------
    # Only BIN-001 is operational.
    # --------------------------------------------------------

    if bin_id != OPERATIONAL_BIN_ID:
        return

    # --------------------------------------------------------
    # Ask Decision Engine for environmental condition.
    # --------------------------------------------------------

    environmental_condition = (
        collection_decision.get(
            "environmental_condition"
        )
        if collection_decision
        else "NORMAL"
    )

    environmental_severity = (
        collection_decision.get(
            "environmental_severity"
        )
        if collection_decision
        else None
    )

    # --------------------------------------------------------
    # Find existing environmental alert.
    # --------------------------------------------------------

    active_alert = find_active_environmental_alert(
        db,
        bin_id
    )

    # ========================================================
    # NORMAL ENVIRONMENT
    # ========================================================

    if environmental_condition == "NORMAL":

        if active_alert is None:
            return

        # ----------------------------------------------------
        # Environmental condition returned to normal.
        # Resolve environmental alert only.
        # ----------------------------------------------------

        alert_id = active_alert["id"]
        janitor_id = active_alert["assigned_janitor_id"]

        db.execute(
            text(
                """
                UPDATE alerts
                SET resolved_at = now()
                WHERE id = :alert_id
                  AND resolved_at IS NULL
                """
            ),
            {
                "alert_id": alert_id
            }
        )

        db.commit()

        print(
            f"Environmental alert #{alert_id} "
            f"RESOLVED for {bin_id}. "
            f"Temperature/smoke returned to normal."
        )

        # ----------------------------------------------------
        # Notify assigned janitor.
        # ----------------------------------------------------

        janitor = get_janitor_by_id(
            db,
            janitor_id
        )

        if janitor and janitor["telegram_chat_id"]:

            message = (
                "✅ Environmental Condition Normal\n\n"
                f"🗑️ Bin: {bin_id}\n"
                f"🌡️ Temperature: "
                f"{float(temperature):.1f}°C\n"
                f"💨 Smoke value: "
                f"{float(smoke_value):.1f}\n"
                f"📡 Smoke status: "
                f"{smoke_status or 'UNKNOWN'}\n\n"
                "The environmental condition has "
                "returned to normal.\n\n"
                "📍 Adama Smart City"
            )

            sent = send_telegram_message(
                str(janitor["telegram_chat_id"]),
                message
            )

            if sent:
                print(
                    "Environmental recovery "
                    "Telegram notification sent."
                )
            else:
                print(
                    "WARNING: Environmental recovery "
                    "Telegram notification failed."
                )

        return

    # ========================================================
    # ENVIRONMENTAL DANGER ALREADY ACTIVE
    # ========================================================

    if active_alert is not None:

        print(
            f"Environmental alert "
            f"#{active_alert['id']} already OPEN "
            f"for {bin_id}. "
            f"Condition: {environmental_condition}"
        )

        # ----------------------------------------------------
        # Do not create duplicate alerts.
        # Do not send repeated Telegram messages.
        # ----------------------------------------------------

        return

    # ========================================================
    # NEW ENVIRONMENTAL ALERT
    # ========================================================

    janitor = find_environmental_janitor(
        db,
        collection_decision
    )

    if environmental_condition == "SMOKE_DETECTED":

        condition_message = (
            "Smoke has been detected inside the bin."
        )

    elif environmental_condition == "HIGH_TEMPERATURE":

        condition_message = (
            "The bin temperature is dangerously high."
        )

    elif environmental_condition == "SMOKE_AND_HIGH_TEMPERATURE":

        condition_message = (
            "Smoke and dangerously high temperature "
            "have been detected inside the bin."
        )

    else:

        condition_message = (
            "An environmental danger condition "
            "has been detected."
        )

    # --------------------------------------------------------
    # Build Telegram message.
    # --------------------------------------------------------

    temperature_text = (
        f"{float(temperature):.1f}°C"
        if temperature is not None
        else "N/A"
    )

    smoke_text = (
        f"{float(smoke_value):.1f}"
        if smoke_value is not None
        else "N/A"
    )

    message = (
        "🔥 Adama Smart City — Environmental Alert\n\n"
        f"🗑️ Bin: {bin_id}\n"
        f"🚨 Condition: {environmental_condition}\n"
        f"⚠️ Priority: {environmental_severity}\n\n"
        f"🌡️ Temperature: {temperature_text}\n"
        f"💨 Smoke value: {smoke_text}\n"
        f"📡 Smoke status: "
        f"{smoke_status or 'UNKNOWN'}\n\n"
        f"⚠️ {condition_message}\n\n"
        "Please inspect the bin and take the "
        "appropriate safety action.\n\n"
        "📍 Adama Smart City"
    )

    # ========================================================
    # CREATE ENVIRONMENTAL ALERT
    # ========================================================

    assigned_janitor_id = (
        janitor["id"]
        if janitor
        else None
    )

    result = db.execute(
        text(
            """
            INSERT INTO alerts (
                bin_id,
                alert_type,
                severity,
                message,
                assigned_janitor_id,
                trigger_fill_level,
                cleanup_notification_sent
            )
            VALUES (
                :bin_id,
                :alert_type,
                :severity,
                :message,
                :assigned_janitor_id,
                NULL,
                FALSE
            )
            RETURNING id
            """
        ),
        {
            "bin_id": bin_id,
            "alert_type": environmental_condition,
            "severity": environmental_severity,
            "message": message,
            "assigned_janitor_id": assigned_janitor_id,
        }
    )

    alert_id = result.scalar_one()

    db.commit()

    print(
        f"Created environmental "
        f"{environmental_severity} alert "
        f"#{alert_id} for {bin_id}"
    )

    # --------------------------------------------------------
    # Show assigned janitor.
    # --------------------------------------------------------

    if janitor:

        print(
            f"Environmental alert assigned to: "
            f"{janitor['name']} "
            f"(ID {janitor['id']})"
        )

    else:

        print(
            f"WARNING: No janitor available for "
            f"environmental alert #{alert_id}"
        )

        return

    # ========================================================
    # SEND ENVIRONMENTAL TELEGRAM
    # ========================================================

    if janitor["telegram_chat_id"]:

        sent = send_telegram_message(
            str(janitor["telegram_chat_id"]),
            message
        )

        if sent:

            db.execute(
                text(
                    """
                    UPDATE alerts
                    SET cleanup_notification_sent = TRUE
                    WHERE id = :alert_id
                    """
                ),
                {
                    "alert_id": alert_id
                }
            )

            db.commit()

            print(
                "Environmental Telegram "
                "notification sent successfully."
            )

        else:

            print(
                "WARNING: Environmental Telegram "
                "notification failed."
            )

    else:

        print(
            "WARNING: Assigned janitor does not have "
            "Telegram configured."
        )


# ============================================================
# PROCESS BIN ALERT / COLLECTION WORKFLOW
# ============================================================

def process_bin_alert(
    db,
    bin_id: str,
    fill_level: float,
    temperature: float | None = None,
    smoke_value: float | None = None,
    smoke_status: str | None = None,
):
    """
    Process operational decisions for BIN-001.

    Existing collection/cleanup workflow is preserved.
    Environmental processing is handled separately.
    """

    # ---------------------------------------------------------
    # Only BIN-001 is operational.
    # ---------------------------------------------------------

    if bin_id != OPERATIONAL_BIN_ID:
        return

    try:

        fill_level = float(fill_level)

    except (TypeError, ValueError):

        print(
            f"Invalid fill level for {bin_id}: {fill_level}"
        )

        return

    # ---------------------------------------------------------
    # Ask the Decision Engine what to do.
    # ---------------------------------------------------------

    decision = evaluate_bin(
        db=db,
        bin_id=bin_id,
        fill_level=fill_level,
        temperature=temperature,
        smoke_value=smoke_value,
        smoke_status=smoke_status,
    )

    decision_type = decision["decision"]

    print(
        f"Decision Engine: "
        f"bin={bin_id}, "
        f"fill={fill_level:.1f}%, "
        f"state={decision.get('state')}, "
        f"decision={decision_type}"
    )

    # =========================================================
    # ENVIRONMENTAL PROCESSING
    # =========================================================
    #
    # This is independent of the fill-level decision.
    # It uses ONLY temperature and smoke information.
    #
    # The collection decision is passed in so that, when
    # possible, an already-assigned collection janitor can
    # also receive the environmental warning.
    # =========================================================

    process_environmental_alert(
        db=db,
        bin_id=bin_id,
        temperature=temperature,
        smoke_value=smoke_value,
        smoke_status=smoke_status,
        collection_decision=decision,
    )

    # =========================================================
    # NO ACTION
    # =========================================================

    if decision_type == "NO_ACTION":
        return

    # =========================================================
    # NEW COLLECTION REQUIRED
    # =========================================================

    if decision_type == "COLLECTION_REQUIRED":

        severity = decision["severity"]
        janitor = decision["janitor"]

        if janitor is None:

            print(
                f"No available janitor for {bin_id}. "
                f"Collection alert will not be assigned."
            )

            return

        message = (
            "🚛 Adama Smart City — Collection Alert\n\n"
            f"🗑️ Bin: {bin_id}\n"
            f"📊 Fill level: {fill_level:.1f}%\n"
            f"🚨 Priority: {severity}\n\n"
            "Please collect this bin.\n\n"
            "📍 Adama Smart City"
        )

        # -----------------------------------------------------
        # Create alert using raw SQL.
        # -----------------------------------------------------

        result = db.execute(
            text(
                """
                INSERT INTO alerts (
                    bin_id,
                    alert_type,
                    severity,
                    message,
                    assigned_janitor_id,
                    trigger_fill_level,
                    cleanup_notification_sent
                )
                VALUES (
                    :bin_id,
                    'FULL_BIN',
                    :severity,
                    :message,
                    :assigned_janitor_id,
                    :trigger_fill_level,
                    FALSE
                )
                RETURNING id
                """
            ),
            {
                "bin_id": bin_id,
                "severity": severity,
                "message": message,
                "assigned_janitor_id": janitor["id"],
                "trigger_fill_level": fill_level,
            }
        )

        alert_id = result.scalar_one()

        # -----------------------------------------------------
        # Reserve the janitor.
        # -----------------------------------------------------

        db.execute(
            text(
                """
                UPDATE janitors
                SET status = 'BUSY',
                    updated_at = now()
                WHERE id = :janitor_id
                  AND status = 'AVAILABLE'
                """
            ),
            {
                "janitor_id": janitor["id"]
            }
        )

        db.commit()

        print(
            f"Created {severity} alert "
            f"#{alert_id} for {bin_id}"
        )

        print(
            f"Assigned janitor: "
            f"{janitor['name']} "
            f"(ID {janitor['id']})"
        )

        # -----------------------------------------------------
        # Send collection Telegram.
        # -----------------------------------------------------

        if janitor["telegram_chat_id"]:

            sent = send_telegram_message(
                str(janitor["telegram_chat_id"]),
                message
            )

            if sent:

                print(
                    "Telegram notification sent successfully."
                )

            else:

                print(
                    "WARNING: Telegram notification failed."
                )

        return

    # =========================================================
    # CLEANUP INCOMPLETE
    # =========================================================

    if decision_type == "CLEANUP_INCOMPLETE":

        alert = decision["active_alert"]

        if alert is None:
            return

        # -----------------------------------------------------
        # Only send the incomplete notification once.
        # -----------------------------------------------------

        if not alert["cleanup_notification_sent"]:

            janitor = None

            if alert["assigned_janitor_id"]:

                janitor = db.execute(
                    text(
                        """
                        SELECT
                            name,
                            telegram_chat_id
                        FROM janitors
                        WHERE id = :janitor_id
                        """
                    ),
                    {
                        "janitor_id":
                            alert["assigned_janitor_id"]
                    }
                ).mappings().first()

            if janitor and janitor["telegram_chat_id"]:

                previous_fill = (
                    float(alert["trigger_fill_level"])
                    if alert["trigger_fill_level"] is not None
                    else 0.0
                )

                message = (
                    "⚠️ Collection Incomplete\n\n"
                    f"🗑️ Bin: {bin_id}\n"
                    f"📊 Previous fill: "
                    f"{previous_fill:.1f}%\n"
                    f"📦 Current fill: "
                    f"{fill_level:.1f}%\n\n"
                    f"Approximately {fill_level:.1f}% "
                    "of waste remains.\n"
                    "Please clean the bin properly.\n\n"
                    "📍 Adama Smart City"
                )

                sent = send_telegram_message(
                    str(janitor["telegram_chat_id"]),
                    message
                )

                if sent:

                    db.execute(
                        text(
                            """
                            UPDATE alerts
                            SET cleanup_notification_sent = TRUE
                            WHERE id = :alert_id
                            """
                        ),
                        {
                            "alert_id": alert["id"]
                        }
                    )

                    db.commit()

                    print(
                        f"Alert #{alert['id']} remains OPEN. "
                        f"{fill_level:.1f}% remains in the bin."
                    )

                else:

                    print(
                        "WARNING: Incomplete cleanup "
                        "Telegram notification failed."
                    )

            else:

                print(
                    "WARNING: Assigned janitor does not have "
                    "Telegram configured."
                )

        return

    # =========================================================
    # CLEANUP SUCCESSFUL
    # =========================================================

    if decision_type == "CLEANUP_SUCCESSFUL":

        alert = decision["active_alert"]

        if alert is None:
            return

        alert_id = alert["id"]
        janitor_id = alert["assigned_janitor_id"]

        # -----------------------------------------------------
        # Resolve the collection alert.
        # -----------------------------------------------------

        db.execute(
            text(
                """
                UPDATE alerts
                SET resolved_at = now()
                WHERE id = :alert_id
                  AND resolved_at IS NULL
                """
            ),
            {
                "alert_id": alert_id
            }
        )

        # -----------------------------------------------------
        # Make the assigned janitor available again.
        # -----------------------------------------------------

        if janitor_id:

            db.execute(
                text(
                    """
                    UPDATE janitors
                    SET status = 'AVAILABLE',
                        updated_at = now()
                    WHERE id = :janitor_id
                    """
                ),
                {
                    "janitor_id": janitor_id
                }
            )

        db.commit()

        # -----------------------------------------------------
        # Get janitor information for Telegram.
        # -----------------------------------------------------

        janitor = None

        if janitor_id:

            janitor = db.execute(
                text(
                    """
                    SELECT
                        name,
                        telegram_chat_id
                    FROM janitors
                    WHERE id = :janitor_id
                    """
                ),
                {
                    "janitor_id": janitor_id
                }
            ).mappings().first()

        # -----------------------------------------------------
        # Send successful cleanup notification.
        # -----------------------------------------------------

        if janitor and janitor["telegram_chat_id"]:

            previous_fill = (
                float(alert["trigger_fill_level"])
                if alert["trigger_fill_level"] is not None
                else 0.0
            )

            message = (
                "✅ Collection Completed\n\n"
                f"🗑️ Bin: {bin_id}\n"
                f"📊 Previous fill: "
                f"{previous_fill:.1f}%\n"
                f"📉 Current fill: "
                f"{fill_level:.1f}%\n\n"
                "The bin has been successfully cleaned.\n\n"
                "📍 Adama Smart City"
            )

            sent = send_telegram_message(
                str(janitor["telegram_chat_id"]),
                message
            )

            if sent:

                print(
                    "Telegram cleanup completion "
                    "notification sent successfully."
                )

            else:

                print(
                    "WARNING: Cleanup completion "
                    "Telegram notification failed."
                )

        else:

            print(
                "WARNING: Assigned janitor does not have "
                "Telegram configured."
            )

        print(
            f"Alert #{alert_id} automatically RESOLVED "
            f"for {bin_id} at {fill_level:.1f}%."
        )

        return


# ============================================================
# MQTT CONNECT CALLBACK
# ============================================================

def on_connect(
    client,
    userdata,
    flags,
    reason_code,
    properties=None
):

    if reason_code == 0:

        print(
            "Connected to MQTT broker:",
            MQTT_BROKER
        )

        client.subscribe(MQTT_TOPIC)

        print(
            "Subscribed to:",
            MQTT_TOPIC
        )

    else:

        print(
            "MQTT connection failed:",
            reason_code
        )


# ============================================================
# MQTT MESSAGE CALLBACK
# ============================================================

def on_message(
    client,
    userdata,
    msg
):

    print()
    print("MQTT message received")
    print("Topic:", msg.topic)

    # ========================================================
    # DECODE JSON
    # ========================================================

    try:

        payload = json.loads(
            msg.payload.decode("utf-8")
        )

        print(
            "Payload:",
            payload
        )

    except json.JSONDecodeError:

        print(
            "ERROR: MQTT payload is not valid JSON"
        )

        return

    # ========================================================
    # GET BIN ID
    # ========================================================

    bin_id = payload.get("bin_id")

    if not bin_id:

        print(
            "ERROR: bin_id missing"
        )

        return

    # ========================================================
    # GET FILL LEVEL
    #
    # Wokwi uses:
    #
    #     fill_level
    #
    # Backend also supports:
    #
    #     fill_level_pct
    # ========================================================

    fill_level = payload.get(
        "fill_level_pct",
        payload.get("fill_level")
    )

    if fill_level is None:

        print(
            f"ERROR: fill level missing for {bin_id}"
        )

        return

    # ========================================================
    # OPEN DATABASE SESSION
    # ========================================================

    db = SessionLocal()

    try:

        # ====================================================
        # SAVE TELEMETRY
        # ====================================================

        query = text(
            """
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
            """
        )

        db.execute(
            query,
            {
                "bin_id": bin_id,

                "fill_level_pct": fill_level,

                "fill_distance":
                    payload.get("fill_distance"),

                "temperature":
                    payload.get("temperature"),

                "smoke_value":
                    payload.get("smoke_value"),

                "smoke_status":
                    payload.get("smoke_status"),

                "human_distance":
                    payload.get("human_distance"),

                "lid_status":
                    payload.get("lid_status"),

                "system_status":
                    payload.get("system_status"),
            }
        )

        db.commit()

        print(
            "Telemetry saved for:",
            bin_id
        )

        # ====================================================
        # PROCESS ALERT / CLEANUP WORKFLOW
        # ====================================================

        process_bin_alert(
            db,
            bin_id,
            fill_level,
            payload.get("temperature"),
            payload.get("smoke_value"),
            payload.get("smoke_status"),
        )

    except Exception as e:

        db.rollback()

        print(
            "Database error:",
            e
        )

    finally:

        db.close()


# ============================================================
# CREATE MQTT CLIENT
# ============================================================

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="adama-smart-city-backend"
)


# ============================================================
# REGISTER CALLBACKS
# ============================================================

client.on_connect = on_connect
client.on_message = on_message


# ============================================================
# START MQTT
# ============================================================

print(
    "Connecting to MQTT broker..."
)

client.connect(
    MQTT_BROKER,
    MQTT_PORT,
    60
)

print(
    "MQTT client running..."
)


# ============================================================
# KEEP MQTT RUNNING
# ============================================================

client.loop_forever()