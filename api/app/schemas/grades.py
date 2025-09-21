from pydantic import BaseModel, Field
from typing import Optional, Dict

class DocenteOut(BaseModel):
    id: int
    usuario_iam_id: int
    nombre_completo: str

class CursoOut(BaseModel):
    id: int
    nombre: str
    grado: Optional[str] = None
    seccion: Optional[str] = None
    docente_id: int
    estado: int

class CursoCreate(BaseModel):
    nombre: str
    grado: Optional[str] = None
    seccion: Optional[str] = None
    docente_id: int

class CursoUpdate(BaseModel):
    nombre: Optional[str] = None
    grado: Optional[str] = None
    seccion: Optional[str] = None
    docente_id: Optional[int] = None
    estado: Optional[int] = None

class EstudianteCreate(BaseModel):
    codigo: str
    nombre_completo: str

class EstudianteOut(BaseModel):
    id: int
    codigo: str | None
    nombre_completo: str

class MatriculaCreate(BaseModel):
    estudiante_id: int
    curso_id: int
    anio_escolar: int

class EvaluacionCreate(BaseModel):
    curso_id: int
    nombre: str
    ponderacion: float = Field(ge=0, le=100)

class EvaluacionOut(BaseModel):
    id: int
    curso_id: int
    nombre: str
    ponderacion: float

class NotaBulkItem(BaseModel):
    estudiante_id: int
    evaluacion_id: int
    puntaje: float | None = Field(default=None, ge=0, le=20)

class NotaBulkRequest(BaseModel):
    curso_id: int
    items: list[NotaBulkItem]
