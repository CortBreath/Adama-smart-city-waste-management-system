from sqlalchemy import create_engine, text
from database import DATABASE_URL
from auth import verify_password

engine = create_engine(DATABASE_URL)

with engine.connect() as connection:
    user = connection.execute(
        text("""
            SELECT username, password_hash, role, is_active
            FROM users
            WHERE username = 'admin'
        """)
    ).mappings().first()

if user is None:
    print("ADMIN USER NOT FOUND")
else:
    print("USERNAME:", user["username"])
    print("ROLE:", user["role"])
    print("ACTIVE:", user["is_active"])
    print("HASH EXISTS:", bool(user["password_hash"]))
    print("HASH PREFIX:", user["password_hash"][:7])
    
    password = input("Enter admin password for verification: ")
    print("PASSWORD MATCH:", verify_password(password, user["password_hash"]))
