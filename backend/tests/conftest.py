"""
conftest.py
===========
Integration test fixture：使用本地 PostgreSQL (docker compose db)。

前置條件：
  cd database-final && docker compose up -d db

Test DB：dbfinal_test（獨立於開發 dbfinal，互不污染）
策略：session 層級建表一次，每個 test function 用 ROLLBACK 隔離，不留資料。
"""
from __future__ import annotations

import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# DATA_DIR → 專案根 data/ 資料夾（graduation_requirements 等 JSON）
os.environ.setdefault(
    "DATA_DIR",
    str(__import__("pathlib").Path(__file__).parent.parent.parent / "data"),
)

TEST_DB_URL = (
    f"postgresql+psycopg2://"
    f"{os.getenv('DB_USER', 'postgres')}:"
    f"{os.getenv('DB_PASSWORD', 'postgres')}@"
    f"{os.getenv('DB_HOST', '127.0.0.1')}:"
    f"{os.getenv('DB_PORT', '5432')}/dbfinal_test"
)

from src.models.models import Base  # noqa: E402


@pytest.fixture(scope="session")
def pg_engine():
    """Session 層級：建一次 schema，結束後 drop。"""
    engine = create_engine(TEST_DB_URL, pool_pre_ping=True)

    with engine.connect() as conn:
        conn.execute(text(
            "DO $$ BEGIN "
            "  CREATE TYPE user_role_enum AS ENUM ('student', 'admin'); "
            "EXCEPTION WHEN duplicate_object THEN NULL; "
            "END $$;"
        ))
        conn.execute(text(
            "DO $$ BEGIN "
            "  CREATE TYPE program_type_enum AS ENUM ('主修', '雙主修', '輔系'); "
            "EXCEPTION WHEN duplicate_object THEN NULL; "
            "END $$;"
        ))
        conn.commit()

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(pg_engine):
    """每個 test 獨立 transaction；結束後 ROLLBACK，不留資料。"""
    connection = pg_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
