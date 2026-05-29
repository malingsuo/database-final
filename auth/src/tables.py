import uuid

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "account"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("student", "admin", name="user_role_enum", create_type=False), nullable=False)

    tokens = relationship("Token", back_populates="owner", cascade="all, delete-orphan")


class Token(Base):
    __tablename__ = "token"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("account.id", ondelete="CASCADE"), nullable=False)
    token = Column(Text, unique=True, nullable=False)

    owner = relationship("Account", back_populates="tokens")


class Student(Base):
    __tablename__ = "student"

    student_id = Column(String(20), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("account.id", ondelete="CASCADE"), unique=True, nullable=False)
    name = Column(String(50))
    admission_year = Column(Integer, nullable=False)


class Department(Base):
    __tablename__ = "department"

    id = Column(String(10), primary_key=True)
    college = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)


class Administrator(Base):
    __tablename__ = "administrator"

    id = Column(UUID(as_uuid=True), ForeignKey("account.id", ondelete="CASCADE"), primary_key=True)
    department_id = Column(String(10), ForeignKey("department.id"), nullable=False)
