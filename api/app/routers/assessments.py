# app/routers/evaluaciones.py
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session, mapped_column
from app.deps import grades_db, get_current_user, require_roles
from app.models.grades import Evaluacion, Curso
from app.schemas.grades import EvaluacionCreate, EvaluacionOut
from app.utils.permissions import assert_course_owner, assert_weights_under_100, assert_evaluacion_belongs_to_docente

router = APIRouter(prefix="/api/notas/v1", tags=['Evaluaciones'])

@router.get("/evaluaciones", response_model=list[EvaluacionOut], dependencies=[Depends(require_roles("DOCENTE","DIRECTIVO"))])
def list_assessments(cursoId: int = Query(..., alias="idCurso"), user=Depends(get_current_user), db: Session = Depends(grades_db)):
    if "DOCENTE" in user["roles"]:
        assert_course_owner(user, cursoId, db)
    rows = db.query(Evaluacion).filter(Evaluacion.curso_id == cursoId).all()
    return [EvaluacionOut(id=r.id, curso_id=r.curso_id, nombre=r.nombre, ponderacion=float(r.ponderacion)) for r in rows]

@router.post("/evaluaciones", response_model=EvaluacionOut, status_code=201, dependencies=[Depends(require_roles("DOCENTE","DIRECTIVO"))])
def create_assessment(body: EvaluacionCreate, user=Depends(get_current_user), db: Session = Depends(grades_db)):
    if "DOCENTE" in user["roles"]:
        assert_course_owner(user, body.curso_id, db)
    assert_weights_under_100(body.curso_id, db, extra_weight=float(body.ponderacion))
    a = Evaluacion(curso_id=body.curso_id, nombre=body.nombre, ponderacion=body.ponderacion)
    db.add(a); db.commit(); db.refresh(a)
    return EvaluacionOut(id=a.id, curso_id=a.curso_id, nombre=a.nombre, ponderacion=float(a.ponderacion))

@router.put("/evaluaciones/{evaluacionId}", response_model=EvaluacionOut, dependencies=[Depends(require_roles("DOCENTE","DIRECTIVO"))])
def update_assessment(evaluacionId: int = Path(...), nombre: str | None = None, ponderacion: float | None = None,
                      user=Depends(get_current_user), db: Session = Depends(grades_db)):
    a = db.get(Evaluacion, evaluacionId)
    if not a:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    # DOCENTE solo si es de su curso
    curso_id = assert_evaluacion_belongs_to_docente(user, evaluacionId, db)
    if ponderacion is not None:
        assert_weights_under_100(curso_id, db, extra_weight=float(ponderacion), exclude_assessment_id=evaluacionId)
    if nombre is not None:
        a.nombre = nombre
    if ponderacion is not None:
        a.ponderacion = ponderacion
    db.commit(); db.refresh(a)
    return EvaluacionOut(id=a.id, curso_id=a.curso_id, nombre=a.nombre, ponderacion=float(a.ponderacion))
