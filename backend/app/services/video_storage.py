import shutil
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, cast
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

    @abstractmethod
    def get_file_path(self, video_id: str) -> Optional[Path]:
        """Retrieve local file path to the video (for high-performance Range streaming)."""
        pass


class PostgresVideoStorage(VideoStorage):
    """
    Stores generated MP4 video bytes directly inside PostgreSQL as BYTEA.
    Maintains a local temporary disk cache to ensure lightning-fast streaming
    and HTTP Range requests without repetitive WAN database round-trips.
    """

    def __init__(self, db_session: Optional[Session] = None):
        self._db = db_session
        self._cache_dir = Path(tempfile.gettempdir()) / "ugc_video_cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_db(self) -> Session:
        if self._db is not None:
            return self._db
        return SessionLocal()

    def _get_cache_path(self, video_id: str) -> Path:
        return self._cache_dir / f"{video_id}.mp4"

    def save(self, video_id: str, file_path: Path) -> None:
        """Reads the MP4 file bytes, updates local cache, and persists to PostgreSQL BYTEA."""
        if not file_path.exists():
            raise FileNotFoundError(f"Video file not found at: {file_path}")

        # Update local disk cache immediately
        cache_path = self._get_cache_path(video_id)
        try:
            shutil.copyfile(file_path, cache_path)
        except Exception:
            pass

        video_bytes = file_path.read_bytes()
        should_close = self._db is None
        db = self._get_db()
        try:
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                raise ValueError(f"Video record with id {video_id} not found.")
            video.video_data = video_bytes
            video.content_type = "video/mp4"  # type: ignore[assignment]
            db.commit()
        finally:
            if should_close:
                db.close()

    def get(self, video_id: str) -> Optional[bytes]:
        """Returns the raw MP4 bytes, checking the local cache first before querying Postgres."""
        cache_path = self._get_cache_path(video_id)
        if cache_path.exists() and cache_path.stat().st_size > 0:
            return cache_path.read_bytes()

        should_close = self._db is None
        db = self._get_db()
        try:
            video = db.query(Video).filter(Video.id == video_id).first()
            if video and video.video_data:
                data = bytes(cast(bytes, video.video_data))
                try:
                    cache_path.write_bytes(data)
                except Exception:
                    pass
                return data
            return None
        finally:
            if should_close:
                db.close()

    def get_file_path(self, video_id: str) -> Optional[Path]:
        """
        Returns a local filesystem path for the video.
        If not present in local cache, fetches bytes from PostgreSQL and hydrates the cache.
        """
        cache_path = self._get_cache_path(video_id)
        if cache_path.exists() and cache_path.stat().st_size > 0:
            return cache_path

        data = self.get(video_id)
        if data and cache_path.exists() and cache_path.stat().st_size > 0:
            return cache_path
        return None

