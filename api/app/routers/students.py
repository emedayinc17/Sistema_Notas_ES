# app/routers/estudiantes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, mapped_column
from app.deps import grades_db, require_roles
from app.models.grades import Estudiante
from app.schemas.grades import EstudianteCreate, EstudianteOut

router = APIRouter(prefix="/api/notas/v1", tags=['Estudiantes'])

@router.post("/estudiantes", response_model=EstudianteOut, status_code=201, dependencies=[Depends(require_roles("DIRECTIVO"))])
def create_student(body: EstudianteCreate, db: Session = Depends(grades_db)):
    s = Estudiante(codigo=body.codigo, nombre_completo=body.nombre_completo, estado=1)
    db.add(s); db.commit(); db.refresh(s)
    return EstudianteOut(id=s.id, codigo=s.codigo, nombre_completo=s.nombre_completo)
