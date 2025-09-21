# app/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, mapped_column
# ⬇️ usa los generators del módulo db
from app.db import get_db_iam, get_db_grades
from app.security.jwt import verify_token
from app.models.iam import Usuario, UsuarioRol, Rol

bearer = HTTPBearer(auto_error=True)

def iam_db():
    # delega al generator del módulo db
    yield from get_db_iam()

def grades_db():
    # delega al generator del módulo db
    yield from get_db_grades()

def get_current_user(
    cred: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(iam_db),
):
    try:
        payload = verify_token(cred.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = int(payload.get("sub"))
    user = db.get(Usuario, user_id)
    if not user or user.eliminado or user.estado != 1:
        raise HTTPException(status_code=401, detail="Usuario deshabilitado o no encontrado")
    roles = [r[0] for r in db.query(Rol.nombre).join(UsuarioRol, Rol.id == UsuarioRol.role_id).filter(UsuarioRol.user_id == user_id)]
    return {"id": user.id, "usuario": user.usuario, "roles": roles}

def require_roles(*allowed):
    def _checker(user=Depends(get_current_user)):
        if not set(user["roles"]).intersection(set(allowed)):
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return _checker
