# app/routers/reportes.py
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session, mapped_column
from sqlalchemy import text
from app.deps import grades_db, iam_db, get_current_user, require_roles
from app.utils.permissions import assert_course_owner, assert_parent_of_student, assert_parent_has_course

router = APIRouter(prefix="/api/notas/v1/reportes", tags=['Reportes'])

@router.get("/course/{courseId}/consolidated", dependencies=[Depends(require_roles("DOCENTE","DIRECTIVO","PADRE"))])
def course_consolidated(courseId: int, year: int | None = Query(None, alias="anio"),
                        user=Depends(get_current_user),
                        db_g: Session = Depends(grades_db),
                        db_i: Session = Depends(iam_db)):
    if "DOCENTE" in user["roles"]:
        assert_course_owner(user, courseId, db_g)
    if "PADRE" in user["roles"]:
        assert_parent_has_course(user["id"], courseId, db_i, db_g)

    # Puedes consultar la vista vw_course_summary para acelerar
    sql = text("""
        SELECT s.id AS estudiante_id, s.nombre_completo AS estudiante_nombre,
               ROUND(IFNULL(SUM(IFNULL(g.puntaje,0) * (a.ponderacion/100.0)), 0), 2) AS promedio_ponderado
        FROM matricula e
        JOIN estudiante s ON s.id = e.estudiante_id
        JOIN evaluacion a ON a.curso_id = e.curso_id
        LEFT JOIN nota g ON g.matricula_id = e.id AND g.evaluacion_id = a.id
        WHERE e.curso_id = :curso_id
        GROUP BY s.id, s.nombre_completo
        ORDER BY s.nombre_completo
    """)
    items = []
    for row in db_g.execute(sql, {"curso_id": courseId}).mappings():
        items.append({
            "estudianteId": int(row["estudiante_id"]),
            "nombre": row["estudiante_nombre"],
            "promedioPonderado": float(row["promedio_ponderado"] or 0.0)
        })
    return items

@router.get("/student/{studentId}/card", dependencies=[Depends(require_roles("DOCENTE","DIRECTIVO","PADRE"))])
def student_card(studentId: int,
                 user=Depends(get_current_user),
                 db_g: Session = Depends(grades_db),
                 db_i: Session = Depends(iam_db)):
    if "PADRE" in user["roles"]:
        assert_parent_of_student(user["id"], studentId, db_i)
    # Si quieres restringir DOCENTE a alumnos de sus cursos, aquí podrías validar que exista enrollment con su curso.
    sql = text("""
        SELECT c.id AS curso_id, c.nombre AS curso_nombre,
               ROUND(IFNULL(SUM(IFNULL(g.puntaje,0) * (a.ponderacion/100.0)), 0), 2) AS promedio_ponderado
        FROM matricula e
        JOIN curso c ON c.id = e.curso_id
        JOIN evaluacion a ON a.curso_id = e.curso_id
        LEFT JOIN nota g ON g.matricula_id = e.id AND g.evaluacion_id = a.id
        WHERE e.estudiante_id = :sid
        GROUP BY c.id, c.nombre
        ORDER BY c.nombre
    """)
    cursos = []
    for row in db_g.execute(sql, {"sid": studentId}).mappings():
        cursos.append({
            "cursoId": int(row["curso_id"]),
            "cursoNombre": row["curso_nombre"],
            "promedioPonderado": float(row["promedio_ponderado"] or 0.0)
        })
    return {"estudianteId": studentId, "promediosPorCurso": cursos}

@router.get("/course/{courseId}/export", dependencies=[Depends(require_roles("DOCENTE","DIRECTIVO","PADRE"))])
def export_csv(courseId: int, format: str = "csv",
               user=Depends(get_current_user),
               db_g: Session = Depends(grades_db),
               db_i: Session = Depends(iam_db)):
    if format != "csv":
        raise HTTPException(status_code=400, detail="Only csv supported")
    if "DOCENTE" in user["roles"]:
        assert_course_owner(user, courseId, db_g)
    if "PADRE" in user["roles"]:
        assert_parent_has_course(user["id"], courseId, db_i, db_g)

    sql = text("""
        SELECT s.id AS estudiante_id, s.nombre_completo AS estudiante_nombre,
               ROUND(IFNULL(SUM(IFNULL(g.puntaje,0) * (a.ponderacion/100.0)), 0), 2) AS promedio_ponderado
        FROM matricula e
        JOIN estudiante s ON s.id = e.estudiante_id
        JOIN evaluacion a ON a.curso_id = e.curso_id
        LEFT JOIN nota g ON g.matricula_id = e.id AND g.evaluacion_id = a.id
        WHERE e.curso_id = :curso_id
        GROUP BY s.id, s.nombre_completo
        ORDER BY s.nombre_completo
    """)
    lines = ["estudianteId,estudianteNombre,promedioPonderado"]
    for row in db_g.execute(sql, {"curso_id": courseId}).mappings():
        lines.append(f'{int(row["estudiante_id"])},{row["estudiante_nombre"]},{float(row["promedio_ponderado"] or 0.0):.2f}')
    csv = "\n".join(lines)
    return Response(content=csv, media_type="text/csv")
