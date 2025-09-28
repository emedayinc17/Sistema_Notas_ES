/* ============================================================
   SISTEMA_NOTAS — MVP (IAM + GRADES) — English version
   MySQL 8 — InnoDB — utf8mb4_0900_ai_ci
   BIGINT AUTO_INCREMENT — No cross-DB FKs (SOA)
   ============================================================ */
SET NAMES utf8mb4;
SET time_zone = '+00:00';

/* =========================
   0) DATABASES
   ========================= */
CREATE DATABASE IF NOT EXISTS sga_iam
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

CREATE DATABASE IF NOT EXISTS sga_grades
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

/* =========================
   1) IAM (users, roles, guardians)
   ========================= */
USE sga_iam;

CREATE TABLE IF NOT EXISTS rol (
  id        BIGINT PRIMARY KEY AUTO_INCREMENT,
  nombre      ENUM('DOCENTE','PADRE','DIRECTIVO') NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS usuario (
  id            BIGINT PRIMARY KEY AUTO_INCREMENT,
  usuario      VARCHAR(80)  NOT NULL UNIQUE,
  hash_contrasena VARCHAR(255) NOT NULL,            -- MVP: SHA2; future: bcrypt/argon2
  correo         VARCHAR(150) NULL,
  estado        TINYINT NOT NULL DEFAULT 1,       -- 1=active, 0=inactive
  eliminado       TINYINT(1) NOT NULL DEFAULT 0,
  creado_en    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en    TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_user_status (estado),
  INDEX idx_user_email (correo)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS usuario_rol (
  user_id BIGINT NOT NULL,
  role_id BIGINT NOT NULL,
  PRIMARY KEY (user_id, role_id),
  CONSTRAINT fk_user_role_user FOREIGN KEY (user_id) REFERENCES usuario(id),
  CONSTRAINT fk_user_role_role FOREIGN KEY (role_id) REFERENCES rol(id)
) ENGINE=InnoDB;

-- Guardian (PADRE) logically linked to sga_grades.estudiante.id
CREATE TABLE IF NOT EXISTS apoderado (
  id             BIGINT PRIMARY KEY AUTO_INCREMENT,
  usuario_padre_id BIGINT NOT NULL,     -- sga_iam.usuario.id with PADRE rol
  estudiante_id     BIGINT NOT NULL,     -- sga_grades.estudiante.id (NO cross-db FK)
  creado_en     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_guardian (usuario_padre_id, estudiante_id),
  INDEX idx_guardian_parent (usuario_padre_id),
  INDEX idx_guardian_student (estudiante_id),
  CONSTRAINT fk_guardian_parent FOREIGN KEY (usuario_padre_id) REFERENCES usuario(id)
) ENGINE=InnoDB;

/* Seeds (roles + 3 demo users using SHA2 for MVP) */
INSERT INTO rol (nombre) VALUES ('DOCENTE'), ('PADRE'), ('DIRECTIVO')
ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);

INSERT INTO usuario (usuario, hash_contrasena, correo, estado)
VALUES
  ('admin',    SHA2('Admin#2025', 256),   'admin@sga.local',    1),
  ('docente1', SHA2('Docente#2025', 256), 'docente1@sga.local', 1),
  ('padre1',   SHA2('Padre#2025',  256),  'padre1@sga.local',   1)
ON DUPLICATE KEY UPDATE correo=VALUES(correo), estado=VALUES(estado);

INSERT INTO usuario_rol (user_id, role_id)
SELECT u.id, r.id FROM usuario u JOIN rol r ON u.usuario='admin' AND r.nombre='DIRECTIVO'
ON DUPLICATE KEY UPDATE user_id=user_id;

INSERT INTO usuario_rol (user_id, role_id)
SELECT u.id, r.id FROM usuario u JOIN rol r ON u.usuario='docente1' AND r.nombre='DOCENTE'
ON DUPLICATE KEY UPDATE user_id=user_id;

INSERT INTO usuario_rol (user_id, role_id)
SELECT u.id, r.id FROM usuario u JOIN rol r ON u.usuario='padre1' AND r.nombre='PADRE'
ON DUPLICATE KEY UPDATE user_id=user_id;

/* =========================
   2) GRADES (academic)
   ========================= */
USE sga_grades;

CREATE TABLE IF NOT EXISTS docente (
  id          BIGINT PRIMARY KEY AUTO_INCREMENT,
  usuario_iam_id BIGINT NOT NULL,                 -- sga_iam.usuario.id (logical)
  nombre_completo   VARCHAR(120) NOT NULL,
  estado      TINYINT NOT NULL DEFAULT 1,
  eliminado     TINYINT(1) NOT NULL DEFAULT 0,
  creado_en  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en  TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_teacher_user (usuario_iam_id),
  INDEX idx_teacher_status (estado),
  INDEX idx_teacher_name (nombre_completo)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS estudiante (
  id         BIGINT PRIMARY KEY AUTO_INCREMENT,
  codigo       VARCHAR(40) UNIQUE,
  nombre_completo  VARCHAR(120) NOT NULL,
  estado     TINYINT NOT NULL DEFAULT 1,
  eliminado    TINYINT(1) NOT NULL DEFAULT 0,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_student_name (nombre_completo),
  INDEX idx_student_status (estado)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS curso (
  id          BIGINT PRIMARY KEY AUTO_INCREMENT,
  nombre        VARCHAR(120) NOT NULL,
  grado VARCHAR(20)  NULL,
  seccion     VARCHAR(10)  NULL,
  docente_id  BIGINT NOT NULL,                 -- responsible docente (required)
  estado      TINYINT NOT NULL DEFAULT 1,
  eliminado     TINYINT(1) NOT NULL DEFAULT 0,
  creado_en  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en  TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_course_teacher FOREIGN KEY (docente_id) REFERENCES docente(id),
  INDEX idx_course_teacher (docente_id, estado),
  INDEX idx_course_name (nombre)
) ENGINE=InnoDB;

-- Enrollment ensured by backend for current year when adding a estudiante to a curso
CREATE TABLE IF NOT EXISTS matricula (
  id          BIGINT PRIMARY KEY AUTO_INCREMENT,
  estudiante_id  BIGINT NOT NULL,
  curso_id   BIGINT NOT NULL,
  anio_escolar YEAR  NOT NULL,
  creado_en  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_enrollment (estudiante_id, curso_id, anio_escolar),
  CONSTRAINT fk_enr_student FOREIGN KEY (estudiante_id) REFERENCES estudiante(id),
  CONSTRAINT fk_enr_course  FOREIGN KEY (curso_id)  REFERENCES curso(id),
  INDEX idx_enr_course_year (curso_id, anio_escolar),
  INDEX idx_enr_student (estudiante_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS evaluacion (
  id         BIGINT PRIMARY KEY AUTO_INCREMENT,
  curso_id  BIGINT NOT NULL,
  nombre       VARCHAR(80) NOT NULL,
  ponderacion     DECIMAL(5,2) NOT NULL,          -- API should validate total ≤ 100 per curso
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_assessment_course FOREIGN KEY (curso_id) REFERENCES curso(id),
  INDEX idx_ass_course (curso_id),
  INDEX idx_ass_name (nombre)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS nota (
  id             BIGINT PRIMARY KEY AUTO_INCREMENT,
  matricula_id  BIGINT NOT NULL,
  evaluacion_id  BIGINT NOT NULL,
  puntaje          DECIMAL(5,2) NULL,          -- 0..20 (allow NULL if pending)
  creado_en     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en     TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_grade (matricula_id, evaluacion_id),
  CONSTRAINT fk_grade_enrollment FOREIGN KEY (matricula_id) REFERENCES matricula(id),
  CONSTRAINT fk_grade_assessment FOREIGN KEY (evaluacion_id) REFERENCES evaluacion(id),
  INDEX idx_grade_assessment (evaluacion_id),
  INDEX idx_grade_enrollment (matricula_id)
) ENGINE=InnoDB;

/* =========================
   2.1) VIEWS (reports)
   ========================= */
CREATE OR REPLACE VIEW vw_notas_por_curso AS
SELECT
  c.id        AS curso_id,
  c.nombre      AS curso_nombre,
  c.grado,
  c.seccion,
  s.id        AS estudiante_id,
  s.codigo      AS estudiante_codigo,
  s.nombre_completo AS estudiante_nombre,
  a.id        AS evaluacion_id,
  a.nombre      AS evaluacion_nombre,
  a.ponderacion    AS evaluacion_ponderacion,
  g.puntaje     AS puntaje
FROM curso c
JOIN evaluacion a        ON a.curso_id = c.id
JOIN matricula e        ON e.curso_id = c.id
JOIN estudiante s           ON s.id       = e.estudiante_id
LEFT JOIN nota g        ON g.matricula_id = e.id AND g.evaluacion_id = a.id;

CREATE OR REPLACE VIEW vw_resumen_curso AS
SELECT
  c.id        AS curso_id,
  c.nombre      AS curso_nombre,
  s.id        AS estudiante_id,
  s.nombre_completo AS estudiante_nombre,
  ROUND(IFNULL(SUM(IFNULL(g.puntaje,0) * (a.ponderacion/100.0)), 0), 2) AS promedio_ponderado
FROM curso c
JOIN evaluacion a ON a.curso_id = c.id
JOIN matricula e ON e.curso_id = c.id
JOIN estudiante s    ON s.id        = e.estudiante_id
LEFT JOIN nota g ON g.matricula_id = e.id AND g.evaluacion_id = a.id
GROUP BY c.id, c.nombre, s.id, s.nombre_completo;

/* =========================
   2.2) MINIMAL SEEDS (demo/QA)
   ========================= */
INSERT INTO docente (usuario_iam_id, nombre_completo, estado)
SELECT iu.id, 'Prof. Docente Demo', 1
FROM sga_iam.usuario iu
WHERE iu.usuario = 'docente1'
ON DUPLICATE KEY UPDATE nombre_completo=VALUES(nombre_completo), estado=VALUES(estado);

INSERT INTO curso (nombre, grado, seccion, docente_id, estado)
SELECT 'Matematicas I', '1ro', 'A', t.id, 1
FROM docente t
WHERE t.usuario_iam_id = (SELECT id FROM sga_iam.usuario WHERE usuario='docente1' LIMIT 1)
LIMIT 1;

INSERT INTO estudiante (codigo, nombre_completo, estado)
VALUES ('STU-0001', 'Estudiante Demo 1', 1)
ON DUPLICATE KEY UPDATE nombre_completo=VALUES(nombre_completo), estado=VALUES(estado);

INSERT INTO matricula (estudiante_id, curso_id, anio_escolar)
SELECT s.id, c.id, YEAR(CURDATE())
FROM estudiante s
JOIN curso c ON c.nombre='Matematicas I' AND c.seccion='A'
WHERE s.codigo='STU-0001'
ON DUPLICATE KEY UPDATE anio_escolar=VALUES(anio_escolar);

INSERT INTO evaluacion (curso_id, nombre, ponderacion)
SELECT c.id, 'Parcial 1', 30 FROM curso c WHERE c.nombre='Matematicas I' AND c.seccion='A'
UNION ALL
SELECT c.id, 'Parcial 2', 30 FROM curso c WHERE c.nombre='Matematicas I' AND c.seccion='A'
UNION ALL
SELECT c.id, 'Final',     40 FROM curso c WHERE c.nombre='Matematicas I' AND c.seccion='A';

INSERT INTO nota (matricula_id, evaluacion_id, puntaje)
SELECT e.id, a.id, CASE a.nombre
  WHEN 'Parcial 1' THEN 15.00
  WHEN 'Parcial 2' THEN 16.50
  ELSE NULL
END
FROM matricula e
JOIN curso c  ON c.id = e.curso_id AND c.nombre='Matematicas I' AND c.seccion='A'
JOIN evaluacion a ON a.curso_id = c.id
ON DUPLICATE KEY UPDATE puntaje=VALUES(puntaje);

INSERT INTO sga_iam.apoderado (usuario_padre_id, estudiante_id)
SELECT u.id, s.id
FROM sga_iam.usuario u
JOIN estudiante s ON s.codigo='STU-0001'
WHERE u.usuario='padre1'
ON DUPLICATE KEY UPDATE usuario_padre_id=usuario_padre_id;

/* =========================
   3) APP USERS & GRANTS
   ========================= */
CREATE USER IF NOT EXISTS 'app_iam'@'%'    IDENTIFIED BY 'Iam_2025!';
CREATE USER IF NOT EXISTS 'app_grades'@'%' IDENTIFIED BY 'Grades_2025!';

ALTER USER 'app_iam'@'%' IDENTIFIED BY 'Iam_2025!';
ALTER USER 'app_grades'@'%' IDENTIFIED BY 'Grades_2025!';

GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,ALTER,INDEX ON sga_iam.*    TO 'app_iam'@'%';
GRANT SELECT,INSERT,UPDATE,DELETE,CREATE,ALTER,INDEX ON sga_grades.* TO 'app_grades'@'%';

FLUSH PRIVILEGES;

/* Quick check 
SELECT id, nombre, grado, seccion, docente_id, estado
FROM curso
WHERE docente_id = 1;*/
