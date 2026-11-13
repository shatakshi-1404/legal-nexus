import json
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_stream_user
from app.db.models import AgentRun, Analysis, Risk, User
from app.db.repositories.access import get_owned_analysis, get_owned_document
from app.db.session import SessionLocal, get_db
from app.schemas.api import AgentRunOut, RiskOut
from app.services.audit import audit
from app.workers.celery_app import run_analysis_task

router = APIRouter(prefix="/analysis", tags=["analysis"])
TERMINAL = {"completed", "failed", "awaiting_approval"}


@router.post("/{document_id}/start", status_code=202)
def start(document_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """NOTE: here {id} is a DOCUMENT id; all other routes take an ANALYSIS id."""
    doc = get_owned_document(db, user, document_id)
    if doc.status != "ready":
        raise HTTPException(409, f"Document is not ready (status: {doc.status})")
    a = Analysis(document_id=doc.id, owner_id=user.id)
    db.add(a)
    db.commit()
    audit(db, user.id, "analysis.start", str(a.id))
    run_analysis_task.delay(str(a.id))
    return {"analysis_id": str(a.id), "status": a.status}


@router.get("/{analysis_id}")
def get_analysis(analysis_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = get_owned_analysis(db, user, analysis_id)
    return {"id": str(a.id), "document_id": str(a.document_id), "status": a.status,
            "error": a.error, "report": a.report}


@router.get("/{analysis_id}/agents", response_model=list[AgentRunOut])
def agents(analysis_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = get_owned_analysis(db, user, analysis_id)
    return db.scalars(select(AgentRun).where(AgentRun.analysis_id == a.id).order_by(AgentRun.started_at)).all()


@router.get("/{analysis_id}/risks", response_model=list[RiskOut])
def risks(analysis_id: str, include_rejected: bool = False, db: Session = Depends(get_db),
          user: User = Depends(get_current_user)):
    a = get_owned_analysis(db, user, analysis_id)
    q = select(Risk).where(Risk.analysis_id == a.id)
    if not include_rejected:
        q = q.where(Risk.status != "rejected")
    return db.scalars(q.order_by(Risk.finding_id)).all()


@router.post("/{analysis_id}/approve", status_code=202)
def approve(analysis_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Human-in-the-loop: resume the paused workflow so the report is finalized."""
    a = get_owned_analysis(db, user, analysis_id)
    if a.status != "awaiting_approval":
        raise HTTPException(409, "Analysis is not awaiting approval")
    audit(db, user.id, "analysis.approve", analysis_id)
    run_analysis_task.delay(analysis_id, True)
    return {"status": "resuming"}


@router.post("/{analysis_id}/resume", status_code=202)
def resume(analysis_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Resume an interrupted/failed workflow from its last checkpoint."""
    a = get_owned_analysis(db, user, analysis_id)
    if a.status not in ("failed", "running"):
        raise HTTPException(409, "Nothing to resume")
    audit(db, user.id, "analysis.resume", analysis_id)
    run_analysis_task.delay(analysis_id, True)
    return {"status": "resuming"}


@router.get("/{analysis_id}/stream")
def stream(analysis_id: str, user: User = Depends(get_stream_user)):
    with SessionLocal() as db:
        a = get_owned_analysis(db, user, analysis_id)
        aid = a.id

    def events():
        seen: dict = {}
        while True:
            with SessionLocal() as s:
                runs = s.scalars(select(AgentRun).where(AgentRun.analysis_id == aid)
                                 .order_by(AgentRun.started_at)).all()
                status = s.get(Analysis, aid).status
                for r in runs:
                    sig = (r.status, r.duration_ms)
                    if seen.get(r.id) != sig:
                        seen[r.id] = sig
                        yield f"data: {json.dumps(AgentRunOut.model_validate(r).model_dump(mode='json'))}\n\n"
            if status in TERMINAL:
                yield f"event: done\ndata: {json.dumps({'status': status})}\n\n"
                return
            time.sleep(1)

    return StreamingResponse(events(), media_type="text/event-stream")
