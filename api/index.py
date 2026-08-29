import os
import sys

# Append project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.app.main import app
