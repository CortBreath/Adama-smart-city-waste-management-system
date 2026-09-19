from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from auth_routes import router as auth_router
from auth import require_admin
from database import DATABASE_URL

# ============================================================
# DATABASE ENGINE
# ============================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Adama Smart City API",
    description="Smart Waste Management System API",
    version="1.0.0",
)
app.include_router(auth_router)


# ============================================================
# CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,
        allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://adama-smart-city-waste-management-sys.netlify.app",
        ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():
    return {
        "message": "Adama Smart City API is running"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }


# ============================================================
# DATABASE TEST
# ============================================================

@app.get("/api/db-test")
async def db_test():
    """
    Test the PostgreSQL database connection.
    """

    query = text(
        """
        SELECT
            id,
            bin_id,
            status,
            data_source,
            last_seen_at,
            created_at,
            updated_at
        FROM bins
        ORDER BY id
        LIMIT 1
        """
    )

    try:
        with engine.connect() as connection:

            result = connection.execute(query)

            row = result.mappings().first()

            if row is None:
                return {
                    "success": True,
                    "message": "Database connected, but no bins found.",
                    "row": None,
                }

            row_data = dict(row)

            # Convert datetime values to ISO strings.
            for key, value in row_data.items():

                if isinstance(value, datetime):
                    row_data[key] = value.isoformat()

            return {
                "success": True,
                "row": row_data,
            }

    except Exception as exc:

        print("=" * 60)
        print("DATABASE ERROR")
        print(repr(exc))
        print("=" * 60)

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {exc}",
        )


# ============================================================
# GET ALL BINS
# ============================================================

@app.get("/api/bins")
async def get_bins(
    current_user: dict = Depends(require_admin),
):
    """
    Return all bins and the latest telemetry reading
    for each bin.

    Bins without telemetry are still returned.
    """

    query = text(
        """
        SELECT
            b.bin_id,
            b.status,
            b.data_source,

            ST_Y(b.geom::geometry) AS latitude,
            ST_X(b.geom::geometry) AS longitude,

            r.fill_level_pct,
            r.fill_distance,
            r.temperature,
            r.smoke_value,
            r.smoke_status,
            r.human_distance,
            r.lid_status,
            r.system_status,
            r.recorded_at

        FROM bins AS b

        LEFT JOIN LATERAL (
            SELECT
                br.fill_level_pct,
                br.fill_distance,
                br.temperature,
                br.smoke_value,
                br.smoke_status,
                br.human_distance,
                br.lid_status,
                br.system_status,
                br.recorded_at

            FROM bin_readings AS br

            WHERE br.bin_id = b.bin_id

            ORDER BY br.recorded_at DESC

            LIMIT 1

        ) AS r ON TRUE

        ORDER BY b.bin_id
        """
    )

    try:

        with engine.connect() as connection:

            result = connection.execute(query)

            rows = result.mappings().all()

            bins = []

            for row in rows:

                bin_data = dict(row)

                # Convert timestamp to ISO format.
                if isinstance(
                    bin_data.get("recorded_at"),
                    datetime,
                ):
                    bin_data["recorded_at"] = (
                        bin_data["recorded_at"].isoformat()
                    )

                bins.append(bin_data)

            return bins

    except SQLAlchemyError as exc:

        print("=" * 60)
        print("DATABASE ERROR - /api/bins")
        print(repr(exc))
        print("=" * 60)

        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve bins: {exc}",
        )


# ============================================================
# GET ONE BIN
# ============================================================

@app.get("/api/bins/{bin_id}")
async def get_bin(
    bin_id: str,
    current_user: dict = Depends(require_admin),
):
    """
    Return one bin and its latest telemetry reading.
    """

    query = text(
        """
        SELECT
            b.bin_id,
            b.status,
            b.data_source,

            ST_Y(b.geom::geometry) AS latitude,
            ST_X(b.geom::geometry) AS longitude,

            r.fill_level_pct,
            r.fill_distance,
            r.temperature,
            r.smoke_value,
            r.smoke_status,
            r.human_distance,
            r.lid_status,
            r.system_status,
            r.recorded_at

        FROM bins AS b

        LEFT JOIN LATERAL (
            SELECT
                br.fill_level_pct,
                br.fill_distance,
                br.temperature,
                br.smoke_value,
                br.smoke_status,
                br.human_distance,
                br.lid_status,
                br.system_status,
                br.recorded_at

            FROM bin_readings AS br

            WHERE br.bin_id = b.bin_id

            ORDER BY br.recorded_at DESC

            LIMIT 1

        ) AS r ON TRUE

        WHERE b.bin_id = :bin_id
        """
    )

    try:

        with engine.connect() as connection:

            result = connection.execute(
                query,
                {
                    "bin_id": bin_id,
                },
            )

            row = result.mappings().first()

            if row is None:

                raise HTTPException(
                    status_code=404,
                    detail=f"Bin {bin_id} not found.",
                )

            bin_data = dict(row)

            if isinstance(
                bin_data.get("recorded_at"),
                datetime,
            ):
                bin_data["recorded_at"] = (
                    bin_data["recorded_at"].isoformat()
                )

            return bin_data

    except HTTPException:
        raise

    except SQLAlchemyError as exc:

        print("=" * 60)
        print("DATABASE ERROR - /api/bins/{bin_id}")
        print(repr(exc))
        print("=" * 60)

        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve bin: {exc}",
        )


# ============================================================
# GET BIN READING HISTORY
# ============================================================

@app.get("/api/bins/{bin_id}/readings")
async def get_bin_readings(
    bin_id: str,
    range: str = "all",
    limit: int = 1000,
    current_user: dict = Depends(require_admin),
):
    """
    Return telemetry history for one bin.

    Supported ranges:
        all  - all available readings
        1h   - last 1 hour
        6h   - last 6 hours
        24h  - last 24 hours
    """

    # Protect API from unreasonable values.
    if limit < 1:
        limit = 1

    if limit > 1000:
        limit = 1000

    # Convert the allowed range into a number of hours.
    range_hours = {
        "1h": 1,
        "6h": 6,
        "24h": 24,
    }.get(range)

    query = text(
        """
        SELECT
            id,
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

        FROM bin_readings

        WHERE bin_id = :bin_id

         AND (
         CAST(:range_hours AS INTEGER) IS NULL
        OR recorded_at >= NOW()
        - (CAST(:range_hours AS INTEGER) * INTERVAL '1 hour')
)
        ORDER BY recorded_at ASC

        LIMIT :limit
        """
    )

    try:

        with engine.connect() as connection:

            result = connection.execute(
                query,
                {
                    "bin_id": bin_id,
                    "range_hours": range_hours,
                    "limit": limit,
                },
            )

            rows = result.mappings().all()

            readings = []

            for row in rows:

                reading = dict(row)

                # Convert timestamp to ISO format.
                if isinstance(
                    reading.get("recorded_at"),
                    datetime,
                ):
                    reading["recorded_at"] = (
                        reading["recorded_at"].isoformat()
                    )

                readings.append(reading)

            return readings

    except SQLAlchemyError as exc:

        print("=" * 60)
        print("DATABASE ERROR - /api/bins/{bin_id}/readings")
        print(repr(exc))
        print("=" * 60)

        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve readings: {exc}",
        )

    # ============================================================
# GET ALERT HISTORY
# ============================================================

@app.get("/api/alerts")
async def get_alerts(
    limit: int = 100,
    current_user: dict = Depends(require_admin),
):
    """
    Return alert history for the operational bin BIN-001.

    Newest alerts are returned first.
    """

    # Protect API from unreasonable values.
    if limit < 1:
        limit = 1

    if limit > 100:
        limit = 100

    query = text(
        """
        SELECT
            a.id,
            a.bin_id,
            a.alert_type,
            a.severity,
            a.message,
            a.created_at,
            a.resolved_at,
            a.assigned_janitor_id,
            j.name AS janitor_name,
            a.trigger_fill_level,
            a.cleanup_notification_sent

        FROM alerts AS a

        LEFT JOIN janitors AS j
            ON j.id = a.assigned_janitor_id

        WHERE a.bin_id = 'BIN-001'

        ORDER BY a.created_at DESC

        LIMIT :limit
        """
    )

    try:

        with engine.connect() as connection:

            result = connection.execute(
                query,
                {
                    "limit": limit,
                },
            )

            rows = result.mappings().all()

            alerts = []

            for row in rows:

                alert = dict(row)

                # Convert timestamps to ISO format.
                if isinstance(
                    alert.get("created_at"),
                    datetime,
                ):
                    alert["created_at"] = (
                        alert["created_at"].isoformat()
                    )

                if isinstance(
                    alert.get("resolved_at"),
                    datetime,
                ):
                    alert["resolved_at"] = (
                        alert["resolved_at"].isoformat()
                    )

                # Convert numeric database value to float.
                if alert.get("trigger_fill_level") is not None:
                    alert["trigger_fill_level"] = float(
                        alert["trigger_fill_level"]
                    )

                # Convenient status for the frontend.
                alert["status"] = (
                    "RESOLVED"
                    if alert["resolved_at"] is not None
                    else "OPEN"
                )

                alerts.append(alert)

            return alerts

    except SQLAlchemyError as exc:

        print("=" * 60)
        print("DATABASE ERROR - /api/alerts")
        print(repr(exc))
        print("=" * 60)

        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve alerts: {exc}",
        )


# ============================================================
# GET ACTIVE ALERTS
# ============================================================

@app.get("/api/alerts/active")
async def get_active_alerts(
    current_user: dict = Depends(require_admin),
):
    """
    Return currently open alerts for BIN-001.
    """

    query = text(
        """
        SELECT
            a.id,
            a.bin_id,
            a.alert_type,
            a.severity,
            a.message,
            a.created_at,
            a.assigned_janitor_id,
            j.name AS janitor_name,
            a.trigger_fill_level,
            a.cleanup_notification_sent

        FROM alerts AS a

        LEFT JOIN janitors AS j
            ON j.id = a.assigned_janitor_id

        WHERE a.bin_id = 'BIN-001'
          AND a.resolved_at IS NULL

        ORDER BY a.created_at DESC
        """
    )

    try:

        with engine.connect() as connection:

            result = connection.execute(query)

            rows = result.mappings().all()

            alerts = []

            for row in rows:

                alert = dict(row)

                if isinstance(
                    alert.get("created_at"),
                    datetime,
                ):
                    alert["created_at"] = (
                        alert["created_at"].isoformat()
                    )

                if alert.get("trigger_fill_level") is not None:
                    alert["trigger_fill_level"] = float(
                        alert["trigger_fill_level"]
                    )

                alert["status"] = "OPEN"

                alerts.append(alert)

            return alerts

    except SQLAlchemyError as exc:

        print("=" * 60)
        print("DATABASE ERROR - /api/alerts/active")
        print(repr(exc))
        print("=" * 60)

        raise HTTPException(
            status_code=500,
            detail=f"Unable to retrieve active alerts: {exc}",
        )


# ============================================================
# STARTUP MESSAGE
# ============================================================

@app.on_event("startup")
async def startup_event():

    print("=" * 60)
    print("Adama Smart City API")
    print("=" * 60)
    print("Database: PostgreSQL/PostGIS")
    print("MQTT broker: broker.emqx.io")
    print("API: http://127.0.0.1:8000")
    print("Docs: http://127.0.0.1:8000/docs")
    print("=" * 60)