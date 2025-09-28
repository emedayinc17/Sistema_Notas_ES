from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ev_shared.db import q
from ev_shared.config import settings
from ev_shared.deps import grades_db, get_current_user

router = APIRouter(prefix="", tags=["reportes"])

@router.get("/reportes/cursos/{curso_id}/notas")
def reporte_notas_por_curso(curso_id: int, db: Session = Depends(grades_db), _=Depends(get_current_user)):
    sql = text(f"""
        SELECT vnc.*
        FROM {q(settings.DB_GRADES_NAME,'vw_notas_por_curso')} AS vnc
        WHERE vnc.curso_id = :cid
        ORDER BY vnc.estudiante_id, vnc.evaluacion_id
    """)
    return db.execute(sql, {"cid": curso_id}).mappings().all()

@router.get("/reportes/cursos/{curso_id}/resumen")
def reporte_resumen_curso(curso_id: int, db: Session = Depends(grades_db), _=Depends(get_current_user)):
    sql = text(f"""
        SELECT vrc.*
        FROM {q(settings.DB_GRADES_NAME,'vw_resumen_curso')} AS vrc
        WHERE vrc.curso_id = :cid
        ORDER BY vrc.estudiante_id
    """)
    return db.execute(sql, {"cid": curso_id}).mappings().all()
