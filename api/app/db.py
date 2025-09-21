# api/app/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, mapped_column
from .settings import DSN_IAM, DSN_GRADES

engine_iam = create_engine(DSN_IAM, pool_pre_ping=True, pool_recycle=1800)
engine_grades = create_engine(DSN_GRADES, pool_pre_ping=True, pool_recycle=1800)

SessionLocalIAM = sessionmaker(autocommit=False, autoflush=False, bind=engine_iam)
SessionLocalGRADES = sessionmaker(autocommit=False, autoflush=False, bind=engine_grades)

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
