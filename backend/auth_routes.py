from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from database import DATABASE_URL
from auth import verify_password, create_access_token

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(credentials: LoginRequest):

    query = text("""
        SELECT
            username,
            password_hash,
            role,
            is_active
        FROM users
        WHERE username = :username
    """)

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {"username": credentials.username},
        )

        user = result.mappings().first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    if not verify_password(
        credentials.password,
        user["password_hash"],
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        username=user["username"],
        role=user["role"],
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user["username"],
        "role": user["role"],
    }
