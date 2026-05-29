-- =============================================================
-- NCCU 畢業學分檢核系統 - PostgreSQL 初始化 DDL
-- 執行時機：docker-compose 啟動 db container 時自動跑
-- =============================================================

-- 帳號角色 enum
DO $$ BEGIN
  CREATE TYPE user_role_enum AS ENUM ('student', 'admin');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- 課程類別 enum
DO $$ BEGIN
  CREATE TYPE req_or_elective_enum AS ENUM ('必', '群', '選');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- =============================================================
-- account：帳號（學生 / 管理員共用）
-- =============================================================
CREATE TABLE IF NOT EXISTS account (
    id              SERIAL PRIMARY KEY,
    account         VARCHAR(20)      NOT NULL,
    password_hash   VARCHAR(255)     NOT NULL,
    role            user_role_enum   NOT NULL,
    created_at      TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_account_account UNIQUE (account)
);

-- =============================================================
-- student：學生基本資料
-- =============================================================
CREATE TABLE IF NOT EXISTS student (
    id                      SERIAL PRIMARY KEY,
    user_id                 INTEGER          NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    student_number          VARCHAR(20)      NOT NULL,
    chinese_name            VARCHAR(50),
    entry_year              INTEGER          NOT NULL,
    register_major          VARCHAR(100)     NOT NULL,
    register_double_major   VARCHAR(100),
    minor1                  VARCHAR(100),
    minor2                  VARCHAR(100),
    graduation_credit       NUMERIC(5, 1),
    total_credits           NUMERIC(5, 1),
    required_point          NUMERIC(5, 1),
    group_point             NUMERIC(5, 1),
    uploaded_at             TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_student_user   UNIQUE (user_id),
    CONSTRAINT uq_student_number UNIQUE (student_number)
);

-- =============================================================
-- admin：管理員（一系一人）
-- =============================================================
CREATE TABLE IF NOT EXISTS admin (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER      NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    dept_code   VARCHAR(10)  NOT NULL,
    dept_name   VARCHAR(100) NOT NULL,
    CONSTRAINT uq_admin_user UNIQUE (user_id)
);

-- =============================================================
-- student_course：學生修課紀錄
-- =============================================================
CREATE TABLE IF NOT EXISTS student_course (
    id                      SERIAL PRIMARY KEY,
    student_id              INTEGER              NOT NULL REFERENCES student(id) ON DELETE CASCADE,
    course_code             VARCHAR(20)          NOT NULL,
    course_name             VARCHAR(200)         NOT NULL,
    credit                  NUMERIC(4, 1)        NOT NULL,
    score                   VARCHAR(20),
    required_or_elective    req_or_elective_enum NOT NULL,
    remark                  VARCHAR(50),
    academic_year           INTEGER              NOT NULL,
    semester                INTEGER              NOT NULL,
    academic_year_semester  VARCHAR(10)          NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_student_course_student ON student_course (student_id);
CREATE INDEX IF NOT EXISTS idx_student_course_code    ON student_course (course_code);

-- =============================================================
-- 測試用管理員帳號（密碼：admin1234，argon2 hash）
-- =============================================================
INSERT INTO account (account, password_hash, role)
VALUES (
    'admin',
    '$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQ$RdescudvJCsgt3ub+b27Gli694kX9aDMRA31tWBmVPU',
    'admin'
) ON CONFLICT DO NOTHING;

INSERT INTO admin (user_id, dept_code, dept_name)
SELECT id, '703', '資訊科學系'
FROM account WHERE account = 'admin'
ON CONFLICT DO NOTHING;
