import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

# On Render, DATABASE_URL is set in the service's Environment tab.
# Locally, it is not set, so the fallback below is used.
_env_url = os.getenv("DATABASE_URL")

if _env_url:
    # Render gives postgres:// or postgresql://
    # SQLAlchemy needs the psycopg (v3) driver name in the URL.
    if _env_url.startswith("postgres://"):
        _env_url = _env_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif _env_url.startswith("postgresql://"):
        _env_url = _env_url.replace("postgresql://", "postgresql+psycopg://", 1)
    DATABASE_URL = _env_url
else:
    # Local development default
    DATABASE_URL = (
        "postgresql+psycopg://"
        "adama_admin:adama_password@"
        "localhost:5432/"
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
# SESSION
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)