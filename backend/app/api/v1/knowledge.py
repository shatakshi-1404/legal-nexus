from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.models import User
from app.db.session import get_db
from app.schemas.api import LegalSourceIn
from app.services.audit import audit
from app.services.knowledge import ingest_legal_source

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/ingest", status_code=201)
def ingest(body: LegalSourceIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    src = ingest_legal_source(db, body.model_dump(exclude={"sections"}), body.sections)
    audit(db, admin.id, "knowledge.ingest", str(src.id), title=src.title)
    return {"source_id": str(src.id), "sections": len(body.sections)}
