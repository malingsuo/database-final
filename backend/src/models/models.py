from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import BIT, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from src.core.database import Base


class Bit8AsInt(TypeDecorator):
    """Store BIT(8) in PostgreSQL; expose as int in Python."""

    impl = BIT(8)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return format(int(value), '08b')

    def process_result_value(self, value, dialect):
        if value is None:
            return 0
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            return int(value, 2)
        # Fallback: psycopg2 Bits object has .tobytes()
        try:
            return int.from_bytes(value.tobytes(), "big")
        except Exception:
            return int(str(value), 2)


class Account(Base):
    __tablename__ = "account"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("student", "admin", name="user_role_enum", create_type=False),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    student: Mapped[Student | None] = relationship(
        "Student", back_populates="account", uselist=False
    )
    administrator: Mapped[Administrator | None] = relationship(
        "Administrator", back_populates="account", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Account {self.email} ({self.role})>"


class Department(Base):
    __tablename__ = "department"

    id: Mapped[str] = mapped_column(String(10), primary_key=True)
    college: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    def __repr__(self) -> str:
        return f"<Department {self.id} {self.name}>"


class Administrator(Base):
    __tablename__ = "administrator"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("account.id", ondelete="CASCADE"),
        primary_key=True,
    )
    department_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("department.id"), nullable=False
    )

    account: Mapped[Account] = relationship("Account", back_populates="administrator")
    department: Mapped[Department] = relationship("Department")

    def __repr__(self) -> str:
        return f"<Administrator {self.id} dept={self.department_id}>"


class Student(Base):
    __tablename__ = "student"

    student_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("account.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    name: Mapped[str | None] = mapped_column(String(50), default=None)
    admission_year: Mapped[int] = mapped_column(Integer, nullable=False)
    advisor_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="on_track", default="on_track"
    )
    advisor_notes: Mapped[str | None] = mapped_column(String(500), default=None)

    account: Mapped[Account] = relationship("Account", back_populates="student")
    enrollments: Mapped[list[Enrollment]] = relationship(
        "Enrollment", back_populates="student", cascade="all, delete-orphan"
    )
    fields_of_study: Mapped[list[FieldOfStudy]] = relationship(
        "FieldOfStudy", back_populates="student", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Student {self.student_id} {self.name}>"


class Course(Base):
    __tablename__ = "course"

    course_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    year: Mapped[str] = mapped_column(String(10), primary_key=True)
    semester: Mapped[str] = mapped_column(String(5), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    credits: Mapped[float] = mapped_column(
        Float, nullable=False, default=0
    )
    type: Mapped[str | None] = mapped_column(String(20), default=None)
    ge_label: Mapped[int] = mapped_column(
        Bit8AsInt, nullable=False, default=0
    )
    department_id: Mapped[str | None] = mapped_column(
        String(10), ForeignKey("department.id"), default=None
    )

    department: Mapped[Department | None] = relationship("Department")

    def __repr__(self) -> str:
        return f"<Course {self.course_code} {self.name}>"


class Enrollment(Base):
    __tablename__ = "enrollment"
    __table_args__ = (
        ForeignKeyConstraint(
            ["course_code", "year", "semester"],
            ["course.course_code", "course.year", "course.semester"],
        ),
    )

    student_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("student.student_id", ondelete="CASCADE"), primary_key=True
    )
    course_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    year: Mapped[str] = mapped_column(String(10), primary_key=True)
    semester: Mapped[str] = mapped_column(String(5), primary_key=True)
    grade: Mapped[str | None] = mapped_column(String(20), default=None)
    is_passed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    required_or_elective: Mapped[str | None] = mapped_column(
        String(10), default=None
    )
    remark: Mapped[str | None] = mapped_column(String(50), default=None)

    student: Mapped[Student] = relationship("Student", back_populates="enrollments")
    course: Mapped[Course] = relationship("Course")

    @property
    def course_name(self) -> str:
        return self.course.name if self.course else ""

    @property
    def credit(self) -> float:
        return float(self.course.credits) if self.course else 0.0

    @property
    def score(self) -> str | None:
        return self.grade

    @property
    def academic_year_semester(self) -> str:
        return f"{self.year}{self.semester}"

    @property
    def is_in_progress(self) -> bool:
        if not self.grade:
            return True
        s = str(self.grade).strip()
        return s in ("成績未到或無成績", "")

    @property
    def is_passed_prop(self) -> bool:
        if not self.grade:
            return False
        s = str(self.grade).strip()
        if s == "通過":
            return True
        if s in ("成績未到或無成績", ""):
            return False
        try:
            return float(s) >= 60
        except ValueError:
            return False

    def __repr__(self) -> str:
        return f"<Enrollment {self.student_id} {self.course_code}>"


class FieldOfStudy(Base):
    __tablename__ = "fields_of_study"

    student_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("student.student_id", ondelete="CASCADE"), primary_key=True
    )
    department_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("department.id"), primary_key=True
    )
    program_type: Mapped[str] = mapped_column(
        Enum("主修", "雙主修", "輔系", name="program_type_enum", create_type=False),
        primary_key=True,
    )
    enrollment_year: Mapped[int | None] = mapped_column(Integer, default=None)

    student: Mapped[Student] = relationship("Student", back_populates="fields_of_study")
    department: Mapped[Department] = relationship("Department")

    def __repr__(self) -> str:
        return f"<FieldOfStudy {self.student_id} {self.department_id} ({self.program_type})>"

def create_all_tables(engine) -> None:
    Base.metadata.create_all(engine)


def drop_all_tables(engine) -> None:
    Base.metadata.drop_all(engine)
