
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.deps import iam_db, get_current_user
from app.models.iam import Usuario, UsuarioRol, Rol
from app.schemas.iam import LoginRequest, LoginResponse
from app.security.jwt import sha2_hex, create_token

router = APIRouter(prefix="/api/identidad/v1", tags=['Identidad'])

@router.post("/autenticacion/iniciar-sesion", response_model=LoginResponse)
async def login(
    body: LoginRequest = None,
    request: Request = None,
    db: Session = Depends(iam_db),
):
    # Si body viene por JSON, Swagger lo documenta y lo usamos directo
    if body is not None:
        usuario = body.usuario
        contrasena = body.contrasena
    else:
        # Si no, intentamos extraer manualmente (form o claves EN)
        payload = {}
        ctype = request.headers.get("content-type", "") if request else ""
        try:
            if ctype.startswith("application/json"):
                payload = await request.json()
            elif ctype.startswith("application/x-www-form-urlencoded"):
                form = await request.form()
                payload = dict(form)
            else:
                try:
                    payload = await request.json()
                except Exception:
                    form = await request.form()
                    payload = dict(form)
        except Exception:
            raise HTTPException(status_code=422, detail="Cuerpo de solicitud inválido")

        usuario = payload.get("usuario") or payload.get("username")
        contrasena = payload.get("contrasena") or payload.get("password")
        if not usuario or not contrasena:
            raise HTTPException(status_code=422, detail="Faltan campos: usuario y/o contrasena")

    u = (
        db.query(Usuario)
          .filter(Usuario.usuario == usuario, Usuario.eliminado == 0, Usuario.estado == 1)
          .first()
    )
    if not u or u.hash_contrasena.lower() != sha2_hex(contrasena).lower():
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    roles = [
        r[0]
        for r in db.query(Rol.nombre)
                   .join(UsuarioRol, Rol.id == UsuarioRol.role_id)
                   .filter(UsuarioRol.user_id == u.id)
    ]
    token = create_token(u.id, u.usuario, roles)
    return {"token": token, "roles": roles, "usuario": {"id": u.id, "usuario": u.usuario}}

@router.get('/usuarios/yo')
def me(user=Depends(get_current_user)):
    return user

@router.get('/roles')
def list_roles(db: Session = Depends(iam_db)):
    return [r[0] for r in db.query(Rol.nombre).all()]
