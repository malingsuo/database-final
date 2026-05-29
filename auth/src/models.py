import uuid

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    email: str
    password: str


class StudentRegisterRequest(BaseModel):
    email: str
    password: str
    student_id: str
    name: str | None = None
    admission_year: int


class AdminRegisterRequest(BaseModel):
    email: str
    password: str
    department_id: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class AccountInfo(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    student_number: str | None = None
    name: str | None = None
    admission_year: int | None = None
    administrator_id: uuid.UUID | None = None
    department_id: str | None = None
    department_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
