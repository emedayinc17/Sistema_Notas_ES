from datetime import datetime, timedelta
from hashlib import sha256
from typing import List, Optional, Union

import jwt
from passlib.context import CryptContext

from ev_shared.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(p: str) -> str:
    return pwd_context.hash(p)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(
    sub: Union[int, str],
    minutes: Optional[int] = None,
    roles: Optional[List[str]] = None,
) -> str:
    """Emite un JWT HS256 con claims básicos."""
    exp_min = minutes or getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    payload = {
        "sub": str(sub),  # <-- siempre string para evitar InvalidSubjectError
        "exp": datetime.utcnow() + timedelta(minutes=exp_min),
    }
    if roles:
        payload["roles"] = roles
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def create_jwt(
    *, sub: str, roles: Optional[List[str]] = None, expires_minutes: Optional[int] = None
) -> str:
    """Wrapper compatible con tu código previo."""
    return create_access_token(sub=sub, minutes=expires_minutes, roles=roles)


def decode_token(token: str) -> dict:
    """Valida firma + exp + alg y retorna payload."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])


def secret_fingerprint() -> str:
    """Útil para verificar que todos los servicios usan el mismo secreto."""
    return sha256(settings.JWT_SECRET.encode("utf-8")).hexdigest()[:12]
