import sys
import os

# Add root directory to sys.path so 'backend' can be imported
sys.path.insert(0, os.path.abspath('.'))

from backend.app.database import SessionLocal
from backend.app.models import User
from backend.app.auth import get_password_hash

db = SessionLocal()
admin = db.query(User).filter(User.username == 'admin').first()
if admin:
    admin.hashed_password = get_password_hash('admin123')
    db.commit()
    print('Password for admin reset to admin123')
else:
    print('Admin user not found')
