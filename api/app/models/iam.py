from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import BigInteger, String, Enum, SmallInteger, TIMESTAMP

BaseIAM = declarative_base()

class Rol(BaseIAM):
    __tablename__ = "rol"
    id: Mapped[int]   = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(Enum('DOCENTE','PADRE','DIRECTIVO'), unique=True, nullable=False)

class Usuario(BaseIAM):
    __tablename__ = "usuario"
    id: Mapped[int]            = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    usuario: Mapped[str] = mapped_column("usuario", String(80), unique=True, nullable=False)
    hash_contrasena: Mapped[str] = mapped_column("hash_contrasena", String(255), nullable=False)
    correo: Mapped[str | None] = mapped_column("correo", String(150))
    estado: Mapped[int] = mapped_column(SmallInteger, default=1)
    eliminado: Mapped[int] = mapped_column(SmallInteger, default=0)

class UsuarioRol(BaseIAM):
    __tablename__ = "usuario_rol"
    user_id: Mapped[int] = mapped_column("user_id", BigInteger, primary_key=True)
    role_id: Mapped[int] = mapped_column("role_id", BigInteger, primary_key=True)

class Apoderado(BaseIAM):
    __tablename__ = "apoderado"
    id: Mapped[int]             = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    usuario_padre_id: Mapped[int]  = mapped_column("usuario_padre_id", BigInteger, nullable=False)  # sga_iam.usuario.id
    estudiante_id: Mapped[int]     = mapped_column("estudiante_id", BigInteger, nullable=False)  # sga_grades.estudiante.id