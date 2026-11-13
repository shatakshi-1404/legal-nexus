from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import User
from app.db.repositories.access import get_owned_analysis
from app.db.session import get_db
from app.services.report import report_markdown

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{analysis_id}")
def get_report(analysis_id: str, format: str = "json", db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    a = get_owned_analysis(db, user, analysis_id)
    if not a.report:
        raise HTTPException(409, f"Report not available (status: {a.status})")
    if format == "md":
        return PlainTextResponse(report_markdown(a.report), media_type="text/markdown")
    return a.report
