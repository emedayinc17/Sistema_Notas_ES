## Instalación rápida (local)

1. **Clona el repositorio:**
   ```sh
   git clone https://github.com/emedayinc17/Sistema_Notas_ES.git
   cd Sistema_Notas_ES
   ```
2. **Crea y activa un entorno virtual:**
   ```sh
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```
3. **Instala dependencias:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Configura la base de datos:**
   - Levanta un MySQL 8 local y ejecuta `sistema_notas_es.sql` para crear y poblar las tablas.
   - Ajusta las credenciales en `api/.env` si es necesario.
5. **Ejecuta la API:**
   ```sh
   cd api
   uvicorn app.main:app --reload --env-file .env --host 0.0.0.0 --port 8000
   ```
6. **Accede a la documentación interactiva:**
   - [http://localhost:8000/docs](http://localhost:8000/docs)

## Despliegue en Kubernetes (opcional)

- Archivos en `deploy/` y `k8s/` para despliegue con Kustomize y manifiestos YAML.
- Requiere un clúster con MySQL y configuración de secretos.

## Endpoints principales
- Autenticación: `/api/identidad/v1/autenticacion/iniciar-sesion`
- Cursos, estudiantes, docentes, evaluaciones, notas, reportes: `/api/notas/v1/*`

## Notas
- El sistema soporta roles y validaciones estrictas.
- Compatible con clientes antiguos (claves en español e inglés para login).
- Código alineado con la estructura real de la base de datos.

---

¿Dudas o sugerencias? Abre un issue en el repositorio o contacta a Emerson Dayan.
