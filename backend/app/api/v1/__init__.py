from fastapi import APIRouter

from app.api.v1 import analysis, auth, chat, documents, feedback, knowledge, reports

api_router = APIRouter(prefix="/api/v1")
for m in (auth, documents, analysis, chat, reports, feedback, knowledge):
    api_router.include_router(m.router)
