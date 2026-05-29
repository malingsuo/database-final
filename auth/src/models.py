from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AccountInfo(BaseModel):
    id: int
    email: str

    model_config = ConfigDict(from_attributes=True)
    model_config = ConfigDict(from_attributes=True)
