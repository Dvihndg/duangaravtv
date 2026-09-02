from typing import List, Optional
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Setting, User, UserRole
from backend.app.auth import require_roles, get_current_user

router = APIRouter(prefix="/api/v1/settings", tags=["System Settings"])

class SettingUpdateRequest(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

@router.get("")
def get_all_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Setting).all()

@router.post("")
def update_or_create_setting(
    req: SettingUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.MANAGER]))
):
    setting = db.query(Setting).filter(Setting.key == req.key).first()
    if setting:
        setting.value = req.value
        if req.description:
            setting.description = req.description
    else:
        setting = Setting(key=req.key, value=req.value, description=req.description)
        db.add(setting)

    db.commit()
    db.refresh(setting)
    return {"success": True, "setting": {"key": setting.key, "value": setting.value}}
