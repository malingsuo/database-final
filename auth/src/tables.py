import uuid
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "account"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    tokens = relationship("Token", back_populates="owner", cascade="all, delete-orphan")


class Token(Base):
    __tablename__ = "token"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(Integer, ForeignKey("account.id", ondelete="CASCADE"), nullable=False)
    token = Column(Text, unique=True, nullable=False)

    owner = relationship("Account", back_populates="tokens")
