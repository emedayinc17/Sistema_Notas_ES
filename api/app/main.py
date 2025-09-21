# app/main.py
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

# 🔐 Importa settings al inicio para cargar /vault/secrets/config (o api/.env en local)
from .settings import settings  # fuerza la carga de variables
# Si usarás las sesiones aquí (p.ej. health con ping a DB), importa get_db_* desde app.db

from .routers import (
    iam, teachers, courses, students, enrollments, assessments, grades, reports
)


from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI(title="Sistema_Notas — API v1 (MVP)")

# Handler para mostrar detalles de error 422 en consola
@app.exception_handler(RequestValidationError)
async def validation_handler(request, exc):
    body = await request.body()
    print("VALIDATION ERROR:", exc.errors(), "BODY RAW:", body.decode("utf-8", errors="ignore"))
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

# CORS (como lo tienes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health-check simple (confirma que settings se cargó)
@app.get("/health", tags=['ops'], include_in_schema=False)
def health():
    return {
        "ok": True,
        "mysql_host": settings.MYSQL_HOST,
        "mysql_port": settings.MYSQL_PORT,
        "db_iam": settings.DB_IAM,
        "db_grades": settings.DB_GRADES,
    }

# Redirige al swagger
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

# Routers (como lo tienes)
app.include_router(iam.router)
app.include_router(teachers.router)
app.include_router(courses.router)
app.include_router(students.router)
app.include_router(enrollments.router)
app.include_router(assessments.router)
app.include_router(grades.router)
app.include_router(reports.router)
