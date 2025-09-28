from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

engine_iam    = create_engine(settings.IAM_URL,    pool_pre_ping=True, future=True)
engine_grades = create_engine(settings.GRADES_URL, pool_pre_ping=True, future=True)

SessionLocalIAM    = sessionmaker(bind=engine_iam,    autocommit=False, autoflush=False, future=True)
SessionLocalGRADES = sessionmaker(bind=engine_grades, autocommit=False, autoflush=False, future=True)

BaseIAM    = declarative_base(metadata=MetaData(schema=settings.DB_IAM_NAME))
BaseGRADES = declarative_base(metadata=MetaData(schema=settings.DB_GRADES_NAME))

def q(schema: str, table: str) -> str:
    return f"`{schema}`.`{table}`"

def get_db_iam():
    db = SessionLocalIAM()
    try:
        yield db
    finally:
        db.close()

def get_db_grades():
    db = SessionLocalGRADES()
    try:
        yield db
    finally:
        db.close()
