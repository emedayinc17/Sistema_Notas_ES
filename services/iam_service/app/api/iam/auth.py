from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta
from typing import Optional
import hashlib, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from passlib.context import CryptContext

from ev_shared.db import q
from ev_shared.config import settings
# ✅ importa los deps correctos (alias)
from ev_shared.deps import iam_db, get_current_user

router = APIRouter(tags=["auth"])
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginPayload(BaseModel):
    username: str
    password: str

def _password_matches(raw: str, stored_hash: str) -> bool:
    if not stored_hash:
        return False
    if stored_hash.startswith("$2"):
        try:
            return pwd_ctx.verify(raw, stored_hash)
        except Exception:
            return False
    sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return sha.lower() == stored_hash.lower()

def _create_jwt(sub: int, minutes: Optional[int] = None) -> str:
    exp_min = minutes or getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    payload = {"sub": str(sub), "exp": datetime.utcnow() + timedelta(minutes=exp_min)}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


@router.post("/login")
def login(payload: LoginPayload, db: Session = Depends(iam_db)):
    sql = text(f"""
        SELECT u.id, u.hash_contrasena
        FROM {q(settings.DB_IAM_NAME, 'usuario')} AS u
        WHERE u.usuario = :username AND u.eliminado = 0
        LIMIT 1
    """)
    row = db.execute(sql, {"username": payload.username}).mappings().first()
    if not row or not _password_matches(payload.password, row["hash_contrasena"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    token = _create_jwt(int(row["id"]))
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me")
def me(user = Depends(get_current_user)):
    return user
