from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ev_shared.db import q
from ev_shared.config import settings
from ev_shared.deps import grades_db, get_current_user, require_roles

router = APIRouter(prefix="", tags=["cursos"])

class CursoCreate(BaseModel):
    nombre: str
    grado: str | None = None
    seccion: str | None = None
    docente_id: int
    estado: int | None = 1

class CursoUpdate(BaseModel):
    nombre: str | None = None
    grado: str | None = None
    seccion: str | None = None
    docente_id: int | None = None
    estado: int | None = None

@router.get("/cursos")
def listar_cursos(limit: int = 50, offset: int = 0, db: Session = Depends(grades_db), _=Depends(get_current_user)):
    sql = text(f"""
        SELECT c.id, c.nombre, c.grado, c.seccion, c.docente_id, c.estado
        FROM {q(settings.DB_GRADES_NAME,'curso')} AS c
        WHERE c.eliminado = 0
        ORDER BY c.id DESC
        LIMIT :limit OFFSET :offset
    """)
    return db.execute(sql, {"limit":limit, "offset":offset}).mappings().all()

@router.get("/cursos/{curso_id}")
def obtener_curso(curso_id: int, db: Session = Depends(grades_db), _=Depends(get_current_user)):
    sql = text(f"""
        SELECT c.id, c.nombre, c.grado, c.seccion, c.docente_id, c.estado
        FROM {q(settings.DB_GRADES_NAME,'curso')} AS c
        WHERE c.id = :id AND c.eliminado = 0
        LIMIT 1
    """)
    row = db.execute(sql, {"id": curso_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    return row

@router.post("/cursos", status_code=201)
def crear_curso(payload: CursoCreate, db: Session = Depends(grades_db), _=Depends(require_roles("DIRECTIVO"))):
    sql = text(f"""
        INSERT INTO {q(settings.DB_GRADES_NAME,'curso')} (nombre, grado, seccion, docente_id, estado, eliminado)
        VALUES (:nombre, :grado, :seccion, :docente_id, COALESCE(:estado,1), 0)
    """)
    db.execute(sql, payload.model_dump())
    db.commit()
    return {"ok": True}

@router.put("/cursos/{curso_id}")
def actualizar_curso(curso_id: int, payload: CursoUpdate, db: Session = Depends(grades_db), _=Depends(require_roles("DIRECTIVO","DOCENTE"))):
    sets, params = [], {"id": curso_id}
    for field in ("nombre","grado","seccion","docente_id","estado"):
        val = getattr(payload, field)
        if val is not None:
            sets.append(f"{field} = :{field}")
            params[field] = val
    if not sets:
        return {"ok": True, "updated": 0}
    sql = text(f"UPDATE {q(settings.DB_GRADES_NAME,'curso')} SET {', '.join(sets)} WHERE id = :id AND eliminado = 0")
    res = db.execute(sql, params)
    db.commit()
    return {"ok": True, "updated": res.rowcount}

@router.delete("/cursos/{curso_id}")
def eliminar_curso(curso_id: int, db: Session = Depends(grades_db), _=Depends(require_roles("DIRECTIVO"))):
    sql = text(f"UPDATE {q(settings.DB_GRADES_NAME,'curso')} SET eliminado = 1 WHERE id = :id AND eliminado = 0")
    res = db.execute(sql, {"id": curso_id})
    db.commit()
    return {"ok": True, "deleted": res.rowcount}
