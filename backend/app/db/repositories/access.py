"""Ownership-enforcing lookups. Every user-data query must go through here or filter owner_id."""
import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import Analysis, Document, User


def _uuid(v: str) -> uuid.UUID:
    try:
        return uuid.UUID(v)
    except ValueError:
        raise HTTPException(404, "Not found")


def get_owned_document(db: Session, user: User, doc_id: str) -> Document:
    d = db.get(Document, _uuid(doc_id))
    if not d or d.owner_id != user.id:
        raise HTTPException(404, "Document not found")  # 404, not 403: don't leak existence
    return d


def get_owned_analysis(db: Session, user: User, analysis_id: str) -> Analysis:
    a = db.get(Analysis, _uuid(analysis_id))
    if not a or a.owner_id != user.id:
        raise HTTPException(404, "Analysis not found")
    return a
