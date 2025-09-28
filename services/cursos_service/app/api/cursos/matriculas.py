from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ev_shared.db import q
from ev_shared.config import settings
from ev_shared.deps import grades_db, get_current_user, require_roles

router = APIRouter(prefix="", tags=["matriculas"])

class MatriculaCreate(BaseModel):
    estudiante_id: int
    curso_id: int
    anio_escolar: int

@router.get("/cursos/{curso_id}/matriculas")
def listar_matriculas_por_curso(curso_id: int, db: Session = Depends(grades_db), _=Depends(get_current_user)):
    sql = text(f"""
        SELECT m.id, m.estudiante_id, m.curso_id, m.anio_escolar, m.creado_en
        FROM {q(settings.DB_GRADES_NAME,'matricula')} AS m
        WHERE m.curso_id = :cid
        ORDER BY m.id DESC
    """)
    return db.execute(sql, {"cid": curso_id}).mappings().all()

@router.post("/matriculas", status_code=201)
def crear_matricula(payload: MatriculaCreate, db: Session = Depends(grades_db), _=Depends(require_roles("DIRECTIVO","DOCENTE"))):
    sql = text(f"""
        INSERT INTO {q(settings.DB_GRADES_NAME,'matricula')} (estudiante_id, curso_id, anio_escolar)
        VALUES (:estudiante_id, :curso_id, :anio_escolar)
        ON DUPLICATE KEY UPDATE anio_escolar = VALUES(anio_escolar)
    """)
    db.execute(sql, payload.model_dump())
    db.commit()
    return {"ok": True}

@router.delete("/matriculas/{matricula_id}")
def eliminar_matricula(matricula_id: int, db: Session = Depends(grades_db), _=Depends(require_roles("DIRECTIVO","DOCENTE"))):
    sql = text(f"DELETE FROM {q(settings.DB_GRADES_NAME,'matricula')} WHERE id = :id")
    res = db.execute(sql, {"id": matricula_id})
    db.commit()
    return {"ok": True, "deleted": res.rowcount}
