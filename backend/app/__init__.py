import os
import sys

# Đảm bảo thư mục gốc dự án luôn có trong sys.path dù uvicorn chạy từ thư mục gốc hay thư mục backend/
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if _root not in sys.path:
    sys.path.insert(0, _root)
