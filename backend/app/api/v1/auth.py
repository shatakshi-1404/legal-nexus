from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import Membership, Organization, User
from app.db.session import get_db
from app.schemas.api import LoginIn, RegisterIn, TokenOut
from app.services.audit import audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Email already registered")
    org = Organization(name=f"{body.full_name or email}'s workspace")
    db.add(org)
    db.flush()
    role = "admin" if email in [e.lower() for e in get_settings().admin_emails] else "user"
    user = User(email=email, password_hash=hash_password(body.password), full_name=body.full_name,
                org_id=org.id, role=role)
    db.add(user)
    db.flush()
    db.add(Membership(user_id=user.id, org_id=org.id, role="owner"))
    db.commit()
    audit(db, user.id, "register")
    return TokenOut(access_token=create_access_token(str(user.id)))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    audit(db, user.id, "login")
    return TokenOut(access_token=create_access_token(str(user.id)))
