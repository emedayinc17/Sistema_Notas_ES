from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import BigInteger, String, SmallInteger, ForeignKey, Integer, DECIMAL

BaseGrades = declarative_base()

class Docente(BaseGrades):
    __tablename__ = "docente"
    id: Mapped[int]          = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    usuario_iam_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(120), nullable=False)
    estado: Mapped[int] = mapped_column(SmallInteger, default=1)
    eliminado: Mapped[int] = mapped_column(SmallInteger, default=0)

class Estudiante(BaseGrades):
    __tablename__ = "estudiante"
    id: Mapped[int]          = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    codigo: Mapped[str | None] = mapped_column(String(40), unique=True)
    nombre_completo: Mapped[str] = mapped_column(String(120), nullable=False)
    estado: Mapped[int] = mapped_column(SmallInteger, default=1)
    eliminado: Mapped[int] = mapped_column(SmallInteger, default=0)

class Curso(BaseGrades):
    __tablename__ = "curso"
    id: Mapped[int]                 = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    grado: Mapped[str | None] = mapped_column(String(20))
    seccion: Mapped[str | None] = mapped_column(String(10))
    docente_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("docente.id"), nullable=False)
    estado: Mapped[int] = mapped_column(SmallInteger, default=1)
    eliminado: Mapped[int] = mapped_column(SmallInteger, default=0)

class Matricula(BaseGrades):
    __tablename__ = "matricula"
    id: Mapped[int]          = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    estudiante_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("estudiante.id"), nullable=False)
    curso_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("curso.id"), nullable=False)
    anio_escolar: Mapped[int] = mapped_column(Integer, nullable=False)
    creado_en: Mapped[str] = mapped_column(String(50))

class Evaluacion(BaseGrades):
    __tablename__ = "evaluacion"
    id: Mapped[int]        = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    curso_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("curso.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    ponderacion: Mapped[float] = mapped_column(DECIMAL(5,2), nullable=False)
    creado_en: Mapped[str] = mapped_column(String(50))

class Nota(BaseGrades):
    __tablename__ = "nota"
    id: Mapped[int]            = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    matricula_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("matricula.id"), nullable=False)
    evaluacion_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("evaluacion.id"), nullable=False)
    puntaje: Mapped[float | None] = mapped_column(DECIMAL(5,2))
    creado_en: Mapped[str] = mapped_column(String(50))