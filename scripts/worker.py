"""
Worker CLI Runner script.
Starts the background investigation worker process from repo root.
"""

import sys
from pathlib import Path

# Add backend/src to python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from recursive_osint.tasks.worker import main

if __name__ == "__main__":
    main()
