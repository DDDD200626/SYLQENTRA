"""IntelliJ entrypoint.

The FastAPI application lives in backend/app/main.py.
This file keeps the existing project run configuration pointed at the repository root.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.main import app  # noqa: E402

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
