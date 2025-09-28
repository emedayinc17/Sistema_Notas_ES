from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from ev_shared.db import q
from ev_shared.config import settings
from ev_shared.deps import iam_db, require_roles

router = APIRouter(prefix="", tags=["apoderados"])

class ApoderadoCreate(BaseModel):
    usuario_padre_id: int
    estudiante_id: int

@router.get("/estudiantes/{estudiante_id}/apoderados")
def listar_apoderados(estudiante_id: int, db: Session = Depends(iam_db), _=Depends(require_roles("DIRECTIVO","PADRE"))):
    sql = text(f"""
        SELECT ap.id, ap.usuario_padre_id, ap.estudiante_id, ap.creado_en
        FROM {q(settings.DB_IAM_NAME,'apoderado')} AS ap
        WHERE ap.estudiante_id = :sid
        ORDER BY ap.id DESC
    """)
    return db.execute(sql, {"sid": estudiante_id}).mappings().all()

@router.post("/apoderados", status_code=201)
def crear_apoderado(payload: ApoderadoCreate, db: Session = Depends(iam_db), _=Depends(require_roles("DIRECTIVO"))):
    sql = text(f"""
        INSERT IGNORE INTO {q(settings.DB_IAM_NAME,'apoderado')} (usuario_padre_id, estudiante_id)
        VALUES (:pid, :sid)
    """)
    db.execute(sql, {"pid": payload.usuario_padre_id, "sid": payload.estudiante_id})
    db.commit()
    return {"ok": True}

@router.delete("/apoderados/{apoderado_id}")
def eliminar_apoderado(apoderado_id: int, db: Session = Depends(iam_db), _=Depends(require_roles("DIRECTIVO"))):
    sql = text(f"DELETE FROM {q(settings.DB_IAM_NAME,'apoderado')} WHERE id = :id")
    res = db.execute(sql, {"id": apoderado_id})
    db.commit()
    return {"ok": True, "deleted": res.rowcount}
