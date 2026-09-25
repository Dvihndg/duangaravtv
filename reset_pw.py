import sys
import os

# Add root directory to sys.path so 'backend' can be imported
sys.path.insert(0, os.path.abspath('.'))

from backend.app.database import SessionLocal
from backend.app.models import User
from backend.app.auth import get_password_hash

new_password = os.getenv("RESET_ADMIN_PASSWORD", "").strip()
if not new_password:
    raise SystemExit("Set RESET_ADMIN_PASSWORD before resetting the admin password.")
db = SessionLocal()
admin = db.query(User).filter(User.username == 'admin').first()
if admin:
    admin.hashed_password = get_password_hash(new_password)
    db.commit()
    print('Admin password reset successfully.')
else:
    print('Admin user not found')
