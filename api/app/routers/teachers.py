# app/routers/docentes.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, mapped_column
from typing import Optional
from app.deps import grades_db, get_current_user, require_roles
from app.models.grades import Docente
from app.schemas.grades import DocenteOut

router = APIRouter(prefix="/api/notas/v1", tags=['Docentes'])

@router.get("/docentes", response_model=list[DocenteOut], dependencies=[Depends(require_roles("DOCENTE","DIRECTIVO"))])
def find_teachers(user=Depends(get_current_user), db: Session = Depends(grades_db), usuarioId: Optional[int] = Query(None, alias="idUsuario")):
    q = db.query(Docente).filter(Docente.estado == 1, Docente.eliminado == 0)
    if usuarioId:
        q = q.filter(Docente.usuario_iam_id == usuarioId)
    rows = q.all()
    return [DocenteOut(id=t.id, usuario_iam_id=t.usuario_iam_id, nombre_completo=t.nombre_completo) for t in rows]
