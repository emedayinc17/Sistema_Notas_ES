from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ev_shared.db import q
from ev_shared.config import settings
from ev_shared.deps import grades_db, get_current_user, require_roles

router = APIRouter(prefix="", tags=["notas"])

class NotaUpsert(BaseModel):
    matricula_id: int
    evaluacion_id: int
    puntaje: float | None = None

@router.get("/matriculas/{matricula_id}/notas")
def listar_notas(matricula_id: int, db: Session = Depends(grades_db), _=Depends(get_current_user)):
    sql = text(f"""
        SELECT n.id, n.matricula_id, n.evaluacion_id, n.puntaje, n.creado_en, n.actualizado_en
        FROM {q(settings.DB_GRADES_NAME,'nota')} AS n
        WHERE n.matricula_id = :mid
        ORDER BY n.evaluacion_id
    """)
    return db.execute(sql, {"mid": matricula_id}).mappings().all()

@router.put("/notas", status_code=200)
def upsert_nota(payload: NotaUpsert, db: Session = Depends(grades_db), _=Depends(require_roles("DIRECTIVO","DOCENTE"))):
    sql = text(f"""
        INSERT INTO {q(settings.DB_GRADES_NAME,'nota')} (matricula_id, evaluacion_id, puntaje)
        VALUES (:matricula_id, :evaluacion_id, :puntaje)
        ON DUPLICATE KEY UPDATE puntaje = VALUES(puntaje), actualizado_en = CURRENT_TIMESTAMP
    """)
    db.execute(sql, payload.model_dump())
    db.commit()
    return {"ok": True}
