-- =============================================================
-- NCCU 畢業學分檢核系統 - PostgreSQL 初始化 DDL
-- 執行時機：docker-compose 啟動 db container 時自動跑
-- 執行順序（依檔名）：
--   00-init.sql         ← 建表
--   01-seed-departments.sql  ← 系所種子資料
--   02-seed-courses.sql      ← 課程種子資料
-- =============================================================

-- ---------------------------------------------------------------------------
-- Extensions
-- ---------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------------------------------------------------------------------------
-- Enum types
-- ---------------------------------------------------------------------------
DO $$ BEGIN
  CREATE TYPE user_role_enum AS ENUM ('student', 'admin');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE program_type_enum AS ENUM ('主修', '雙主修', '輔系');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- =============================================================
-- account：帳號（學生 / 管理員共用）
-- PK: uuid（auth service 生成，放進 JWT）
-- =============================================================
CREATE TABLE IF NOT EXISTS account (
    id            UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    email         VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          user_role_enum NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_account_email UNIQUE (email)
);

-- =============================================================
-- department：系所
-- PK: id = 系所代碼（如 "703"、"303"），天然唯一
-- =============================================================
CREATE TABLE IF NOT EXISTS department (
    id      VARCHAR(10)  PRIMARY KEY,
    college VARCHAR(100) NOT NULL,
    name    VARCHAR(100) NOT NULL
);

-- =============================================================
-- administrator：管理員（1:1 account，綁定一個系所）
-- =============================================================
CREATE TABLE IF NOT EXISTS administrator (
    id            UUID        PRIMARY KEY REFERENCES account(id) ON DELETE CASCADE,
    department_id VARCHAR(10) NOT NULL REFERENCES department(id),
    CONSTRAINT uq_admin_dept UNIQUE (department_id)
);

-- =============================================================
-- student：學生基本資料（1:1 account）
-- PK: student_id = 學號（天然唯一）
-- =============================================================
CREATE TABLE IF NOT EXISTS student (
    student_id   VARCHAR(20) PRIMARY KEY,
    user_id      UUID        NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    name         VARCHAR(50),
    admission_year INTEGER   NOT NULL,
    CONSTRAINT uq_student_user UNIQUE (user_id)
);

-- =============================================================
-- course：課程總表（從全校課表預建）
-- PK: (course_code, year, semester) 複合唯一
-- =============================================================
CREATE TABLE IF NOT EXISTS course (
    course_code   VARCHAR(20)  NOT NULL,
    year          VARCHAR(10)  NOT NULL,
    semester      VARCHAR(5)   NOT NULL,
    name          VARCHAR(200) NOT NULL,
    credits       NUMERIC(4,1) NOT NULL DEFAULT 0,
    type          VARCHAR(20),
    ge_label      SMALLINT     NOT NULL DEFAULT 0,
    department_id VARCHAR(10)  REFERENCES department(id),
    PRIMARY KEY (course_code, year, semester)
);

CREATE INDEX IF NOT EXISTS idx_course_dept ON course (department_id);

-- =============================================================
-- enrollment：學生修課紀錄（M:N student × course）
-- PK: (student_id, course_code, year, semester)
-- =============================================================
CREATE TABLE IF NOT EXISTS enrollment (
    student_id    VARCHAR(20) NOT NULL REFERENCES student(student_id) ON DELETE CASCADE,
    course_code   VARCHAR(20) NOT NULL,
    year          VARCHAR(10) NOT NULL,
    semester      VARCHAR(5)  NOT NULL,
    grade         VARCHAR(20),
    is_passed     BOOLEAN     NOT NULL DEFAULT FALSE,
    required_or_elective VARCHAR(10),
    remark        VARCHAR(50),
    PRIMARY KEY (student_id, course_code, year, semester),
    FOREIGN KEY (course_code, year, semester) REFERENCES course(course_code, year, semester)
);

CREATE INDEX IF NOT EXISTS idx_enrollment_student ON enrollment (student_id);
CREATE INDEX IF NOT EXISTS idx_enrollment_course  ON enrollment (course_code, year, semester);

-- =============================================================
-- fields_of_study：學生主修/雙主修/輔系關聯（M:N student × department）
-- PK: (student_id, department_id, program_type)
-- =============================================================
CREATE TABLE IF NOT EXISTS fields_of_study (
    student_id     VARCHAR(20)       NOT NULL REFERENCES student(student_id) ON DELETE CASCADE,
    department_id  VARCHAR(10)       NOT NULL REFERENCES department(id),
    program_type   program_type_enum NOT NULL,
    enrollment_year INTEGER,
    PRIMARY KEY (student_id, department_id, program_type)
);

-- =============================================================
-- 測試用管理員帳號（密碼：admin1234，argon2 hash）
-- =============================================================
INSERT INTO account (id, email, password_hash, role)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'admin@nccu.edu.tw',
    '$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQ$RdescudvJCsgt3ub+b27Gli694kX9aDMRA31tWBmVPU',
    'admin'
) ON CONFLICT DO NOTHING;
