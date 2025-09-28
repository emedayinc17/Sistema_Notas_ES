# --- bootstrap sys.path for ev_shared (works with uvicorn --reload & Windows) ---
import sys, pathlib
def _add_ev_shared_to_path():
    here = pathlib.Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "libs" / "shared" / "ev_shared"
        if candidate.exists() and candidate.is_dir():
            sys.path.insert(0, str(candidate.parent))
            return
_add_ev_shared_to_path()
# -------------------------------------------------------------------------------

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from ev_shared.config import settings
from ev_shared.db import engine_grades

from app.api.cursos import cursos, matriculas

API_PREFIX = "/v1"

app = FastAPI(title="cursos-service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.APP_ENV == "dev" else [],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

@app.get("/")
def root():
    return {"name": "cursos-service", "docs": "/docs", "env": settings.APP_ENV}

@app.get("/health")
def health():
    with engine_grades.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"ok": True, "service": "cursos", "env": settings.APP_ENV}

app.include_router(cursos.router,     prefix=API_PREFIX)
app.include_router(matriculas.router, prefix=API_PREFIX)
