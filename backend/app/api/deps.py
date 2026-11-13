import uuid

from fastapi import Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.models import User
from app.db.session import get_db

bearer = HTTPBearer(auto_error=False)


def _user_from_token(db: Session, token: str | None) -> User:
    uid = decode_token(token) if token else None
    user = db.get(User, uuid.UUID(uid)) if uid else None
    if not user:
        raise HTTPException(401, "Invalid or missing credentials")
    return user


def get_current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer),
                     db: Session = Depends(get_db)) -> User:
    return _user_from_token(db, creds.credentials if creds else None)


def get_stream_user(token: str = Query(...), db: Session = Depends(get_db)) -> User:
    """EventSource cannot send headers, so the SSE endpoint accepts ?token=."""
    return _user_from_token(db, token)


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(403, "Admin only")
    return user
