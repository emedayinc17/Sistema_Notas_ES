# app/security/jwt.py
import os, time, hashlib, jwt
from typing import List

JWT_SECRET = os.getenv("JWT_SECRET", "dev")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
JWT_EXP_MIN = int(os.getenv("JWT_EXP_MIN", "480"))

def sha2_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def create_token(user_id: int, username: str, roles: List[str]) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "preferred_username": username,
        "roles": roles,
        "iat": now,
        "exp": now + 60 * JWT_EXP_MIN,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def verify_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
