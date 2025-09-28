/* ============================================================
   SEEDS MASIVOS — SISTEMA_NOTAS (ES)
   Ejecutar DESPUÉS de crear tablas (tu script base)
   MySQL 8 (CTEs, ROW_NUMBER, RAND)
   ============================================================ */

/* =========================
   1) IAM
   ========================= */
USE sga_iam;

/* Asegura los 3 roles y NADA más */
INSERT INTO rol (nombre) VALUES ('DOCENTE'), ('PADRE'), ('DIRECTIVO')
ON DUPLICATE KEY UPDATE nombre = VALUES(nombre);

/* Asegura admin único (DIRECTIVO) */
INSERT INTO usuario (usuario, hash_contrasena, correo, estado)
VALUES ('admin', SHA2('Admin#2025',256), 'admin@sga.local', 1)
ON DUPLICATE KEY UPDATE correo=VALUES(correo), estado=VALUES(estado);

/* Vincula admin → DIRECTIVO */
INSERT INTO usuario_rol (user_id, role_id)
SELECT u.id, r.id
FROM usuario u
JOIN rol r ON r.nombre='DIRECTIVO'
WHERE u.usuario='admin'
ON DUPLICATE KEY UPDATE user_id=user_id;

/* ---------- Crea 60 DOCENTES (docente01..docente60) ---------- */
INSERT IGNORE INTO usuario (usuario, hash_contrasena, correo, estado)
WITH RECURSIVE seq(n) AS (
  SELECT 1
  UNION ALL
  SELECT n+1 FROM seq WHERE n < 60
)
SELECT CONCAT('docente', LPAD(n,2,'0')),
       SHA2('Docente#2025',256),
       CONCAT('docente', LPAD(n,2,'0'), '@sga.local'),
       1
FROM seq;


/* ---------- Crea 120 PADRES (padre001..padre120) ---------- */
INSERT IGNORE INTO usuario (usuario, hash_contrasena, correo, estado)
WITH RECURSIVE seq(n) AS (
  SELECT 1
  UNION ALL
  SELECT n+1 FROM seq WHERE n < 120
)
SELECT CONCAT('padre', LPAD(n,3,'0')),
       SHA2('Padre#2025',256),
       CONCAT('padre', LPAD(n,3,'0'), '@sga.local'),
       1
FROM seq;

/* =========================
   2) GRADES
   ========================= */
USE sga_grades;

/* ---------- 60 DOCENTES (uno por usuario_iam docenteXX) ---------- */
INSERT INTO docente (usuario_iam_id, nombre_completo, estado)
SELECT iu.id, CONCAT('Prof. ', UPPER(iu.usuario)), 1
FROM sga_iam.usuario iu
WHERE iu.usuario LIKE 'docente%'
ON DUPLICATE KEY UPDATE nombre_completo = VALUES(nombre_completo), estado=VALUES(estado);

/* ---------- 200 ESTUDIANTES ---------- */
INSERT IGNORE INTO estudiante (codigo, nombre_completo, estado)
WITH RECURSIVE seq(n) AS (
  SELECT 1
  UNION ALL
  SELECT n+1 FROM seq WHERE n < 200
)
SELECT CONCAT('STU-', LPAD(n,4,'0')),
       CONCAT('Estudiante ', LPAD(n,4,'0')),
       1
FROM seq;


/* ---------- 60 CURSOS (repartidos entre docentes) ---------- */
INSERT INTO curso (nombre, grado, seccion, docente_id, estado, eliminado, creado_en)
WITH RECURSIVE
seq(n) AS (
  SELECT 1
  UNION ALL
  SELECT n+1 FROM seq WHERE n < 60
),
d AS (
  SELECT id,
         ROW_NUMBER() OVER (ORDER BY id) AS rn,
         COUNT(*)     OVER ()            AS total
  FROM docente
)
SELECT CONCAT('Curso ', LPAD(s.n,2,'0'))                           AS nombre,
       CONCAT(FLOOR(1 + (s.n-1) % 6), 'ro')                        AS grado,      -- 1ro..6ro
       CHAR(64 + 1 + ((s.n-1) % 3))                                AS seccion,    -- A/B/C
       (SELECT id FROM d WHERE rn = ((s.n-1) % d.total) + 1)       AS docente_id,
       1                                                           AS estado,
       0                                                           AS eliminado,
       CURRENT_TIMESTAMP                                           AS creado_en
FROM seq s
ON DUPLICATE KEY UPDATE grado=VALUES(grado),
                        seccion=VALUES(seccion),
                        docente_id=VALUES(docente_id),
                        estado=VALUES(estado);

/* ---------- 200 MATRÍCULAS (200 estudiantes → cursos en round-robin, año actual) ---------- */
INSERT IGNORE INTO matricula (estudiante_id, curso_id, anio_escolar, creado_en)
WITH RECURSIVE
s(n) AS (
  SELECT 1
  UNION ALL
  SELECT n+1 FROM s WHERE n < 200
),
st AS (
  SELECT id,
         ROW_NUMBER() OVER (ORDER BY id) AS rn,
         COUNT(*)     OVER ()            AS total
  FROM estudiante
),
c AS (
  SELECT id,
         ROW_NUMBER() OVER (ORDER BY id) AS rn,
         COUNT(*)     OVER ()            AS total
  FROM curso
)
SELECT
  (SELECT id FROM st WHERE rn = s.n)                                  AS estudiante_id,
  (SELECT id FROM c  WHERE rn = ((s.n-1) % c.total) + 1)              AS curso_id,
  YEAR(CURDATE())                                                     AS anio_escolar,
  CURRENT_TIMESTAMP                                                   AS creado_en
FROM s;

/* ---------- 180 EVALUACIONES (3 por curso: 30/30/40) ---------- */
INSERT IGNORE INTO evaluacion (curso_id, nombre, ponderacion, creado_en)
SELECT c.id, 'Parcial 1', 30.00, CURRENT_TIMESTAMP FROM curso c
UNION ALL
SELECT c.id, 'Parcial 2', 30.00, CURRENT_TIMESTAMP FROM curso c
UNION ALL
SELECT c.id, 'Final',     40.00, CURRENT_TIMESTAMP FROM curso c;

/* ---------- 600 NOTAS (3 por matrícula; puntaje 10–20 con dos decimales) ---------- */
INSERT IGNORE INTO nota (matricula_id, evaluacion_id, puntaje, creado_en)
SELECT m.id AS matricula_id,
       a.id AS evaluacion_id,
       ROUND(10 + (RAND() * 10), 2) AS puntaje,
       CURRENT_TIMESTAMP
FROM matricula m
JOIN evaluacion a ON a.curso_id = m.curso_id;

/* ---------- 120 APODERADOS (cada padre asignado a un estudiante aleatorio/rr) ---------- */
USE sga_iam;
INSERT IGNORE INTO apoderado (usuario_padre_id, estudiante_id, creado_en)
WITH
p AS (
  SELECT u.id AS usuario_padre_id,
         ROW_NUMBER() OVER (ORDER BY u.id) AS rn,
         COUNT(*)     OVER ()            AS total
  FROM usuario u
  JOIN usuario_rol ur ON ur.user_id = u.id
  JOIN rol r          ON r.id = ur.role_id AND r.nombre = 'PADRE'
),
s AS (
  SELECT e.id AS estudiante_id,
         ROW_NUMBER() OVER (ORDER BY e.id) AS rn,
         COUNT(*)     OVER ()             AS total
  FROM sga_grades.estudiante e
)
SELECT
  p.usuario_padre_id,
  /* round-robin sobre estudiantes; GREATEST evita /0 si no hubiera estudiantes */
  (SELECT estudiante_id
     FROM s
    WHERE rn = ((p.rn - 1) % GREATEST(s.total, 1)) + 1),
  CURRENT_TIMESTAMP
FROM p
/* si no hay estudiantes, no insertamos nada */
WHERE (SELECT MAX(total) FROM s) IS NOT NULL;

/* ====== CHEQUEOS RÁPIDOS ====== */
SELECT COUNT(*) AS usuarios_total,
       SUM(usuario LIKE 'docente%') AS usuarios_docentes,
       SUM(usuario LIKE 'padre%')   AS usuarios_padres
FROM sga_iam.usuario;

SELECT (SELECT COUNT(*) FROM sga_grades.docente)    AS docentes,
       (SELECT COUNT(*) FROM sga_grades.estudiante) AS estudiantes,
       (SELECT COUNT(*) FROM sga_grades.curso)      AS cursos,
       (SELECT COUNT(*) FROM sga_grades.matricula)  AS matriculas,
       (SELECT COUNT(*) FROM sga_grades.evaluacion) AS evaluaciones,
       (SELECT COUNT(*) FROM sga_grades.nota)       AS notas;
