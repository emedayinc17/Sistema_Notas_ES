from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ev_shared.db import q
from ev_shared.config import settings
from ev_shared.deps import grades_db, get_current_user, require_roles

router = APIRouter(prefix="", tags=["evaluaciones"])

class EvaluacionCreate(BaseModel):
    curso_id: int
    nombre: str
    ponderacion: float

class EvaluacionUpdate(BaseModel):
    nombre: str | None = None
    ponderacion: float | None = None

def _peso_total_curso(db: Session, curso_id: int) -> float:
    sql = text(f"SELECT COALESCE(SUM(e.ponderacion),0) FROM {q(settings.DB_GRADES_NAME,'evaluacion')} AS e WHERE e.curso_id = :cid")
    return float(db.execute(sql, {"cid": curso_id}).scalar() or 0.0)

@router.get("/cursos/{curso_id}/evaluaciones")
def listar_evaluaciones(curso_id: int, db: Session = Depends(grades_db), _=Depends(get_current_user)):
    sql = text(f"""
        SELECT e.id, e.curso_id, e.nombre, e.ponderacion, e.creado_en, e.actualizado_en
        FROM {q(settings.DB_GRADES_NAME,'evaluacion')} AS e
        WHERE e.curso_id = :cid
        ORDER BY e.id DESC
    """)
    return db.execute(sql, {"cid": curso_id}).mappings().all()

@router.post("/evaluaciones", status_code=201)
def crear_evaluacion(payload: EvaluacionCreate, db: Session = Depends(grades_db), _=Depends(require_roles("DIRECTIVO","DOCENTE"))):
    total = _peso_total_curso(db, payload.curso_id)
    if total + float(payload.ponderacion) > 100.0 + 1e-6:
        raise HTTPException(status_code=400, detail=f"Ponderación excede 100% (actual {total})")
    sql = text(f"""
        INSERT INTO {q(settings.DB_GRADES_NAME,'evaluacion')} (curso_id, nombre, ponderacion)
        VALUES (:curso_id, :nombre, :ponderacion)
    """)
    db.execute(sql, payload.model_dump())
    db.commit()
    return {"ok": True}

@router.put("/evaluaciones/{evaluacion_id}")
def actualizar_evaluacion(evaluacion_id: int, payload: EvaluacionUpdate, db: Session = Depends(grades_db), _=Depends(require_roles("DIRECTIVO","DOCENTE"))):
    if payload.ponderacion is not None:
        sql0 = text(f"SELECT curso_id, ponderacion FROM {q(settings.DB_GRADES_NAME,'evaluacion')} WHERE id = :id")
        row = db.execute(sql0, {"id": evaluacion_id}).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        total = _peso_total_curso(db, row["curso_id"]) - float(row["ponderacion"]) + float(payload.ponderacion)
        if total > 100.0 + 1e-6:
            raise HTTPException(status_code=400, detail=f"Ponderación excede 100% (nuevo total {total})")

    sets, params = [], {"id": evaluacion_id}
    if payload.nombre is not None:
        sets.append("nombre = :nombre"); params["nombre"] = payload.nombre
    if payload.ponderacion is not None:
        sets.append("ponderacion = :ponderacion"); params["ponderacion"] = float(payload.ponderacion)
    if not sets:
        return {"ok": True, "updated": 0}
    sql = text(f"UPDATE {q(settings.DB_GRADES_NAME,'evaluacion')} SET {', '.join(sets)} WHERE id = :id")
    res = db.execute(sql, params)
    db.commit()
    return {"ok": True, "updated": res.rowcount}

@router.delete("/evaluaciones/{evaluacion_id}")
def eliminar_evaluacion(evaluacion_id: int, db: Session = Depends(grades_db), _=Depends(require_roles("DIRECTIVO","DOCENTE"))):
    sql = text(f"DELETE FROM {q(settings.DB_GRADES_NAME,'evaluacion')} WHERE id = :id")
    res = db.execute(sql, {"id": evaluacion_id})
    db.commit()
    return {"ok": True, "deleted": res.rowcount}
