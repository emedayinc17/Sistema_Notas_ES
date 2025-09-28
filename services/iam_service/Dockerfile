FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Paquetes base (gcc para bcrypt, libmariadb/mysql headers, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiamos shared + solo el servicio
COPY libs/shared /app/libs/shared
COPY services/iam_service /app/service

# Reqs mínimos (si ya tienes uno en el svc, úsalo)
COPY services/iam_service/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

WORKDIR /app/service
EXPOSE 8000

# Uvicorn detrás de Ingress
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
