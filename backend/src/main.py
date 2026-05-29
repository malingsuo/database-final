import asyncio
import os
import sys
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USERNAME = os.getenv("DB_USERNAME", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "dbfinal")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/test")
async def test_api(
    x_user_id: str | None = Header(None, alias="X-User-Id"),
):
    print(f"[HTTP] test_api called by user {x_user_id}", flush=True)
    return {"status": "ok", "user_id": x_user_id}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)