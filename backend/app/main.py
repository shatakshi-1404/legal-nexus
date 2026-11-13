from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1 import api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
import app.db.models  # noqa: F401  (register models)

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_tables:  # dev only; production uses Alembic migrations
        with engine.begin() as c:
            c.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(engine)
    yield


app = FastAPI(title="LegalNexus", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok"}
