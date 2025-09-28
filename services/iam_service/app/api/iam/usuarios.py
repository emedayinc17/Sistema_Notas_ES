from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import text
from ev_shared.db import q
from ev_shared.config import settings
from ev_shared.deps import iam_db, require_roles

router = APIRouter(prefix="", tags=["usuarios"])

class UsuarioCreate(BaseModel):
    usuario: str
    correo: EmailStr | None = None
    password: str

class UsuarioUpdate(BaseModel):
    correo: EmailStr | None = None
    estado: int | None = None
    password: str | None = None

@router.get("/usuarios")
def listar_usuarios(limit: int = 50, offset: int = 0, db: Session = Depends(iam_db), _=Depends(require_roles("DIRECTIVO"))):
    sql = text(f"""
        SELECT u.id, u.usuario, u.correo, u.estado
        FROM {q(settings.DB_IAM_NAME,'usuario')} AS u
        WHERE u.eliminado = 0
        ORDER BY u.id
        LIMIT :limit OFFSET :offset
    """)
    return db.execute(sql, {"limit": limit, "offset": offset}).mappings().all()

@router.get("/usuarios/{user_id}")
def obtener_usuario(user_id: int, db: Session = Depends(iam_db), _=Depends(require_roles("DIRECTIVO"))):
    sql = text(f"""
        SELECT u.id, u.usuario, u.correo, u.estado
        FROM {q(settings.DB_IAM_NAME,'usuario')} AS u
        WHERE u.id = :id AND u.eliminado = 0
        LIMIT 1
    """)
    row = db.execute(sql, {"id": user_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return row

@router.post("/usuarios", status_code=201)
def crear_usuario(payload: UsuarioCreate, db: Session = Depends(iam_db), _=Depends(require_roles("DIRECTIVO"))):
    import hashlib
    sha = hashlib.sha256(payload.password.encode("utf-8")).hexdigest()
    sql = text(f"""
        INSERT INTO {q(settings.DB_IAM_NAME,'usuario')} (usuario, hash_contrasena, correo, estado, eliminado)
        VALUES (:usuario, :hash, :correo, 1, 0)
    """)
    db.execute(sql, {"usuario": payload.usuario, "hash": sha, "correo": str(payload.correo) if payload.correo else None})
    db.commit()
    return {"ok": True}

@router.put("/usuarios/{user_id}")
def actualizar_usuario(user_id: int, payload: UsuarioUpdate, db: Session = Depends(iam_db), _=Depends(require_roles("DIRECTIVO"))):
    sets = []
    params = {"id": user_id}
    if payload.correo is not None:
        sets.append("correo = :correo"); params["correo"] = str(payload.correo)
    if payload.estado is not None:
        sets.append("estado = :estado"); params["estado"] = int(payload.estado)
    if payload.password:
        import hashlib
        sets.append("hash_contrasena = :hash"); params["hash"] = hashlib.sha256(payload.password.encode("utf-8")).hexdigest()
    if not sets:
        return {"ok": True, "updated": 0}
    sql = text(f"""
        UPDATE {q(settings.DB_IAM_NAME,'usuario')} SET {", ".join(sets)}
        WHERE id = :id AND eliminado = 0
    """)
    res = db.execute(sql, params)
    db.commit()
    return {"ok": True, "updated": res.rowcount}

@router.delete("/usuarios/{user_id}")
def eliminar_usuario(user_id: int, db: Session = Depends(iam_db), _=Depends(require_roles("DIRECTIVO"))):
    sql = text(f"""
        UPDATE {q(settings.DB_IAM_NAME,'usuario')} SET eliminado = 1
        WHERE id = :id AND eliminado = 0
    """)
    res = db.execute(sql, {"id": user_id})
    db.commit()
    return {"ok": True, "deleted": res.rowcount}
