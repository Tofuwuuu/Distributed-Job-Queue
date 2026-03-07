from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import engine, Base, get_async_db
from app.api.jobs import router as jobs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (for dev; use Alembic in production)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Distributed Job Queue API",
    description="Submit and track async jobs. Workers process from Redis queues.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)


@app.get("/health")
def health():
    return {"status": "ok"}
