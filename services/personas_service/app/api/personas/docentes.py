from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ev_shared.db import q
from ev_shared.config import settings
from ev_shared.deps import grades_db, get_current_user, require_roles

router = APIRouter(prefix="", tags=["docentes"])

class DocenteCreate(BaseModel):
    usuario_iam_id: int
    nombre_completo: str
    estado: int | None = 1

class DocenteUpdate(BaseModel):
    nombre_completo: str | None = None
    estado: int | None = None

@router.get("/docentes")
def listar_docentes(limit: int = 50, offset: int = 0, db: Session = Depends(grades_db), _=Depends(get_current_user)):
    sql = text(f"""
        SELECT d.id, d.usuario_iam_id, d.nombre_completo, d.estado
        FROM {q(settings.DB_GRADES_NAME,'docente')} AS d
        WHERE d.eliminado = 0
        ORDER BY d.id DESC
        LIMIT :limit OFFSET :offset
    """)
    return db.execute(sql, {"limit":limit, "offset":offset}).mappings().all()

@router.post("/docentes", status_code=201)
def crear_docente(payload: DocenteCreate, db: Session = Depends(grades_db), _=Depends(require_roles("DIRECTIVO"))):
    sql = text(f"""
        INSERT INTO {q(settings.DB_GRADES_NAME,'docente')} (usuario_iam_id, nombre_completo, estado, eliminado)
        VALUES (:uid, :nombre, COALESCE(:estado,1), 0)
    """)
    db.execute(sql, {"uid": payload.usuario_iam_id, "nombre": payload.nombre_completo, "estado": payload.estado})
    db.commit()
    return {"ok": True}

@router.put("/docentes/{docente_id}")
def actualizar_docente(docente_id: int, payload: DocenteUpdate, db: Session = Depends(grades_db), _=Depends(require_roles("DIRECTIVO"))):
    sets, params = [], {"id": docente_id}
    if payload.nombre_completo is not None:
        sets.append("nombre_completo = :nombre"); params["nombre"] = payload.nombre_completo
    if payload.estado is not None:
        sets.append("estado = :estado"); params["estado"] = int(payload.estado)
    if not sets:
        return {"ok": True, "updated": 0}
    sql = text(f"UPDATE {q(settings.DB_GRADES_NAME,'docente')} SET {', '.join(sets)} WHERE id = :id AND eliminado = 0")
    res = db.execute(sql, params)
    db.commit()
    return {"ok": True, "updated": res.rowcount}

@router.delete("/docentes/{docente_id}")
def eliminar_docente(docente_id: int, db: Session = Depends(grades_db), _=Depends(require_roles("DIRECTIVO"))):
    sql = text(f"UPDATE {q(settings.DB_GRADES_NAME,'docente')} SET eliminado = 1 WHERE id = :id AND eliminado = 0")
    res = db.execute(sql, {"id": docente_id})
    db.commit()
    return {"ok": True, "deleted": res.rowcount}
