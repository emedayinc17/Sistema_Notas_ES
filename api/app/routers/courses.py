# app/routers/cursos.py
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session, mapped_column
from typing import Optional
from app.deps import grades_db, get_current_user, require_roles
from app.models.grades import Curso, Docente
from app.schemas.grades import CursoOut, CursoCreate, CursoUpdate
from app.utils.permissions import get_docente_for_user

router = APIRouter(prefix="/api/notas/v1", tags=['Cursos'])

@router.get("/cursos", response_model=list[CursoOut], dependencies=[Depends(require_roles("DOCENTE","DIRECTIVO"))])
def list_courses(
    user=Depends(get_current_user),
    db: Session = Depends(grades_db),
    docenteId: Optional[int] = Query(None, alias="idDocente"),
    anio: Optional[int] = Query(None, alias="anio"),
):
    q = db.query(Curso).filter(Curso.estado == 1)
    if "DOCENTE" in user["roles"]:
        docente_id = get_docente_for_user(user["id"], db)
        q = q.filter(Curso.docente_id == docente_id if docente_id else Curso.id == -1)
    elif docenteId:
        q = q.filter(Curso.docente_id == docenteId)
    rows = q.all()
    return [CursoOut(id=r.id, nombre=r.nombre, grado=r.grado, seccion=r.seccion, docente_id=r.docente_id, estado=r.estado) for r in rows]

@router.post("/cursos", response_model=CursoOut, status_code=201, dependencies=[Depends(require_roles("DIRECTIVO"))])
def create_course(body: CursoCreate, db: Session = Depends(grades_db)):
    c = Curso(nombre=body.nombre, grado=body.grado, seccion=body.seccion, docente_id=body.docente_id, estado=1)
    db.add(c); db.commit(); db.refresh(c)
    return CursoOut(id=c.id, nombre=c.nombre, grado=c.grado, seccion=c.seccion, docente_id=c.docente_id, estado=c.estado)

@router.put("/cursos/{cursoId}", response_model=CursoOut, dependencies=[Depends(require_roles("DIRECTIVO"))])
def update_course(cursoId: int = Path(...), body: CursoUpdate | None = None, db: Session = Depends(grades_db)):
    c = db.get(Curso, cursoId)
    if not c:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    for f in ("nombre","grado","seccion","docente_id","estado"):
        v = getattr(body, f) if body else None
        if v is not None:
            setattr(c, f, v)
    db.commit(); db.refresh(c)
    return CursoOut(id=c.id, nombre=c.nombre, grado=c.grado, seccion=c.seccion, docente_id=c.docente_id, estado=c.estado)

@router.delete("/cursos/{cursoId}", status_code=204, dependencies=[Depends(require_roles("DIRECTIVO"))])
def delete_course(cursoId: int, db: Session = Depends(grades_db)):
    c = db.get(Curso, cursoId)
    if not c:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    db.delete(c); db.commit()
    return

@router.put("/cursos/{cursoId}/asignar-docente", response_model=CursoOut, dependencies=[Depends(require_roles("DIRECTIVO"))])
def assign_teacher(cursoId: int, docenteId: int = Query(..., alias="idDocente"), db: Session = Depends(grades_db)):
    c = db.get(Curso, cursoId)
    if not c:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    c.docente_id = docenteId
    db.commit(); db.refresh(c)
    return CursoOut(id=c.id, nombre=c.nombre, grado=c.grado, seccion=c.seccion, docente_id=c.docente_id, estado=c.estado)
