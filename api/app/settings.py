# api/app/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import validator

class Settings(BaseSettings):
    # Bases y credenciales (2 DBs)
    DB_IAM: str
    DB_GRADES: str
    MYSQL_USER_IAM: str
    MYSQL_PASS_IAM: str
    MYSQL_USER_GRADES: str
    MYSQL_PASS_GRADES: str

    # Opcional: parametrizar host/puerto por Vault
    MYSQL_HOST: str = "mysql.sistema-notas.svc.cluster.local"
    MYSQL_PORT: int = 3306

    # Otros secretos
    JWT_SECRET: str

    # Validador para MYSQL_PORT - maneja el formato "tcp://host:port" de Vault
    @validator('MYSQL_PORT', pre=True)
    def parse_mysql_port(cls, v):
        if isinstance(v, str) and '://' in v:
            # Extraer solo el puerto de strings como "tcp://host:port"
            return int(v.split(':')[-1])
        return int(v)

    # 1) En K8s (Vault Agent) → /vault/secrets/config
    # 2) En local → .env (en la carpeta api/)
    model_config = SettingsConfigDict(
        env_file=("/vault/secrets/config", "api/.env"),
        extra="ignore"
    )

settings = Settings()

# DSNs listos para SQLAlchemy
DSN_IAM = (
    f"mysql+pymysql://{settings.MYSQL_USER_IAM}:"
    f"{settings.MYSQL_PASS_IAM}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.DB_IAM}"
)
DSN_GRADES = (
    f"mysql+pymysql://{settings.MYSQL_USER_GRADES}:"
    f"{settings.MYSQL_PASS_GRADES}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.DB_GRADES}"
)