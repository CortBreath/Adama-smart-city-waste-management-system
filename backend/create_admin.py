from sqlalchemy import create_engine, text
from database import DATABASE_URL
from auth import get_password_hash

USERNAME = "admin"
PASSWORD = "CHANGE_ME_NOW"

engine = create_engine(DATABASE_URL)

password_hash = get_password_hash(PASSWORD)

sql = text("""
INSERT INTO users (username, password_hash, role, is_active)
VALUES (:username, :password_hash, 'admin', TRUE)
ON CONFLICT (username)
DO UPDATE SET
    password_hash = EXCLUDED.password_hash,
    role = 'admin',
    is_active = TRUE,
    updated_at = NOW()
""")

with engine.begin() as connection:
    connection.execute(
        sql,
        {
            "username": USERNAME,
            "password_hash": password_hash,
        },
    )

print("ADMIN USER CREATED/UPDATED")
print("Username:", USERNAME)
