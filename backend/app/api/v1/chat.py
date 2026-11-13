from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import User
from app.db.repositories.access import get_owned_document
from app.db.session import get_db
from app.schemas.api import ChatIn
from app.services import chat as chat_svc

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
def chat(body: ChatIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.document_id:
        get_owned_document(db, user, str(body.document_id))  # ownership check
    return chat_svc.answer(db, user, body.question, body.document_id, body.include_legal, body.conversation_id)
