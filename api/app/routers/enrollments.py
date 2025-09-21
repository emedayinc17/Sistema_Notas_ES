# app/routers/matriculas.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, mapped_column
from app.deps import grades_db, require_roles
from app.models.grades import Matricula, Curso
from app.schemas.grades import MatriculaCreate

router = APIRouter(prefix="/api/notas/v1", tags=['Matriculas'])

@router.post("/matriculas", status_code=200, dependencies=[Depends(require_roles("DIRECTIVO"))])
def ensure_enrollment(body: MatriculaCreate, db: Session = Depends(grades_db)):
    c = db.get(Curso, body.curso_id)
    if not c:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    e = db.query(Matricula).filter(
        Matricula.estudiante_id == body.estudiante_id,
        Matricula.curso_id == body.curso_id,
        Matricula.anio_escolar == body.anio_escolar
    ).first()
    if not e:
        e = Matricula(estudiante_id=body.estudiante_id, curso_id=body.curso_id, anio_escolar=body.anio_escolar)
        db.add(e); db.commit()
    return {"ok": True}
