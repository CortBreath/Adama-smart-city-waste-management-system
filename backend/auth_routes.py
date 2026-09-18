from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
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


# ============================================================
# FRONTEND LOGIN REQUEST
# ============================================================

class LoginRequest(BaseModel):
    username: str
    password: str


# ============================================================
# SHARED LOGIN LOGIC
# ============================================================

def authenticate_user(
    username: str,
    password: str,
):
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
            {
                "username": username,
            },
        )

        user = result.mappings().first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    if not verify_password(
        password,
        user["password_hash"],
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
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


# ============================================================
# FRONTEND JSON LOGIN
# ============================================================

@router.post("/login")
async def login(
    credentials: LoginRequest,
):
    """
    Login endpoint used by the frontend.

    Accepts JSON:
    {
        "username": "...",
        "password": "..."
    }
    """

    return authenticate_user(
        username=credentials.username,
        password=credentials.password,
    )


# ============================================================
# SWAGGER / OAUTH2 LOGIN
# ============================================================

@router.post("/login/oauth2")
async def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    OAuth2-compatible login endpoint for Swagger.

    Accepts form data:
        username
        password
    """

    return authenticate_user(
        username=form_data.username,
        password=form_data.password,
    )