import json
from datetime import datetime
from typing import Any, Dict
from sqlalchemy.orm import Session
from backend.app.models import AuditLog

class AuditService:
    """
    Dịch vụ Ghi Nhật Ký Kiểm Toán An Ninh (Audit Log Service).
    Ghi nhận mọi thao tác quan trọng: Đăng nhập, Tạo/Sửa/Xóa, Chuyển trạng thái, Xuất kho, Thanh toán.
    """

    @staticmethod
    def log_event(
        db: Session,
        action: str,
        resource: str,
        resource_id: str = None,
        user_id: int = None,
        ip_address: str = None,
        metadata: Dict[str, Any] = None
    ) -> AuditLog:
        try:
            log_entry = AuditLog(
                user_id=user_id,
                action=action.upper(),
                resource=resource.upper(),
                resource_id=str(resource_id) if resource_id is not None else None,
                ip_address=ip_address,
                metadata_json=json.dumps(metadata, default=str, ensure_ascii=False) if metadata else None,
                created_at=datetime.utcnow()
            )
            db.add(log_entry)
            db.commit()
            return log_entry
        except Exception as e:
            # Audit log failure should never crash the main transaction
            print(f"[AuditLog Warning] Failed to log event: {e}")
            db.rollback()
            return None
