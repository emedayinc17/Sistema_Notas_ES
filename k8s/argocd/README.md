# Sistema-Notas — Manifests (Kustomize + Vault Agent Injector)

## Estructura
```
k8s-sistema-notas/
  base/
    namespace.yaml
    serviceaccount.yaml
    services/
      iam/deploy-svc.yaml
      personas/deploy-svc.yaml
      cursos/deploy-svc.yaml
      evaluaciones/deploy-svc.yaml
    ingress/ingress.yaml
    kustomization.yaml
  overlays/
    dev/kustomization.yaml
    prod/kustomization.yaml
  infra/
    mysql/statefulset.yaml
```

## Despliegue
1) **MySQL** (una vez):
```bash
kubectl apply -f infra/mysql/statefulset.yaml
```

2) **Vault** — crea los secretos por servicio (KV v2):
Claves esperadas en cada ruta (`kv/sistema-notas/<svc>`): 
`APP_ENV, DB_HOST, DB_PORT, DB_IAM_NAME, DB_IAM_USER, DB_IAM_PASS, DB_GRADES_NAME, DB_GRADES_USER, DB_GRADES_PASS, JWT_SECRET, JWT_ALG, ACCESS_TOKEN_EXPIRE_MINUTES`.

Ejemplo:
```bash
vault kv put kv/sistema-notas/iam   APP_ENV=prod DB_HOST=mysql.sistema-notas.svc.cluster.local DB_PORT=3306   DB_IAM_NAME=sga_iam DB_IAM_USER=app_iam DB_IAM_PASS='Iam_2025!'   DB_GRADES_NAME=sga_grades DB_GRADES_USER=app_grades DB_GRADES_PASS='Grades_2025!'   JWT_SECRET='super-secret' JWT_ALG=HS256 ACCESS_TOKEN_EXPIRE_MINUTES=60

# Duplicar para los demás (puedes copiar los mismos pares clave/valor):
vault kv put kv/sistema-notas/personas     @<(vault kv get -format=json kv/sistema-notas/iam | jq -r '.data.data')
vault kv put kv/sistema-notas/cursos       @<(vault kv get -format=json kv/sistema-notas/iam | jq -r '.data.data')
vault kv put kv/sistema-notas/evaluaciones @<(vault kv get -format=json kv/sistema-notas/iam | jq -r '.data.data')
```

> Asegúrate de tener el **Vault Agent Injector** y el role `sistema-notas-role` que permita leer `kv/data/sistema-notas/*` al ServiceAccount `app-notas` del namespace `sistema-notas`.

3) **Servicios + Ingress** (Kustomize; apunta ArgoCD a `overlays/prod` o `dev`):
```bash
kubectl apply -k overlays/dev
# o
kubectl apply -k overlays/prod
```

4) **Probar** (asumiendo DNS a tu LB):
```bash
curl -i http://api-notas.emeday.inc/iam/health
curl -i http://api-notas.emeday.inc/personas/health
curl -i http://api-notas.emeday.inc/cursos/health
curl -i http://api-notas.emeday.inc/evaluaciones/health
```
