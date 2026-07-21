import hashlib
import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from backend.core.config import settings
from backend.core.exceptions import AuthenticationError
from backend.core.logging import get_logger

logger = get_logger(__name__)


def hash_password(password: str) -> str:
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return salt.hex() + ":" + key.hex()


def verify_password(password: str, hashed: str) -> bool:
    salt_hex, key_hex = hashed.split(":")
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(key_hex)
    computed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return computed == expected


def create_access_token(user_id: UUID, role: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expires,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")
