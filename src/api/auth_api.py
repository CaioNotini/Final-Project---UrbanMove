from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from src.utils.logging_config import setup_logger

import jwt

from src.db.auth_db import get_user_by_username, create_user
from src.security.auth import (
    verify_password,
    create_access_token,
    oauth2_scheme,
    SECRET_KEY,
    ALGORITHM,
)

router = APIRouter(prefix="/auth", tags=["auth"])
logger = setup_logger("auth-api", "api.log")


class RegisterRequest(BaseModel):
    username: str
    password: str


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if username is None:
            logger.warning("Token validation failed: missing subject")
            raise credentials_exception

    except jwt.PyJWTError:
        logger.warning("Token validation failed: invalid JWT")
        raise credentials_exception

    user = get_user_by_username(username)

    if not user:
        logger.warning("Token validation failed: user not found | username=%s", username)
        raise credentials_exception

    if not user["is_active"]:
        logger.warning("Inactive user tried to authenticate | username=%s", username)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    logger.info("Authenticated user | username=%s | role=%s", user["username"], user["role"])
    return user


def require_admin(current_user=Depends(get_current_user)):
    if current_user["role"] != "admin":
        logger.warning(
            "Admin access denied | username=%s | role=%s",
            current_user["username"],
            current_user["role"],
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    logger.info("Admin access granted | username=%s", current_user["username"])
    return current_user


@router.post("/register")
def register(payload: RegisterRequest):
    logger.info("POST /auth/register | username=%s", payload.username)

    try:
        existing_user = get_user_by_username(payload.username)

        if existing_user:
            logger.warning("Register failed: user exists | username=%s", payload.username)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )

        user = create_user(
            username=payload.username,
            password=payload.password,
            role="user"
        )

        access_token = create_access_token({
            "sub": user["username"],
            "role": user["role"]
        })

        logger.info("User registered successfully | username=%s", user["username"])

        return {
            "message": "User created successfully",
            "access_token": access_token,
            "token_type": "bearer",
            "role": user["role"],
            "username": user["username"]
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Register failed unexpectedly | username=%s", payload.username)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    logger.info("POST /auth/login | username=%s", form_data.username)

    try:
        user = get_user_by_username(form_data.username)

        if not user:
            logger.warning("Login failed: user not found | username=%s", form_data.username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(form_data.password, user["password_hash"]):
            logger.warning("Login failed: invalid password | username=%s", form_data.username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user["is_active"]:
            logger.warning("Login failed: inactive user | username=%s", form_data.username)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )

        access_token = create_access_token({
            "sub": user["username"],
            "role": user["role"]
        })

        logger.info("Login success | username=%s | role=%s", user["username"], user["role"])

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": user["role"],
            "username": user["username"]
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Login failed unexpectedly | username=%s", form_data.username)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me")
def read_me(current_user=Depends(get_current_user)):
    logger.info("GET /auth/me | username=%s", current_user["username"])
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "role": current_user["role"],
        "is_active": current_user["is_active"],
        "created_at": current_user["created_at"]
    }


@router.get("/admin-test")
def admin_test(current_user=Depends(require_admin)):
    logger.info("GET /auth/admin-test | username=%s", current_user["username"])
    return {
        "message": "Admin access granted",
        "user": current_user["username"]
    }