"""Ancestra Backend Server Launcher with Hot Reloading.

Run this file with Python to start the FastAPI server with auto-reload:
    python run.py
"""

import os
import sys
import uvicorn

# Ensure the backend directory is on Python's module search path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.config import settings

def main():
    """Launch Uvicorn server with auto-reload."""
    host = os.environ.get("HOST", settings.HOST)
    port = int(os.environ.get("PORT", settings.PORT))
    
    print(f"[*] Launching Ancestra Backend on http://{host}:{port}")
    print(f"[*] Interactive API Docs: http://localhost:{port}/docs")
    print(f"[*] Auto-reloader active watching: '{os.path.join(backend_dir, 'app')}'")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        reload_dirs=[os.path.join(backend_dir, "app")],
        log_level="info",
    )

if __name__ == "__main__":
    main()
