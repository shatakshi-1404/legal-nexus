from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Analysis, Document, User
from app.db.repositories.access import get_owned_document
from app.db.session import get_db
from app.schemas.api import DocumentOut
from app.services import documents as svc
from app.services.audit import audit
from app.workers.celery_app import ingest_document_task

router = APIRouter(prefix="/documents", tags=["documents"])


def _out(db: Session, d: Document) -> DocumentOut:
    out = DocumentOut.model_validate(d)
    a = db.scalar(select(Analysis).where(Analysis.document_id == d.id).order_by(Analysis.created_at.desc()))
    if a:
        out.latest_analysis_id, out.latest_analysis_status = a.id, a.status
    return out


@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload(file: UploadFile, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = svc.create_document(db, user, file.filename or "upload", await file.read())
    audit(db, user.id, "document.upload", str(doc.id), filename=doc.filename)
    ingest_document_task.delay(str(doc.id))
    db.refresh(doc)
    return _out(db, doc)


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    docs = db.scalars(select(Document).where(Document.owner_id == user.id).order_by(Document.created_at.desc()))
    return [_out(db, d) for d in docs]


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _out(db, get_owned_document(db, user, doc_id))


@router.delete("/{doc_id}", status_code=204)
def delete_document(doc_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = get_owned_document(db, user, doc_id)
    audit(db, user.id, "document.delete", doc_id)
    svc.delete_document(db, doc)
