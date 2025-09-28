from pathlib import Path
from typing import Optional, Tuple
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import conint, computed_field

def _env_paths() -> Optional[Tuple[str, ...]]:
    candidates = [Path('/vault/secrets/app.env'), Path('.env'), Path('app/.env')]
    paths = [str(p) for p in candidates if p.exists()]
    return tuple(paths) if paths else None

class Settings(BaseSettings):
    APP_NAME: str = 'sistema-notas-es'
    APP_ENV: str = 'dev'
    APP_HOST: str = '0.0.0.0'
    APP_PORT: conint(gt=0) = 8000

    DB_HOST: str = '127.0.0.1'
    DB_PORT: conint(gt=0) = 3306

    DB_IAM_NAME: str = 'sga_iam'
    DB_IAM_USER: str = 'app_iam'
    DB_IAM_PASS: str = 'Iam_2025!'

    DB_GRADES_NAME: str = 'sga_grades'
    DB_GRADES_USER: str = 'app_grades'
    DB_GRADES_PASS: str = 'Grades_2025!'

    JWT_SECRET: str = 'change-me'
    JWT_ALG: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: conint(gt=0) = 60

    model_config = SettingsConfigDict(
        env_file=_env_paths(),
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False,
    )

    @computed_field
    @property
    def IAM_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_IAM_USER}:{self.DB_IAM_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_IAM_NAME}?charset=utf8mb4"

    @computed_field
    @property
    def GRADES_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_GRADES_USER}:{self.DB_GRADES_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_GRADES_NAME}?charset=utf8mb4"

settings = Settings()
