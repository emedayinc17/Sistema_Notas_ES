# app/utils/permissions.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, mapped_column
from sqlalchemy import func, exists, and_
from app.models.grades import Docente, Curso, Matricula, Evaluacion
from app.models.iam import Apoderado

# ------ Helpers base

def get_docente_for_user(usuario_iam_id: int, db_grades: Session) -> int | None:
    t = db_grades.query(Docente).filter(Docente.usuario_iam_id == usuario_iam_id, Docente.eliminado == 0, Docente.estado == 1).first()
    return t.id if t else None

def assert_course_owner(user: dict, curso_id: int, db_grades: Session) -> None:
    """DOCENTE solo puede operar sobre sus cursos."""
    if "DOCENTE" not in user["roles"]:
        return
    docente_id = get_docente_for_user(user["id"], db_grades)
    if not docente_id:
        raise HTTPException(status_code=403, detail="Perfil de docente no encontrado")
    owned = db_grades.query(Curso.id).filter(Curso.id == curso_id, Curso.docente_id == docente_id).first()
    if not owned:
        raise HTTPException(status_code=403, detail="Prohibido: no es tu curso")

def assert_evaluacion_belongs_to_docente(user: dict, evaluacion_id: int, db_grades: Session) -> int:
    """Asegura que la evaluación es del curso del docente. Retorna curso_id."""
    if "DOCENTE" not in user["roles"]:
        # para DIRECTIVO no hace falta verificar ownership
        a = db_grades.get(Evaluacion, evaluacion_id)
        if not a:
            raise HTTPException(status_code=404, detail="Evaluación no encontrada")
        return a.curso_id
    docente_id = get_docente_for_user(user["id"], db_grades)
    if not docente_id:
        raise HTTPException(status_code=403, detail="Perfil de docente no encontrado")
    row = (
        db_grades.query(Evaluacion.curso_id, Curso.docente_id)
        .join(Curso, Curso.id == Evaluacion.curso_id)
        .filter(Evaluacion.id == evaluacion_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada")
    curso_id, owner_docente = row
    if owner_docente != docente_id:
        raise HTTPException(status_code=403, detail="Prohibido: no es tu curso")
    return curso_id

def assert_parent_of_student(parent_user_id: int, student_id: int, db_iam: Session) -> None:
    """PADRE solo accede a sus hijos."""
    ok = db_iam.query(Guardian.id).filter(
        Guardian.parent_user_id == parent_user_id,
        Guardian.student_id == student_id
    ).first()
    if not ok:
        raise HTTPException(status_code=403, detail="Forbidden: not your child")

def assert_parent_has_course(parent_user_id: int, course_id: int, db_iam: Session, db_grades: Session) -> None:
    """
    PADRE puede ver info del curso si al menos uno de sus hijos está matriculado allí.
    """
    # hijos del padre
    child_ids = [sid for (sid,) in db_iam.query(Guardian.student_id).filter(Guardian.parent_user_id == parent_user_id).all()]
    if not child_ids:
        raise HTTPException(status_code=403, detail="Forbidden: no linked students")
    exists_row = (
        db_grades.query(Enrollment.id)
        .filter(Enrollment.course_id == course_id, Enrollment.student_id.in_(child_ids))
        .first()
    )
    if not exists_row:
        raise HTTPException(status_code=403, detail="Forbidden: your students are not in this course")

def assert_weights_under_100(course_id: int, db_grades: Session, extra_weight: float | None = None, exclude_assessment_id: int | None = None) -> None:
    """
    Valida que la suma de ponderaciones para el curso no supere 20.
    - extra_weight: ponderación a añadir (para POST).
    - exclude_assessment_id: evaluación a excluir del sum (para PUT).
    """
    q = db_grades.query(func.coalesce(func.sum(Assessment.weight), 0.0)).filter(Assessment.course_id == course_id)
    if exclude_assessment_id:
        q = q.filter(Assessment.id != exclude_assessment_id)
    current_sum = float(q.scalar() or 0.0)
    total = current_sum + (float(extra_weight) if extra_weight is not None else 0.0)
    if total > 20.0:
        raise HTTPException(status_code=400, detail=f"Total weight exceeds 100 (would be {total})")
