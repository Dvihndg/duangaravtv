from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import AuditLog, User, UserRole
from backend.app.auth import require_roles

router = APIRouter(prefix="/api/v1/audit-logs", tags=["Audit Logs"])

@router.get("")
def list_audit_logs(
    action: Optional[str] = None,
    resource: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER]))
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action.upper())
    if resource:
        query = query.filter(AuditLog.resource == resource.upper())
    return query.order_by(AuditLog.created_at.desc()).limit(limit).all()
