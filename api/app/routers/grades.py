# app/routers/notas.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, mapped_column
from sqlalchemy import func
from app.deps import grades_db, get_current_user, require_roles
from app.models.grades import Nota, Matricula, Evaluacion, Curso
from app.schemas.grades import NotaBulkRequest
from app.utils.permissions import assert_course_owner

router = APIRouter(prefix="/api/notas/v1", tags=['Notas'])

@router.get("/notas", dependencies=[Depends(require_roles("DOCENTE","DIRECTIVO"))])
def get_grades(
    cursoId: int = Query(..., alias="idCurso"),
    evaluacionId: int | None = Query(None, alias="idEvaluacion"),
    user=Depends(get_current_user),
    db: Session = Depends(grades_db),
):
    if "DOCENTE" in user["roles"]:
        assert_course_owner(user, cursoId, db)
    # DIRECTIVO lectura libre
    q = (
        db.query(Matricula.estudiante_id, Evaluacion.id.label("evaluacion_id"), Nota.puntaje)
        .join(Curso, Curso.id == Matricula.curso_id)
        .join(Evaluacion, Evaluacion.curso_id == Curso.id)
        .outerjoin(Nota, (Nota.matricula_id == Matricula.id) & (Nota.evaluacion_id == Evaluacion.id))
        .filter(Curso.id == cursoId)
    )
    if evaluacionId:
        q = q.filter(Evaluacion.id == evaluacionId)
    rows = q.all()
    return [{"estudianteId": s, "evaluacionId": a, "puntaje": float(sc) if sc is not None else None} for (s, a, sc) in rows]

@router.post("/notas/bulk", dependencies=[Depends(require_roles("DOCENTE","DIRECTIVO"))])
def save_grades_bulk(
    body: NotaBulkRequest,
    user=Depends(get_current_user),
    db: Session = Depends(grades_db),
):
    # DIRECTIVO: solo lectura → bloquear escritura
    if "DIRECTIVO" in user["roles"]:
        raise HTTPException(status_code=403, detail="DIRECTIVO no puede modificar notas")
    # DOCENTE: solo sus cursos
    assert_course_owner(user, body.curso_id, db)

    # mapa estudiante -> matricula en ese curso (año no requerido por contrato aquí)
    enrolls = db.query(Matricula.id, Matricula.estudiante_id).filter(Matricula.curso_id == body.curso_id).all()
    e_by_estudiante = {s: e for (e, s) in enrolls}
    updated = 0
    for it in body.items:
        e_id = e_by_estudiante.get(it.estudiante_id)
        if not e_id:
            continue
        g = db.query(Nota).filter(Nota.matricula_id == e_id, Nota.evaluacion_id == it.evaluacion_id).first()
        if not g:
            g = Nota(matricula_id=e_id, evaluacion_id=it.evaluacion_id, puntaje=it.puntaje)
            db.add(g)
        else:
            g.puntaje = it.puntaje
        updated += 1
    db.commit()
    return {"actualizados": updated}

@router.get("/notas/summary", dependencies=[Depends(require_roles("DOCENTE","DIRECTIVO","PADRE"))])
def course_summary(
    cursoId: int = Query(..., alias="idCurso"),
    anio: int | None = Query(None, alias="anio"),
    user=Depends(get_current_user),
    db: Session = Depends(grades_db),
):
    # DOCENTE: solo sus cursos
    if "DOCENTE" in user["roles"]:
        assert_course_owner(user, cursoId, db)
    # PADRE: validación se hará en reports endpoint más específico; aquí puedes dejarlo cerrado a PADRE si deseas
    # (o replicar la validación parent_has_course si quieres permitir aquí también para PADRE)
    if "PADRE" in user["roles"]:
        # por simplicidad, negamos aquí y lo exponemos por reports
        raise HTTPException(status_code=403, detail="Los padres deben usar los endpoints de /reportes")

    # promedio ponderado por estudiante en el curso
    rows = (
        db.query(
            Matricula.estudiante_id,
            func.sum(func.coalesce(Nota.puntaje, 0) * (func.coalesce(Evaluacion.ponderacion, 0)/100.0)).label("ponderado")
        )
        .join(Evaluacion, Evaluacion.curso_id == Matricula.curso_id)
        .outerjoin(Nota, (Nota.matricula_id == Matricula.id) & (Nota.evaluacion_id == Evaluacion.id))
        .filter(Matricula.curso_id == cursoId)
        .group_by(Matricula.estudiante_id)
        .all()
    )
    return [{"estudianteId": sid, "promedioPonderado": float(w or 0)} for (sid, w) in rows]
