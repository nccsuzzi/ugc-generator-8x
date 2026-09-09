import sys
import os
from pathlib import Path

# Add backend directory to sys.path so app.* modules can be imported
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
backend_dir = root_dir / "backend"

for path_str in [str(backend_dir), str(root_dir)]:
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

# Import the main FastAPI application
from app.main import app

# Export Mangum ASGI adapter for Lambda/Vercel serverless execution
try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except ImportError:
    handler = None

__all__ = ["app", "handler"]

