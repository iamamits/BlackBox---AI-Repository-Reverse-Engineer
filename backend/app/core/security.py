"""BlackBox — Cryptographic security, password hashing, and token handling."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any, Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

# Secret key for HMAC token signing (falls back to a persistent or generated key)
AUTH_SECRET_KEY = os.environ.get("AUTH_SECRET_KEY", "blackbox-super-secret-key-change-in-prod-2026")
TOKEN_EXPIRATION_SECONDS = 60 * 60 * 24 * 7  # 7 days

security_bearer = HTTPBearer(auto_error=False)


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using PBKDF2-HMAC-SHA256 with a unique salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    )
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Safely verify a plaintext password against a stored PBKDF2 hash."""
    try:
        salt, key_hex = hashed_password.split("$", 1)
        key = bytes.fromhex(key_hex)
        computed_key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000,
        )
        return hmac.compare_digest(key, computed_key)
    except Exception:
        return False


def create_access_token(payload_data: dict[str, Any], expires_delta_seconds: int = TOKEN_EXPIRATION_SECONDS) -> str:
    """Create a URL-safe signed JWT-like token using HMAC-SHA256."""
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = dict(payload_data)
    payload["iat"] = now
    payload["exp"] = now + expires_delta_seconds

    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode("utf-8")).decode("utf-8").rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8").rstrip("=")
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(AUTH_SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Verify and decode a signed access token. Returns None if invalid or expired."""
    try:
        parts = token.strip().split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(AUTH_SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()

        # Add back base64 padding
        padding = "=" * (-len(sig_b64) % 4)
        actual_sig = base64.urlsafe_b64decode(sig_b64 + padding)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload_padding = "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + payload_padding).decode("utf-8"))

        # Check expiration
        now = int(time.time())
        if payload.get("exp", 0) < now:
            return None

        return payload
    except Exception:
        return None


async def get_optional_user(
    auth: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db: AsyncSession = Depends(get_db),
) -> Optional[Any]:
    """Dependency that extracts the authenticated user if Bearer token is provided, or returns None."""
    if not auth or not auth.credentials:
        return None

    payload = decode_access_token(auth.credentials)
    if not payload or "sub" not in payload:
        return None

    from app.core.models import User

    try:
        user_id = int(payload["sub"])
        result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
        return result.scalar_one_or_none()
    except Exception:
        return None


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Dependency that requires a valid authenticated user, raising 401 if unauthenticated."""
    user = await get_optional_user(auth=auth, db=db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
