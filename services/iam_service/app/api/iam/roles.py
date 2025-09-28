from typing import Literal
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ev_shared.db import q
from ev_shared.config import settings
from ev_shared.deps import iam_db, require_roles

router = APIRouter(prefix="", tags=["roles"])
RolNombre = Literal["DOCENTE","PADRE","DIRECTIVO"]

@router.get("/usuarios/{user_id}/roles")
def roles_de_usuario(user_id: int, db: Session = Depends(iam_db), _=Depends(require_roles("DIRECTIVO"))):
    sql = text(f"""
        SELECT r.id, r.nombre
        FROM {q(settings.DB_IAM_NAME,'usuario_rol')} AS ur
        JOIN {q(settings.DB_IAM_NAME,'rol')} AS r ON r.id = ur.role_id
        WHERE ur.user_id = :uid
    """)
    return db.execute(sql, {"uid": user_id}).mappings().all()

class RolAssign(BaseModel):
    rol: RolNombre

@router.post("/usuarios/{user_id}/roles", status_code=201)
def asignar_rol(user_id: int, payload: RolAssign, db: Session = Depends(iam_db), _=Depends(require_roles("DIRECTIVO"))):
    sql = text(f"""
        INSERT IGNORE INTO {q(settings.DB_IAM_NAME,'usuario_rol')} (user_id, role_id)
        SELECT :uid, r.id FROM {q(settings.DB_IAM_NAME,'rol')} AS r WHERE r.nombre = :rol
    """)
    db.execute(sql, {"uid": user_id, "rol": payload.rol})
    db.commit()
    return {"ok": True}

@router.delete("/usuarios/{user_id}/roles/{rol}")
def quitar_rol(user_id: int, rol: RolNombre, db: Session = Depends(iam_db), _=Depends(require_roles("DIRECTIVO"))):
    sql = text(f"""
        DELETE ur FROM {q(settings.DB_IAM_NAME,'usuario_rol')} AS ur
        JOIN {q(settings.DB_IAM_NAME,'rol')} AS r ON r.id = ur.role_id
        WHERE ur.user_id = :uid AND r.nombre = :rol
    """)
    res = db.execute(sql, {"uid": user_id, "rol": rol})
    db.commit()
    return {"ok": True, "deleted": res.rowcount}
