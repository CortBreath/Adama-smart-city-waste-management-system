from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from auth_routes import router as auth_router
from auth import require_admin


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DATABASE_URL = (
    "postgresql+psycopg://"
    "adama_admin:adama_password"
    "@localhost:5432/"
    "adama_smart_city"
)


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
    limit: int = 100,
    current_user: dict = Depends(require_admin),
):
    """
    Return telemetry history for one bin.
    """

    # Protect API from unreasonable values.
    if limit < 1:
        limit = 1

    if limit > 1000:
        limit = 1000

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

        ORDER BY recorded_at DESC

        LIMIT :limit
        """
    )

    try:

        with engine.connect() as connection:

            result = connection.execute(
                query,
                {
                    "bin_id": bin_id,
                    "limit": limit,
                },
            )

            rows = result.mappings().all()

            readings = []

            for row in rows:

                # Convert SQLAlchemy RowMapping to a normal dictionary.
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