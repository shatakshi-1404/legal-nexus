from sqlalchemy.orm import Session

from app.db.models import AuditLog


def audit(db: Session, user_id, action: str, resource: str = "", **detail):
    db.add(AuditLog(user_id=user_id, action=action, resource=resource, detail=detail))
    db.commit()
