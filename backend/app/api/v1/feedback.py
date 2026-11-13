from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import Feedback, User
from app.db.session import get_db
from app.schemas.api import FeedbackIn

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", status_code=201)
def submit(body: FeedbackIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.add(Feedback(user_id=user.id, **body.model_dump()))
    db.commit()
    return {"ok": True}
