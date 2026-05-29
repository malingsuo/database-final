"""
SQLAlchemy ORM models aligned with db/00-init.sql.

Static graduation/course requirements live in JSON or seeded course rows.
Student uploads are stored as student + enrollment rows.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    DECIMAL,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Account(Base):
    __tablename__ = "account"
    __table_args__ = (UniqueConstraint("email", name="uq_account_email"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum("student", "admin", name="user_role_enum"),
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


class Department(Base):
    __tablename__ = "department"

    id: Mapped[str] = mapped_column(String(10), primary_key=True)
    college: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    courses: Mapped[list[Course]] = relationship("Course", back_populates="department")
    students: Mapped[list[FieldOfStudy]] = relationship(
        "FieldOfStudy", back_populates="department"
    )
    administrator: Mapped[Administrator | None] = relationship(
        "Administrator", back_populates="department", uselist=False
    )


class Administrator(Base):
    __tablename__ = "administrator"
    __table_args__ = (UniqueConstraint("department_id", name="uq_admin_dept"),)

    id: Mapped[str] = mapped_column(
        String(36), ForeignKey("account.id", ondelete="CASCADE"), primary_key=True
    )
    department_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("department.id"), nullable=False
    )

    account: Mapped[Account] = relationship("Account", back_populates="administrator")
    department: Mapped[Department] = relationship(
        "Department", back_populates="administrator"
    )


class Student(Base):
    __tablename__ = "student"
    __table_args__ = (UniqueConstraint("user_id", name="uq_student_user"),)

    student_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("account.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(50), default=None)
    admission_year: Mapped[int] = mapped_column(Integer, nullable=False)

    account: Mapped[Account] = relationship("Account", back_populates="student")
    enrollments: Mapped[list[Enrollment]] = relationship(
        "Enrollment", back_populates="student", cascade="all, delete-orphan"
    )
    fields_of_study: Mapped[list[FieldOfStudy]] = relationship(
        "FieldOfStudy", back_populates="student", cascade="all, delete-orphan"
    )

    @property
    def id(self) -> str:
        return self.student_id

    @property
    def student_number(self) -> str:
        return self.student_id

    @property
    def chinese_name(self) -> str | None:
        return self.name

    @property
    def entry_year(self) -> int:
        return self.admission_year

    @property
    def register_major(self) -> str:
        for field in self.fields_of_study:
            if field.program_type == "主修":
                return field.department.name
        return ""

    @property
    def register_double_major(self) -> str | None:
        for field in self.fields_of_study:
            if field.program_type == "雙主修":
                return field.department.name
        return None

    @property
    def minor1(self) -> str | None:
        minors = [
            field.department.name
            for field in self.fields_of_study
            if field.program_type == "輔系"
        ]
        return minors[0] if minors else None

    @property
    def minor2(self) -> str | None:
        minors = [
            field.department.name
            for field in self.fields_of_study
            if field.program_type == "輔系"
        ]
        return minors[1] if len(minors) > 1 else None

    @property
    def courses(self) -> list[Enrollment]:
        return self.enrollments

    @property
    def total_credits(self) -> float:
        return sum(float(enrollment.credit or 0) for enrollment in self.enrollments if enrollment.is_passed)

    @property
    def graduation_credit(self) -> float:
        return 128.0

    @property
    def required_point(self) -> None:
        return None

    @property
    def group_point(self) -> None:
        return None

    def __repr__(self) -> str:
        return f"<Student {self.student_id} {self.name}>"


class Course(Base):
    __tablename__ = "course"
    __table_args__ = (
        PrimaryKeyConstraint("course_code", "year", "semester"),
        Index("idx_course_dept", "department_id"),
    )

    course_code: Mapped[str] = mapped_column(String(20), nullable=False)
    year: Mapped[str] = mapped_column(String(10), nullable=False)
    semester: Mapped[str] = mapped_column(String(5), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    credits: Mapped[float] = mapped_column(DECIMAL(4, 1), nullable=False, default=0)
    type: Mapped[str | None] = mapped_column(String(20), default=None)
    ge_label: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    department_id: Mapped[str | None] = mapped_column(
        String(10), ForeignKey("department.id"), default=None
    )

    department: Mapped[Department | None] = relationship(
        "Department", back_populates="courses"
    )
    enrollments: Mapped[list[Enrollment]] = relationship(
        "Enrollment", back_populates="course"
    )


class Enrollment(Base):
    __tablename__ = "enrollment"
    __table_args__ = (
        PrimaryKeyConstraint("student_id", "course_code", "year", "semester"),
        ForeignKeyConstraint(
            ["course_code", "year", "semester"],
            ["course.course_code", "course.year", "course.semester"],
        ),
        Index("idx_enrollment_student", "student_id"),
        Index("idx_enrollment_course", "course_code", "year", "semester"),
    )

    student_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("student.student_id", ondelete="CASCADE"), nullable=False
    )
    course_code: Mapped[str] = mapped_column(String(20), nullable=False)
    year: Mapped[str] = mapped_column(String(10), nullable=False)
    semester: Mapped[str] = mapped_column(String(5), nullable=False)
    grade: Mapped[str | None] = mapped_column(String(20), default=None)
    is_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    required_or_elective: Mapped[str | None] = mapped_column(String(10), default=None)
    remark: Mapped[str | None] = mapped_column(String(50), default=None)

    student: Mapped[Student] = relationship("Student", back_populates="enrollments")
    course: Mapped[Course] = relationship("Course", back_populates="enrollments")

    @property
    def course_name(self) -> str:
        return self.course.name

    @property
    def credit(self) -> float:
        return float(self.course.credits or 0)

    @property
    def score(self) -> str | None:
        return self.grade

    @property
    def academic_year(self) -> int:
        try:
            return int(self.year)
        except ValueError:
            return 0

    @property
    def academic_year_semester(self) -> str:
        return f"{self.year}{self.semester}"

    @property
    def is_in_progress(self) -> bool:
        if self.grade is None:
            return True
        return str(self.grade).strip() in ("", "成績未到或無成績")

    def __repr__(self) -> str:
        return f"<Enrollment {self.student_id} {self.course_code} ({self.grade})>"


class FieldOfStudy(Base):
    __tablename__ = "fields_of_study"
    __table_args__ = (PrimaryKeyConstraint("student_id", "department_id", "program_type"),)

    student_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("student.student_id", ondelete="CASCADE"), nullable=False
    )
    department_id: Mapped[str] = mapped_column(
        String(10), ForeignKey("department.id"), nullable=False
    )
    program_type: Mapped[str] = mapped_column(
        Enum("主修", "雙主修", "輔系", name="program_type_enum"), nullable=False
    )
    enrollment_year: Mapped[int | None] = mapped_column(Integer, default=None)

    student: Mapped[Student] = relationship("Student", back_populates="fields_of_study")
    department: Mapped[Department] = relationship(
        "Department", back_populates="students"
    )


User = Account
Admin = Administrator
StudentCourse = Enrollment


def create_all_tables(engine) -> None:
    Base.metadata.create_all(engine)


def drop_all_tables(engine) -> None:
    Base.metadata.drop_all(engine)
