from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.video import Video


class VideoStorage(ABC):
    """Abstract base class for video storage backend."""

    @abstractmethod
    def save(self, video_id: str, file_path: Path) -> None:
        """Save a generated video file into persistent storage."""
        pass

    @abstractmethod
    def get(self, video_id: str) -> Optional[bytes]:
        """Retrieve video binary bytes by video_id."""
        pass


class PostgresVideoStorage(VideoStorage):
    """
    Stores generated MP4 video bytes directly inside PostgreSQL as BYTEA.
    Avoids cloud storage dependencies while keeping video storage isolated.
    """

    def __init__(self, db_session: Optional[Session] = None):
        self._db = db_session

    def _get_db(self) -> Session:
        if self._db is not None:
            return self._db
        return SessionLocal()

    def save(self, video_id: str, file_path: Path) -> None:
        """Reads the MP4 file bytes and persists into PostgreSQL BYTEA column."""
        if not file_path.exists():
            raise FileNotFoundError(f"Video file not found at: {file_path}")

        video_bytes = file_path.read_bytes()
        should_close = self._db is None
        db = self._get_db()
        try:
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                raise ValueError(f"Video record with id {video_id} not found.")
            video.video_data = video_bytes
            video.content_type = "video/mp4"
            db.commit()
        finally:
            if should_close:
                db.close()

    def get(self, video_id: str) -> Optional[bytes]:
        """Returns the raw MP4 bytes stored in PostgreSQL."""
        should_close = self._db is None
        db = self._get_db()
        try:
            video = db.query(Video).filter(Video.id == video_id).first()
            if video and video.video_data:
                return bytes(video.video_data)
            return None
        finally:
            if should_close:
                db.close()
