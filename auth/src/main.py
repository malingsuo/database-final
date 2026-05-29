from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import close_engine
from .routers.auth import router as auth_router
from .routers.validate import router as validate_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Auth service started.")
    yield
    await close_engine()
    print("Database engine disposed.")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(validate_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
