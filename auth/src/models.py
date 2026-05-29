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

    model_config = ConfigDict(from_attributes=True)
