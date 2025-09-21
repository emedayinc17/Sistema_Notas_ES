from pydantic import BaseModel, Field, AliasChoices

class LoginRequest(BaseModel):
    usuario: str = Field(validation_alias=AliasChoices('usuario','username'))
    contrasena: str = Field(validation_alias=AliasChoices('contrasena','contraseña','password'))

class LoginResponse(BaseModel):
    token: str
    roles: list[str]
    usuario: dict