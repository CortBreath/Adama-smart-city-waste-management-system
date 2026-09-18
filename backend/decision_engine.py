from sqlalchemy import text


COLLECTION_THRESHOLD = 90.0
CRITICAL_THRESHOLD = 95.0
WARNING_THRESHOLD = 60.0
CLEANUP_COMPLETE_THRESHOLD = 10.0
SMOKE_THRESHOLD = 2000
FIRE_TEMPERATURE_THRESHOLD = 60.0


def determine_fill_state(fill_level: float) -> str:
    """Determine the operational fill state of BIN-001."""

    if fill_level >= COLLECTION_THRESHOLD:
        return "FULL"

    if fill_level >= WARNING_THRESHOLD:
        return "WARNING"

    return "NORMAL"


def determine_severity(fill_level: float) -> str | None:
    """Determine alert severity when collection is required."""

    if fill_level >= CRITICAL_THRESHOLD:
        return "CRITICAL"

    if fill_level >= COLLECTION_THRESHOLD:
        return "HIGH"

    return None

def determine_environmental_condition(
    temperature: float | None,
    smoke_value: float | None,
    smoke_status: str | None,
) -> tuple[str, str | None]:
    """Determine environmental condition of the bin."""

    temperature_danger = (
        temperature is not None
        and temperature >= FIRE_TEMPERATURE_THRESHOLD
    )

    smoke_danger = (
        (
            smoke_value is not None
            and smoke_value > SMOKE_THRESHOLD
        )
        or
        (
            smoke_status is not None
            and smoke_status.upper() == "DANGER"
        )
    )

    if smoke_danger and temperature_danger:
        return "SMOKE_AND_HIGH_TEMPERATURE", "CRITICAL"

    if smoke_danger:
        return "SMOKE_DETECTED", "CRITICAL"

    if temperature_danger:
        return "HIGH_TEMPERATURE", "CRITICAL"

    return "NORMAL", None


def find_available_janitor(db):
    """Find an available janitor with a Telegram chat ID."""

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


def find_active_collection_alert(db, bin_id: str):
    """Find the current unresolved FULL_BIN alert."""

    return db.execute(
        text(
            """
            SELECT
                id,
                assigned_janitor_id,
                trigger_fill_level,
                cleanup_notification_sent
            FROM alerts
            WHERE bin_id = :bin_id
              AND alert_type = 'FULL_BIN'
              AND resolved_at IS NULL
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        {
            "bin_id": bin_id
        }
    ).mappings().first()


def evaluate_bin(
    db,
    bin_id: str,
    fill_level: float,
    temperature: float | None = None,
    smoke_value: float | None = None,
    smoke_status: str | None = None,
):
    """
    Main Decision Engine for BIN-001.

    Returns a decision dictionary describing
    what the system decided.
    """

    fill_level = float(fill_level)

    if temperature is not None:
        temperature = float(temperature)

    if smoke_value is not None:
        smoke_value = float(smoke_value)

    environmental_condition, environmental_severity = (
        determine_environmental_condition(
            temperature,
            smoke_value,
            smoke_status,
        )
    )

    # ---------------------------------------------------------
    # Only BIN-001 is operational.
    # ---------------------------------------------------------
    if bin_id != "BIN-001":
                return {
            "decision": "NO_ACTION",
            "state": "NORMAL",
            "severity": None,
            "janitor": None,
            "active_alert": None,
            "action": "NONE",
            "environmental_condition": environmental_condition,
            "environmental_severity": environmental_severity,
        }

    state = determine_fill_state(fill_level)

    active_alert = find_active_collection_alert(
        db,
        bin_id,
    )

    # ---------------------------------------------------------
    # CLEANUP SUCCESSFUL
    # ---------------------------------------------------------

    if active_alert and fill_level <= CLEANUP_COMPLETE_THRESHOLD:

        return {
            "decision": "CLEANUP_SUCCESSFUL",
            "state": "NORMAL",
            "severity": None,
            "janitor": None,
            "active_alert": active_alert,
            "action": "RESOLVE_ALERT",
            "environmental_condition": environmental_condition,
            "environmental_severity": environmental_severity,
        }

    # ---------------------------------------------------------
    # CLEANUP STILL INCOMPLETE
    # ---------------------------------------------------------

    if active_alert and fill_level > CLEANUP_COMPLETE_THRESHOLD:

        return {
            "decision": "CLEANUP_INCOMPLETE",
            "state": state,
            "severity": None,
            "janitor": None,
            "active_alert": active_alert,
            "action": "KEEP_ALERT_OPEN",
            "environmental_condition": environmental_condition,
            "environmental_severity": environmental_severity,
        }

    # ---------------------------------------------------------
    # NO ACTIVE ALERT + COLLECTION REQUIRED
    # ---------------------------------------------------------

    if not active_alert and fill_level >= COLLECTION_THRESHOLD:

        severity = determine_severity(fill_level)

        janitor = find_available_janitor(db)

        return {
            "decision": "COLLECTION_REQUIRED",
            "state": "FULL",
            "severity": severity,
            "janitor": janitor,
            "active_alert": None,
            "action": "CREATE_ALERT",
            "environmental_condition": environmental_condition,
            "environmental_severity": environmental_severity,
        }

    # ---------------------------------------------------------
    # NORMAL / WARNING
    # ---------------------------------------------------------

    return {
        "decision": "NO_ACTION",
        "state": state,
        "severity": None,
        "janitor": None,
        "active_alert": None,
        "action": "NONE",
        "environmental_condition": environmental_condition,
        "environmental_severity": environmental_severity,
    }