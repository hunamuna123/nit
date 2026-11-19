from datetime import timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings
from app.db import utcnow

_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _hasher.verify(password, hashed)
    except Exception:
        return False


def create_session_token(user_id: int) -> str:
    s = get_settings()
    now = utcnow()
    payload = {"sub": str(user_id), "iat": now, "exp": now + timedelta(days=s.session_days)}
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def read_session_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
