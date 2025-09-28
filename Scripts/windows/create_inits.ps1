$paths = @(
  "app", "app\api",
  "app\api\iam", "app\api\iam\admin",
  "app\api\personas", "app\api\personas\admin",
  "app\api\cursos", "app\api\cursos\admin",
  "app\api\evaluaciones", "app\api\evaluaciones\admin"
)
foreach ($p in $paths) {
  $f = Join-Path $p "__init__.py"
  if (!(Test-Path $f)) { New-Item -ItemType File -Path $f -Force | Out-Null }
}
"__init__.py creados (si faltaban)."
