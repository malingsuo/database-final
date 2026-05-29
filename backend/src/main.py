import os

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware

from src.api.router import router
from src.core.exceptions import AppException, app_exception_handler, unhandled_exception_handler

app = FastAPI(title="NCCU 畢業學分檢核系統")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(router, prefix="/api")


@app.get("/api/test")
async def test_api(
    x_user_id: str | None = Header(None, alias="X-User-Id"),
):
    return {"status": "ok", "user_id": x_user_id}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
