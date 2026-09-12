from sqlalchemy import create_engine, text
from database import DATABASE_URL

engine = create_engine(DATABASE_URL)

with engine.connect() as connection:
    result = connection.execute(
        text("SELECT to_regclass('public.users')")
    )
    print("USERS TABLE:", result.scalar())
