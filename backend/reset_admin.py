from sqlalchemy import create_engine, text
from database import DATABASE_URL
from auth import get_password_hash

engine = create_engine(DATABASE_URL)

password = input("Enter NEW admin password: ")

if len(password) < 8:
    raise SystemExit("Password must be at least 8 characters.")

password_hash = get_password_hash(password)

with engine.begin() as connection:
    result = connection.execute(
        text("""
            UPDATE users
            SET password_hash = :password_hash,
                role = 'admin',
                is_active = TRUE,
                updated_at = NOW()
            WHERE username = 'admin'
        """),
        {"password_hash": password_hash},
    )

    if result.rowcount != 1:
        raise SystemExit("Admin user was not found.")

print("ADMIN PASSWORD RESET SUCCESSFULLY")
