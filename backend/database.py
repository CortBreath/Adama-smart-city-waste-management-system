from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

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