"""
src/models/models.py - SQLAlchemy 2.x ORM Models

DB 只存帳號層 + 學生資料層。
畢業規定（各系課表、通識、輔系等）全部存 JSON，不進 DB。

Tables:
  account       帳號（學生 / 管理員共用）
  student        學生基本資料（1:1 account）
  admin          管理員（1:1 account，綁一個系所）
  student_course 學生修課紀錄（N:1 student）
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DECIMAL,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


# ---------------------------------------------------------------------------
# 帳號（學生 / 管理員共用）
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "account"
    __table_args__ = (UniqueConstraint("account", name="uq_account_account"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account: Mapped[str] = mapped_column(String(20), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("student", "admin", name="user_role_enum"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    student: Mapped[Student | None] = relationship(
        "Student", back_populates="user", uselist=False
    )
    admin: Mapped[Admin | None] = relationship(
        "Admin", back_populates="user", uselist=False
    )

    def __repr__(self) -> str:
        return f"<User {self.account} ({self.role})>"


# ---------------------------------------------------------------------------
# 學生基本資料
# ---------------------------------------------------------------------------
class Student(Base):
    __tablename__ = "student"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_student_user"),
        UniqueConstraint("student_number", name="uq_student_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("account.id", ondelete="CASCADE"), nullable=False
    )
    student_number: Mapped[str] = mapped_column(String(20), nullable=False)
    chinese_name: Mapped[str | None] = mapped_column(String(50), default=None)
    entry_year: Mapped[int] = mapped_column(Integer, nullable=False)
    register_major: Mapped[str] = mapped_column(String(100), nullable=False)
    register_double_major: Mapped[str | None] = mapped_column(String(100), default=None)
    minor1: Mapped[str | None] = mapped_column(String(100), default=None)
    minor2: Mapped[str | None] = mapped_column(String(100), default=None)

    graduation_credit: Mapped[float | None] = mapped_column(DECIMAL(5, 1), default=None)
    total_credits: Mapped[float | None] = mapped_column(DECIMAL(5, 1), default=None)
    required_point: Mapped[float | None] = mapped_column(DECIMAL(5, 1), default=None)
    group_point: Mapped[float | None] = mapped_column(DECIMAL(5, 1), default=None)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    user: Mapped[User] = relationship("User", back_populates="student")
    courses: Mapped[list[StudentCourse]] = relationship(
        "StudentCourse", back_populates="student", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Student {self.student_number} {self.chinese_name}>"


# ---------------------------------------------------------------------------
# 管理員（一系一人）
# ---------------------------------------------------------------------------
class Admin(Base):
    __tablename__ = "admin"
    __table_args__ = (UniqueConstraint("user_id", name="uq_admin_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("account.id", ondelete="CASCADE"), nullable=False
    )
    dept_code: Mapped[str] = mapped_column(String(10), nullable=False)
    dept_name: Mapped[str] = mapped_column(String(100), nullable=False)

    user: Mapped[User] = relationship("User", back_populates="admin")

    def __repr__(self) -> str:
        return f"<Admin {self.dept_code} {self.dept_name}>"


# ---------------------------------------------------------------------------
# 學生修課紀錄
# ---------------------------------------------------------------------------
class StudentCourse(Base):
    __tablename__ = "student_course"
    __table_args__ = (
        Index("idx_student_course_student", "student_id"),
        Index("idx_student_course_code", "course_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("student.id", ondelete="CASCADE"), nullable=False
    )
    course_code: Mapped[str] = mapped_column(String(20), nullable=False)
    course_name: Mapped[str] = mapped_column(String(200), nullable=False)
    credit: Mapped[float] = mapped_column(DECIMAL(4, 1), nullable=False)
    score: Mapped[str | None] = mapped_column(String(20), default=None)
    required_or_elective: Mapped[str] = mapped_column(
        Enum("必", "群", "選", name="req_or_elective_enum"), nullable=False
    )
    remark: Mapped[str | None] = mapped_column(String(50), default=None)

    academic_year: Mapped[int] = mapped_column(Integer, nullable=False)
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    academic_year_semester: Mapped[str] = mapped_column(String(10), nullable=False)

    student: Mapped[Student] = relationship("Student", back_populates="courses")

    @property
    def is_passed(self) -> bool:
        if not self.score:
            return False
        s = str(self.score).strip()
        if s == "透過":
            return True
        if s in ("成績未到或無成績", ""):
            return False
        try:
            return float(s) >= 60
        except ValueError:
            return False

    @property
    def is_in_progress(self) -> bool:
        if not self.score:
            return True
        s = str(self.score).strip()
        return s in ("成績未到或無成績", "")

    def __repr__(self) -> str:
        return f"<StudentCourse {self.course_code} {self.course_name} ({self.score})>"


# ---------------------------------------------------------------------------
# 建立 / 刪除所有表格的便利函式
# ---------------------------------------------------------------------------
def create_all_tables(engine) -> None:
    Base.metadata.create_all(engine)


def drop_all_tables(engine) -> None:
    Base.metadata.drop_all(engine)
