from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ev_shared.db import q
from ev_shared.config import settings
from ev_shared.deps import grades_db, get_current_user, require_roles

router = APIRouter(prefix="", tags=["estudiantes"])

class EstudianteCreate(BaseModel):
    codigo: str | None = None
    nombre_completo: str
    estado: int | None = 1

class EstudianteUpdate(BaseModel):
    codigo: str | None = None
    nombre_completo: str | None = None
    estado: int | None = None

@router.get("/estudiantes")
def listar_estudiantes(limit: int = 50, offset: int = 0, db: Session = Depends(grades_db), _=Depends(get_current_user)):
    sql = text(f"""
        SELECT s.id, s.codigo, s.nombre_completo, s.estado
        FROM {q(settings.DB_GRADES_NAME,'estudiante')} AS s
        WHERE s.eliminado = 0
        ORDER BY s.id DESC
        LIMIT :limit OFFSET :offset
    """)
    return db.execute(sql, {"limit":limit, "offset":offset}).mappings().all()

@router.get("/estudiantes/{estudiante_id}")
def obtener_estudiante(estudiante_id: int, db: Session = Depends(grades_db), _=Depends(get_current_user)):
    sql = text(f"""
        SELECT s.id, s.codigo, s.nombre_completo, s.estado
        FROM {q(settings.DB_GRADES_NAME,'estudiante')} AS s
        WHERE s.id = :id AND s.eliminado = 0
        LIMIT 1
    """)
    row = db.execute(sql, {"id": estudiante_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return row

@router.post("/estudiantes", status_code=201)
def crear_estudiante(payload: EstudianteCreate, db: Session = Depends(grades_db), _=Depends(require_roles("DIRECTIVO","DOCENTE"))):
    sql = text(f"""
        INSERT INTO {q(settings.DB_GRADES_NAME,'estudiante')} (codigo, nombre_completo, estado, eliminado)
        VALUES (:codigo, :nombre, COALESCE(:estado,1), 0)
    """)
    db.execute(sql, {"codigo": payload.codigo, "nombre": payload.nombre_completo, "estado": payload.estado})
    db.commit()
    return {"ok": True}

@router.put("/estudiantes/{estudiante_id}")
def actualizar_estudiante(estudiante_id: int, payload: EstudianteUpdate, db: Session = Depends(grades_db), _=Depends(require_roles("DIRECTIVO","DOCENTE"))):
    sets, params = [], {"id": estudiante_id}
    if payload.codigo is not None:
        sets.append("codigo = :codigo"); params["codigo"] = payload.codigo
    if payload.nombre_completo is not None:
        sets.append("nombre_completo = :nombre"); params["nombre"] = payload.nombre_completo
    if payload.estado is not None:
        sets.append("estado = :estado"); params["estado"] = int(payload.estado)
    if not sets:
        return {"ok": True, "updated": 0}
    sql = text(f"UPDATE {q(settings.DB_GRADES_NAME,'estudiante')} SET {', '.join(sets)} WHERE id = :id AND eliminado = 0")
    res = db.execute(sql, params)
    db.commit()
    return {"ok": True, "updated": res.rowcount}

@router.delete("/estudiantes/{estudiante_id}")
def eliminar_estudiante(estudiante_id: int, db: Session = Depends(grades_db), _=Depends(require_roles("DIRECTIVO"))):
    sql = text(f"UPDATE {q(settings.DB_GRADES_NAME,'estudiante')} SET eliminado = 1 WHERE id = :id AND eliminado = 0")
    res = db.execute(sql, {"id": estudiante_id})
    db.commit()
    return {"ok": True, "deleted": res.rowcount}
