"""
Vercel Serverless Function entry point for FastAPI backend.
"""

import os
import sys
from pathlib import Path

# Add backend/src directory to sys.path
backend_root = Path(__file__).resolve().parent.parent
src_dir = backend_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Ensure writable local storage directory in serverless environments
storage_root = os.getenv("STORAGE_LOCAL_ROOT", "")
if not storage_root or not (storage_root.startswith("/tmp") or storage_root.startswith("\\tmp")):
    os.environ["STORAGE_LOCAL_ROOT"] = "/tmp/storage/uploads"


from recursive_osint.main import app  # noqa: E402
