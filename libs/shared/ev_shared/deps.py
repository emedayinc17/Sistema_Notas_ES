# libs/shared/ev_shared/deps.py
from typing import Callable, Dict, Any, Iterable

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text

from ev_shared.config import settings
from ev_shared.db import get_db_iam, get_db_grades, q
from ev_shared.security import decode_token

# === Bearer puro (sin OAuth2) ===
_bearer = HTTPBearer(auto_error=True)

def iam_db(db: Session = Depends(get_db_iam)) -> Session:
    return db

def grades_db(db: Session = Depends(get_db_grades)) -> Session:
    return db

def get_current_user(
    creds: HTTPAuthorizationCredentials = Security(_bearer),  # <- Security para que Swagger adjunte el token
    db: Session = Depends(get_db_iam),
) -> Dict[str, Any]:
    token = creds.credentials
    try:
        payload = decode_token(token)
        uid = int(payload.get("sub", 0))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sql = text(
        f"""
        SELECT u.id, u.usuario, u.correo, u.estado
        FROM {q(settings.DB_IAM_NAME, "usuario")} u
        WHERE u.id = :uid AND u.eliminado = 0
        LIMIT 1
        """
    )
    row = db.execute(sql, {"uid": uid}).mappings().first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
        )
    return dict(row)

def _in_clause(bind_name: str, values: Iterable[str]) -> str:
    items = list(values)
    if not items:
        return "(NULL)"
    return "(" + ", ".join(f":{bind_name}{i}" for i in range(len(items))) + ")"

def require_roles(*roles: str) -> Callable:
    if not roles:
        def _noop(user=Depends(get_current_user)):
            return True
        return _noop

    def _dep(
        user: Dict[str, Any] = Depends(get_current_user),
        db: Session = Depends(get_db_iam),
    ):
        placeholders = _in_clause("r", roles)
        sql = text(
            f"""
            SELECT 1
            FROM {q(settings.DB_IAM_NAME, "usuario_rol")} ur
            JOIN {q(settings.DB_IAM_NAME, "rol")} r ON r.id = ur.role_id
            WHERE ur.user_id = :uid AND r.nombre IN {placeholders}
            LIMIT 1
            """
        )
        params = {"uid": user["id"], **{f"r{i}": v for i, v in enumerate(roles)}}
        ok = db.execute(sql, params).first()
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requiere rol: {', '.join(roles)}",
            )
        return True

    return _dep
