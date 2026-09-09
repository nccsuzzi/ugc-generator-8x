import shutil
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings
from app.services.groq_service import groq_service

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    # Check DB
    db_ok = False
    try:
        db.execute(text("SELECT 1;"))
        db_ok = True
    except Exception:
        pass

    # Check FFmpeg
    ffmpeg_path = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
    ffmpeg_ok = shutil.which(ffmpeg_path) is not None

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "error",
        "ffmpeg": "available" if ffmpeg_ok else "missing",
        "groq_configured": groq_service.is_available,
        "groq_model": settings.GROQ_MODEL,
    }
