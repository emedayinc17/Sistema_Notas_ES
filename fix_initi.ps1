# (opcional) renombrar dirs con '-' a '_' para import por puntos
Set-Location services
"iam-service","cursos-service","evaluaciones-service","personas-service" | ForEach-Object {
  if (Test-Path $_) { Rename-Item $_ ($_.Replace("-", "_")) }
}
Set-Location ..

# crear __init__.py en paquetes comunes
New-Item -ItemType File -Force -Path "services\__init__.py" | Out-Null
Get-ChildItem services -Directory -Filter "*_service" | ForEach-Object {
  New-Item -ItemType File -Force -Path (Join-Path $_.FullName "__init__.py") | Out-Null
  foreach ($d in "app","app\routers","app\models","app\schemas","app\security","app\utils") {
    $p = Join-Path $_.FullName $d
    if (Test-Path $p) {
      New-Item -ItemType File -Force -Path (Join-Path $p "__init__.py") | Out-Null
    }
  }
}

# (extra) en cualquier subcarpeta con .py, crear __init__.py
Get-ChildItem services -Recurse -Directory | ForEach-Object {
  if (Get-ChildItem $_.FullName -Filter *.py -File -ErrorAction SilentlyContinue) {
    New-Item -ItemType File -Force -Path (Join-Path $_.FullName "__init__.py") | Out-Null
  }
}
