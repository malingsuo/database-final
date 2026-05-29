import os
import uuid
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, ConfigDict

# --- Configuration (DB connection commented out for prototype) ---
# DB_HOST = os.getenv("DB_HOST")
# DB_PORT = os.getenv("DB_PORT", "5432")
# DB_USER = os.getenv("DB_USER")
# DB_PASSWORD = os.getenv("DB_PASSWORD")
# DB_NAME = os.getenv("DB_NAME")
# DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- Dummy data ---
DUMMY_USER_UUID = "00000000-0000-0000-0000-000000000001"
DUMMY_TOKEN = "dummy-token-for-prototype"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# --- Pydantic Models ---
class UserBase(BaseModel):
    email: str
    phone_number: str
    name: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    uuid: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # DB pool creation commented out for prototype
    # pool = await asyncpg.create_pool(DATABASE_URL)
    print("Skipping DB pool for prototype.")
    yield
    # if pool:
    #     await pool.close()


# --- Main Application Instance ---
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- API Endpoints ---

@app.post("/api/auth/login", response_model=Token)
async def login_for_access_token(body: LoginRequest):
    return {"access_token": DUMMY_TOKEN}


@app.post("/api/auth/logout")
async def logout():
    return {"message": "Successfully logged out"}


@app.get("/auth/validate")
async def validate_token_for_nginx(token: str = Depends(oauth2_scheme)):
    # Always valid for prototype
    return JSONResponse(
        content={"status": "ok"},
        headers={"X-User-ID": DUMMY_USER_UUID, "X-Email": "dummy@example.com"},
    )


@app.post("/api/auth/register", response_model=User)
async def register_user(user_data: UserCreate):
    return User(
        uuid=uuid.UUID(DUMMY_USER_UUID),
        email=user_data.email,
        phone_number=user_data.phone_number,
        name=user_data.name,
    )


@app.delete("/api/auth/user/{user_uuid}")
async def delete_user(user_uuid: uuid.UUID):
    return {"message": "User account deleted successfully."}


@app.get("/api/auth/status", response_model=User)
async def read_users_me(token: str = Depends(oauth2_scheme)):
    return User(
        uuid=uuid.UUID(DUMMY_USER_UUID),
        email="dummy@example.com",
        phone_number="0000000000",
        name="Dummy User",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
