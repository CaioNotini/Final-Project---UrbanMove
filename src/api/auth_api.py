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


@router.post("/register")
def register(payload: RegisterRequest):
    logger.info("POST /auth/register | username=%s", payload.username)

    try:
        existing_user = get_user_by_username(payload.username)

        if existing_user:
            logger.warning("Register failed: user exists | %s", payload.username)
            raise HTTPException(status_code=400, detail="Username already exists")

        user = create_user(payload.username, payload.password, role="user")

        token = create_access_token({"sub": user["username"], "role": user["role"]})

        logger.info("User registered successfully | %s", payload.username)

        return {
            "message": "User created successfully",
            "access_token": token,
            "token_type": "bearer",
            "role": user["role"],
            "username": user["username"]
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Register failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    logger.info("POST /auth/login | username=%s", form_data.username)

    try:
        user = get_user_by_username(form_data.username)

        if not user or not verify_password(form_data.password, user["password_hash"]):
            logger.warning("Login failed | username=%s", form_data.username)
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_access_token({"sub": user["username"], "role": user["role"]})

        logger.info("Login success | username=%s", form_data.username)

        return {
            "access_token": token,
            "token_type": "bearer",
            "role": user["role"],
            "username": user["username"]
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Login failed unexpectedly")
        raise HTTPException(status_code=500, detail="Internal server error")