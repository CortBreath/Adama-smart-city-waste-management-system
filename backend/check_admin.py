from sqlalchemy import create_engine, text
from database import DATABASE_URL

engine = create_engine(DATABASE_URL)

with engine.connect() as connection:
    result = connection.execute(
        text("SELECT username, role, is_active FROM users")
    )

    for row in result.mappings():
        print(
            "USERNAME:", row["username"],
            "| ROLE:", row["role"],
            "| ACTIVE:", row["is_active"]
        )
